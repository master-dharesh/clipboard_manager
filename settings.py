APP_TITLE = "Accessible Clipboard Manager"

WINDOW_WIDTH = 700
WINDOW_HEIGHT = 600

MAX_HISTORY = 100

# How often (in seconds) the clipboard is checked. A smaller value
# catches quick, back-to-back copies that a 1 second poll would miss.
MONITOR_INTERVAL = 0.3

# Default text size in the history list.
DEFAULT_FONT_SIZE = 11
MIN_FONT_SIZE = 8
MAX_FONT_SIZE = 28

# Auto-delete items older than this many days (0 = never delete).
# Favourites and pinned items are always kept.
AUTO_DELETE_DAYS = 30

# Hide password-like items behind dots in the list.
MASK_PASSWORDS = True

# The two colour themes the user can switch between.
THEMES = {
    "dark": {
        "bg": (30, 30, 30),
        "fg": (255, 255, 255),
    },
    "light": {
        "bg": (245, 245, 245),
        "fg": (0, 0, 0),
    },
}

DEFAULT_THEME = "dark"
