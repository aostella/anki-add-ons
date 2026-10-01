from aqt import mw
from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QPushButton, QApplication, QGroupBox, QScrollArea, QWidget, QCheckBox
)
from aqt.utils import tooltip, showInfo

def get_studied_today():
    try:
        # Anki 2.1+ dayCutoff is the end of the day.
        day_start = (mw.col.sched.day_cutoff - 86400) * 1000
    except AttributeError:
        try:
            day_start = (mw.col.sched.dayCutoff - 86400) * 1000
        except AttributeError:
            import time
            t = time.localtime()
            day_start = int(time.mktime((t.tm_year, t.tm_mon, t.tm_mday, 4, 0, 0, t.tm_wday, t.tm_yday, t.tm_isdst))) * 1000

    try:
        today = mw.col.sched.today
    except AttributeError:
        today = 0 # Fallback, might cause minor inaccuracy if missing, but usually exists.

    raw_studied = {}
    
    # 1. New cards studied today
    new_studied = mw.col.db.all(f"""
        select c.did, count(distinct r.cid)
        from revlog r
        join cards c on r.cid = c.id
        where r.id >= {day_start} and r.type = 0
        group by c.did
    """)
    
    for did, count in new_studied:
        if did not in raw_studied:
            raw_studied[did] = {"s_new": 0, "s_rev": 0, "s_lfn": 0}
        raw_studied[did]["s_new"] += count
        
    # 2. Review cards studied today that are NO LONGER pending today
    # (queue 2 = review, queue 3 = day learn, queue 4 = buried, -1 = suspended)
    rev_studied = mw.col.db.all(f"""
        select c.did, count(distinct r.cid)
        from revlog r
        join cards c on r.cid = c.id
        where r.id >= {day_start} and r.type in (1, 2, 3)
        and (
            (c.queue = 2 and c.due > {today}) or 
            (c.queue = 3 and c.due > {today}) or 
            c.queue in (4, -1)
        )
        group by c.did
    """)
    
    for did, count in rev_studied:
        if did not in raw_studied:
            raw_studied[did] = {"s_new": 0, "s_rev": 0, "s_lfn": 0}
        raw_studied[did]["s_rev"] += count

    # 3. Cards that were introduced today but are STILL pending learn today
    # We subtract these from the review_total so they don't inflate the review counts!
    learn_from_new = mw.col.db.all(f"""
        select c.did, count(distinct r.cid)
        from revlog r
        join cards c on r.cid = c.id
        where r.id >= {day_start} and r.type = 0
        and c.queue in (1, 3) and c.due <= {today}
        group by c.did
    """)
    
    for did, count in learn_from_new:
        if did not in raw_studied:
            raw_studied[did] = {"s_new": 0, "s_rev": 0, "s_lfn": 0}
        raw_studied[did]["s_lfn"] += count

    return raw_studied

def get_total_studied(node, raw_studied):
    did = getattr(node, 'deck_id', 0)
    s_new = raw_studied.get(did, {}).get("s_new", 0)
    s_rev = raw_studied.get(did, {}).get("s_rev", 0)
    s_lfn = raw_studied.get(did, {}).get("s_lfn", 0)
    
    for child in getattr(node, 'children', []):
        c_new, c_rev, c_lfn = get_total_studied(child, raw_studied)
        s_new += c_new
        s_rev += c_rev
        s_lfn += c_lfn
        
    return s_new, s_rev, s_lfn

def build_flat_tree(node, raw_studied, level=0):
    result = []
    did = getattr(node, 'deck_id', 0)
    
    s_new, s_rev, s_lfn = get_total_studied(node, raw_studied)
    
    p_new = getattr(node, 'new_count', 0)
    p_learn = getattr(node, 'learn_count', 0)
    p_review = getattr(node, 'review_count', 0)
    
    if did > 0:
        result.append({
            "name": node.name,
            "id": did,
            "level": level,
            # Initial New = Pending New + New Studied
            "new_total": p_new + s_new,
            # Initial Review = Pending Review + Pending Learn + Completed Reviews - (Pending Learn that were New today)
            "review_total": p_review + p_learn + s_rev - s_lfn,
        })
        
    for child in getattr(node, 'children', []):
        result.extend(build_flat_tree(child, raw_studied, level + 1 if did > 0 else level))
        
    return result

