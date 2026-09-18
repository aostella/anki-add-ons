# Today's Words Exporter for Anki
# Author: aostella

from aqt import mw, gui_hooks
from aqt.qt import QAction

from .exporter import export_today_words, export_selected_browser_words

def setup_menus():
    # Tools menu in main window
    action = QAction("Export Today's Added Words", mw)
    action.triggered.connect(export_today_words)
    mw.form.menuTools.addAction(action)

def on_browser_menus_init(browser):
    # Context/Edit menu in Card Browser
    action = QAction("Export Words from Selected Notes", browser)
    action.triggered.connect(lambda: export_selected_browser_words(browser))
    browser.form.menuEdit.addAction(action)

if mw:
    setup_menus()
    if hasattr(gui_hooks, "browser_menus_did_init"):
        gui_hooks.browser_menus_did_init.append(on_browser_menus_init)
