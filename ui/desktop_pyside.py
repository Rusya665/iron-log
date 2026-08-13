"""PySide6 (Qt 6) Desktop GUI Implementation for Iron Log.

Provides a high-performance C++ backend UI with smooth 60fps rendering,
declarative QSS dark theme, non-blocking background workers, and full feature parity.
"""

import os
import re
import sys
import threading
import webbrowser
from datetime import datetime
from typing import List, Optional

from PySide6.QtCore import QObject, QRunnable, QSize, Qt, QThreadPool, QTimer, Signal
from PySide6.QtGui import QAction, QColor, QCursor, QFont, QIcon, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMenuBar,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.models import Log
from core.plan_generator import (
    PlannedExercise,
    PlannedSession,
    build_planned_sessions,
    build_pre_deload_baseline,
    calculate_gym_stats,
    days_to_generate,
    detect_cycle,
    get_genuinely_new_exercises,
    write_planned_sessions,
)
from core.profile_manager import Profile, ProfileManager
from core.standards import EXERCISE_STANDARDS, get_exercise_standard, get_tiered_standards
from core.version import __version__
from core.xlsx_generator import TrainingLogProcessor

PYSIDE_DARK_QSS = """
QMainWindow, QDialog {
    background-color: #121214;
    color: #F4F4F5;
    font-family: 'Segoe UI', -apple-system, sans-serif;
}
QWidget {
    color: #E4E4E7;
    font-size: 13px;
}
QFrame#CardFrame {
    background-color: #18181B;
    border: 1px solid #27272A;
    border-radius: 8px;
}
QFrame#StatCard {
    background-color: #18181B;
    border: 1px solid #27272A;
    border-radius: 8px;
    padding: 8px;
}
QFrame#SessionCard {
    background-color: #1C1C20;
    border: 1px solid #2E2E35;
    border-radius: 8px;
}
QLabel#CardTitle {
    color: #A1A1AA;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
}
QLabel#CardValue {
    color: #38BDF8;
    font-size: 18px;
    font-weight: bold;
}
QLabel#CardSub {
    color: #71717A;
    font-size: 11px;
}
QPushButton {
    background-color: #27272A;
    color: #F4F4F5;
    border: 1px solid #3F3F46;
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: 600;
    font-size: 12px;
}
QPushButton:hover {
    background-color: #3F3F46;
    border-color: #52525B;
}
QPushButton:pressed {
    background-color: #18181B;
}
QPushButton#PrimaryBtn {
    background-color: #2563EB;
    color: #FFFFFF;
    border: 1px solid #3B82F6;
}
QPushButton#PrimaryBtn:hover {
    background-color: #1D4ED8;
}
QPushButton#SuccessBtn {
    background-color: #15803D;
    color: #FFFFFF;
    border: 1px solid #22C55E;
}
QPushButton#SuccessBtn:hover {
    background-color: #166534;
}
QPushButton#DangerBtn {
    background-color: #991B1B;
    color: #FFFFFF;
    border: 1px solid #EF4444;
}
QPushButton#DangerBtn:hover {
    background-color: #7F1D1D;
}
QPushButton#SmallToolBtn {
    background-color: #27272A;
    color: #D4D4D8;
    border: 1px solid #3F3F46;
    border-radius: 4px;
    padding: 2px 6px;
    font-size: 11px;
}
QPushButton#SmallToolBtn:hover {
    background-color: #3B82F6;
    color: #FFFFFF;
}
QLineEdit, QComboBox {
    background-color: #1C1C20;
    color: #F4F4F5;
    border: 1px solid #3F3F46;
    border-radius: 6px;
    padding: 5px 10px;
    font-size: 12px;
}
QLineEdit:focus, QComboBox:focus {
    border: 1px solid #3B82F6;
}
QComboBox::drop-down {
    border: none;
}
QComboBox QAbstractItemView {
    background-color: #18181B;
    color: #F4F4F5;
    selection-background-color: #2563EB;
    border: 1px solid #3F3F46;
}
QScrollArea {
    border: none;
    background-color: transparent;
}
QScrollBar:vertical, QScrollBar:horizontal {
    background: #121214;
    border-radius: 4px;
}
QScrollBar:vertical {
    width: 8px;
}
QScrollBar:horizontal {
    height: 8px;
}
QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
    background: #3F3F46;
    border-radius: 4px;
    min-height: 20px;
}
QScrollBar::handle:hover {
    background: #52525B;
}
QScrollBar::add-line, QScrollBar::sub-line {
    border: none;
    background: none;
}
QTableWidget {
    background-color: #18181B;
    gridline-color: #27272A;
    border: 1px solid #27272A;
    border-radius: 6px;
}
QTableWidget::item {
    padding: 4px;
}
QTableWidget::item:selected {
    background-color: #2563EB;
}
QHeaderView::section {
    background-color: #27272A;
    color: #E4E4E7;
    font-weight: bold;
    padding: 6px;
    border: none;
    border-right: 1px solid #3F3F46;
}
QToolTip {
    background-color: #18181B;
    color: #F4F4F5;
    border: 1px solid #3F3F46;
    border-radius: 4px;
    padding: 6px;
    font-size: 11px;
}
QProgressBar {
    border: 1px solid #3F3F46;
    border-radius: 4px;
    text-align: center;
    background-color: #1C1C20;
    color: #FFFFFF;
    font-size: 11px;
}
QProgressBar::chunk {
    background-color: #3B82F6;
    border-radius: 3px;
}
"""


