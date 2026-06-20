import os
import re
from datetime import datetime, timedelta

import wx
import pyperclip
import keyboard

from clipboard_monitor import ClipboardMonitor
from database import (
    create_database,
    load_history,
    load_favorites,
    delete_item,
    clear_history,
    set_favorite,
    set_pinned,
    delete_older_than,
    import_items
)

from hotkeys import register_hotkeys
from exporter import export_history
from speech import speak

from settings import (
    APP_TITLE,
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    DEFAULT_FONT_SIZE,
    MIN_FONT_SIZE,
    MAX_FONT_SIZE,
    AUTO_DELETE_DAYS,
    MASK_PASSWORDS,
    THEMES,
    DEFAULT_THEME
)

CATEGORIES = ["All", "Text", "URL", "Email", "Phone", "Code", "Password", "Image"]

class ClipboardFrame(wx.Frame):

    def __init__(self):

        super().__init__(
            parent=None,
            title=APP_TITLE,
            size=(WINDOW_WIDTH, WINDOW_HEIGHT)
        )

        create_database()

        # Auto-delete old plain items on startup (favourites/pinned kept).
        if AUTO_DELETE_DAYS > 0:
            cutoff = (datetime.now() - timedelta(days=AUTO_DELETE_DAYS)).strftime("%Y-%m-%d %H:%M")
            delete_older_than(cutoff)

        self.theme = DEFAULT_THEME
        self.font_size = DEFAULT_FONT_SIZE
        self.mask_passwords = MASK_PASSWORDS

        self.panel = wx.Panel(self)

        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # --- Search ---
        search_label = wx.StaticText(self.panel, label="Search clipboard history:")
        self.search = wx.TextCtrl(self.panel)
        self.search.SetHint("Search (plain text or regex)")
        self.search.SetName("Search clipboard history")

        # --- Category filter ---
        filter_label = wx.StaticText(self.panel, label="Filter by category:")
        self.category_filter = wx.Choice(self.panel, choices=CATEGORIES)
        self.category_filter.SetSelection(0)
        self.category_filter.SetName("Filter by category")

        # --- History list ---
        list_label = wx.StaticText(self.panel, label="Clipboard history:")
        self.listbox = wx.ListBox(self.panel)
        self.listbox.SetName("Clipboard history list")

        # --- Item count ---
        self.count_label = wx.StaticText(self.panel, label="Items: 0")

        # --- Buttons (in a grid so they all fit) ---
        self.copy_button = wx.Button(self.panel, label="Copy Selected")
        self.paste_button = wx.Button(self.panel, label="Paste Selected")
        self.delete_button = wx.Button(self.panel, label="Delete Selected")
        self.add_favorite_button = wx.Button(self.panel, label="Add to Favorites")
        self.remove_favorite_button = wx.Button(self.panel, label="Remove from Favorites")
        self.pin_button = wx.Button(self.panel, label="Pin")
        self.unpin_button = wx.Button(self.panel, label="Unpin")
        self.show_favorites_button = wx.Button(self.panel, label="Show Favorites")
        self.export_button = wx.Button(self.panel, label="Export History")
        self.import_button = wx.Button(self.panel, label="Import History")
        self.clear_button = wx.Button(self.panel, label="Clear History")
        self.theme_button = wx.Button(self.panel, label="Light Theme")
        self.font_up_button = wx.Button(self.panel, label="Font +")
        self.font_down_button = wx.Button(self.panel, label="Font -")
        self.mask_button = wx.Button(self.panel, label="Show Passwords")

        button_grid = wx.GridSizer(cols=3, gap=(5, 5))
        for btn in [
            self.copy_button, self.paste_button, self.delete_button,
            self.add_favorite_button, self.remove_favorite_button,
            self.pin_button, self.unpin_button, self.show_favorites_button,
            self.export_button, self.import_button, self.clear_button,
            self.theme_button, self.font_up_button, self.font_down_button,
            self.mask_button,
        ]:
            button_grid.Add(btn, 0, wx.EXPAND)

        main_sizer.Add(search_label, 0, wx.LEFT | wx.TOP, 5)
        main_sizer.Add(self.search, 0, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(filter_label, 0, wx.LEFT | wx.TOP, 5)
        main_sizer.Add(self.category_filter, 0, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(list_label, 0, wx.LEFT | wx.TOP, 5)
        main_sizer.Add(self.listbox, 1, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(self.count_label, 0, wx.LEFT, 5)
        main_sizer.Add(button_grid, 0, wx.EXPAND | wx.ALL, 5)

        self.panel.SetSizer(main_sizer)

        # State
        self.records = []
        self.showing_favorites = False

        self.apply_theme()
        self.apply_font()

        self.load_clipboard_history()

        # Bindings
        self.copy_button.Bind(wx.EVT_BUTTON, self.copy_selected)
        self.paste_button.Bind(wx.EVT_BUTTON, self.paste_selected)
        self.delete_button.Bind(wx.EVT_BUTTON, self.delete_selected)
        self.add_favorite_button.Bind(wx.EVT_BUTTON, self.add_favorite)
        self.remove_favorite_button.Bind(wx.EVT_BUTTON, self.remove_favorite)
        self.pin_button.Bind(wx.EVT_BUTTON, self.pin_selected)
        self.unpin_button.Bind(wx.EVT_BUTTON, self.unpin_selected)
        self.show_favorites_button.Bind(wx.EVT_BUTTON, self.toggle_view)
        self.export_button.Bind(wx.EVT_BUTTON, self.export_data)
        self.import_button.Bind(wx.EVT_BUTTON, self.import_data)
        self.clear_button.Bind(wx.EVT_BUTTON, self.clear_data)
        self.theme_button.Bind(wx.EVT_BUTTON, self.toggle_theme)
        self.font_up_button.Bind(wx.EVT_BUTTON, self.font_bigger)
        self.font_down_button.Bind(wx.EVT_BUTTON, self.font_smaller)
        self.mask_button.Bind(wx.EVT_BUTTON, self.toggle_mask)

        self.search.Bind(wx.EVT_TEXT, self.on_search)
        self.category_filter.Bind(wx.EVT_CHOICE, self.on_filter)
        self.listbox.Bind(wx.EVT_LISTBOX_DCLICK, self.copy_selected)

        self.monitor = ClipboardMonitor(self.add_clipboard_item)
        self.monitor.start()

        register_hotkeys(self.show_window)

    # ----- Appearance -----

    def apply_theme(self):

        colours = THEMES[self.theme]
        bg = wx.Colour(*colours["bg"])
        fg = wx.Colour(*colours["fg"])

        self.SetBackgroundColour(bg)
        self.panel.SetBackgroundColour(bg)
        self.panel.SetForegroundColour(fg)

        for child in self.panel.GetChildren():
            child.SetForegroundColour(fg)
            if isinstance(child, (wx.TextCtrl, wx.ListBox, wx.Choice)):
                child.SetBackgroundColour(bg)

        self.panel.Refresh()

    def apply_font(self):

        font = wx.Font(
            self.font_size,
            wx.FONTFAMILY_DEFAULT,
            wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_NORMAL
        )
        self.listbox.SetFont(font)

    def toggle_theme(self, event):

        self.theme = "light" if self.theme == "dark" else "dark"
        self.theme_button.SetLabel(
            "Dark Theme" if self.theme == "light" else "Light Theme"
        )
        speak(f"{self.theme} theme")
        self.apply_theme()

    def font_bigger(self, event):

        self.font_size = min(MAX_FONT_SIZE, self.font_size + 2)
        speak("Bigger text")
        self.apply_font()

    def font_smaller(self, event):

        self.font_size = max(MIN_FONT_SIZE, self.font_size - 2)
        speak("Smaller text")
        self.apply_font()

    def toggle_mask(self, event):

        self.mask_passwords = not self.mask_passwords
        self.mask_button.SetLabel(
            "Hide Passwords" if not self.mask_passwords else "Show Passwords"
        )
        self.refresh_listbox()

    # ----- List rendering -----

    def format_label(self, record):

        pin = "[Pin] " if record["pinned"] else ""
        star = "* " if record["favorite"] else ""
        stamp = f"{record['created']} " if record["created"] else ""

        content = record["content"]

        if record["category"] == "Image":
            content = os.path.basename(content)
        elif record["category"] == "Password" and self.mask_passwords:
            content = "*" * 8

        return f"{pin}{star}{stamp}[{record['category']}] {content}"

    def refresh_listbox(self):

        labels = [self.format_label(r) for r in self.records]
        self.listbox.Set(labels)
        self.count_label.SetLabel(f"Items: {len(self.records)}")

    def current_source(self):

        return load_favorites() if self.showing_favorites else load_history()

    def apply_filters(self):

        records = self.current_source()

        # Category filter
        chosen = self.category_filter.GetStringSelection()
        if chosen and chosen != "All":
            records = [r for r in records if r["category"] == chosen]

        # Search (substring, plus regex if it is a valid pattern)
        keyword = self.search.GetValue().strip()
        if keyword:
            low = keyword.lower()
            regex = None
            try:
                regex = re.compile(keyword, re.IGNORECASE)
            except re.error:
                regex = None

            def matches(text):
                if low in text.lower():
                    return True
                return bool(regex.search(text)) if regex else False

            records = [r for r in records if matches(r["content"])]

        self.records = records
        self.refresh_listbox()

    def load_clipboard_history(self):

        self.apply_filters()

    # ----- Monitor callback -----

    def add_clipboard_item(self, text, category, created):

        wx.CallAfter(self.on_new_clip)

    def on_new_clip(self):

        # Only the full (non-favourites) view updates live; respect filters.
        if not self.showing_favorites:
            self.apply_filters()

    # ----- Selection helpers -----

    def get_selected_record(self):

        selection = self.listbox.GetSelection()
        if selection == wx.NOT_FOUND:
            return None
        return self.records[selection]

    # ----- Actions -----

    def copy_to_clipboard(self, record):

        if record["category"] == "Image" and os.path.exists(record["content"]):
            self.copy_image(record["content"])
        else:
            pyperclip.copy(record["content"])
        # Stop the monitor re-saving what we just copied.
        if self.monitor:
            self.monitor.last_text = record["content"]

    def copy_image(self, path):

        try:
            bitmap = wx.Bitmap(path, wx.BITMAP_TYPE_PNG)
            data = wx.BitmapDataObject(bitmap)
            if wx.TheClipboard.Open():
                wx.TheClipboard.SetData(data)
                wx.TheClipboard.Close()
        except Exception:
            pass

    def copy_selected(self, event):

        record = self.get_selected_record()
        if record:
            self.copy_to_clipboard(record)
            speak("Copied")
            wx.MessageBox("Copied to clipboard", "Success")

    def paste_selected(self, event):

        record = self.get_selected_record()
        if not record:
            return

        self.copy_to_clipboard(record)
        speak("Pasting")

        # Hide our window so the previous app gets focus, then paste.
        self.Iconize(True)
        wx.CallLater(350, self._send_paste)

    def _send_paste(self):
        try:
            keyboard.send("ctrl+v")
        except Exception:
            pass

    def delete_selected(self, event):

        record = self.get_selected_record()
        if record:
            delete_item(record["content"])
            speak("Deleted")
            self.apply_filters()

    def add_favorite(self, event):

        record = self.get_selected_record()
        if record:
            set_favorite(record["content"], True)
            speak("Added to favorites")
            self.apply_filters()
            wx.MessageBox("Added to favorites", "Favorite")

    def remove_favorite(self, event):

        record = self.get_selected_record()
        if record:
            set_favorite(record["content"], False)
            speak("Removed from favorites")
            self.apply_filters()
            wx.MessageBox("Removed from favorites", "Favorite")

    def pin_selected(self, event):

        record = self.get_selected_record()
        if record:
            set_pinned(record["content"], True)
            speak("Pinned")
            self.apply_filters()

    def unpin_selected(self, event):

        record = self.get_selected_record()
        if record:
            set_pinned(record["content"], False)
            speak("Unpinned")
            self.apply_filters()

    def toggle_view(self, event):

        self.showing_favorites = not self.showing_favorites
        self.show_favorites_button.SetLabel(
            "Show All" if self.showing_favorites else "Show Favorites"
        )
        self.search.SetValue("")
        self.apply_filters()
        speak(
            f"Showing favorites, {len(self.records)} items"
            if self.showing_favorites
            else f"Showing all, {len(self.records)} items"
        )

    def export_data(self, event):

        contents = [r["content"] for r in load_history()]
        contents.reverse()

        filename = export_history(contents)

        combined = "\n".join(contents)
        if self.monitor:
            self.monitor.last_text = combined
        pyperclip.copy(combined)

        speak("Exported and copied")
        wx.MessageBox(
            f"Exported {len(contents)} items to {filename}\n"
            "The whole history is also copied to the clipboard - paste it anywhere.",
            "Export Success"
        )

    def import_data(self, event):

        with wx.FileDialog(
            self, "Import history from a text file",
            wildcard="Text files (*.txt)|*.txt",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
        ) as dialog:

            if dialog.ShowModal() == wx.ID_CANCEL:
                return

            path = dialog.GetPath()

        try:
            with open(path, "r", encoding="utf-8") as file:
                lines = [line.rstrip("\n") for line in file]
        except Exception:
            wx.MessageBox("Could not read the file.", "Import Failed")
            return

        stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        import_items(lines, stamp)

        speak("Imported")
        self.apply_filters()
        wx.MessageBox(f"Imported items from {os.path.basename(path)}", "Import Success")

    def clear_data(self, event):

        answer = wx.MessageBox(
            "Clear the entire clipboard history?\nThis cannot be undone.",
            "Clear History",
            wx.YES_NO | wx.ICON_WARNING
        )
        if answer != wx.YES:
            return

        clear_history()
        speak("History cleared")

        self.showing_favorites = False
        self.show_favorites_button.SetLabel("Show Favorites")
        self.search.SetValue("")
        self.category_filter.SetSelection(0)
        self.apply_filters()

    def on_search(self, event):

        self.apply_filters()

    def on_filter(self, event):

        self.apply_filters()
        speak(f"{self.category_filter.GetStringSelection()}, {len(self.records)} items")

    def show_window(self):

        self.Iconize(False)
        self.Show()
        self.Raise()
