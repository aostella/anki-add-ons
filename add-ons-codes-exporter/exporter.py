# Add-ons Codes Exporter
# Author: aostella

from aqt import mw
from aqt.qt import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QPushButton,
    QApplication,
    QGroupBox,
)
from aqt.utils import tooltip

def get_installed_addons():
    """Retrieve installed add-ons and separate numeric AnkiWeb codes from local add-ons."""
    if not mw or not hasattr(mw, "addonManager"):
        return [], []

    if hasattr(mw.addonManager, "all_addons"):
        all_addons = mw.addonManager.all_addons()
    elif hasattr(mw.addonManager, "allAddons"):
        all_addons = mw.addonManager.allAddons()
    else:
        all_addons = []

    numeric_addons = []
    local_addons = []

    for addon in all_addons:
        name = addon
        if hasattr(mw.addonManager, "addon_name"):
            name = mw.addonManager.addon_name(addon)
        elif hasattr(mw.addonManager, "addonName"):
            name = mw.addonManager.addonName(addon)

        if addon.isdigit():
            numeric_addons.append({"code": addon, "name": name})
        else:
            local_addons.append({"dir": addon, "name": name})

    return numeric_addons, local_addons


class AddonCodesExportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Export Add-on Codes")
        self.setMinimumWidth(500)
        self.setMinimumHeight(380)
        
        self.numeric_addons, self.local_addons = get_installed_addons()
        self.codes = [item["code"] for item in self.numeric_addons]

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Header Info
        header_text = f"Found <b>{len(self.codes)}</b> AnkiWeb add-on code(s) installed."
        if self.local_addons:
            header_text += f" ({len(self.local_addons)} custom/local add-on(s) excluded)."
        
        header_label = QLabel(header_text)
        header_label.setStyleSheet("font-size: 13px; margin-bottom: 5px;")
        layout.addWidget(header_label)

        # Single Clean Output Box (Space-separated for direct Anki paste)
        codes_group = QGroupBox("Add-on Codes (Ready to paste into Anki)")
        codes_layout = QHBoxLayout()
        
        codes_str = " ".join(self.codes) if self.codes else "No AnkiWeb add-ons found."
        self.codes_edit = QLineEdit(codes_str)
        self.codes_edit.setReadOnly(True)
        codes_layout.addWidget(self.codes_edit)

        copy_btn = QPushButton("Copy")
        copy_btn.clicked.connect(lambda: self.copy_to_clipboard(codes_str, "Add-on codes copied!"))
        codes_layout.addWidget(copy_btn)
        
        codes_group.setLayout(codes_layout)
        layout.addWidget(codes_group)

        # Installed Add-ons Details Summary
        details_group = QGroupBox("Installed Add-ons Summary")
        details_layout = QVBoxLayout()

        details_text = ""
        if self.numeric_addons:
            details_text += "AnkiWeb Add-ons:\n"
            for item in self.numeric_addons:
                details_text += f"  • [{item['code']}] {item['name']}\n"
        
        if self.local_addons:
            details_text += "\nLocal / Non-AnkiWeb Add-ons (no numeric code):\n"
            for item in self.local_addons:
                details_text += f"  • [{item['dir']}] {item['name']}\n"

        self.details_edit = QTextEdit()
        self.details_edit.setPlainText(details_text)
        self.details_edit.setReadOnly(True)
        details_layout.addWidget(self.details_edit)

        details_group.setLayout(details_layout)
        layout.addWidget(details_group)

        # Bottom Close Button
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        bottom_layout.addWidget(close_btn)

        layout.addLayout(bottom_layout)

    def copy_to_clipboard(self, text: str, message: str):
        if not text or text.startswith("No AnkiWeb"):
            tooltip("Nothing to copy!", period=2000)
            return

        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        tooltip(message, period=2000)


def show_export_dialog():
    dialog = AddonCodesExportDialog(mw)
    dialog.exec()
