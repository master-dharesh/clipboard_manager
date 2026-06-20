import os
import re
import time
import threading
from datetime import datetime

import pyperclip

from database import save_clipboard
from settings import MONITOR_INTERVAL

try:
    from PIL import ImageGrab
    IMAGE_SUPPORT = True
except Exception:
    IMAGE_SUPPORT = False

# Folder where copied images are stored.
IMAGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^\+?[\d][\d\s\-()]{6,16}\d$")
CODE_HINTS = (";", "{", "}", "=>", "def ", "function ", "import ", "</", "/>")

def detect_category(text):

    stripped = text.strip()

    if stripped.startswith(("http://", "https://", "www.")):
        return "URL"

    if EMAIL_RE.match(stripped):
        return "Email"

    if PHONE_RE.match(stripped) and sum(c.isdigit() for c in stripped) >= 7:
        return "Phone"

    if "\n" in stripped or any(h in stripped for h in CODE_HINTS):
        return "Code"

    # Password-like: one token, 8-32 chars, mixes letters and digits.
    if (
        " " not in stripped
        and 8 <= len(stripped) <= 32
        and any(c.isalpha() for c in stripped)
        and any(c.isdigit() for c in stripped)
    ):
        return "Password"

    return "Text"

def now_stamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M")

class ClipboardMonitor:

    def __init__(self, callback):

        self.callback = callback
        self.last_text = ""
        self.last_image_size = None

    def start(self):

        thread = threading.Thread(
            target=self.monitor,
            daemon=True
        )

        thread.start()

    def monitor(self):

        while True:

            try:
                self.check_image()
                self.check_text()
                time.sleep(MONITOR_INTERVAL)

            except Exception:
                pass

    def check_text(self):

        text = pyperclip.paste()

        if text and text != self.last_text:

            self.last_text = text

            category = detect_category(text)
            stamp = now_stamp()

            save_clipboard(text, category, stamp)

            self.callback(text, category, stamp)

    def check_image(self):

        if not IMAGE_SUPPORT:
            return

        image = ImageGrab.grabclipboard()

        # A real bitmap (not a file list, not None).
        if image is None or isinstance(image, list):
            return

        if image.size == self.last_image_size:
            return

        self.last_image_size = image.size

        os.makedirs(IMAGE_DIR, exist_ok=True)

        stamp = now_stamp()
        filename = datetime.now().strftime("img_%Y%m%d_%H%M%S.png")
        path = os.path.join(IMAGE_DIR, filename)

        image.save(path, "PNG")

        # Store the saved path as the item content.
        save_clipboard(path, "Image", stamp)

        self.callback(path, "Image", stamp)
