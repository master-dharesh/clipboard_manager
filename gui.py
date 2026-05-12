import wx
import pyperclip

from clipboard_monitor import ClipboardMonitor
from database import (
    create_database,
    load_history,
    delete_item,
    mark_favorite
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

        self.search = wx.TextCtrl(panel)
        self.search.SetHint("Search clipboard history")

        self.listbox = wx.ListBox(panel)

        self.copy_button = wx.Button(panel, label="Copy Selected")
        self.delete_button = wx.Button(panel, label="Delete Selected")
        self.favorite_button = wx.Button(panel, label="Add to Favorites")
        self.export_button = wx.Button(panel, label="Export History")

        main_sizer.Add(self.search, 0, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(self.listbox, 1, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(self.copy_button, 0, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(self.delete_button, 0, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(self.favorite_button, 0, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(self.export_button, 0, wx.EXPAND | wx.ALL, 5)

        panel.SetSizer(main_sizer)

        self.history = []

        self.load_clipboard_history()

        self.copy_button.Bind(wx.EVT_BUTTON, self.copy_selected)
        self.delete_button.Bind(wx.EVT_BUTTON, self.delete_selected)
        self.favorite_button.Bind(wx.EVT_BUTTON, self.add_favorite)
        self.export_button.Bind(wx.EVT_BUTTON, self.export_data)

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

    def load_clipboard_history(self):

        self.history = load_history()

        self.listbox.Set(self.history)

    def add_clipboard_item(self, text):

        wx.CallAfter(
            self.update_history,
            text
        )

    def update_history(self, text):

        if text not in self.history:

            self.history.insert(0, text)

            self.listbox.Set(self.history)

    def copy_selected(self, event):

        selection = self.listbox.GetSelection()

        if selection != wx.NOT_FOUND:

            text = self.listbox.GetString(selection)

            pyperclip.copy(text)

            speak("Copied")

            wx.MessageBox(
                "Copied to clipboard",
                "Success"
            )

    def delete_selected(self, event):

        selection = self.listbox.GetSelection()

        if selection != wx.NOT_FOUND:

            text = self.listbox.GetString(selection)

            delete_item(text)

            self.history.remove(text)

            self.listbox.Set(self.history)

    def add_favorite(self, event):

        selection = self.listbox.GetSelection()

        if selection != wx.NOT_FOUND:

            text = self.listbox.GetString(selection)

            mark_favorite(text)

            wx.MessageBox(
                "Added to favorites",
                "Favorite"
            )

    def export_data(self, event):

        filename = export_history(self.history)

        wx.MessageBox(
            f"Exported to {filename}",
            "Export Success"
        )

    def on_search(self, event):

        keyword = self.search.GetValue().lower()

        filtered = [
            item for item in self.history
            if keyword in item.lower()
        ]

        self.listbox.Set(filtered)

    def show_window(self):

        self.Show()

        self.Raise()