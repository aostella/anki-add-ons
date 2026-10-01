from aqt import mw
from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QPushButton, QApplication, QGroupBox, QScrollArea, QWidget, QCheckBox
)
from aqt.utils import tooltip, showInfo

class StudyPlanDialog(QDialog):
    def __init__(self, tree_nodes, parent=None):
        super().__init__(parent)
        self.tree_nodes = tree_nodes
        self.setWindowTitle("Export Today's Study Plan")
        self.setMinimumWidth(550)
        self.setMinimumHeight(450)
        self.checkboxes = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        info_label = QLabel("Select the decks to include in your study plan summary:")
        layout.addWidget(info_label)

        # Decks Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        for node in self.tree_nodes:
            cb = QCheckBox(f"{node['name']}  (New: {node['new']}, Learn: {node['learn']}, Due: {node['review']})")
            cb.setStyleSheet(f"margin-left: {node['level'] * 20}px;")
            # Default to checked only for decks that have cards due
            if node['new'] > 0 or node['learn'] > 0 or node['review'] > 0:
                cb.setChecked(True)
            else:
                cb.setChecked(False)
            cb.node_data = node
            cb.stateChanged.connect(self.update_text)
            self.checkboxes.append(cb)
            scroll_layout.addWidget(cb)
            
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        # Result Group
        output_group = QGroupBox("Result")
        output_layout = QVBoxLayout()
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        output_layout.addWidget(self.text_edit)
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)

        # Buttons
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
        
        self.update_text()

    def update_text(self):
        lines = []
        for cb in self.checkboxes:
            if cb.isChecked():
                node = cb.node_data
                # Format based on user's preference: "Deck: X reviewed, Y learned"
                lines.append(f"{node['name']}: {node['review']} reviewed, {node['new']} learned")
        
        self.text_edit.setPlainText("\n".join(lines))

    def copy_to_clipboard(self):
        content = self.text_edit.toPlainText().strip()
        if not content:
            tooltip("Nothing to copy!", period=2000)
            return

        clipboard = QApplication.clipboard()
        clipboard.setText(content)
        tooltip("Study plan copied to clipboard!", period=2000)

def extract_tree(node, level=0):
    result = []
    # In Anki 2.1+, root node might have deck_id == 0 or None.
    # The actual decks have deck_id > 0
    if getattr(node, 'deck_id', 0) > 0:
        result.append({
            "name": node.name,
            "id": node.deck_id,
            "level": level,
            "new": getattr(node, 'new_count', 0),
            "learn": getattr(node, 'learn_count', 0),
            "review": getattr(node, 'review_count', 0)
        })
    for child in getattr(node, 'children', []):
        result.extend(extract_tree(child, level + 1 if getattr(node, 'deck_id', 0) > 0 else level))
    return result

def export_study_plan():
    if not mw or not mw.col:
        return
    
    # Refresh to ensure counts are accurate
    mw.col.reset() 
    tree = mw.col.sched.deck_due_tree()
    nodes = extract_tree(tree)
    
    if not nodes:
        showInfo("No decks found.")
        return
        
    dialog = StudyPlanDialog(nodes, parent=mw)
    dialog.exec()
