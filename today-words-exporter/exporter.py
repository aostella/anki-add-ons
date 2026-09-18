# Today's Words Exporter
# Author: aostella

import re
from aqt import mw
from aqt.qt import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTextEdit,
    QPushButton,
    QRadioButton,
    QButtonGroup,
    QApplication,
    QGroupBox,
)
from aqt.utils import tooltip, showInfo

def clean_word(raw_text: str) -> str:
    """Clean HTML tags and extra whitespace from field text."""
    if not raw_text:
        return ""
    # Strip HTML tags
    cleaned = re.sub(r"<[^>]+>", "", raw_text)
    # Strip sound tags or media references if any e.g. [sound:...]
    cleaned = re.sub(r"\[sound:[^\]]+\]", "", cleaned)
    # Strip leading/trailing whitespaces
    return cleaned.strip()

def extract_words_from_notes(nids) -> list:
    """Extract first field (expression/word) from given note IDs without duplicates."""
    words = []
    seen = set()

    for nid in nids:
        try:
            note = mw.col.get_note(nid)
            if note and note.fields:
                word = clean_word(note.fields[0])
                if word and word not in seen:
                    seen.add(word)
                    words.append(word)
        except Exception:
            continue

    return words


class WordsExportDialog(QDialog):
    def __init__(self, words: list, title_suffix: str = "Today's Added Words", parent=None):
        super().__init__(parent)
        self.words = words
        self.setWindowTitle(f"Export Words - {title_suffix}")
        self.setMinimumWidth(550)
        self.setMinimumHeight(400)

        # Default separator: Japanese comma
        self.current_separator = "、"

        self.init_ui(title_suffix)

    def init_ui(self, title_suffix: str):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Header Info
        header_text = f"Found <b>{len(self.words)}</b> unique word(s) from {title_suffix}."
        header_label = QLabel(header_text)
        header_label.setStyleSheet("font-size: 13px; margin-bottom: 5px;")
        layout.addWidget(header_label)

        # Separator Option Group
        sep_group = QGroupBox("Separator Style")
        sep_layout = QHBoxLayout()

        self.btn_group = QButtonGroup(self)

        self.rb_ja = QRadioButton("Japanese Comma ( 、 )")
        self.rb_ja_space = QRadioButton("Japanese Comma + Space ( 、 )")
        self.rb_std = QRadioButton("Standard Comma ( ,  )")

        self.rb_ja.setChecked(True)

        self.btn_group.addButton(self.rb_ja, 1)
        self.btn_group.addButton(self.rb_ja_space, 2)
        self.btn_group.addButton(self.rb_std, 3)

        self.btn_group.idClicked.connect(self.on_separator_changed)

        sep_layout.addWidget(self.rb_ja)
        sep_layout.addWidget(self.rb_ja_space)
        sep_layout.addWidget(self.rb_std)
        sep_group.setLayout(sep_layout)
        layout.addWidget(sep_group)

        # Result Text Box
        output_group = QGroupBox("Result (Sentence / Word List)")
        output_layout = QVBoxLayout()

        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.update_text()
        output_layout.addWidget(self.text_edit)

        output_group.setLayout(output_layout)
        layout.addWidget(output_group)

        # Action Buttons
        btn_layout = QHBoxLayout()

        copy_btn = QPushButton("Copy to Clipboard")
        copy_btn.setStyleSheet("font-weight: bold; padding: 6px 14px;")
        copy_btn.clicked.connect(self.copy_to_clipboard)
        btn_layout.addWidget(copy_btn)

        btn_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

    def on_separator_changed(self, button_id: int):
        if button_id == 1:
            self.current_separator = "、"
        elif button_id == 2:
            self.current_separator = "、 "
        elif button_id == 3:
            self.current_separator = ", "
        self.update_text()

    def update_text(self):
        if not self.words:
            self.text_edit.setPlainText("No words found.")
        else:
            self.text_edit.setPlainText(self.current_separator.join(self.words))

    def copy_to_clipboard(self):
        content = self.text_edit.toPlainText().strip()
        if not content or content == "No words found.":
            tooltip("Nothing to copy!", period=2000)
            return

        clipboard = QApplication.clipboard()
        clipboard.setText(content)
        tooltip("Words copied to clipboard!", period=2000)


def export_today_words():
    """Query cards/notes added today (added:1) and display export dialog."""
    if not mw or not mw.col:
        return

    nids = mw.col.find_notes("added:1")
    if not nids:
        showInfo("No cards/notes found that were added today (added:1).")
        return

    words = extract_words_from_notes(nids)
    if not words:
        showInfo("Found notes added today, but could not extract words from the first field.")
        return

    dialog = WordsExportDialog(words, title_suffix="Today's Added Cards", parent=mw)
    dialog.exec()


def export_selected_browser_words(browser):
    """Extract words from currently selected notes in browser."""
    if not browser:
        return

    nids = browser.selected_notes()
    if not nids:
        # Fallback to selected cards if notes not directly returned
        cids = browser.selected_cards()
        if cids and mw and mw.col:
            nids = list({mw.col.get_card(cid).nid for cid in cids})

    if not nids:
        showInfo("Please select at least one note/card in the browser first.")
        return

    words = extract_words_from_notes(nids)
    if not words:
        showInfo("No words could be extracted from the selected notes.")
        return

    dialog = WordsExportDialog(words, title_suffix="Selected Notes", parent=browser)
    dialog.exec()
