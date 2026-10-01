from aqt import mw
from aqt.qt import QAction
from . import exporter

def setup_menu():
    # Tools menu action
    action = QAction("Export Today's Study Plan", mw)
    action.triggered.connect(exporter.export_study_plan)
    mw.form.menuTools.addAction(action)

setup_menu()
