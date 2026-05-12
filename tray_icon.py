import threading

from pystray import Icon, Menu, MenuItem
from PIL import Image

def create_tray(frame):

    image = Image.new(
        "RGB",
        (64, 64),
        color=(0, 0, 0)
    )

    def show_window(icon, item):

        frame.Show()
        frame.Raise()

    def exit_app(icon, item):

        icon.stop()
        frame.Close()

    icon = Icon(
        "ClipboardManager",
        image,
        "Clipboard Manager",
        menu=Menu(
            MenuItem("Open", show_window),
            MenuItem("Exit", exit_app)
        )
    )

    threading.Thread(
        target=icon.run,
        daemon=True
    ).start()