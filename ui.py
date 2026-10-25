#!/usr/bin/env python3
"""
Configuration Builder GUI for EN13508-2 / WinCan Tronçon reports.

Lets the user fill in Project info, create/reuse Regards de visite, and
create Tronçons quickly (most fields inherited or defaulted), then either
save the project as XML or generate the .txt save file directly.

It plugs straight into generate_wincan.py's own writer functions
(build_file / parse_source), so the GUI and the command-line generator
always produce byte-identical output -- there is only one code path
that knows the save-file format.

Run:
    python3 ui.py

Requires: generate_wincan.py in the same folder.
Uses only the Python standard library (tkinter) -- nothing to install.
"""
import os
import sys
import logging
import queue
import threading
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk, filedialog, messagebox
import xml.etree.ElementTree as ET
from xml.dom import minidom

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import generate_wincan as core


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)


PROJECT_FIELDS = [
    ("commune", "Commune"),
    ("adresse", "Adresse"),
    ("date", "Date d'inspection (AAAA-MM-JJ)"),
]
# Opérateur is hardcoded per spec -- not an editable Project field.
DEFAULT_OPERATEUR = "Kais Mougeot"


def _as_pairs(codes):
    """Normalize a {code: label} dict or [(code, label), ...] list to pairs."""
    return codes.items() if isinstance(codes, dict) else codes


def _code_values(codes):
    """Turn code tables into ['CODE - label', ...] combobox values."""
    return [f"{code} - {label}" if code else f"(vide) - {label}" for code, label in _as_pairs(codes)]


def _code_to_display(codes, code):
    label = next((l for c, l in _as_pairs(codes) if c == code), "")
    return f"{code} - {label}" if code else f"(vide) - {label}"


def _display_to_code(display):
    code = display.split(" - ", 1)[0]
    return "" if code == "(vide)" else code


# Dropdown code tables, keyed by the Tronçon field they populate.
CODE_FIELD_TABLES = {
    "emplacement": core.EMPLACEMENT_CODES,
    "usage_reseau": core.USAGE_RESEAU_CODES,
    "type_ecoulement": core.TYPE_ECOULEMENT_CODES,
    "etat_reseau": core.ETAT_RESEAU_CODES,
    "statut_reseau": core.STATUT_RESEAU_CODES,
    "forme": core.FORME_CODES,
    "materiau": core.MATERIAU_CODES,
}

# Dialog layout: (category label or None for the top / uncategorised group,
# then [(key, label, kind), ...]).  kind is one of:
#   "regards"   -> combobox over existing Regards (départ/arrivée)
#   "direction" -> readonly combobox départ->arrivée / arrivée->départ
#   "code"      -> dropdown fed from CODE_FIELD_TABLES[key]
#   "bool"      -> checkbutton
#   "text"      -> plain text entry
DIALOG_SECTIONS = [
    (None, [
        ("depart", "Nœud de départ *:", "regards"),
        ("arrivee", "Nœud d'arrivée *:", "regards"),
        ("direction", "Sens d'écoulement :", "direction"),
        ("profondeur_depart", "Profondeur radier départ (m) :", "text"),
        ("profondeur_arrivee", "Profondeur radier arrivée (m) :", "text"),
        ("dimension_regard", "Dimension du regard :", "text"),
        ("profondeur_ouvrage", "Profondeur de l'ouvrage (m) :", "text"),
        ("profondeur_radier", "Profondeur du radier (m) :", "text"),
        ("hauteur_total", "Hauteur totale :", "text"),
    ]),
    ("Adresse / Situation", [
        ("emplacement", "Emplacement / Conditions :", "code"),
    ]),
    ("Conditions d'intervention", [
        ("curage", "Curage réalisé avant inspection :", "bool"),
    ]),
    ("Caractéristiques de la canalisation", [
        ("longueur", "Longueur mesurée (m) :", "text"),
        ("usage_reseau", "Usage du réseau :", "code"),
        ("type_ecoulement", "Type d'écoulement :", "code"),
        ("etat_reseau", "État du réseau (Ancien / Neuf) :", "code"),
        ("statut_reseau", "Statut du réseau :", "code"),
    ]),
    ("Caractéristiques des tuyaux", [
        ("forme", "Forme :", "code"),
        ("hauteur_diametre", "Hauteur / Diamètre (mm) :", "text"),
        ("materiau", "Matériau :", "code"),
    ]),
]