class StudyPlanDialog(QDialog):
    def __init__(self, tree_nodes, parent=None):
        super().__init__(parent)
        self.tree_nodes = tree_nodes
        self.setWindowTitle("Export Today's Study Plan")
        self.setMinimumWidth(550)
        self.setMinimumHeight(450)
        self.checkboxes = []
        
        self.addon_name = __name__.split('.')[0]
        self.addon_config = mw.addonManager.getConfig(self.addon_name) or {}
        
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        info_label = QLabel("Select the decks to include in your study plan summary:")
        layout.addWidget(info_label)

        self.merge_cb = QCheckBox("Merge subdecks into parent decks (Show top-level only)")
        self.merge_cb.setChecked(self.addon_config.get("merge_subdecks", False))
        self.merge_cb.stateChanged.connect(self.on_merge_toggled)
        layout.addWidget(self.merge_cb)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        has_run_before = self.addon_config.get("has_run_before", False)
        saved_decks = self.addon_config.get("selected_decks", [])
        
        for node in self.tree_nodes:
            cb = QCheckBox(f"{node['name']}  (Total New: {node['new_total']}, Total Due: {node['review_total']})")
            cb.setStyleSheet(f"margin-left: {node['level'] * 20}px;")
            
            if not has_run_before:
                cb.setChecked(node['new_total'] > 0 or node['review_total'] > 0)
            else:
                cb.setChecked(node['id'] in saved_decks)
                
            cb.node_data = node
            cb.stateChanged.connect(self.on_checkbox_changed)
            self.checkboxes.append(cb)
            scroll_layout.addWidget(cb)
            
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        output_group = QGroupBox("Result")
        output_layout = QVBoxLayout()
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        output_layout.addWidget(self.text_edit)
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)

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
        
        self.apply_merge_visibility()
        self.update_text()

    def on_merge_toggled(self):
        self.addon_config["merge_subdecks"] = self.merge_cb.isChecked()
        self.save_config()
        self.apply_merge_visibility()
        self.update_text()
        
    def apply_merge_visibility(self):
        is_merged = self.merge_cb.isChecked()
        for cb in self.checkboxes:
            if is_merged and cb.node_data['level'] > 0:
                cb.setVisible(False)
            else:
                cb.setVisible(True)

    def on_checkbox_changed(self):
        selected = []
        for cb in self.checkboxes:
            if cb.isChecked():
                selected.append(cb.node_data['id'])
        self.addon_config["selected_decks"] = selected
        self.addon_config["has_run_before"] = True
        self.save_config()
        self.update_text()
        
    def save_config(self):
        mw.addonManager.writeConfig(self.addon_name, self.addon_config)

    def update_text(self):
        lines = []
        is_merged = self.merge_cb.isChecked()
        
        for cb in self.checkboxes:
            node = cb.node_data
            if is_merged and node['level'] > 0:
                continue
            if cb.isChecked():
                lines.append(f"{node['name']}: {node['review_total']} reviewed, {node['new_total']} learned")
        
        self.text_edit.setPlainText("\n".join(lines))

    def copy_to_clipboard(self):
        content = self.text_edit.toPlainText().strip()
        if not content:
            tooltip("Nothing to copy!", period=2000)
            return

        clipboard = QApplication.clipboard()
        clipboard.setText(content)
        tooltip("Study plan copied to clipboard!", period=2000)

def export_study_plan():
    if not mw or not mw.col:
        return
    
    mw.col.reset()
    tree = mw.col.sched.deck_due_tree()
    raw_studied = get_studied_today()
    nodes = build_flat_tree(tree, raw_studied)
    
    if not nodes:
        showInfo("No decks found.")
        return
        
    dialog = StudyPlanDialog(nodes, parent=mw)
    dialog.exec()
