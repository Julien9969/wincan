"""
licclient.py - drop this file next to your software.

    from licclient import LicenseClient
    lic = LicenseClient(
        server_url="https://license.example.com",
        product="mysoft",
        public_key_b64="<output of `server.py init`>",
    )
    status = lic.check()           # call at startup (and periodically)
    if not status.ok:
        sys.exit(f"License problem: {status.reason}")

Behavior:
  - Server reachable and says OK      -> fresh signed token cached, access granted.
  - Server reachable and says NO      -> cache deleted, access denied (revoked, expired...).
  - Server unreachable / no network   -> cached token used if valid. With fail_open=True
    / unsigned answer (default)          (default) access is ALLOWED even if there is no
                                         valid cached token (fresh install, wiped config,
                                         clock off, machine-id changed...). Only a signed
                                         denial from the server ever blocks.
                                         fail_open=False = strict: cached token required.
Only the PUBLIC key is embedded, so tokens can be verified but not forged.
Requires: pip install cryptography
"""
import base64
import hashlib
import json
import os
import platform
import socket
import time
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


@dataclass
class Status:
    ok: bool
    reason: str          # "ok", "ok_offline", "revoked", "expired", "no_license", ...
    offline: bool = False
    expires_at: int | None = None
    grace_until: int | None = None


