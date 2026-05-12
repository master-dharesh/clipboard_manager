from gui import ClipboardFrame
from startup import enable_startup
from tray_icon import create_tray
import wx

enable_startup()

app = wx.App()

frame = ClipboardFrame()
create_tray(frame)

frame.Show()

app.MainLoop()