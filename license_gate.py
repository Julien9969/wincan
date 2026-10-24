"""Startup license verification for the configuration builder."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
import os
from pathlib import Path

from licence.licclient import LicenseClient, Status


LICENSE_SERVER_URL = "https://lic.trizottoserver.freeddns.org"
LICENSE_PRODUCT = "wincan"
LICENSE_PUBLIC_KEY_B64 = "H8c+g2J7HB3Uf+M+U+RGPC+sxCv9kmVVeLo8SEdhc4M="
LICENSE_CONFIG_DIR = Path(
    os.environ.get("LOCALAPPDATA")
    or os.environ.get("APPDATA")
    or Path.home() / "AppData" / "Local"
) / "Wincan"


def create_license_client() -> LicenseClient:
    client = LicenseClient(
        server_url=LICENSE_SERVER_URL,
        product=LICENSE_PRODUCT,
        public_key_b64=LICENSE_PUBLIC_KEY_B64,
        app_name="wincan",
        config_dir=LICENSE_CONFIG_DIR,
        # A server outage must not block an already configured installation.
        # Signed online denials still block access.
        fail_open=True,
    )
    legacy_dir = Path.home() / ".config" / "wincan"
    legacy_key = legacy_dir / "license.key"
    if not client.get_key() and legacy_key.is_file():
        try:
            client.set_key(legacy_key.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            pass
    return client


def _ask_for_key(parent: tk.Misc, client: LicenseClient, status: Status) -> bool:
    dialog = tk.Toplevel(parent)
    dialog.title("Activation de la licence")
    dialog.resizable(False, False)
    dialog.transient(parent)
    dialog.grab_set()

    result = {"accepted": False}
    key_var = tk.StringVar()
    status_var = tk.StringVar(
        value=f"Licence non valide : {status.reason}. Saisissez votre clé."
    )

    frame = ttk.Frame(dialog, padding=14)
    frame.pack(fill="both", expand=True)
    ttk.Label(
        frame,
        text="Une clé de licence est nécessaire pour utiliser ce logiciel.",
        wraplength=420,
    ).pack(anchor="w", pady=(0, 10))
    ttk.Label(frame, textvariable=status_var, wraplength=420).pack(anchor="w", pady=(0, 8))
    entry = ttk.Entry(frame, textvariable=key_var, width=52)
    entry.pack(fill="x")
    entry.focus_set()

    buttons = ttk.Frame(frame)
    buttons.pack(fill="x", pady=(12, 0))

    def cancel() -> None:
        dialog.destroy()

    def verify() -> None:
        key = key_var.get().strip()
        if not key:
            status_var.set("Saisissez une clé de licence.")
            return
        verify_button.configure(state="disabled")
        status_var.set("Vérification de la licence...")
        dialog.update_idletasks()
        try:
            client.set_key(key)
            checked = client.check()
        except OSError as exc:
            verify_button.configure(state="normal")
            status_var.set(f"Impossible d'enregistrer la licence : {exc}")
            return
        if checked.ok:
            result["accepted"] = True
            dialog.destroy()
        else:
            verify_button.configure(state="normal")
            status_var.set(f"Licence refusée : {checked.reason}.")

    verify_button = ttk.Button(buttons, text="Vérifier", command=verify)
    verify_button.pack(side="right")
    ttk.Button(buttons, text="Quitter", command=cancel).pack(side="right", padx=(0, 8))
    dialog.protocol("WM_DELETE_WINDOW", cancel)
    dialog.bind("<Return>", lambda _event: verify())
    dialog.bind("<Escape>", lambda _event: cancel())
    parent.wait_window(dialog)
    return result["accepted"]


def verify_startup_license(parent: tk.Misc) -> bool:
    """Check the cached license and ask for a key when activation is needed."""
    try:
        client = create_license_client()
        status = client.check()
    except Exception as exc:
        messagebox.showerror(
            "Licence indisponible",
            f"Impossible d'initialiser la vérification de licence :\n{exc}",
            parent=parent,
        )
        return False

    if status.ok:
        return True
    return _ask_for_key(parent, client, status)