def _b64d(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


# Independent hosts used only to answer "does this machine have internet?"
DEFAULT_PROBES = (("1.1.1.1", 443), ("8.8.8.8", 53), ("9.9.9.9", 443))


def has_internet(probes=DEFAULT_PROBES, timeout=3) -> bool:
    for host, port in probes:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except OSError:
            continue
    return False


def machine_id() -> str:
    """Stable per-machine identifier (hashed so no raw hardware ids leave the machine)."""
    raw = ""
    for p in ("/etc/machine-id", "/var/lib/dbus/machine-id"):
        try:
            raw = Path(p).read_text().strip()
            break
        except OSError:
            continue
    if not raw:
        raw = f"{uuid.getnode()}-{platform.node()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


class LicenseClient:
    def __init__(self, server_url, product, public_key_b64, app_name=None,
                 config_dir=None, timeout=5, probes=DEFAULT_PROBES, fail_open=True):
        # fail_open=True: whenever the server can't give a trustworthy answer, access is
        # allowed. Only a signed denial from the server (revoked/expired/invalid) blocks.
        self.fail_open = fail_open
        self.probes = probes
        self.server_url = server_url.rstrip("/")
        self.product = product
        self.pub = Ed25519PublicKey.from_public_bytes(base64.b64decode(public_key_b64))
        self.timeout = timeout
        self.machine_id = machine_id()
        if config_dir:
            base = Path(config_dir)
        elif os.name == "nt":
            base = Path(
                os.environ.get("LOCALAPPDATA")
                or os.environ.get("APPDATA")
                or Path.home() / "AppData" / "Local"
            ) / (app_name or product)
        else:
            base = Path(
                os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")
            ) / (app_name or product)
        base.mkdir(parents=True, exist_ok=True)
        self.key_file = base / "license.key"
        self.token_file = base / "license.token"

    # ---- license key storage
    def set_key(self, key: str):
        normalized = key.strip()
        if not normalized:
            raise ValueError("License key cannot be empty")
        self.key_file.write_text(normalized, encoding="utf-8")
        try:
            os.chmod(self.key_file, 0o600)
        except OSError:
            pass

    def get_key(self):
        try:
            return self.key_file.read_text(encoding="utf-8").strip() or None
        except OSError:
            return None

    # ---- token verification (works offline)
    def _verify_token(self, token: str):
        try:
            body_b64, sig_b64 = token.split(".")
            body = _b64d(body_b64)
            self.pub.verify(_b64d(sig_b64), body)
            return json.loads(body)
        except (ValueError, InvalidSignature):
            return None

    def _check_cached(self) -> Status:
        try:
            token = self.token_file.read_text().strip()
        except OSError:
            return Status(False, "no_license_cached", offline=True)
        p = self._verify_token(token)
        if p is None:
            return Status(False, "bad_token", offline=True)
        if p["product"] != self.product or p["machine_id"] != self.machine_id:
            return Status(False, "token_mismatch", offline=True)
        now = time.time()
        # Guard against clock rollback: token can't have been issued in the future.
        if p["issued_at"] > now + 300:
            return Status(False, "clock_error", offline=True)
        if p["expires_at"] is not None and p["expires_at"] < now:
            return Status(False, "expired", offline=True)
        # Two tiers: no internet at all -> long grace; internet works but the
        # license server doesn't answer -> short grace (outage or deliberate block).
        if has_internet(self.probes):
            limit, reason_ok, reason_bad = (
                p.get("unreachable_grace_until"),
                "ok_server_unreachable", "server_unreachable_grace_exceeded")
        else:
            limit, reason_ok, reason_bad = (
                p["grace_until"], "ok_offline", "offline_grace_exceeded")
        if limit is not None and limit < now:
            return Status(False, reason_bad, offline=True,
                          expires_at=p["expires_at"], grace_until=limit)
        return Status(True, reason_ok, offline=True,
                      expires_at=p["expires_at"], grace_until=limit)

    # ---- online check
    def _call_server(self, key: str):
        """Returns (response_dict, None) or (None, error) when unreachable."""
        data = json.dumps({"key": key, "machine_id": self.machine_id,
                           "product": self.product}).encode()
        req = urllib.request.Request(
            self.server_url + "/v1/verify", data=data,
            headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                return json.loads(r.read()), None
        except urllib.error.HTTPError as e:
            if e.code == 403:  # may be a real denial; check() verifies the signature
                try:
                    return json.loads(e.read()), None
                except ValueError:
                    return None, e
            return None, e  # 400 / 429 / 5xx: treat as "server unavailable"
        except (urllib.error.URLError, OSError, ValueError) as e:
            return None, e

    def _unreachable(self) -> Status:
        """Server could not give a trustworthy answer (down, no network, fake server)."""
        s = self._check_cached()
        if not s.ok and self.fail_open:
            # No/invalid cached token, clock off, machine-id changed, grace or license
            # date passed... none of that may lock anyone out while the server is gone.
            return Status(True, "ok_fail_open", offline=True)
        return s

    def check(self) -> Status:
        """Verify the license: online if possible, cached token otherwise."""
        key = self.get_key()
        if not key and not self.fail_open:
            return Status(False, "no_license")
        # With fail_open and no key we still ask the server: if it is up it signs a
        # denial (user must activate); if it is down, nobody is blocked.
        resp, err = self._call_server(key or "")
        if resp is None:                      # no network / server down
            return self._unreachable()
        if not resp.get("ok"):
            # Only a denial signed by OUR server key counts. Anything else
            # (fake server, captive portal, hijacked domain) is treated as unreachable.
            proof = self._verify_token(resp.get("proof", "")) if resp.get("proof") else None
            if (proof is None or proof.get("machine_id") != self.machine_id
                    or proof.get("product") != self.product
                    or abs(time.time() - proof.get("issued_at", 0)) > 600):
                return self._unreachable()
            try:
                self.token_file.unlink()
            except OSError:
                pass
            return Status(False, proof["denied"] if key else "no_license")
        token = resp["token"]
        p = self._verify_token(token)
        if p is None:                          # wrong key / tampered response
            return Status(False, "bad_server_signature")
        self.token_file.write_text(token)
        os.chmod(self.token_file, 0o600)
        return Status(True, "ok", expires_at=p["expires_at"], grace_until=p["grace_until"])


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="License client test tool")
    ap.add_argument("--server", required=True)
    ap.add_argument("--product", required=True)
    ap.add_argument("--pubkey", required=True)
    ap.add_argument("--activate", metavar="KEY", help="store a license key first")
    a = ap.parse_args()
    c = LicenseClient(a.server, a.product, a.pubkey)
    if a.activate:
        c.set_key(a.activate)
    s = c.check()
    print(s)
    raise SystemExit(0 if s.ok else 1)
