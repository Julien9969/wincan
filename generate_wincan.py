#!/usr/bin/env python3
"""
Generate an EN 13508-2 "WinCan-style" save file (.txt) from the
Configuration Builder's source XML (Project / Tronçons).

Usage:
    python3 generate_wincan.py source.xml output.txt

Source XML shape:

<Project commune="..." adresse="..." operateur="Kais Mougeot" date="YYYY-MM-DD">
  <Troncons>
    <Troncon depart="G1" arrivee="RB1" sens_ecoulement="A"
             hauteur_diametre="200" profondeur_depart="" profondeur_arrivee=""
             emplacement="H" usage_reseau="A" type_ecoulement="A"
             etat_reseau="A" statut_reseau="A" forme="A" materiau="A"
             nom="Tronçon n° 1" curage="0"/>
    ...
  </Troncons>
</Project>

Regards de visite are NOT stored in the XML: they are derived from each
Tronçon's depart/arrivee references (in order of first appearance).

This version intentionally has NO <Commentaire> support: the
Configuration Builder only produces the pre-inspection setup data
(Project + Tronçons), not on-site observations. That is
also why fields like "heure", "video" and "reference" are not part
of the data model any more -- they are written to the file as
fixed/blank defaults purely because the TXT format still requires
the columns to be present.

------------------------------------------------------------------
FIELD MAPPING NOTES / ASSUMPTIONS
------------------------------------------------------------------
The exact EN 13508-2 letter-code table for this export profile was
not supplied. The mapping below was reverse engineered by diffing
"demo2 - 13508.txt" against "TEST (1).txt":

  Confirmed by observed variation across samples:
    AAK  -> Sens d'écoulement     (varies within demo2: B / A; "A" = the
                                   base départ→arrivée order, "B" = the
                                   reversed order -- user-selected, see
                                   prompt.txt: "Sens d'écoulement: this is
                                   the B,A or A,A after the adress field")
    AAL  -> Emplacement / Conditions (varies per Tronçon within the
            sample files: H = sous un bâtiment permanent, A = sous une
            route -- see EMPLACEMENT_CODES)
    AAQ  -> Curage réalisé      (last B01 field; A = coché, B = non coché,
            default coché -- confirmed by the user; AAQ was previously
            mistaken for the Statut du réseau)
    ABP  -> Statut du réseau     (empty in demo2/16.11, "A" in TEST)
    ACM  -> État du réseau       (Neuf/Ancien) ("B" in TEST, "A" in demo2)

  Best-effort / unverified (both samples happened to hold these
  constant, so there was no direct evidence to confirm the letter
  codes -- double-check against the real software before relying on
  this for anything important):
    ABE  -> fixed "B" (constant across every sample; the old
            "Curage -> ABE" guess was wrong -- curage lives at AAQ)
    ACJ  -> Type d'écoulement
    ACK  -> Usage du réseau   (confirmed by "USE INDURSTR" sample: D)

  Fields with no free/available column in this export profile were
  dropped from the data model entirely, per instruction:
    - "Matériel" (no unused slot found in B01-B04)
    - Emplacement is stored in AAL (was previously misread as
      "Propriété foncière" -- the EN 13508-2 location codes match
      AAL's values across the sample files)

  Fields kept but not exposed to the user (protocol/system defaults
  or not part of the new spec, always written with a fixed/blank
  value): ABA (standard version), ABC, ABL, ABM, ABR, ACC, ACE, ACF,
  ACG, AAM, AAO, AAP, ABF/ABN/ABO (reference), ABG (heure), ABS
  (video), and the whole #B04 line. ABQ (longueur) is now a user input
  exposed in the GUI (formatted as a float with two decimals).
------------------------------------------------------------------
"""
import sys
import xml.etree.ElementTree as ET

# ---------------------------------------------------------------------------
# Dropdown value lists shared with the GUI (label -> code written to TXT)
# ---------------------------------------------------------------------------

