import os

from datetime import datetime

def export_history(history):

    name = datetime.now().strftime(
        "clipboard_export_%Y%m%d_%H%M%S.txt"
    )

    # Save the export next to this file, not wherever the app was launched.
    filename = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        name
    )

    with open(filename, "w", encoding="utf-8") as file:

        # One item per line, in copy order, with no separator lines.
        for item in history:
            file.write(item)
            file.write("\n")

    return filename