# Fixed attribute order for the <Troncon> XML elements. Regards are not
# stored in the XML -- they are derived from the Tronçons' depart/arrivee.
TRONCON_XML_ATTR_ORDER = (
    "depart", "arrivee", "direction", "hauteur_diametre",
    "profondeur_depart", "profondeur_arrivee", "emplacement",
    "usage_reseau", "type_ecoulement", "etat_reseau", "statut_reseau",
    "forme", "materiau", "longueur", "dimension_regard",
    "profondeur_ouvrage", "profondeur_radier", "hauteur_total",
    "nom", "curage",
)


class TronconDialog(tk.Toplevel):
    """Modal form to create/edit a Tronçon. Only exposes the fields the
    spec marks as editable; inherited project fields (date/operateur/
    adresse) and the auto-generated name are not shown here."""

    def __init__(self, parent, regards, initial=None):
        super().__init__(parent)
        self.title("Tronçon")
        self.resizable(False, False)
        self.result = None
        self._regards = regards
        initial = dict(core.DEFAULT_TRONCON, **(initial or {}))

        frame = ttk.Frame(self, padding=10)
        frame.grid(row=0, column=0)
        row = 0

        self._field_vars = {}  # key -> (kind, var[, codes])
        for section, fields in DIALOG_SECTIONS:
            if section is not None:
                ttk.Label(frame, text=section,
                          font=tkfont.nametofont("TkHeadingFont"),
                          foreground="#005090").grid(
                    row=row, column=0, columnspan=2, sticky="w", padx=4, pady=(10, 2))
                row += 1

            for key, label, kind in fields:
                if kind == "regards":
                    var = tk.StringVar(value=initial.get(key, ""))
                    ttk.Label(frame, text=label).grid(row=row, column=0, sticky="e", padx=4, pady=3)
                    ttk.Combobox(frame, textvariable=var, values=regards, width=30).grid(
                        row=row, column=1, sticky="w", padx=4, pady=3)
                    self._field_vars[key] = (kind, var)
                    if key == "depart":
                        self.depart_var = var
                    else:
                        self.arrivee_var = var
                elif kind == "direction":
                    ttk.Label(frame, text=label).grid(row=row, column=0, sticky="e", padx=4, pady=3)
                    var = tk.StringVar()
                    self.direction_combo = ttk.Combobox(frame, textvariable=var,
                                                        state="readonly", width=30)
                    self.direction_combo.grid(row=row, column=1, sticky="w", padx=4, pady=3)
                    self.direction_var = var
                    self._field_vars[key] = (kind, var)
                elif kind == "code":
                    codes = CODE_FIELD_TABLES[key]
                    ttk.Label(frame, text=label).grid(row=row, column=0, sticky="e", padx=4, pady=3)
                    var = tk.StringVar(value=_code_to_display(codes, initial.get(key, "")))
                    ttk.Combobox(frame, textvariable=var, values=_code_values(codes),
                                 width=30, state="readonly").grid(
                        row=row, column=1, sticky="w", padx=4, pady=3)
                    self._field_vars[key] = (kind, var, codes)
                elif kind == "bool":
                    ttk.Label(frame, text=label).grid(row=row, column=0, sticky="e", padx=4, pady=3)
                    var = tk.BooleanVar(value=bool(initial.get(key, False)))
                    ttk.Checkbutton(frame, variable=var).grid(
                        row=row, column=1, sticky="w", padx=4, pady=3)
                    self._field_vars[key] = (kind, var)
                else:  # "text"
                    ttk.Label(frame, text=label).grid(row=row, column=0, sticky="e", padx=4, pady=3)
                    var = tk.StringVar(value=str(initial.get(key, "")))
                    ttk.Entry(frame, textvariable=var, width=33).grid(
                        row=row, column=1, sticky="w", padx=4, pady=3)
                    self._field_vars[key] = (kind, var)
                row += 1

        ttk.Label(frame,
                  text="(un nom de regard non existant sera créé automatiquement)",
                  font=tkfont.nametofont("TkSmallCaptionFont")).grid(
            row=row, column=0, columnspan=2, sticky="w", padx=4)
        row += 1

        self.depart_var.trace_add("write", lambda *a: self._update_direction_options(initial))
        self.arrivee_var.trace_add("write", lambda *a: self._update_direction_options(initial))
        self._update_direction_options(initial)

        btn_frame = ttk.Frame(self, padding=(10, 0, 10, 10))
        btn_frame.grid(row=1, column=0, sticky="e")
        ttk.Button(btn_frame, text="Annuler", command=self._cancel).pack(side="right", padx=4)
        ttk.Button(btn_frame, text="OK", command=self._ok).pack(side="right", padx=4)

        self.update_idletasks()

        x = (self.winfo_screenwidth() - self.winfo_reqwidth()) // 2
        y = (self.winfo_screenheight() - self.winfo_reqheight()) // 2
        self.geometry(f"+{x}+{y}")

        self.transient(parent)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self.bind("<Escape>", lambda e: self._cancel())

    def _update_direction_options(self, initial):
        depart = self.depart_var.get().strip()
        arrivee = self.arrivee_var.get().strip()
        options = (
            [f"{depart} -> {arrivee}", f"{arrivee} -> {depart}"]
            if depart and arrivee and depart != arrivee
            else []
        )
        self.direction_combo["values"] = options
        if not options:
            self.direction_var.set("")
            return
        if self.direction_var.get() in options:
            return
        self.direction_var.set(options[1] if initial.get("direction") == "B" else options[0])

    def _ok(self):
        depart = self.depart_var.get().strip()
        arrivee = self.arrivee_var.get().strip()
        if not depart or not arrivee:
            messagebox.showerror("Champs manquants", "Nœud de départ et nœud d'arrivée sont obligatoires.", parent=self)
            return
        if depart == arrivee:
            messagebox.showerror("Erreur", "Le nœud de départ et le nœud d'arrivée doivent être différents.", parent=self)
            return

        result = {
            "direction": "B" if self.direction_var.get() == f"{arrivee} -> {depart}" else "A",
        }
        for key, (kind, var, *rest) in self._field_vars.items():
            if key == "direction":
                continue
            if kind == "bool":
                result[key] = var.get()
            elif kind == "code":
                result[key] = _display_to_code(var.get())
            else:
                result[key] = var.get().strip()

        self.result = result
        self.destroy()

    def _cancel(self):
        self.result = None
        self.destroy()


