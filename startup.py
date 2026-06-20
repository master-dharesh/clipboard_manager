import os
import sys

def enable_startup():
    startup_folder = os.path.join(
        os.getenv("APPDATA"),
        r"Microsoft\Windows\Start Menu\Programs\Startup"
    )

    project_dir = os.path.dirname(os.path.abspath(__file__))
    main_script = os.path.join(project_dir, "main.py")

    # Prefer pythonw.exe so the app starts without a console window.
    python_exe = sys.executable
    pythonw_exe = python_exe.replace("python.exe", "pythonw.exe")
    if os.path.exists(pythonw_exe):
        python_exe = pythonw_exe

    launcher = os.path.join(startup_folder, "clipboard_manager.bat")

    # The launcher changes into the project directory first so all the
    # local modules import correctly, then runs the app.
    content = (
        "@echo off\r\n"
        f'cd /d "{project_dir}"\r\n'
        f'start "" "{python_exe}" "{main_script}"\r\n'
    )

    try:
        with open(launcher, "w", encoding="utf-8") as file:
            file.write(content)
    except Exception as error:
        print(f"Could not set up startup launcher: {error}")
