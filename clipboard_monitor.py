import threading
import time
import pyperclip

from database import save_clipboard
from settings import MONITOR_INTERVAL

def detect_category(text):

    if text.startswith("http://") or text.startswith("https://"):
        return "URL"

    return "Text"

class ClipboardMonitor:

    def __init__(self, callback):

        self.callback = callback
        self.last_text = ""

    def start(self):

        thread = threading.Thread(
            target=self.monitor,
            daemon=True
        )

        thread.start()

    def monitor(self):

        while True:

            try:

                text = pyperclip.paste()

                if text and text != self.last_text:

                    self.last_text = text

                    category = detect_category(text)

                    save_clipboard(text, category)

                    self.callback(text, category)

                time.sleep(MONITOR_INTERVAL)

            except Exception as error:
                print(f"Clipboard monitor error: {error}")
                time.sleep(MONITOR_INTERVAL)