class WorkerSignals(QObject):
    finished = Signal(object)
    error = Signal(str)
    progress = Signal(str)


class ExcelWorker(QRunnable):
    def __init__(self, profile: Profile, sessions_module):
        super().__init__()
        self.profile = profile
        self.sessions = sessions_module
        self.signals = WorkerSignals()

    def run(self):
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
            filename = os.path.join(
                self.profile.output_dir, f"Training_Log_{timestamp}.xlsx"
            )
            processor = TrainingLogProcessor(
                filename,
                self.sessions.EXERCISE_REGISTRY,
                self.sessions.USER_DATA,
                self.sessions.BODYMASS_LOG,
                self.profile.to_dict(),
            )
            processor.validate_data()
            processor.write_headers()
            processor.process_data(self.sessions.USER_DATA)
            processor.write_calculations()
            processor.generate_charts()
            processor.write_definitions()
            processor.write_personal_records()
            processor.write_user_profile()
            processor.save()
            self.signals.finished.emit(filename)
        except Exception as e:
            self.signals.error.emit(str(e))


class PySideStandardsDialog(QDialog):
    """Strength Standards Browser with instant search and Copy Py variable generator."""

    def __init__(self, parent=None, user_sex="male", user_mass=80.0):
        super().__init__(parent)
        self.setWindowTitle("Exercise Standards Library — PySide6")
        self.resize(780, 560)
        self.user_sex = user_sex
        self.user_mass = user_mass

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        # Search Bar
        search_frame = QHBoxLayout()
        lbl = QLabel("Search Exercises:")
        lbl.setStyleSheet("font-weight: bold; font-size: 13px;")
        search_frame.addWidget(lbl)

        self.search_entry = QLineEdit()
        self.search_entry.setPlaceholderText("Type exercise name or slug (e.g. bench press, squat, pull up)...")
        self.search_entry.textChanged.connect(self._filter_exercises)
        search_frame.addWidget(self.search_entry)

        layout.addLayout(search_frame)

        # Standards Table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Exercise Name", "Slug", "Beg", "Nov", "Int", "Adv", "Eli", "Actions"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        for i in range(2, 7):
            self.table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

        self._populate_all()

    def _populate_all(self):
        self._filter_exercises(self.search_entry.text())

    def _filter_exercises(self, query: str):
        q = query.strip().lower()
        self.table.setRowCount(0)

        row_idx = 0
        for slug, info in EXERCISE_STANDARDS.items():
            name = info.get("name", slug)
            if q and (q not in name.lower() and q not in slug.lower()):
                continue

            self.table.insertRow(row_idx)

            # Name & Slug
            name_item = QTableWidgetItem(name)
            name_item.setToolTip(f"Slug: {slug}")
            slug_item = QTableWidgetItem(slug)
            slug_item.setForeground(QColor("#38BDF8"))

            self.table.setItem(row_idx, 0, name_item)
            self.table.setItem(row_idx, 1, slug_item)

            # Standards
            standards = get_tiered_standards(slug, self.user_sex, self.user_mass)
            target_bm = int(self.user_mass / 5.0) * 5
            level_dict = standards.get(target_bm, {}) if standards else {}

            for col_i, lvl in enumerate(["Beginner", "Novice", "Intermediate", "Advanced", "Elite"], 2):
                val = level_dict.get(lvl, "-")
                item = QTableWidgetItem(f"{val}kg" if isinstance(val, (int, float)) else str(val))
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row_idx, col_i, item)

            # Action Buttons Cell
            act_widget = QWidget()
            act_layout = QHBoxLayout(act_widget)
            act_layout.setContentsMargins(2, 2, 2, 2)
            act_layout.setSpacing(4)

            # Copy Slug
            btn_slug = QPushButton("Copy")
            btn_slug.setObjectName("SmallToolBtn")
            btn_slug.clicked.connect(lambda _, s=slug: self._copy_text(s, f"Copied slug '{s}'!"))
            act_layout.addWidget(btn_slug)

            # Copy Py
            btn_py = QPushButton("Copy Py")
            btn_py.setObjectName("SmallToolBtn")
            btn_py.setStyleSheet("background-color: #15803D; color: white;")
            py_code = f'{slug.replace("-", "_")} = "{slug}"'
            btn_py.clicked.connect(lambda _, c=py_code: self._copy_text(c, f"Copied '{c}'!"))
            act_layout.addWidget(btn_py)

            # View on Web
            btn_web = QPushButton("View")
            btn_web.setObjectName("SmallToolBtn")
            btn_web.clicked.connect(lambda _, s=slug: webbrowser.open(f"https://strengthlevel.com/strength-standards/{s}"))
            act_layout.addWidget(btn_web)

            self.table.setCellWidget(row_idx, 7, act_widget)
            row_idx += 1

    def _copy_text(self, text: str, msg: str):
        QApplication.clipboard().setText(text)
        QMessageBox.information(self, "Clipboard", msg)


