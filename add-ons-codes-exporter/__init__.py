# Add-ons Codes Exporter for Anki
# Author: aostella

from aqt import mw
from aqt.qt import QAction
from aqt.utils import showInfo

from .exporter import show_export_dialog

def setup_menu():
    action = QAction("Export Add-on Codes", mw)
    action.setShortcut("Ctrl+Alt+E")
    action.triggered.connect(show_export_dialog)
    mw.form.menuTools.addAction(action)

if mw:
    setup_menu()
