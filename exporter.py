from datetime import datetime

def export_history(history):

    filename = datetime.now().strftime(
        "clipboard_export_%Y%m%d_%H%M%S.txt"
    )

    with open(filename, "w", encoding="utf-8") as file:

        for item in history:
            file.write(item)
            file.write("\n")
            file.write("-" * 50)
            file.write("\n")

    return filename