# List of (code, label) pairs -- several labels share the code "Z".
EMPLACEMENT_CODES = [
    ("A", "Sous une route"),
    ("B", "Sous un trottoir"),
    ("C", "Sous l'accotement d'une route"),
    ("D", "Dans une zone piétonnière"),
    ("E", "Dans un champ"),
    ("F", "Sous une propriété bâtie"),
    ("G", "Sous des jardins"),
    ("H", "Sous un bâtiment permanent"),
    ("I", "Sous un terrain boisé"),
    ("J", "Accès difficile"),
    ("K", "Sous une voie navigable"),
    ("Z", "Autre"),
    ("Z", "Sous une voie ferrée"),
    ("Z", "Sous un parking"),
    ("Z", "Sous un chemin en terre"),
    ("Z", "Sous une voie lourde"),
    ("Z", "Sous une voie légère"),
]
STATUT_RESEAU_CODES = {"": "Non précisé", "A": "En service", "B": "Hors service", "C": "Désaffecté"}
ETAT_RESEAU_CODES = {"A": "Neuf", "B": "Ancien"}
USAGE_RESEAU_CODES = {
    "A": "Eaux usées",
    "B": "Eaux pluviales",
    "C": "Unitaire",
    "D": "Eaux usées industrielles",
    "E": "Cours d'eau en caniveau",
    "F": "Drainage souterrain ou agricole",
    "Z": "Autre",
}
TYPE_ECOULEMENT_CODES = {
    "A": "Gravitaire",
    "B": "Conduite de relèvement",
    "C": "Tuyau d'aspiration",
}
FORME_CODES = {
    "A": "Circulaire",
    "B": "Rectangulaire",
    "C": "Ovoïde",
    "D": "En U",
    "E": "En arc",
    "F": "Ovale",
    "Z": "Autre",
}
# List of (code, label) pairs -- several labels share the code "Z", so a
# plain {code: label} dict would collapse them. The GUI treats it the same
# way (it just shows "CODE - label" and stores the code).
MATERIAU_CODES = [
    ("AA", "Amiante-ciment"),
    ("AB", "Bitume"),
    ("AC", "Fibres projetées"),
    ("AD", "Briquetage"),
    ("AE", "Grès"),
    ("AF", "Mortier de ciment"),
    ("AG", "Béton"),
    ("AH", "Béton armé"),
    ("AI", "Béton projeté"),
    ("AJ", "Segments de béton"),
    ("AK", "Fibres-ciment"),
    ("AL", "Plastiques renforcés de fibres"),
    ("AM", "Fonte"),
    ("AN", "Fonte grise"),
    ("AO", "Fonte ductile"),
    ("AP", "Acier"),
    ("AQ", "Type non identifié de fer ou d'acier"),
    ("AR", "Maçonnerie (appareillée)"),
    ("AS", "Maçonnerie (non appareillée)"),
    ("AU", "Polyester"),
    ("AV", "Polyéthylène"),
    ("AW", "Polypropylène"),
    ("AX", "PVC-U"),
    ("AY", "Type non identifié de plastique"),
    ("AZ", "Matériau non identifié"),
    ("Z", "Autre"),
    ("Z", "Fibre de verre"),
    ("Z", "Gainage"),
    ("Z", "PRV (Polyester renforcé de fibres de verre)"),
]

DEFAULT_TRONCON = {
    "emplacement": "A",
    "curage": True,
    "usage_reseau": "A",
    "type_ecoulement": "A",
    "etat_reseau": "A",
    "statut_reseau": "A",
    "forme": "A",
    "hauteur_diametre": "",
    "materiau": "AX",
    "longueur": "",
    "sens_ecoulement": "A",
    "profondeur_depart": "",
    "profondeur_arrivee": "",
    "dimension_regard": "",
    "profondeur_ouvrage": "",
    "profondeur_radier": "",
    "hauteur_total": "",
}

# ---------------------------------------------------------------------------
# Low level CSV-ish writer matching the file's own delimiter declaration
# (#A3=, field sep / #A4=. decimal sep / #A5=" quote char)
# ---------------------------------------------------------------------------

def q(value):
    """Quote a text field the way the save file does: "value" """
    return '"{}"'.format(value if value is not None else "")


