"""Click the Canalyse 2 button named "Modification des paramètres"."""

from pywinauto import Application


APP_PATH = r"C:\Program Files (x86)\Canalyse 2\Canalyse2.exe"
WINDOW_TITLE_RE = r".*Canalyse 2.*"
BUTTON_TEXT = "Modification des paramètres"


def main():
    app = Application(backend="uia").connect(path=APP_PATH, timeout=10)
    window = app.window(title_re=WINDOW_TITLE_RE)
    button = window.child_window(title=BUTTON_TEXT, control_type="Button")
    button.wait("ready", timeout=10)
    button.invoke()


if __name__ == "__main__":
    main()
