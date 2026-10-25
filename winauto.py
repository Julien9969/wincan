## 1. Quick Decision Matrix

# | Scenario | Primary Library | Inspection Tool | Key Advantage |
# | --- | --- | --- | --- |
# | **Modern Windows App** (WPF, Qt, WinForms, Electron) | `pywinauto` (`backend="uia"`) | `Inspect.exe` / Accessibility Insights | Clicks/types in background; immune to window position or resolution. |
# | **Legacy Windows App** (Win32, MFC, VB6, Delphi) | `pywinauto` (`backend="win32"`) | `Spy++` / AutoIt Window Info | Direct Win32 message passing (`WM_SETTEXT`, `WM_CLICK`). |
# | **Custom Rendered UI** (Games, Canvas, Citrix/RDP) | `pyautogui` + `opencv-python` | Screenshot crop tool | Works on anything visible on screen via `(x, y)` or image matching. |
# | **Web Application** (Chromium, Firefox, WebKit) | `playwright` | Browser DevTools (`F12`) | Auto-waits for DOM elements, supports headless execution & network interception. |

# ```bash
# # All-in-one installation for the full toolkit
# pip install pywinauto pyautogui opencv-python pillow pyperclip playwright
# playwright install

# ```

# ---

## 2. `pywinauto` Cheat Sheet (Windows Native UI)

### A. App Connection & Window Management

# ```python
from pywinauto import Application, Desktop
from pywinauto.controls.uia_controls import Window
from pywinauto.timings import Timings

# Global speed adjustments: Timings.fast(), Timings.slow(), or Timings.defaults()
Timings.window_find_timeout = 10.0

# Start or Connect
# app = Application(backend="uia").start(r"C:/Program Files (x86)/Canalyse 2/Canalyse2.exe")
app = Application(backend="uia").connect(r"C:/Program Files (x86)/Canalyse 2/Canalyse2.exe")
# app = Application(backend="uia").connect(title_re=".*App Title.*", timeout=10)
# app = Application(backend="uia").connect(process=12345)          # Connect by PID
# app = Application(backend="uia").connect(path=r"C:\app.exe")     # Connect by executable path




win:Window = app.window(title_re=".*Canalyse 2.*") 


# Cross-process / System-wide windows (e.g., Windows 11 Notepad, File Dialogs, Popups)
# win = Desktop(backend="uia").window(title_re=".*Save As.*")

# # Window State Manipulation
# win.restore()       # Un-minimize
# win.maximize()
# win.minimize()
# win.set_focus()     # Bring to foreground
# win.close()

# # ```

# ### B. Locating Elements (`child_window`)

# # ```python
# # Combine criteria for strict matching
# el = win.child_window(
#     title="Save",               # Exact text match
#     title_re=".*Save.*",        # Regex text match
#     auto_id="btnSave",          # Developer automation ID (Most reliable in UIA)
#     control_type="Button",      # UIA role (Button, Edit, ComboBox, CheckBox, etc.)
#     class_name="Button",        # Win32 class name
#     found_index=0,              # 0-based index if multiple elements match
#     visible_only=True,          # Ignore hidden elements
#     enabled_only=True           # Ignore greyed-out elements
# )

# # Debugging & Tree Inspection
# win.print_control_identifiers()                       # Dump UI tree to terminal
# win.print_control_identifiers(filename="tree.txt")    # Dump UI tree to file
# el.draw_outline(colour="red", thickness=2)            # Highlight element on screen

# # ```

# # ### C. Actions & Widget Controls

# # | Control / Action | Background / API Method *(No Mouse Required)* | Physical Simulation *(Moves Cursor / Focus)* |
# # | --- | --- | --- |
# # | **Button** | `btn.click()` or `btn.invoke()` | `btn.click_input()` / `btn.double_click_input()` |
# # | **Right Click** | *(Not supported via pure UIA invoke)* | `btn.right_click_input()` |
# # | **Edit (Text Field)** | `edit.set_edit_text("Fast inject")` | `edit.type_keys("Typed text", with_spaces=True)` |
# # | **Clear & Type** | `edit.set_edit_text("")` | `edit.type_keys("^a{BACKSPACE}New", with_spaces=True)` |
# # | **ComboBox (Dropdown)** | `combo.select("Option Name")` or `combo.select(0)` | `combo.click_input()` then `type_keys("{DOWN}{ENTER}")` |
# # | **CheckBox** | `chk.toggle()` | `chk.click_input()` |
# # | **RadioButton** | `radio.select()` | `radio.click_input()` |
# # | **Tab Control** | `tab.select("Tab Name")` or `tab.select(1)` | `tab.click_input()` |
# # | **List / DataGrid** | `lst.item("Row Text").select()` | `lst.item(0).click_input()` |
# # | **TreeView** | `tree.get_item(r"\Root\Child").select()` | `tree.get_item(r"\Root\Child").click_input()` |
# # | **Top Menu Bar** | `win.menu_select("File -> Open...")` | `win.type_keys("%fo")` *(Alt+F, then O)* |

# ### D. Waiting, State & Property Reading

# # ```python
# # Synchronization (States: 'exists', 'visible', 'enabled', 'ready', 'active')
# el.wait("ready", timeout=15, retry_interval=0.5)
# el.wait_not("visible", timeout=15)  # Wait for spinners/modals to close

# # Safe existence check (returns True/False instead of raising ElementNotFoundError)
# if win.child_window(title="Error").exists(timeout=2):
#     win.child_window(title="OK", control_type="Button").click()

# # Reading Properties
# text_str   = el.window_text()          # Visible title/label
# edit_val   = edit.get_value()          # Current text value (UIA Edit control)
# all_texts  = el.texts()                # List of strings inside control/sub-items
# chk_state  = chk.get_toggle_state()    # 0 = Unchecked, 1 = Checked, 2 = Indeterminate
# is_ready   = el.is_visible() and el.is_enabled()
# rect       = el.rectangle()            # rect.left, rect.top, rect.width(), rect.height()
# mid_point  = rect.mid_point()          # Returns (x, y) center tuple

# # ```

# # ### E. `type_keys()` Key Code Reference

# # * **Modifiers:** `^` (Ctrl), `%` (Alt), `+` (Shift). *Group with parentheses:* `^(ac)` = Ctrl+A then Ctrl+C; `+(hello)` = HELLO.
# # * **Navigation & Editing:** `{ENTER}`, `{TAB}`, `{ESC}`, `{SPACE}`, `{BACKSPACE}`, `{DELETE}`, `{HOME}`, `{END}`, `{PGUP}`, `{PGDN}`.
# # * **Arrows & Function Keys:** `{UP}`, `{DOWN}`, `{LEFT}`, `{RIGHT}`, `{F1}` ... `{F12}`.
# # * **Key Hold/Release:** `{VK_SHIFT down}text{VK_SHIFT up}`.