def raw(value):
    """Unquoted field (numbers / single-letter codes). Empty allowed."""
    return "" if value is None else str(value)


def csv_line(fields):
    return ",".join(fields)


# ---------------------------------------------------------------------------
# Block builders
# ---------------------------------------------------------------------------

def build_b01(nom, depart, arrivee, adresse, commune, emplacement, sens_ecoulement, curage):
    lines = ["#B01=AAA,AAB,AAD,AAF,AAJ,AAK,AAL,AAM,AAN,AAO,AAP,AAQ"]
    lines.append(csv_line([
        q(nom),                    # AAA - section name/reference
        q(depart),                 # AAB - start node
        q(depart),                 # AAD - start node (repeated, as in source files)
        q(arrivee),                # AAF - end node
        q(adresse),                # AAJ - street / location (inherited from project)
        raw(sens_ecoulement),            # AAK - Sens d'écoulement (A = base départ->arrivée, B = inverse)
        raw(emplacement),          # AAL - Emplacement / Conditions
        q(""),                     # AAM - unused
        q(commune),                # AAN - Commune (inherited from project)
        q(""),                     # AAO - unused
        q(""),                     # AAP - unused
        "A" if curage else "B",    # AAQ - Curage réalisé (A = coché, B = non coché)
    ]))
    return lines


def build_b02(date, operateur, statut_reseau, longueur):
    lines = ["#B02=ABA,ABC,ABE,ABF,ABG,ABH,ABL,ABM,ABN,ABO,ABP,ABQ,ABR,ABS"]
    try:
        longueur_str = "{:.2f}".format(float(longueur))
    except (TypeError, ValueError):
        longueur_str = "0.00"
    lines.append(csv_line([
        q("EN 13508-2:2003+A1:2011"),   # ABA - standard version (fixed)
        "Z",                            # ABC - fixed
        "B",                            # ABE - fixed
        q(date),                        # ABF - inspection date (inherited)
        q("00:00"),                     # ABG - heure (not user-managed, default)
        q(operateur),                   # ABH - operator (inherited, hardcoded project-wide)
        "E",                            # ABL - fixed
        "A",                            # ABM - fixed
        q(""),                          # ABN - reference (not in new spec, blank)
        q(""),                          # ABO - reference (blank)
        raw(statut_reseau),             # ABP - Statut du réseau
        raw(longueur_str),              # ABQ - Longueur mesurée (m)
        "B",                            # ABR - fixed
        "",                             # ABS - video (empty: no quotes, as in original files)
    ]))
    return lines


def build_b03(materiau, hauteur_diametre, forme, prof_depart, prof_arrivee, usage_reseau, type_ecoulement, etat_reseau):
    lines = ["#B03=ACA,ACB,ACC,ACD,ACE,ACF,ACG,ACH,ACI,ACJ,ACK,ACM"]
    lines.append(csv_line([
        raw(forme),             # ACA - Forme
        raw(hauteur_diametre),  # ACB - Hauteur / Diamètre
        "",                     # ACC - unused
        raw(materiau),          # ACD - Matériau
        "",                     # ACE - unused
        "",                     # ACF - unused
        "3000",                 # ACG - fixed
        raw(prof_depart),       # ACH - Profondeur radier départ
        raw(prof_arrivee),      # ACI - Profondeur radier arrivée
        raw(type_ecoulement),   # ACJ - Type d'écoulement
        raw(usage_reseau),      # ACK - Usage du réseau
        raw(etat_reseau),       # ACM - État du réseau (Ancien/Neuf)
    ]))
    return lines


def build_b04():
    return ["#B04=ADA,ADB,ADC,ADE", "A,A,A,"]


# ---------------------------------------------------------------------------
# XML -> save file
# ---------------------------------------------------------------------------