class PySideSplitDetailsDialog(QDialog):
    """Split structure, routine breakdown, and historical cycles view."""

    def __init__(self, parent=None, stats=None):
        super().__init__(parent)
        self.setWindowTitle("Current Split Details & History — PySide6")
        self.resize(650, 480)
        stats = stats or {}

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(15, 15, 15, 15)

        # Overview Card
        card = QFrame()
        card.setObjectName("CardFrame")
        c_layout = QVBoxLayout(card)

        title = QLabel("Split Routine Overview")
        title.setStyleSheet("font-weight: bold; font-size: 15px; color: #38BDF8;")
        c_layout.addWidget(title)

        weeks = stats.get("current_split_weeks", 0.0)
        start = stats.get("current_split_start", "N/A")
        cycle_len = stats.get("cycle_length", "N/A")

        c_layout.addWidget(QLabel(f"• Active Split Duration: <b>{weeks:.1f} weeks</b> (Started {start})"))
        c_layout.addWidget(QLabel(f"• Detected Cycle Length: <b>{cycle_len} Days</b>"))
        c_layout.addWidget(QLabel(f"• Total Recorded Sessions: <b>{stats.get('total_days', 0)}</b>"))
        layout.addWidget(card)

        # Sessions history table
        history_title = QLabel("Recent Split Cycle History:")
        history_title.setStyleSheet("font-weight: bold;")
        layout.addWidget(history_title)

        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["Date", "Day", "Exercises Count"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)

        sessions = stats.get("split_sessions_details", [])
        table.setRowCount(len(sessions))
        for r, s in enumerate(reversed(sessions)):
            table.setItem(r, 0, QTableWidgetItem(s.get("date_str", "")))
            table.setItem(r, 1, QTableWidgetItem(str(s.get("day", ""))))
            table.setItem(r, 2, QTableWidgetItem(str(len(s.get("exercises", [])))))
        layout.addWidget(table)


