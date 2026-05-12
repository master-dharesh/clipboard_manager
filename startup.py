import os
import shutil

def enable_startup():
    startup_folder = os.path.join(
        os.getenv("APPDATA"),
        r"Microsoft\Windows\Start Menu\Programs\Startup"
    )

    current_file = os.path.abspath("main.py")

    destination = os.path.join(
        startup_folder,
        "clipboard_manager.py"
    )

    try:
        shutil.copy(current_file, destination)
    except:
        pass