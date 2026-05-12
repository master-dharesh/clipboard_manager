import keyboard

def register_hotkeys(show_window_callback):

    keyboard.add_hotkey(
        "ctrl+shift+v",
        show_window_callback
    )