def parse_source(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()

    project = {
        "commune": root.get("commune", ""),
        "adresse": root.get("adresse", ""),
        "operateur": root.get("operateur", "Kais Mougeot"),
        "date": root.get("date", ""),
    }

    troncons = []
    troncons_el = root.find("Troncons")
    if troncons_el is not None:
        for t in troncons_el.findall("Troncon"):
            entry = dict(DEFAULT_TRONCON)
            entry.update({
                "nom": t.get("nom", ""),
                "depart": t.get("depart", ""),
                "arrivee": t.get("arrivee", ""),
                "emplacement": t.get("emplacement", t.get("propriete_fonciere", DEFAULT_TRONCON["emplacement"])),
                "curage": t.get("curage", "0") in ("1", "true", "True"),
                "usage_reseau": t.get("usage_reseau", DEFAULT_TRONCON["usage_reseau"]),
                "type_ecoulement": t.get("type_ecoulement", DEFAULT_TRONCON["type_ecoulement"]),
                "etat_reseau": t.get("etat_reseau", DEFAULT_TRONCON["etat_reseau"]),
                "statut_reseau": t.get("statut_reseau", DEFAULT_TRONCON["statut_reseau"]),
                "forme": t.get("forme", DEFAULT_TRONCON["forme"]),
                "hauteur_diametre": t.get("hauteur_diametre", ""),
                "materiau": t.get("materiau", DEFAULT_TRONCON["materiau"]),
                "sens_ecoulement": t.get(
                    "sens_ecoulement",
                    t.get("direction", DEFAULT_TRONCON["sens_ecoulement"]),
                ),
                "profondeur_depart": t.get("profondeur_depart", ""),
                "profondeur_arrivee": t.get("profondeur_arrivee", ""),
                "dimension_regard": t.get("dimension_regard", ""),
                "profondeur_ouvrage": t.get("profondeur_ouvrage", ""),
                "profondeur_radier": t.get("profondeur_radier", ""),
                "hauteur_total": t.get("hauteur_total", ""),
                "longueur": t.get("longueur", DEFAULT_TRONCON["longueur"]),
            })
            troncons.append(entry)

    # Regards are not stored in the XML any more -- they are derived from
    # the Tronçons' depart/arrivee references, in order of first appearance.
    regards = []
    seen = set()
    for t in troncons:
        for key in ("depart", "arrivee"):
            name = t.get(key, "")
            if name and name not in seen:
                seen.add(name)
                regards.append(name)

    return project, regards, troncons


def build_file(project, regards, troncons):
    out = [
        "#A1=ISO-8859-1:1998",
        "#A2=fr",
        "#A3=,",
        "#A4=.",
        '#A5="',
        "#A6=2010",
    ]

    for t in troncons:
        out += build_b01(
            t["nom"], t["depart"], t["arrivee"],
            project.get("adresse", ""), project.get("commune", ""),
            t["emplacement"], t["sens_ecoulement"], t["curage"],
        )
        out += build_b02(
            project.get("date", ""), project.get("operateur", "Kais Mougeot"),
            t["statut_reseau"], t["longueur"],
        )
        out += build_b03(
            t["materiau"], t["hauteur_diametre"], t["forme"],
            t["profondeur_depart"], t["profondeur_arrivee"],
            t["usage_reseau"], t["type_ecoulement"], t["etat_reseau"],
        )
        out += build_b04()
        out.append("#Z")

    return out


def validate(regards, troncons):
    """Raise ValueError if a Tronçon references a Regard that isn't
    registered, since the TXT has no way to represent that."""
    regard_set = set(regards)
    for t in troncons:
        for key in ("depart", "arrivee"):
            if t[key] not in regard_set:
                raise ValueError(
                    f"Tronçon '{t['nom']}' référence le Regard '{t[key]}' "
                    "qui n'est pas enregistré dans la liste des Regards."
                )


def main():
    if len(sys.argv) != 3:
        print("Usage: python3 generate_wincan.py source.xml output.txt")
        sys.exit(1)

    xml_path, out_path = sys.argv[1], sys.argv[2]
    project, regards, troncons = parse_source(xml_path)
    validate(regards, troncons)
    lines = build_file(project, regards, troncons)

    with open(out_path, "w", encoding="iso-8859-1", newline="\r\n") as f:
        f.write("\n".join(lines) + "\n")

    print(f"Wrote {out_path} ({len(troncons)} tronçon(s))")


if __name__ == "__main__":
    main()
