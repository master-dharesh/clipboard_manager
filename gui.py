import wx
import pyperclip

from clipboard_monitor import ClipboardMonitor
from database import (
    create_database,
    load_history,
    load_favorites,
    delete_item,
    set_favorite,
    clear_history
)

from hotkeys import register_hotkeys
from exporter import export_history
from speech import speak

from settings import (
    APP_TITLE,
    WINDOW_WIDTH,
    WINDOW_HEIGHT
)

class ClipboardFrame(wx.Frame):

    def __init__(self):

        super().__init__(
            parent=None,
            title=APP_TITLE,
            size=(WINDOW_WIDTH, WINDOW_HEIGHT)
        )

        self.SetBackgroundColour(wx.Colour(30, 30, 30))
        self.SetForegroundColour(wx.Colour(255, 255, 255))

        create_database()

        panel = wx.Panel(self)

        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Visible label that screen readers announce for the search box.
        search_label = wx.StaticText(panel, label="Search clipboard history:")
        search_label.SetForegroundColour(wx.Colour(255, 255, 255))

        self.search = wx.TextCtrl(panel)
        self.search.SetHint("Search clipboard history")
        # Accessible name read aloud by screen readers (e.g. NVDA / Narrator).
        self.search.SetName("Search clipboard history")

        # Visible label for the history list.
        list_label = wx.StaticText(panel, label="Clipboard history:")
        list_label.SetForegroundColour(wx.Colour(255, 255, 255))

        self.listbox = wx.ListBox(panel)
        self.listbox.SetName("Clipboard history list")

        self.copy_button = wx.Button(panel, label="Copy Selected")
        self.delete_button = wx.Button(panel, label="Delete Selected")
        self.add_favorite_button = wx.Button(panel, label="Add to Favorites")
        self.remove_favorite_button = wx.Button(panel, label="Remove from Favorites")
        self.show_favorites_button = wx.Button(panel, label="Show Favorites")
        self.export_button = wx.Button(panel, label="Export History")
        self.clear_button = wx.Button(panel, label="Clear History")

        main_sizer.Add(search_label, 0, wx.LEFT | wx.TOP, 5)
        main_sizer.Add(self.search, 0, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(list_label, 0, wx.LEFT | wx.TOP, 5)
        main_sizer.Add(self.listbox, 1, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(self.copy_button, 0, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(self.delete_button, 0, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(self.add_favorite_button, 0, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(self.remove_favorite_button, 0, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(self.show_favorites_button, 0, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(self.export_button, 0, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(self.clear_button, 0, wx.EXPAND | wx.ALL, 5)

        panel.SetSizer(main_sizer)

        # records: the currently displayed list of items (dicts).
        self.records = []
        # showing_favorites: which view is active.
        self.showing_favorites = False

        self.load_clipboard_history()

        self.copy_button.Bind(wx.EVT_BUTTON, self.copy_selected)
        self.delete_button.Bind(wx.EVT_BUTTON, self.delete_selected)
        self.add_favorite_button.Bind(wx.EVT_BUTTON, self.add_favorite)
        self.remove_favorite_button.Bind(wx.EVT_BUTTON, self.remove_favorite)
        self.show_favorites_button.Bind(wx.EVT_BUTTON, self.toggle_view)
        self.export_button.Bind(wx.EVT_BUTTON, self.export_data)
        self.clear_button.Bind(wx.EVT_BUTTON, self.clear_data)

        self.search.Bind(wx.EVT_TEXT, self.on_search)

        self.listbox.Bind(
            wx.EVT_LISTBOX_DCLICK,
            self.copy_selected
        )

        self.monitor = ClipboardMonitor(
            self.add_clipboard_item
        )

        self.monitor.start()

        register_hotkeys(self.show_window)

    def format_label(self, record):

        star = "* " if record["favorite"] else ""

        return f"{star}[{record['category']}] {record['content']}"

    def refresh_listbox(self):

        labels = [
            self.format_label(record)
            for record in self.records
        ]

        self.listbox.Set(labels)

    def load_clipboard_history(self):

        if self.showing_favorites:
            self.records = load_favorites()
        else:
            self.records = load_history()

        self.refresh_listbox()

    def add_clipboard_item(self, text, category):

        wx.CallAfter(
            self.update_history,
            text,
            category
        )

    def update_history(self, text, category):

        # New clipboard items only show up in the full history view.
        if self.showing_favorites:
            return

        self.records = [
            r for r in self.records if r["content"] != text
        ]

        self.records.insert(
            0,
            {"content": text, "category": category, "favorite": 0}
        )

        self.refresh_listbox()

    def get_selected_record(self):

        selection = self.listbox.GetSelection()

        if selection == wx.NOT_FOUND:
            return None

        return self.records[selection]

    def copy_selected(self, event):

        record = self.get_selected_record()

        if record:

            pyperclip.copy(record["content"])

            speak("Copied")

            wx.MessageBox(
                "Copied to clipboard",
                "Success"
            )

    def delete_selected(self, event):

        record = self.get_selected_record()

        if record:

            delete_item(record["content"])

            speak("Deleted")

            self.load_clipboard_history()

    def add_favorite(self, event):

        record = self.get_selected_record()

        if record:

            set_favorite(record["content"], True)

            speak("Added to favorites")

            self.load_clipboard_history()

            wx.MessageBox("Added to favorites", "Favorite")

    def remove_favorite(self, event):

        record = self.get_selected_record()

        if record:

            set_favorite(record["content"], False)

            speak("Removed from favorites")

            self.load_clipboard_history()

            wx.MessageBox("Removed from favorites", "Favorite")

    def toggle_view(self, event):

        self.showing_favorites = not self.showing_favorites

        self.show_favorites_button.SetLabel(
            "Show All" if self.showing_favorites
            else "Show Favorites"
        )

        speak(
            "Showing favorites" if self.showing_favorites
            else "Showing all clips"
        )

        self.search.SetValue("")

        self.load_clipboard_history()

    def export_data(self, event):

        # Always export the COMPLETE history from the database,
        # regardless of the current search filter or favourites view.
        # load_history() returns newest first, so reverse it to get the
        # order the items were actually copied (first copied = first line).
        contents = [r["content"] for r in load_history()]
        contents.reverse()

        filename = export_history(contents)

        # Also put the WHOLE history on the clipboard as one block so it
        # can be pasted (e.g. into Notepad) in a single paste: one item
        # per line, in copy order, with no blank lines in between.
        combined = "\n".join(contents)

        # Stop the monitor from re-saving this big block as a new clip.
        if self.monitor:
            self.monitor.last_text = combined

        pyperclip.copy(combined)

        speak("Exported and copied")

        wx.MessageBox(
            f"Exported {len(contents)} items to {filename}\n"
            "The whole history is also copied to the clipboard - "
            "paste it anywhere.",
            "Export Success"
        )

    def clear_data(self, event):

        # Ask before wiping everything - this cannot be undone.
        answer = wx.MessageBox(
            "Clear the entire clipboard history?\n"
            "This cannot be undone.",
            "Clear History",
            wx.YES_NO | wx.ICON_WARNING
        )

        if answer != wx.YES:
            return

        clear_history()

        speak("History cleared")

        # Reset the view back to full history and refresh.
        self.showing_favorites = False
        self.show_favorites_button.SetLabel("Show Favorites")
        self.search.SetValue("")
        self.load_clipboard_history()

    def on_search(self, event):

        keyword = self.search.GetValue().lower()

        if self.showing_favorites:
            source = load_favorites()
        else:
            source = load_history()

        self.records = [
            record for record in source
            if keyword in record["content"].lower()
        ]

        self.refresh_listbox()

    def show_window(self):

        self.Show()

        self.Raise()