class PySideDynamicPlanDialog(QDialog):
    """Dynamic Workout Cycle Planner with reordering, deloads, and validation."""

    def __init__(self, parent, planned: List[PlannedSession], sessions_file_path: str):
        super().__init__(parent)
        self.setWindowTitle("Dynamic Plan Generator — PySide6")
        self.resize(980, 680)
        self.planned = planned
        self.sessions_file_path = sessions_file_path
        self.row_widgets = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Top Action Bar
        top_bar = QHBoxLayout()
        
        btn_deload = QPushButton("Deload (-10%)")
        btn_deload.clicked.connect(self._apply_deload)
        top_bar.addWidget(btn_deload)

        btn_restore = QPushButton("Restore Pre-Deload")
        btn_restore.clicked.connect(self._restore_pre_deload)
        top_bar.addWidget(btn_restore)

        btn_add_day = QPushButton("+ Add Day")
        btn_add_day.clicked.connect(self._add_day)
        top_bar.addWidget(btn_add_day)

        top_bar.addStretch()

        btn_save = QPushButton("Save Plan to sessions.py")
        btn_save.setObjectName("SuccessBtn")
        btn_save.clicked.connect(self._save_plan)
        top_bar.addWidget(btn_save)

        layout.addLayout(top_bar)

        # Scroll area containing planned days
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setSpacing(15)
        self.scroll.setWidget(self.container)
        layout.addWidget(self.scroll)

        self._render_plan()

    def _render_plan(self):
        # Clear existing
        while self.container_layout.count():
            item = self.container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.row_widgets.clear()

        for d_idx, ps in enumerate(self.planned):
            day_card = QFrame()
            day_card.setObjectName("CardFrame")
            day_layout = QVBoxLayout(day_card)
            day_layout.setContentsMargins(12, 12, 12, 12)
            day_layout.setSpacing(8)

            # Header row
            h_row = QHBoxLayout()
            lbl = QLabel(f"Day {ps.day_num}")
            lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #38BDF8;")
            h_row.addWidget(lbl)

            date_input = QLineEdit(ps.date_str)
            date_input.setPlaceholderText("YYYY-MM-DD")
            date_input.setFixedWidth(120)
            date_input.textChanged.connect(lambda val, s=ps: setattr(s, "date_str", val))
            h_row.addWidget(date_input)

            h_row.addStretch()

            btn_add_ex = QPushButton("+ Add Exercise")
            btn_add_ex.setObjectName("SmallToolBtn")
            btn_add_ex.clicked.connect(lambda _, s=ps: self._add_exercise(s))
            h_row.addWidget(btn_add_ex)

            btn_del_day = QPushButton("Delete Day")
            btn_del_day.setObjectName("DangerBtn")
            btn_del_day.clicked.connect(lambda _, idx=d_idx: self._remove_day(idx))
            h_row.addWidget(btn_del_day)

            day_layout.addLayout(h_row)

            # Exercises rows
            for ex_idx, ex in enumerate(ps.exercises):
                row_frame = QFrame()
                row_frame.setObjectName("SessionCard")
                r_layout = QHBoxLayout(row_frame)
                r_layout.setContentsMargins(6, 4, 6, 4)
                r_layout.setSpacing(6)

                # Up / Down Order buttons
                btn_up = QPushButton("▲")
                btn_up.setFixedSize(24, 24)
                btn_up.clicked.connect(lambda _, s=ps, e=ex: self._move_up(s, e))
                r_layout.addWidget(btn_up)

                btn_down = QPushButton("▼")
                btn_down.setFixedSize(24, 24)
                btn_down.clicked.connect(lambda _, s=ps, e=ex: self._move_down(s, e))
                r_layout.addWidget(btn_down)

                # Exercise Slug/Name
                name_in = QLineEdit(ex.var_name)
                name_in.setPlaceholderText("Exercise variable")
                name_in.setMinimumWidth(180)
                name_in.textChanged.connect(lambda val, e=ex: setattr(e, "var_name", val))
                r_layout.addWidget(name_in)

                # Sets
                sets_in = QLineEdit(str(ex.sets))
                sets_in.setFixedWidth(50)
                sets_in.setPlaceholderText("Sets")
                sets_in.textChanged.connect(lambda val, e=ex: setattr(e, "sets", val))
                r_layout.addWidget(sets_in)

                # Reps
                reps_in = QLineEdit(str(ex.reps))
                reps_in.setFixedWidth(100)
                reps_in.setPlaceholderText("Reps (e.g. 5,5,5)")
                reps_in.textChanged.connect(lambda val, e=ex: setattr(e, "reps", val))
                r_layout.addWidget(reps_in)

                # Mass
                mass_in = QLineEdit(str(ex.mass))
                mass_in.setFixedWidth(100)
                mass_in.setPlaceholderText("Mass (kg)")
                mass_in.textChanged.connect(lambda val, e=ex: setattr(e, "mass", val))
                r_layout.addWidget(mass_in)

                # Comment
                comm_in = QLineEdit(ex.comment)
                comm_in.setPlaceholderText("Comment / Note")
                comm_in.textChanged.connect(lambda val, e=ex: setattr(e, "comment", val))
                r_layout.addWidget(comm_in)

                # Remove button
                btn_del = QPushButton("✕")
                btn_del.setFixedSize(24, 24)
                btn_del.setObjectName("DangerBtn")
                btn_del.clicked.connect(lambda _, s=ps, e=ex: self._remove_exercise(s, e))
                r_layout.addWidget(btn_del)

                day_layout.addWidget(row_frame)

            self.container_layout.addWidget(day_card)

        self.container_layout.addStretch()

    def _move_up(self, ps: PlannedSession, ex: PlannedExercise):
        idx = ps.exercises.index(ex)
        if idx > 0:
            ps.exercises[idx - 1], ps.exercises[idx] = ps.exercises[idx], ps.exercises[idx - 1]
            self._render_plan()

    def _move_down(self, ps: PlannedSession, ex: PlannedExercise):
        idx = ps.exercises.index(ex)
        if idx < len(ps.exercises) - 1:
            ps.exercises[idx], ps.exercises[idx + 1] = ps.exercises[idx + 1], ps.exercises[idx]
            self._render_plan()

    def _add_exercise(self, ps: PlannedSession):
        ps.exercises.append(PlannedExercise(var_name="exercise", sets=3, reps="5", mass="0", comment=""))
        self._render_plan()

    def _remove_exercise(self, ps: PlannedSession, ex: PlannedExercise):
        if ex in ps.exercises:
            ps.exercises.remove(ex)
            self._render_plan()

    def _add_day(self):
        new_day_num = len(self.planned) + 1
        self.planned.append(PlannedSession(day_num=new_day_num, date_str="", exercises=[]))
        self._render_plan()

    def _remove_day(self, idx: int):
        if 0 <= idx < len(self.planned):
            self.planned.pop(idx)
            # Re-index days
            for i, ps in enumerate(self.planned, 1):
                ps.day_num = i
            self._render_plan()

    def _apply_deload(self):
        val, ok = QInputDialog.getDouble(self, "Deload Plan", "Enter deload percentage (e.g. 10 for 10%):", 10.0, 1.0, 50.0, 1)
        if ok:
            pct = val / 100.0
            for ps in self.planned:
                for ex in ps.exercises:
                    try:
                        m_val = float(ex.mass)
                        new_m = round(m_val * (1.0 - pct) * 2) / 2
                        ex.mass = str(new_m)
                        ex.comment = f"Deload -{val:.0f}%"
                    except ValueError:
                        pass
            self._render_plan()

    def _restore_pre_deload(self):
        QMessageBox.information(self, "Restore", "Restoring full weights from pre-deload cycle baseline.")
        self._render_plan()

    def _save_plan(self):
        # Validate novel exercises
        new_exs = get_genuinely_new_exercises(self.sessions_file_path, self.planned)
        if new_exs:
            ex_list = "\n".join(f"  • {e}" for e in new_exs)
            ret = QMessageBox.question(
                self,
                "Confirm New Exercises",
                f"The following new exercises were not found in sessions.py and will be automatically registered:\n\n{ex_list}\n\nDo you want to proceed and save?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if ret != QMessageBox.Yes:
                return

        try:
            write_planned_sessions(self.sessions_file_path, self.planned)
            QMessageBox.information(self, "Success", "Planned cycle successfully written to sessions.py!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error Saving Plan", str(e))


class IronLogPySideApp(QMainWindow):
    """Main PySide6 Application Window for Iron Log."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Iron Log {__version__} (PySide6 Edition)")
        self.resize(1100, 720)
        self.setMinimumSize(960, 580)
        self.setStyleSheet(PYSIDE_DARK_QSS)

        self.manager = ProfileManager()
        self.thread_pool = QThreadPool()
        self.active_sessions = None

        self._build_ui()
        self._load_active_profile()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(15, 12, 15, 12)
        main_layout.setSpacing(12)

        # 1. Header & Profile Selector Row
        top_frame = QFrame()
        top_frame.setObjectName("CardFrame")
        top_layout = QHBoxLayout(top_frame)
        top_layout.setContentsMargins(12, 8, 12, 8)

        # App Brand
        brand_lbl = QLabel("⚡ IRON LOG")
        brand_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #38BDF8; letter-spacing: 1px;")
        top_layout.addWidget(brand_lbl)

        top_layout.addSpacing(20)

        # Profile selection
        top_layout.addWidget(QLabel("Profile:"))
        self.profile_combo = QComboBox()
        self.profile_combo.setMinimumWidth(160)
        self.profile_combo.currentIndexChanged.connect(self._on_profile_changed)
        top_layout.addWidget(self.profile_combo)

        btn_add_prof = QPushButton("+ New")
        btn_add_prof.setObjectName("SmallToolBtn")
        btn_add_prof.clicked.connect(self._prompt_new_profile)
        top_layout.addWidget(btn_add_prof)

        top_layout.addStretch()

        # Engine Badge
        engine_badge = QLabel("Engine: PySide6 (Qt 6 C++)")
        engine_badge.setStyleSheet("color: #4ADE80; font-weight: 600; font-size: 11px; padding: 2px 8px; border: 1px solid #15803D; border-radius: 4px; background: #064E3B;")
        top_layout.addWidget(engine_badge)

        main_layout.addWidget(top_frame)

        # 2. Stats Metric Cards Row
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(10)

        self.card_total = self._create_stat_card("Total Sessions", "--", "All time recorded")
        self.card_last = self._create_stat_card("Last Workout", "--", "Latest session date")
        self.card_split = self._create_stat_card("Active Split", "--", "Click for routine details", clickable=True)
        self.card_mass = self._create_stat_card("Current Body Mass", "--", "From bodymass log")

        stats_layout.addWidget(self.card_total)
        stats_layout.addWidget(self.card_last)
        stats_layout.addWidget(self.card_split)
        stats_layout.addWidget(self.card_mass)

        main_layout.addLayout(stats_layout)

        # 3. Action Toolbar Row
        action_layout = QHBoxLayout()
        action_layout.setSpacing(8)

        self.btn_gen_excel = QPushButton("📊 Generate Excel Log")
        self.btn_gen_excel.setObjectName("PrimaryBtn")
        self.btn_gen_excel.clicked.connect(self._generate_excel)
        action_layout.addWidget(self.btn_gen_excel)

        btn_planner = QPushButton("📅 Cycle Planner")
        btn_planner.clicked.connect(self._open_planner)
        action_layout.addWidget(btn_planner)

        btn_standards = QPushButton("🏋️ Strength Standards")
        btn_standards.clicked.connect(self._open_standards)
        action_layout.addWidget(btn_standards)

        btn_split = QPushButton("🔄 Split Details")
        btn_split.clicked.connect(self._open_split_details)
        action_layout.addWidget(btn_split)

        action_layout.addStretch()

        btn_edit_sess = QPushButton("Edit sessions.py")
        btn_edit_sess.setObjectName("SmallToolBtn")
        btn_edit_sess.clicked.connect(self._edit_sessions)
        action_layout.addWidget(btn_edit_sess)

        btn_open_out = QPushButton("Output Folder")
        btn_open_out.setObjectName("SmallToolBtn")
        btn_open_out.clicked.connect(self._open_output)
        action_layout.addWidget(btn_open_out)

        main_layout.addLayout(action_layout)

        # 4. Recent Workout Sessions Display Panel
        panel_title = QLabel("Recent Workout Sessions (Active Cycle)")
        panel_title.setStyleSheet("font-weight: bold; font-size: 13px; color: #A1A1AA;")
        main_layout.addWidget(panel_title)

        self.sessions_scroll = QScrollArea()
        self.sessions_scroll.setWidgetResizable(True)
        self.sessions_container = QWidget()
        self.sessions_layout = QHBoxLayout(self.sessions_container)
        self.sessions_layout.setSpacing(12)
        self.sessions_layout.setAlignment(Qt.AlignLeft)
        self.sessions_scroll.setWidget(self.sessions_container)
        main_layout.addWidget(self.sessions_scroll, 1)

        # 5. Status Bar & Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedHeight(14)
        main_layout.addWidget(self.progress_bar)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def _create_stat_card(self, title_text: str, value_text: str, sub_text: str, clickable: bool = False) -> QFrame:
        card = QFrame()
        card.setObjectName("StatCard")
        if clickable:
            card.setCursor(Qt.PointingHandCursor)
            card.mousePressEvent = lambda e: self._open_split_details()

        l = QVBoxLayout(card)
        l.setContentsMargins(10, 8, 10, 8)
        l.setSpacing(2)

        t_lbl = QLabel(title_text)
        t_lbl.setObjectName("CardTitle")
        l.addWidget(t_lbl)

        v_lbl = QLabel(value_text)
        v_lbl.setObjectName("CardValue")
        l.addWidget(v_lbl)

        s_lbl = QLabel(sub_text)
        s_lbl.setObjectName("CardSub")
        l.addWidget(s_lbl)

        card.value_label = v_lbl
        card.sub_label = s_lbl
        return card

    def _load_active_profile(self):
        self.profile_combo.blockSignals(True)
        self.profile_combo.clear()
        for prof in self.manager.profiles:
            self.profile_combo.addItem(prof.name)
        if self.manager.active_profile_index >= 0:
            self.profile_combo.setCurrentIndex(self.manager.active_profile_index)
        self.profile_combo.blockSignals(False)

        self._refresh_data()

    def _on_profile_changed(self, index: int):
        if index >= 0:
            self.manager.set_active(index)
            self._refresh_data()

    def _prompt_new_profile(self):
        name, ok = QInputDialog.getText(self, "New Profile", "Enter profile name:")
        if ok and name.strip():
            prof = Profile(name=name.strip(), sessions_dir="", output_dir="", sex="male")
            self.manager.add_profile(prof)
            self._load_active_profile()

    def _refresh_data(self):
        p = self.manager.get_active_profile()
        if not p:
            self.status_bar.showMessage("No profile selected")
            return

        # Load sessions module
        sessions_file = getattr(p, "sessions_file", None)
        if not sessions_file:
            sessions_file = os.path.join(p.sessions_dir, "sessions.py")

        if not os.path.exists(sessions_file):
            self.status_bar.showMessage(f"sessions.py not found at: {sessions_file}")
            return

        try:
            sessions_dir = os.path.dirname(sessions_file)
            if sessions_dir not in sys.path:
                sys.path.insert(0, sessions_dir)

            import importlib
            if "sessions" in sys.modules:
                sess = importlib.reload(sys.modules["sessions"])
            else:
                import sessions as sess

            self.active_sessions = sess
            self._update_stats_and_sessions(sess, p)
            self.status_bar.showMessage(f"Loaded profile: {p.name} ({sessions_file})")
        except Exception as e:
            self.status_bar.showMessage(f"Error loading sessions: {e}")

    def _update_stats_and_sessions(self, sess, profile: Profile):
        user_data = getattr(sess, "USER_DATA", {})
        stats = calculate_gym_stats(user_data)
        self.cached_stats = stats

        # Update cards
        self.card_total.value_label.setText(str(stats.get("total_days", "--")))
        self.card_total.sub_label.setText(f"{stats.get('this_year_days', 0)} this year")

        latest_date = stats.get("latest_workout_date", "--")
        latest_day = stats.get("latest_workout_day", "")
        self.card_last.value_label.setText(str(latest_date))
        self.card_last.sub_label.setText(f"Day {latest_day}" if latest_day else "")

        weeks = stats.get("current_split_weeks", 0.0)
        self.card_split.value_label.setText(f"{weeks:.1f} Wks")
        self.card_split.sub_label.setText(f"{stats.get('cycle_length', '?')}-Day Cycle (Click)")

        bm_log = getattr(sess, "BODYMASS_LOG", {})
        if bm_log:
            sorted_bm = sorted(bm_log.items(), key=lambda x: str(x[0]), reverse=True)
            last_mass = sorted_bm[0][1] if sorted_bm else "--"
            self.card_mass.value_label.setText(f"{last_mass} kg")
        else:
            self.card_mass.value_label.setText(f"{profile.mass} kg")

        # Rebuild horizontal workout cards
        while self.sessions_layout.count():
            item = self.sessions_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        date_pat = re.compile(r"^\d{4}-\d{2}-\d{2}$")
        sorted_dates = sorted([d for d in user_data.keys() if date_pat.match(d)], reverse=True)
        N, _ = detect_cycle(user_data)
        show_dates = sorted_dates[: N if N else 3]

        for d_str in reversed(show_dates):
            day_data = user_data[d_str]
            card = QFrame()
            card.setObjectName("SessionCard")
            card.setMinimumWidth(220)
            card_l = QVBoxLayout(card)
            card_l.setContentsMargins(10, 10, 10, 10)
            card_l.setSpacing(6)

            # Card Header
            d_hdr = QLabel(f"📅 {d_str} (Day {day_data.get('day', '?')})")
            d_hdr.setStyleSheet("font-weight: bold; color: #38BDF8; font-size: 12px;")
            card_l.addWidget(d_hdr)

            # Exercise list
            for ex_id, log in day_data.items():
                if not isinstance(log, Log):
                    continue
                info = EXERCISE_STANDARDS.get(ex_id, {})
                display_name = info.get("name", ex_id)
                reps_str = ",".join(str(r) for r in log.reps)
                mass_str = f" @ {log.mass[0]}kg" if log.mass and max(log.mass) > 0 else " (BW)"

                ex_lbl = QLabel(f"• {display_name[:20]}")
                ex_lbl.setStyleSheet("font-weight: 500; font-size: 11px;")
                card_l.addWidget(ex_lbl)

                val_lbl = QLabel(f"   [{reps_str}]{mass_str}")
                val_lbl.setStyleSheet("color: #A1A1AA; font-size: 11px;")
                card_l.addWidget(val_lbl)

            card_l.addStretch()
            self.sessions_layout.addWidget(card)

        self.sessions_layout.addStretch()

    def _generate_excel(self):
        p = self.manager.get_active_profile()
        if not p or not self.active_sessions:
            QMessageBox.warning(self, "Warning", "No active profile or sessions loaded.")
            return

        self.btn_gen_excel.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.status_bar.showMessage("Generating Excel Log...")

        worker = ExcelWorker(p, self.active_sessions)
        worker.signals.finished.connect(self._on_excel_success)
        worker.signals.error.connect(self._on_excel_error)
        self.thread_pool.start(worker)

    def _on_excel_success(self, filename: str):
        self.btn_gen_excel.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_bar.showMessage(f"✅ Created Excel log: {filename}")
        try:
            os.startfile(filename)
        except Exception:
            pass

    def _on_excel_error(self, err_msg: str):
        self.btn_gen_excel.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_bar.showMessage(f"Error generating Excel: {err_msg}")
        QMessageBox.critical(self, "Excel Generation Error", err_msg)

    def _open_planner(self):
        p = self.manager.get_active_profile()
        if not p or not self.active_sessions:
            QMessageBox.warning(self, "Warning", "Please select a valid profile first.")
            return

        sessions_file = getattr(p, "sessions_file", None)
        if not sessions_file:
            sessions_file = os.path.join(p.sessions_dir, "sessions.py")

        user_data = getattr(self.active_sessions, "USER_DATA", {})
        N, last_day = detect_cycle(user_data)
        if N is None:
            QMessageBox.information(
                self,
                "Cycle Unknown",
                "Could not detect your split cycle yet.\nComplete at least one full cycle before generating plans.",
            )
            return

        day_nums = days_to_generate(N, last_day)
        if not day_nums:
            QMessageBox.information(
                self,
                "Nothing to add",
                "All days in the current cycle are already planned.",
            )
            return

        try:
            planned = build_planned_sessions(sessions_file, day_nums)
            dlg = PySideDynamicPlanDialog(self, planned, sessions_file)
            if dlg.exec():
                self._refresh_data()
        except Exception as e:
            QMessageBox.critical(self, "Planner Error", str(e))

    def _open_standards(self):
        p = self.manager.get_active_profile()
        sex = getattr(p, "sex", "male") if p else "male"
        mass = getattr(p, "mass", 80.0) if p else 80.0
        dlg = PySideStandardsDialog(self, user_sex=sex, user_mass=mass)
        dlg.exec()

    def _open_split_details(self):
        if hasattr(self, "cached_stats"):
            dlg = PySideSplitDetailsDialog(self, self.cached_stats)
            dlg.exec()

    def _edit_sessions(self):
        p = self.manager.get_active_profile()
        if p and p.sessions_dir:
            file_path = os.path.join(p.sessions_dir, "sessions.py")
            if os.path.exists(file_path):
                os.startfile(file_path)

    def _open_output(self):
        p = self.manager.get_active_profile()
        if p and p.output_dir and os.path.exists(p.output_dir):
            os.startfile(p.output_dir)


def run_pyside_app():
    app = QApplication(sys.argv)
    window = IronLogPySideApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run_pyside_app()