class App(tk.Tk):
    BASE_SIZE = (900, 720)
    SCALE_INIT = 1.0
    SCALE_STEP = 0.1
    SCALE_MIN = 0.8
    SCALE_MAX = 2.0
    FONT_NAMES = (
        "TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont",
        "TkCaptionFont", "TkSmallCaptionFont", "TkIconFont", "TkTooltipFont",
    )

    def __init__(self):
        super().__init__()
        self.title("Générateur de configuration - EN13508-2 / WinCan")
        self.scale = self.SCALE_INIT
        self.scale_label_var = tk.StringVar(value=f"{int(self.scale * 100)}%")
        self._font_bases = self._capture_font_bases()
        self._tree_col_width = 110

        self.project = {k: "" for k, _ in PROJECT_FIELDS}
        self.project["operateur"] = DEFAULT_OPERATEUR
        self.regards = []   # list[str], unique Regard names -- derived from Tronçons, never created manually
        self.troncons = []  # list[dict] (core.DEFAULT_TRONCON shape + nom/depart/arrivee)
        self.debug_automation_var = tk.BooleanVar(value=False)

        self._build_ui()
        self._apply_scale()

    def _capture_font_bases(self):
        """Capture the named fonts' point sizes once, so scaling is relative
        to them. 'tk scaling' alone does not resize existing widgets, so the
        fonts themselves are reconfigured instead."""
        bases = {}
        for name in self.FONT_NAMES:
            try:
                bases[name] = tkfont.nametofont(name).cget("size")
            except tk.TclError:
                pass
        return bases

    def _apply_scale(self):
        scale = self.scale
        for name, base in self._font_bases.items():
            tkfont.nametofont(name).configure(size=round(base * scale))
        for col in ("nom", "depart", "arrivee", "direction", "forme", "materiau"):
            self.troncon_tree.column(col, width=int(self._tree_col_width * scale))
        self.geometry(f"{int(self.BASE_SIZE[0] * scale)}x{int(self.BASE_SIZE[1] * scale)}")
        self.update_idletasks()

    def set_license_valid(self):
        """Display the successful license check in the application header."""
        self.license_status_label.configure(text="● Licence valide")
        self.title("Générateur de configuration - EN13508-2 / WinCan — Licence valide")

    def change_scale(self, delta):
        new_scale = round(self.scale + delta, 1)
        if not (self.SCALE_MIN <= new_scale <= self.SCALE_MAX):
            return
        self.scale = new_scale
        self.scale_label_var.set(f"{int(self.scale * 100)}%")
        self._apply_scale()

    # ------------------------------------------------------------ UI setup
    def _build_ui(self):
        self.license_status_label = ttk.Label(
            self,
            text="",
            foreground="#16803c",
            font=("TkDefaultFont", 10, "bold"),
        )
        self.license_status_label.pack(anchor="w", padx=10, pady=(6, 0))

        project_frame = ttk.LabelFrame(self, text="Projet", padding=8)
        project_frame.pack(fill="x", padx=8, pady=6)

        self.project_vars = {}
        for i, (key, label) in enumerate(PROJECT_FIELDS):
            ttk.Label(project_frame, text=label + " :").grid(row=0, column=i * 2, sticky="e", padx=4, pady=3)
            var = tk.StringVar()
            var.trace_add("write", lambda *a, k=key, v=var: self.project.__setitem__(k, v.get()))
            self.project_vars[key] = var
            ttk.Entry(project_frame, textvariable=var, width=24).grid(row=0, column=i * 2 + 1, sticky="w", padx=4, pady=3)

        ttk.Label(project_frame, text="Opérateur :").grid(row=1, column=0, sticky="e", padx=4, pady=3)
        ttk.Label(project_frame, text=DEFAULT_OPERATEUR, foreground="#555").grid(row=1, column=1, sticky="w", padx=4, pady=3)

        body = ttk.Panedwindow(self, orient="horizontal")
        body.pack(fill="both", expand=True, padx=8, pady=6)

        # --- Left: Regards (read-only; created on the fly by Tronçons) ---
        left = ttk.LabelFrame(body, text="Regards de visite", padding=6)
        body.add(left, weight=1)

        self.regard_list = tk.Listbox(left, width=24, exportselection=False)
        self.regard_list.pack(fill="both", expand=True, side="top")

        # --- Right: Tronçons ---
        right = ttk.LabelFrame(body, text="Tronçons", padding=6)
        body.add(right, weight=3)

        columns = ("nom", "depart", "arrivee", "direction", "forme", "materiau")
        self.troncon_tree = ttk.Treeview(right, columns=columns, show="headings", height=18)
        headers = {"nom": "Nom", "depart": "Départ", "arrivee": "Arrivée", "direction": "Sens",
                   "forme": "Forme", "materiau": "Matériau"}
        for c in columns:
            self.troncon_tree.heading(c, text=headers[c])
            self.troncon_tree.column(c, width=self._tree_col_width, anchor="w")
        self.troncon_tree.pack(fill="both", expand=True, side="top")
        self.troncon_tree.bind("<Double-1>", lambda e: self.edit_troncon())

        tbtns = ttk.Frame(right)
        tbtns.pack(fill="x", pady=4)
        ttk.Button(tbtns, text="Ajouter", command=self.add_troncon).pack(side="left", expand=True, fill="x")
        ttk.Button(tbtns, text="Modifier", command=self.edit_troncon).pack(side="left", expand=True, fill="x")
        ttk.Button(tbtns, text="Supprimer", command=self.delete_troncon).pack(side="left", expand=True, fill="x")

        bottom = ttk.Frame(self, padding=8)
        bottom.pack(fill="x")
        ttk.Button(bottom, text="Charger XML...", command=self.load_xml).pack(side="left", padx=4)
        ttk.Button(bottom, text="Enregistrer XML...", command=self.save_xml).pack(side="left", padx=4)
        self.automation_button = ttk.Button(
            bottom,
            text="Appliquer à Canalyse",
            command=self.apply_to_canalyse,
        )
        self.automation_button.pack(side="left", padx=4)
        ttk.Checkbutton(
            bottom,
            text="Logs DEBUG",
            variable=self.debug_automation_var,
        ).pack(side="left", padx=4)
        ttk.Button(bottom, text="Générer fichier .txt...", command=self.generate_txt).pack(side="right", padx=4)

        scale_frame = ttk.Frame(bottom)
        scale_frame.pack(side="right", padx=4)
        ttk.Button(scale_frame, text="-", width=3,
                   command=lambda: self.change_scale(-self.SCALE_STEP)).pack(side="left", padx=1)
        ttk.Label(scale_frame, textvariable=self.scale_label_var, width=5, anchor="center").pack(side="left", padx=2)
        ttk.Button(scale_frame, text="+", width=3,
                   command=lambda: self.change_scale(self.SCALE_STEP)).pack(side="left", padx=1)

    # ------------------------------------------------------------ Regards
    def _refresh_regard_list(self):
        self.regard_list.delete(0, "end")
        for r in self.regards:
            self.regard_list.insert("end", r)

    def _ensure_regard(self, name):
        """Register a Regard on the fly if the Tronçon dialog was given a
        new name that isn't in the list yet (per spec: create-if-missing)."""
        if name and name not in self.regards:
            self.regards.append(name)

    def _prune_unused_regards(self):
        """Drop Regards that no Tronçon references. Regards are only ever
        created by Tronçon creation, so anything unused is an orphan."""
        used = set()
        for t in self.troncons:
            used.add(t.get("depart", ""))
            used.add(t.get("arrivee", ""))
        self.regards = [r for r in self.regards if r in used]
        self._refresh_regard_list()

    # ------------------------------------------------------------ Tronçons
    def _refresh_troncon_tree(self, select_iid=None):
        self.troncon_tree.delete(*self.troncon_tree.get_children())
        for i, t in enumerate(self.troncons):
            sens = f"{t['depart']} -> {t['arrivee']}" if t.get("direction") != "B" else f"{t['arrivee']} -> {t['depart']}"
            values = (t["nom"], t["depart"], t["arrivee"], sens, t["forme"], t["materiau"])
            self.troncon_tree.insert("", "end", iid=str(i), values=values)
        if select_iid is not None:
            self.troncon_tree.selection_set(str(select_iid))

    def _selected_troncon_index(self):
        sel = self.troncon_tree.selection()
        return int(sel[0]) if sel else None

    def add_troncon(self):
        dlg = TronconDialog(self, self.regards)
        self.wait_window(dlg)
        if dlg.result is not None:
            self._ensure_regard(dlg.result["depart"])
            self._ensure_regard(dlg.result["arrivee"])
            dlg.result["nom"] = f"Tronçon n° {len(self.troncons) + 1}"
            self.troncons.append(dlg.result)
            self._prune_unused_regards()
            self._refresh_troncon_tree(select_iid=len(self.troncons) - 1)

    def edit_troncon(self):
        idx = self._selected_troncon_index()
        if idx is None:
            messagebox.showinfo("Sélection", "Sélectionnez d'abord un tronçon.")
            return
        dlg = TronconDialog(self, self.regards, initial=self.troncons[idx])
        self.wait_window(dlg)
        if dlg.result is not None:
            self._ensure_regard(dlg.result["depart"])
            self._ensure_regard(dlg.result["arrivee"])
            dlg.result["nom"] = self.troncons[idx]["nom"]  # name stays fixed once created
            self.troncons[idx] = dlg.result
            self._prune_unused_regards()
            self._refresh_troncon_tree(select_iid=idx)

    def delete_troncon(self):
        idx = self._selected_troncon_index()
        if idx is None:
            return
        if messagebox.askyesno("Confirmer", "Supprimer ce tronçon ?"):
            del self.troncons[idx]
            # Renumber sequential names to stay contiguous ("Tronçon n° 1", "n° 2", ...)
            for i, t in enumerate(self.troncons):
                t["nom"] = f"Tronçon n° {i + 1}"
            self._prune_unused_regards()
            self._refresh_troncon_tree()

    # ------------------------------------------------------- File actions
    def save_xml(self):
        if not self.troncons:
            messagebox.showinfo("Aucun tronçon", "Ajoutez au moins un tronçon avant d'enregistrer.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".xml", filetypes=[("Fichier XML", "*.xml")])
        if not path:
            return

        root = ET.Element("Project", {k: v for k, v in self.project.items() if v})

        troncons_el = ET.SubElement(root, "Troncons")
        for t in self.troncons:
            attrs = {}
            for key in TRONCON_XML_ATTR_ORDER:
                if key == "curage":
                    attrs[key] = "1" if t.get("curage") else "0"
                else:
                    attrs[key] = str(t.get(key, ""))
            ET.SubElement(troncons_el, "Troncon", attrs)

        pretty = minidom.parseString(ET.tostring(root, encoding="utf-8")).toprettyxml(indent="  ")
        with open(path, "w", encoding="utf-8") as f:
            f.write(pretty)
        messagebox.showinfo("Enregistré", f"Projet enregistré :\n{path}")

    def load_xml(self):
        path = filedialog.askopenfilename(filetypes=[("Fichier XML", "*.xml")])
        if not path:
            return
        try:
            project, regards, troncons = core.parse_source(path)
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger ce fichier :\n{e}")
            return

        self.project = project
        self.project.setdefault("operateur", DEFAULT_OPERATEUR)
        for key, var in self.project_vars.items():
            var.set(self.project.get(key, ""))

        self.regards = regards
        self.troncons = troncons
        self._prune_unused_regards()
        self._refresh_troncon_tree()

    def generate_txt(self):
        if not self.troncons:
            messagebox.showinfo("Aucun tronçon", "Ajoutez au moins un tronçon avant de générer le fichier.")
            return
        try:
            core.validate(self.regards, self.troncons)
        except ValueError as e:
            messagebox.showerror("Erreur", str(e))
            return

        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Fichier de sauvegarde", "*.txt")])
        if not path:
            return

        try:
            lines = core.build_file(self.project, self.regards, self.troncons)
            with open(path, "w", encoding="iso-8859-1", newline="\r\n") as f:
                f.write("\n".join(lines) + "\n")
        except Exception as e:
            messagebox.showerror("Erreur", f"Échec de la génération :\n{e}")
            return

        messagebox.showinfo("Terminé", f"Fichier généré :\n{path}\n({len(self.troncons)} tronçon(s))")

    def apply_to_canalyse(self):
        if not self.troncons:
            messagebox.showinfo(
                "Aucun tronçon",
                "Chargez ou ajoutez au moins un tronçon avant de lancer l'automatisation.",
            )
            return

        from canalyse_automation import apply_troncons

        debug_enabled = self.debug_automation_var.get()
        logging.getLogger().setLevel(
            logging.DEBUG if debug_enabled else logging.INFO
        )
        dialog = tk.Toplevel(self)
        dialog.title("Automatisation Canalyse")
        dialog.resizable(True, True)
        dialog.minsize(620, 360)
        dialog.transient(self)
        dialog.attributes("-topmost", True)
        dialog.lift()

        status_var = tk.StringVar(value="Démarrage...")
        ttk.Label(dialog, textvariable=status_var).pack(fill="x", padx=10, pady=(10, 4))
        log_text = tk.Text(dialog, height=16, state="disabled", wrap="none")
        log_text.pack(fill="both", expand=True, padx=10, pady=4)
        progress = ttk.Progressbar(dialog, maximum=len(self.troncons), mode="determinate")
        progress.pack(fill="x", padx=10, pady=(4, 10))
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill="x", padx=10, pady=(0, 10))
        cancel_event = threading.Event()

        def request_cancel():
            cancel_event.set()
            cancel_button.configure(state="disabled")
            status_var.set("Annulation demandée...")

        cancel_button = ttk.Button(
            button_frame,
            text="Annuler",
            command=request_cancel,
        )
        cancel_button.pack(side="left")
        close_button = ttk.Button(
            button_frame,
            text="Fermer",
            state="disabled",
            command=dialog.destroy,
        )
        close_button.pack(side="right")

        events = queue.Queue()
        self.automation_button.configure(state="disabled")

        def append_log(level, message):
            events.put(("log", level, message))

        def update_progress(current, total, message):
            events.put(("progress", current, total, message))

        def worker():
            try:
                apply_troncons(
                    self.troncons,
                    self.project.get("operateur", DEFAULT_OPERATEUR),
                    debug=debug_enabled,
                    log_callback=append_log,
                    progress_callback=update_progress,
                    cancel_event=cancel_event,
                )
            except Exception as exc:
                events.put(("error", exc))
            else:
                events.put(("done",))

        threading.Thread(target=worker, name="canalyse-automation", daemon=True).start()

        def poll_events():
            try:
                while True:
                    event = events.get_nowait()
                    if event[0] == "log":
                        log_text.configure(state="normal")
                        log_text.insert("end", f"[{event[1]}] {event[2]}\n")
                        log_text.see("end")
                        log_text.configure(state="disabled")
                    elif event[0] == "progress":
                        _, current, total, message = event
                        progress.configure(maximum=total, value=current)
                        status_var.set(message)
                    elif event[0] == "error":
                        self.automation_button.configure(state="normal")
                        cancel_button.configure(state="disabled")
                        close_button.configure(state="normal")
                        status_var.set("Échec de l'automatisation")
                        messagebox.showerror(
                            "Erreur d'automatisation",
                            f"Impossible d'appliquer les paramètres dans Canalyse :\n{event[1]}",
                            parent=dialog,
                        )
                    elif event[0] == "done":
                        self.automation_button.configure(state="normal")
                        cancel_button.configure(state="disabled")
                        close_button.configure(state="normal")
                        if cancel_event.is_set():
                            status_var.set("Automatisation annulée")
                            log_text.configure(state="normal")
                            log_text.insert("end", "[INFO] Traitement arrêté par l'utilisateur\n")
                            log_text.see("end")
                            log_text.configure(state="disabled")
                        else:
                            status_var.set("Automatisation terminée")
                            messagebox.showinfo(
                                "Terminé",
                                f"Paramètres appliqués à {len(self.troncons)} tronçon(s) dans Canalyse.",
                                parent=dialog,
                            )
            except queue.Empty:
                pass
            if close_button["state"] == "disabled":
                dialog.after(100, poll_events)

        dialog.protocol("WM_DELETE_WINDOW", lambda: None)
        poll_events()


def main():
    app = App()
    from license_gate import verify_startup_license

    if not verify_startup_license(app):
        app.destroy()
        return
    app.set_license_valid()
    app.mainloop()


if __name__ == "__main__":
    main()
