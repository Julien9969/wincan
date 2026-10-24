# Copilot instructions

## Project overview

This is a small Python 3 desktop tool for preparing EN 13508-2 / WinCan
inspection configuration data. It has no third-party runtime dependencies:
the GUI uses the Python standard library's Tkinter module.

- [`ui.py`](../ui.py) implements the French-language Tkinter editor for
  project metadata and canal sections ("Tronçons").
- [`generate_wincan.py`](../generate_wincan.py) is the shared data/model and
  output layer. It parses the source XML, validates node references, maps
  dropdown values to protocol codes, and writes the ISO-8859-1 WinCan-style
  `.txt` file.
- The GUI imports the core module directly. Keep XML loading, validation, and
  `.txt` serialization in the core so GUI and command-line output continue to
  use the same code path.
- [`etst.xml`](../etst.xml) is a sample source XML file. [`GEN.txt`](../GEN.txt)
  is a sample generated WinCan-style output file. [`ai-prompt.md`](../ai-prompt.md)
  records the field defaults and French code-table vocabulary used by the
  configuration workflow.
- [`ConfigurateurTroncons.spec`](../ConfigurateurTroncons.spec) is the
  PyInstaller configuration for a windowed executable named
  `ConfigurateurTroncons`.

The source XML contains a `Project` element with project attributes and a
`Troncons` collection. Regards de visite are not serialized separately:
they are inferred from the first appearance of each `depart` and `arrivee`
value. The generated text file is organized into `#B01` through `#B04`
blocks followed by `#Z` for each Tronçon, with fixed protocol fields retained
where the export format requires them.

## Commands

Run these commands from the repository root. The existing source documentation
uses `python3`; on Windows, `py -3` is an equivalent choice when `python3` is
not on `PATH`.

### Run the application

```powershell
python3 ui.py
```

This opens the Tkinter editor. It can load/save the source XML and generate a
WinCan `.txt` file.

### Generate a text file from XML

```powershell
python3 generate_wincan.py etst.xml output.txt
```

The command requires exactly two arguments: an input XML path and an output
`.txt` path. It validates that every Tronçon node is represented in the
derived Regards list before writing.

### Syntax and smoke checks

There is currently no automated test suite or configured linter. For a
single-module check, run:

```powershell
python3 -m py_compile generate_wincan.py
```

For the full source syntax check and a serialization smoke test, run:

```powershell
python3 -m py_compile ui.py generate_wincan.py
python3 generate_wincan.py etst.xml "$env:TEMP\kaid-wincan-smoke.txt"
```

Inspect the generated file if changing field mappings, encoding, line endings,
or block layout.

### Build the Windows executable

PyInstaller is not declared as a project dependency. If it is installed in
the active Python environment, build with:

```powershell
pyinstaller ConfigurateurTroncons.spec
```

The spec builds `ui.py` as a windowed executable and imports
`generate_wincan.py` through the normal Python module relationship.

## Repository-specific conventions

- Preserve the XML attribute names and the field order in
  `TRONCON_XML_ATTR_ORDER`; the generated XML is consumed as an interchange
  format and is also used as the input to the CLI generator.
- Keep `DEFAULT_TRONCON`, the code tables, and the `build_b01`/`build_b02`/
  `build_b03` mappings synchronized. The GUI displays labels but stores
  protocol codes in XML.
- `curage` is represented as a Boolean in memory, `"1"`/`"0"` in XML, and
  `"A"`/`"B"` in the `AAQ` field of the generated text.
- `direction` is stored as `"A"` or `"B"`; the GUI derives the displayed
  direction from the two node names and prevents identical departure and
  arrival nodes.
- A new Tronçon gets the sequential name `Tronçon n° N`. Deleting a Tronçon
  renumbers the remaining names, while editing preserves the existing name.
  Regards are created from Tronçon references and unused entries are pruned.
- XML loading accepts the legacy `propriete_fonciere` attribute as a fallback
  for `emplacement`; preserve this compatibility when changing the parser.
- Generated files must remain ISO-8859-1 encoded with CRLF line endings and
  the header declarations currently emitted by `build_file`. Text fields in
  the WinCan format are quoted; numeric and protocol-code fields are emitted
  raw according to the existing block builders.
- The export intentionally contains pre-inspection setup data only. Do not add
  on-site observation/comment fields unless the data model and output format
  are deliberately extended together.
- Error reporting follows the current surface: the CLI raises/parses errors
  normally, while the GUI shows validation and file-operation errors through
  Tkinter message boxes. Keep failures visible rather than silently falling
  back to a success-shaped output.
