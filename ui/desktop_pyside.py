"""PySide6 (Qt 6) Desktop GUI Implementation for Iron Log.

Styled to precisely match the CustomTkinter layout, colors, sidebar,
and interactive workflow (including the Dynamic Plan Cycler).
"""

import copy
import importlib
import os
import re
import sys
import threading
import webbrowser
from datetime import datetime, timedelta
from typing import List, Optional

from PySide6.QtCore import QObject, QPoint, QRect, QRunnable, QSize, Qt, QThreadPool, QTimer, Signal
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
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QToolTip,
    QVBoxLayout,
    QWidget,
)

from core.models import Log
from core.plan_generator import (
    PlannedExercise,
    PlannedSession,
    build_planned_sessions,
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

CTK_MATCHING_QSS = """
QMainWindow, QDialog {
    background-color: #121212;
    color: #FFFFFF;
    font-family: 'Roboto', 'Segoe UI', sans-serif;
}
QWidget {
    color: #FFFFFF;
    font-size: 12px;
}
/* Left Sidebar */
QFrame#Sidebar {
    background-color: #161616;
    border-right: 1px solid #222222;
}
QLabel#ProfileTitle {
    font-size: 17px;
    font-weight: bold;
    color: #FFFFFF;
}
QLabel#AppSubtitle {
    font-size: 11px;
    color: #555555;
}
QFrame#Divider {
    background-color: #2E2E2E;
    max-height: 1px;
    min-height: 1px;
}
/* Primary Action Buttons */
QPushButton#PrimaryAction1 {
    background-color: #1565C0;
    color: #FFFFFF;
    font-size: 13px;
    font-weight: bold;
    border-radius: 8px;
    padding: 10px;
    border: none;
}
QPushButton#PrimaryAction1:hover {
    background-color: #1976D2;
}
QPushButton#PrimaryAction2 {
    background-color: #6A1B9A;
    color: #FFFFFF;
    font-size: 13px;
    font-weight: bold;
    border-radius: 8px;
    padding: 10px;
    border: none;
}
QPushButton#PrimaryAction2:hover {
    background-color: #7B1FA2;
}
QPushButton#PrimaryAction3 {
    background-color: #1B5E20;
    color: #FFFFFF;
    font-size: 13px;
    font-weight: bold;
    border-radius: 8px;
    padding: 10px;
    border: none;
}
QPushButton#PrimaryAction3:hover {
    background-color: #2E7D32;
}
/* Secondary Action Buttons */
QPushButton#SecondaryAction {
    background-color: #252525;
    color: #BBBBBB;
    font-size: 12px;
    border-radius: 7px;
    padding: 8px 12px;
    text-align: left;
    border: none;
}
QPushButton#SecondaryAction:hover {
    background-color: #333333;
    color: #FFFFFF;
}
/* Cards */
QFrame#StatCard {
    background-color: #1C1C1E;
    border: 1px solid #2E2E2E;
    border-radius: 10px;
}
QFrame#StatCard:hover {
    background-color: #222224;
}
QLabel#StatCardTitle {
    font-size: 10px;
    font-weight: bold;
    color: #777777;
    text-transform: uppercase;
}
QLabel#StatCardValue {
    font-size: 24px;
    font-weight: bold;
    color: #FFFFFF;
}
QLabel#StatCardSub {
    font-size: 11px;
    color: #555555;
}
QFrame#WorkoutCard {
    background-color: #1C1C1E;
    border: 1px solid #2E2E2E;
    border-radius: 10px;
}
QFrame#WorkoutCardPR {
    background-color: #2A1A00;
    border: 1px solid #5A3000;
    border-radius: 10px;
}
QLabel#WorkoutHeader {
    font-size: 13px;
    font-weight: bold;
    color: #FFFFFF;
}
QLabel#WorkoutHeaderPR {
    font-size: 13px;
    font-weight: bold;
    color: #B45309;
}
QLineEdit {
    background-color: #252525;
    color: #FFFFFF;
    border: 1px solid #3A3A3A;
    border-radius: 6px;
    padding: 4px 8px;
    font-size: 12px;
}
QLineEdit:focus {
    border: 1px solid #1976D2;
}
QScrollArea {
    border: none;
    background-color: transparent;
}
QScrollBar:vertical, QScrollBar:horizontal {
    background: #121212;
    width: 8px;
    height: 8px;
}
QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
    background: #333333;
    border-radius: 4px;
}
QScrollBar::handle:hover {
    background: #555555;
}
QTableWidget {
    background-color: #181818;
    gridline-color: #2E2E2E;
    border: 1px solid #2E2E2E;
    border-radius: 6px;
}
QHeaderView::section {
    background-color: #252525;
    color: #FFFFFF;
    font-weight: bold;
    padding: 6px;
    border: none;
    border-right: 1px solid #333333;
}
QToolTip {
    background-color: #1C1C1E;
    color: #FFFFFF;
    border: 1px solid #333333;
    padding: 6px;
    font-size: 11px;
}
"""


class PySideStandardsDialog(QDialog):
    """Exercise standards browser matching CTk style."""

    def __init__(self, parent=None, user_sex="male", user_mass=80.0):
        super().__init__(parent)
        self.setWindowTitle("Strength Standards Browser — PySide6")
        self.resize(800, 560)
        self.user_sex = user_sex
        self.user_mass = user_mass

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Search Bar
        search_layout = QHBoxLayout()
        lbl = QLabel("Search:")
        lbl.setStyleSheet("font-size: 13px; font-weight: bold;")
        search_layout.addWidget(lbl)

        self.search_in = QLineEdit()
        self.search_in.setPlaceholderText("Filter exercises (e.g. bench press, squat)...")
        self.search_in.textChanged.connect(self._filter)
        search_layout.addWidget(self.search_in)
        layout.addLayout(search_layout)

        # Table
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
        layout.addWidget(self.table)

        self._filter("")

    def _filter(self, q: str):
        q = q.strip().lower()
        self.table.setRowCount(0)
        row_i = 0
        target_bm = int(self.user_mass / 5.0) * 5

        for slug, info in EXERCISE_STANDARDS.items():
            name = info.get("name", slug)
            if q and (q not in name.lower() and q not in slug.lower()):
                continue

            self.table.insertRow(row_i)
            self.table.setItem(row_i, 0, QTableWidgetItem(name))
            
            slug_item = QTableWidgetItem(slug)
            slug_item.setForeground(QColor("#38BDF8"))
            self.table.setItem(row_i, 1, slug_item)

            standards = get_tiered_standards(slug, self.user_sex, self.user_mass)
            lvl_dict = standards.get(target_bm, {}) if standards else {}

            for col_i, lvl in enumerate(["Beginner", "Novice", "Intermediate", "Advanced", "Elite"], 2):
                val = lvl_dict.get(lvl, "-")
                item = QTableWidgetItem(f"{val}kg" if isinstance(val, (int, float)) else str(val))
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row_i, col_i, item)

            # Actions
            btn_box = QWidget()
            b_layout = QHBoxLayout(btn_box)
            b_layout.setContentsMargins(2, 2, 2, 2)
            b_layout.setSpacing(4)

            b_copy = QPushButton("Copy")
            b_copy.setStyleSheet("background: #252525; padding: 3px 8px; border-radius: 4px; font-size: 11px;")
            b_copy.clicked.connect(lambda _, s=slug: self._clip(s, f"Copied slug '{s}'"))
            b_layout.addWidget(b_copy)

            b_py = QPushButton("Copy Py")
            b_py.setStyleSheet("background: #1B5E20; color: white; padding: 3px 8px; border-radius: 4px; font-size: 11px;")
            py_code = f'{slug.replace("-", "_")} = "{slug}"'
            b_py.clicked.connect(lambda _, c=py_code: self._clip(c, f"Copied '{c}'"))
            b_layout.addWidget(b_py)

            b_view = QPushButton("View")
            b_view.setStyleSheet("background: #1565C0; padding: 3px 8px; border-radius: 4px; font-size: 11px;")
            b_view.clicked.connect(lambda _, s=slug: webbrowser.open(f"https://strengthlevel.com/strength-standards/{s}"))
            b_layout.addWidget(b_view)

            self.table.setCellWidget(row_i, 7, btn_box)
            row_i += 1

    def _clip(self, text: str, msg: str):
        QApplication.clipboard().setText(text)
        QMessageBox.information(self, "Clipboard", msg)


class PySideSplitDetailsDialog(QDialog):
    """Split routine and cycle history dialog."""

    def __init__(self, parent=None, stats=None):
        super().__init__(parent)
        self.setWindowTitle("Current Split Details & History — PySide6")
        self.resize(620, 460)
        stats = stats or {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        card = QFrame()
        card.setObjectName("StatCard")
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(14, 14, 14, 14)

        t = QLabel("CURRENT SPLIT ROUTINE")
        t.setObjectName("StatCardTitle")
        c_layout.addWidget(t)

        weeks = stats.get("current_split_weeks", 0.0)
        c_layout.addWidget(QLabel(f"• Active Split Duration: <b>{weeks:.1f} Weeks</b> (Started {stats.get('current_split_start', 'N/A')})"))
        c_layout.addWidget(QLabel(f"• Detected Cycle Length: <b>{stats.get('cycle_length', 'N/A')} Days</b>"))
        c_layout.addWidget(QLabel(f"• Total Recorded Sessions: <b>{stats.get('total_days', 0)}</b>"))
        layout.addWidget(card)

        layout.addWidget(QLabel("Recent Split Sessions History:"))
        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["Date", "Day", "Exercises Count"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)

        sessions = stats.get("split_sessions_details", [])
        table.setRowCount(len(sessions))
        for r, s in enumerate(reversed(sessions)):
            table.setItem(r, 0, QTableWidgetItem(s.get("date_str", "")))
            table.setItem(r, 1, QTableWidgetItem(f"Day {s.get('day', '')}"))
            table.setItem(r, 2, QTableWidgetItem(str(len(s.get("exercises", [])))))
        layout.addWidget(table)


class PySideDynamicPlanDialog(QDialog):
    """Dynamic workout cycle plan generator matching CTk DynamicPlanDialog."""

    def __init__(self, parent, file_path: str, planned: List[PlannedSession], title: str = "Plan Next Cycle"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(980, 700)
        self.file_path = file_path
        self.planned = copy.deepcopy(planned)
        self.confirmed = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Header Info Banner
        hdr_frame = QFrame()
        hdr_frame.setStyleSheet("background: #1A1A1A; border-radius: 6px; padding: 10px;")
        h_layout = QVBoxLayout(hdr_frame)
        h_layout.setContentsMargins(4, 4, 4, 4)
        
        t_lbl = QLabel(title)
        t_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #FFFFFF;")
        h_layout.addWidget(t_lbl)

        sub_lbl = QLabel("Define your training split. Type exercise variable name, sets, reps, mass, and notes.")
        sub_lbl.setStyleSheet("font-size: 12px; color: #888888;")
        h_layout.addWidget(sub_lbl)
        layout.addWidget(hdr_frame)

        # Scroll area for planned days
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setSpacing(12)
        self.scroll.setWidget(self.container)
        layout.addWidget(self.scroll, 1)

        # Footer Actions Bar
        footer = QFrame()
        footer.setStyleSheet("background: #111111; padding: 8px; border-top: 1px solid #222;")
        f_layout = QHBoxLayout(footer)
        f_layout.setContentsMargins(8, 6, 8, 6)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setStyleSheet("background: #333333; color: white; padding: 8px 16px; border-radius: 6px; font-weight: bold;")
        btn_cancel.clicked.connect(self.reject)
        f_layout.addWidget(btn_cancel)

        btn_add_day = QPushButton("+ Add Day")
        btn_add_day.setStyleSheet("background: #6A1B9A; color: white; padding: 8px 16px; border-radius: 6px; font-weight: bold;")
        btn_add_day.clicked.connect(self._add_day)
        f_layout.addWidget(btn_add_day)

        btn_deload = QPushButton("🧪 Deload Next Cycle (-10%)")
        btn_deload.setStyleSheet("background: #333333; color: white; padding: 8px 14px; border-radius: 6px;")
        btn_deload.clicked.connect(self._prompt_deload)
        f_layout.addWidget(btn_deload)

        f_layout.addStretch()

        btn_save = QPushButton("✅ Write to sessions.py")
        btn_save.setStyleSheet("background: #1B5E20; color: white; padding: 8px 24px; border-radius: 6px; font-size: 13px; font-weight: bold;")
        btn_save.clicked.connect(self._save_plan)
        f_layout.addWidget(btn_save)

        layout.addWidget(footer)

        self._render_plan()

    def _render_plan(self):
        while self.container_layout.count():
            item = self.container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for s_idx, ps in enumerate(self.planned):
            day_box = QFrame()
            day_box.setStyleSheet("background: #1A1A1A; border: 1px solid #2E2E2E; border-radius: 8px;")
            d_layout = QVBoxLayout(day_box)
            d_layout.setContentsMargins(10, 10, 10, 10)
            d_layout.setSpacing(6)

            # Day Header
            dh = QFrame()
            dh.setStyleSheet("background: #222222; border-radius: 6px;")
            dh_layout = QHBoxLayout(dh)
            dh_layout.setContentsMargins(10, 6, 10, 6)

            day_badge = QLabel(f"Day {ps.day_number}")
            day_badge.setStyleSheet("background: #00695C; color: white; font-weight: bold; border-radius: 4px; padding: 4px 10px;")
            dh_layout.addWidget(day_badge)

            dh_layout.addWidget(QLabel("Date:"))
            d_input = QLineEdit(ps.date_str)
            d_input.setPlaceholderText("YYYY-MM-DD")
            d_input.setFixedWidth(110)
            d_input.textChanged.connect(lambda val, s=ps: setattr(s, "date_str", val))
            dh_layout.addWidget(d_input)

            dh_layout.addStretch()

            btn_add_ex = QPushButton("+ Add Exercise")
            btn_add_ex.setStyleSheet("background: #0277BD; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold;")
            btn_add_ex.clicked.connect(lambda _, s=ps: self._add_ex(s))
            dh_layout.addWidget(btn_add_ex)

            btn_del_day = QPushButton("🗑️")
            btn_del_day.setStyleSheet("background: #5A1A1A; color: white; padding: 4px 8px; border-radius: 4px;")
            btn_del_day.clicked.connect(lambda _, idx=s_idx: self._remove_day(idx))
            dh_layout.addWidget(btn_del_day)

            d_layout.addWidget(dh)

            # Column Headers
            col_hdr = QWidget()
            ch_layout = QHBoxLayout(col_hdr)
            ch_layout.setContentsMargins(4, 2, 4, 2)
            
            lbl_order = QLabel("Order")
            lbl_order.setFixedWidth(55)
            lbl_order.setStyleSheet("color: #777; font-weight: bold;")
            ch_layout.addWidget(lbl_order)

            lbl_name = QLabel("Exercise Name / Slug")
            lbl_name.setStyleSheet("color: #777; font-weight: bold;")
            ch_layout.addWidget(lbl_name, 2)

            lbl_sets = QLabel("Sets")
            lbl_sets.setFixedWidth(50)
            lbl_sets.setStyleSheet("color: #777; font-weight: bold;")
            ch_layout.addWidget(lbl_sets)

            lbl_reps = QLabel("Reps")
            lbl_reps.setFixedWidth(100)
            lbl_reps.setStyleSheet("color: #777; font-weight: bold;")
            ch_layout.addWidget(lbl_reps)

            lbl_mass = QLabel("Mass (kg)")
            lbl_mass.setFixedWidth(110)
            lbl_mass.setStyleSheet("color: #777; font-weight: bold;")
            ch_layout.addWidget(lbl_mass)

            lbl_comm = QLabel("Comment")
            lbl_comm.setStyleSheet("color: #777; font-weight: bold;")
            ch_layout.addWidget(lbl_comm, 1)

            lbl_act = QLabel("Actions")
            lbl_act.setFixedWidth(120)
            lbl_act.setStyleSheet("color: #777; font-weight: bold;")
            ch_layout.addWidget(lbl_act)

            d_layout.addWidget(col_hdr)

            # Exercise Rows
            for ex in ps.exercises:
                row_w = QWidget()
                r_layout = QHBoxLayout(row_w)
                r_layout.setContentsMargins(4, 2, 4, 2)

                # Order Up/Down
                up_btn = QPushButton("▲")
                up_btn.setFixedSize(22, 22)
                up_btn.setStyleSheet("background: #333333; border-radius: 3px;")
                up_btn.clicked.connect(lambda _, s=ps, e=ex: self._move_up(s, e))
                r_layout.addWidget(up_btn)

                down_btn = QPushButton("▼")
                down_btn.setFixedSize(22, 22)
                down_btn.setStyleSheet("background: #333333; border-radius: 3px;")
                down_btn.clicked.connect(lambda _, s=ps, e=ex: self._move_down(s, e))
                r_layout.addWidget(down_btn)

                # Name
                name_in = QLineEdit(ex.var_name)
                name_in.textChanged.connect(lambda val, e=ex: setattr(e, "var_name", val))
                r_layout.addWidget(name_in, 2)

                # Sets
                sets_in = QLineEdit(str(ex.sets))
                sets_in.setFixedWidth(50)
                sets_in.textChanged.connect(lambda val, e=ex: setattr(e, "sets", val))
                r_layout.addWidget(sets_in)

                # Reps
                reps_in = QLineEdit(str(ex.reps))
                reps_in.setFixedWidth(100)
                reps_in.textChanged.connect(lambda val, e=ex: setattr(e, "reps", val))
                r_layout.addWidget(reps_in)

                # Mass
                mass_in = QLineEdit(str(ex.mass))
                mass_in.setFixedWidth(110)
                mass_in.textChanged.connect(lambda val, e=ex: setattr(e, "mass", val))
                r_layout.addWidget(mass_in)

                # Comment
                comm_in = QLineEdit(str(ex.comment))
                comm_in.textChanged.connect(lambda val, e=ex: setattr(e, "comment", val))
                r_layout.addWidget(comm_in, 1)

                # Quick Actions (+2.5, +1, ✕)
                btn_p25 = QPushButton("+2.5")
                btn_p25.setFixedSize(36, 24)
                btn_p25.setStyleSheet("background: #252525; font-size: 10px; border-radius: 3px;")
                btn_p25.clicked.connect(lambda _, e=ex, mi=mass_in: self._add_mass(e, mi, 2.5))
                r_layout.addWidget(btn_p25)

                btn_del = QPushButton("✕")
                btn_del.setFixedSize(24, 24)
                btn_del.setStyleSheet("background: #5A1A1A; color: white; border-radius: 3px; font-weight: bold;")
                btn_del.clicked.connect(lambda _, s=ps, e=ex: self._remove_ex(s, e))
                r_layout.addWidget(btn_del)

                d_layout.addWidget(row_w)

            self.container_layout.addWidget(day_box)

        self.container_layout.addStretch()

    def _add_mass(self, ex: PlannedExercise, input_widget: QLineEdit, delta: float):
        try:
            m = float(ex.mass)
            new_m = m + delta
            ex.mass = str(new_m)
            input_widget.setText(str(new_m))
        except ValueError:
            pass

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

    def _add_ex(self, ps: PlannedSession):
        ps.exercises.append(PlannedExercise(var_name="exercise", display_name="Exercise", sets=3, reps="5", mass="0", comment=""))
        self._render_plan()

    def _remove_ex(self, ps: PlannedSession, ex: PlannedExercise):
        if ex in ps.exercises:
            ps.exercises.remove(ex)
            self._render_plan()

    def _add_day(self):
        new_num = len(self.planned) + 1
        self.planned.append(PlannedSession(day_number=new_num, date_str="", exercises=[]))
        self._render_plan()

    def _remove_day(self, idx: int):
        if 0 <= idx < len(self.planned):
            self.planned.pop(idx)
            for i, ps in enumerate(self.planned, 1):
                ps.day_number = i
            self._render_plan()

    def _prompt_deload(self):
        val, ok = QInputDialog.getDouble(self, "Deload Plan", "Enter deload percentage (e.g. 10 for 10%):", 10.0, 1.0, 50.0, 1)
        if ok:
            pct = val / 100.0
            for ps in self.planned:
                for ex in ps.exercises:
                    try:
                        m = float(ex.mass)
                        ex.mass = str(round(m * (1.0 - pct) * 2) / 2)
                        ex.comment = f"Deload -{val:.0f}%"
                    except ValueError:
                        pass
            self._render_plan()

    def _save_plan(self):
        new_exs = get_genuinely_new_exercises(self.file_path, self.planned)
        if new_exs:
            ex_list = "\n".join(f"  • {e}" for e in new_exs)
            ret = QMessageBox.question(
                self,
                "Confirm New Exercises",
                f"The following new exercises were not found in sessions.py and will be automatically registered:\n\n{ex_list}\n\nDo you want to proceed?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if ret != QMessageBox.Yes:
                return

        try:
            write_planned_sessions(self.file_path, self.planned)
            self.confirmed = True
            QMessageBox.information(self, "Success", "Planned cycle successfully written to sessions.py!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error Saving Plan", str(e))


class IronLogPySideApp(QMainWindow):
    """Main PySide6 Window with exact CustomTkinter layout and color theme."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Iron Log {__version__} (PySide6 Edition)")
        self.resize(1100, 720)
        self.setMinimumSize(960, 580)
        self.setStyleSheet(CTK_MATCHING_QSS)

        self.manager = ProfileManager()
        self.active_sessions = None
        self.cached_stats = {}
        self.last_generated_at = None

        self._build_ui()
        self._load_active_profile()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── 1. LEFT SIDEBAR (Width 210px, Color #161616) ──────────────────────
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(210)
        s_layout = QVBoxLayout(sidebar)
        s_layout.setContentsMargins(16, 20, 16, 16)
        s_layout.setSpacing(4)

        # Profile title & subtitle
        self.lbl_profile_name = QLabel("Default User")
        self.lbl_profile_name.setObjectName("ProfileTitle")
        s_layout.addWidget(self.lbl_profile_name)

        lbl_sub = QLabel("Iron Log (PySide6)")
        lbl_sub.setObjectName("AppSubtitle")
        s_layout.addWidget(lbl_sub)

        div1 = QFrame()
        div1.setObjectName("Divider")
        s_layout.addWidget(div1)
        s_layout.addSpacing(6)

        # Primary Actions
        btn_gen = QPushButton("🚀 Generate Excel Log")
        btn_gen.setObjectName("PrimaryAction1")
        btn_gen.clicked.connect(self.run_log_generator)
        s_layout.addWidget(btn_gen)

        btn_plan = QPushButton("🗓️ Plan Next Cycle")
        btn_plan.setObjectName("PrimaryAction2")
        btn_plan.clicked.connect(self.run_plan_generator)
        s_layout.addWidget(btn_plan)

        btn_open_excel = QPushButton("📂 Open Latest Log")
        btn_open_excel.setObjectName("PrimaryAction3")
        btn_open_excel.clicked.connect(self.open_latest_excel)
        s_layout.addWidget(btn_open_excel)

        s_layout.addSpacing(6)
        div2 = QFrame()
        div2.setObjectName("Divider")
        s_layout.addWidget(div2)
        s_layout.addSpacing(6)

        # Secondary Actions
        btn_edit = QPushButton("  📝  Edit Sessions")
        btn_edit.setObjectName("SecondaryAction")
        btn_edit.clicked.connect(self.edit_sessions)
        s_layout.addWidget(btn_edit)

        btn_out = QPushButton("  📊  Output Folder")
        btn_out.setObjectName("SecondaryAction")
        btn_out.clicked.connect(self.open_output)
        s_layout.addWidget(btn_out)

        btn_std = QPushButton("  📚  Exercise Library")
        btn_std.setObjectName("SecondaryAction")
        btn_std.clicked.connect(self.show_exercise_library)
        s_layout.addWidget(btn_std)

        btn_split = QPushButton("  🔄  Split Details")
        btn_split.setObjectName("SecondaryAction")
        btn_split.clicked.connect(self.show_split_details)
        s_layout.addWidget(btn_split)

        s_layout.addStretch()

        # Status footer
        self.lbl_status = QLabel("Ready")
        self.lbl_status.setStyleSheet("color: #555555; font-size: 11px;")
        s_layout.addWidget(self.lbl_status)

        self.lbl_last_gen = QLabel("")
        self.lbl_last_gen.setStyleSheet("color: #444444; font-size: 10px;")
        s_layout.addWidget(self.lbl_last_gen)

        main_layout.addWidget(sidebar)

        # ── 2. MAIN CONTENT AREA (#121212) ────────────────────────────────────
        content = QWidget()
        c_layout = QVBoxLayout(content)
        c_layout.setContentsMargins(18, 14, 18, 14)
        c_layout.setSpacing(14)

        # Header Row
        hdr_row = QHBoxLayout()
        hdr_title = QLabel("Recent Sessions")
        hdr_title.setStyleSheet("font-size: 22px; font-weight: bold; color: #FFFFFF;")
        hdr_row.addWidget(hdr_title)

        hdr_row.addStretch()

        btn_refresh = QPushButton("↻  Refresh")
        btn_refresh.setFixedSize(100, 30)
        btn_refresh.setStyleSheet("background: #252525; color: white; border-radius: 6px; font-weight: bold;")
        btn_refresh.clicked.connect(self._load_recent_sessions)
        hdr_row.addWidget(btn_refresh)
        c_layout.addLayout(hdr_row)

        # 3 Stats Metric Cards Row
        self.stats_layout = QHBoxLayout()
        self.stats_layout.setSpacing(12)

        # Card 1: Gym Attendance
        self.c1 = QFrame()
        self.c1.setObjectName("StatCard")
        c1_l = QVBoxLayout(self.c1)
        c1_l.setContentsMargins(14, 12, 14, 12)
        c1_l.addWidget(QLabel("GYM ATTENDANCE", objectName="StatCardTitle"))
        self.c1_val = QLabel("-- Days", objectName="StatCardValue")
        c1_l.addWidget(self.c1_val)
        self.c1_sub = QLabel("-- this year · -- this month", objectName="StatCardSub")
        c1_l.addWidget(self.c1_sub)
        self.stats_layout.addWidget(self.c1)

        # Card 2: Current Split Duration (Clickable)
        self.c2 = QFrame()
        self.c2.setObjectName("StatCard")
        self.c2.setCursor(Qt.PointingHandCursor)
        self.c2.mousePressEvent = lambda e: self.show_split_details()
        c2_l = QVBoxLayout(self.c2)
        c2_l.setContentsMargins(14, 12, 14, 12)
        c2_l.addWidget(QLabel("CURRENT SPLIT DURATION", objectName="StatCardTitle"))
        self.c2_val = QLabel("-- Weeks", objectName="StatCardValue")
        c2_l.addWidget(self.c2_val)
        self.c2_sub = QLabel("N-Day Split · started --", objectName="StatCardSub")
        c2_l.addWidget(self.c2_sub)
        self.stats_layout.addWidget(self.c2)

        # Card 3: Last Workout
        self.c3 = QFrame()
        self.c3.setObjectName("StatCard")
        c3_l = QVBoxLayout(self.c3)
        c3_l.setContentsMargins(14, 12, 14, 12)
        c3_l.addWidget(QLabel("LAST WORKOUT", objectName="StatCardTitle"))
        self.c3_val = QLabel("--", objectName="StatCardValue")
        c3_l.addWidget(self.c3_val)
        self.c3_sub = QLabel("Day --", objectName="StatCardSub")
        c3_l.addWidget(self.c3_sub)
        self.stats_layout.addWidget(self.c3)

        c_layout.addLayout(self.stats_layout)

        # Recent Sessions Horizontal Card Row
        self.sessions_scroll = QScrollArea()
        self.sessions_scroll.setWidgetResizable(True)
        self.sessions_container = QWidget()
        self.sessions_layout = QHBoxLayout(self.sessions_container)
        self.sessions_layout.setSpacing(12)
        self.sessions_layout.setContentsMargins(0, 0, 0, 0)
        self.sessions_scroll.setWidget(self.sessions_container)
        c_layout.addWidget(self.sessions_scroll, 1)

        main_layout.addWidget(content, 1)

    def _load_active_profile(self):
        p = self.manager.get_active_profile()
        if p:
            self.lbl_profile_name.setText(p.name)
        self._load_recent_sessions()

    def _load_recent_sessions(self):
        p = self.manager.get_active_profile()
        if not p:
            self.lbl_status.setText("No active profile.")
            return

        sessions_file = getattr(p, "sessions_file", None) or os.path.join(p.sessions_dir, "sessions.py")
        if not os.path.exists(sessions_file):
            self.lbl_status.setText(f"sessions.py not found at {sessions_file}")
            return

        try:
            sessions_dir = os.path.dirname(sessions_file)
            if sessions_dir not in sys.path:
                sys.path.insert(0, sessions_dir)

            if "sessions" in sys.modules:
                sess = importlib.reload(sys.modules["sessions"])
            else:
                import sessions as sess

            self.active_sessions = sess
            user_data = getattr(sess, "USER_DATA", {})
            stats = calculate_gym_stats(user_data)
            self.cached_stats = stats

            # Update Stats Cards
            self.c1_val.setText(f"{stats.get('total_days', 0)} Days")
            self.c1_sub.setText(f"{stats.get('this_year_days', 0)} this year · {stats.get('this_month_days', 0)} this month")

            self.c2_val.setText(f"{stats.get('current_split_weeks', 0.0):.1f} Weeks")
            self.c2_sub.setText(f"{stats.get('cycle_length', 'N/A')}-Day Split · started {stats.get('current_split_start', 'N/A')}")

            self.c3_val.setText(str(stats.get("latest_workout_date", "N/A")))
            self.c3_sub.setText(f"Day {stats.get('latest_workout_day', 'N/A')}")

            # Rebuild Horizontal Workout Cards
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
                v = day_data.get("day")
                is_pr = isinstance(v, str) and v.upper() == "PR"

                card = QFrame()
                card.setObjectName("WorkoutCardPR" if is_pr else "WorkoutCard")
                card_l = QVBoxLayout(card)
                card_l.setContentsMargins(14, 14, 14, 14)
                card_l.setSpacing(6)

                # Header
                hdr_str = f"📅  {d_str}  ·  Day {v}" if isinstance(v, int) else f"📅  {d_str}  ·  {v}"
                hdr_lbl = QLabel(hdr_str)
                hdr_lbl.setObjectName("WorkoutHeaderPR" if is_pr else "WorkoutHeader")
                card_l.addWidget(hdr_lbl)

                sep = QFrame()
                sep.setStyleSheet(f"background: {'#5A3000' if is_pr else '#2E2E2E'}; max-height: 1px; min-height: 1px;")
                card_l.addWidget(sep)

                # Exercises
                for ex_id, log in day_data.items():
                    if not isinstance(log, Log):
                        continue
                    info = EXERCISE_STANDARDS.get(ex_id, {})
                    ex_name = info.get("name", ex_id)
                    reps_str = "-".join(str(r) for r in log.reps) if len(set(log.reps)) > 1 else f"{len(log.reps)} × {log.reps[0]}"
                    mass_str = f" @ {log.mass[0]}kg" if log.mass and max(log.mass) > 0 else " (BW)"

                    ex_row = QHBoxLayout()
                    lbl_n = QLabel(ex_name)
                    lbl_n.setStyleSheet("color: #DDDDDD; font-size: 12px;")
                    ex_row.addWidget(lbl_n)
                    ex_row.addStretch()

                    lbl_s = QLabel(f"{reps_str}{mass_str}")
                    lbl_s.setStyleSheet("color: #888888; font-size: 11px;")
                    ex_row.addWidget(lbl_s)

                    card_l.addLayout(ex_row)

                card_l.addStretch()
                self.sessions_layout.addWidget(card, 1)

            self.lbl_status.setText(f"Ready ({p.name})")

        except Exception as e:
            self.lbl_status.setText(f"Error: {e}")

    def run_log_generator(self):
        p = self.manager.get_active_profile()
        if not p or not self.active_sessions:
            QMessageBox.warning(self, "Warning", "No active profile loaded.")
            return

        self.lbl_status.setText("Generating Excel Log...")

        def _task():
            try:
                timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
                filename = os.path.join(p.output_dir, f"Training_Log_{timestamp}.xlsx")
                processor = TrainingLogProcessor(
                    filename,
                    self.active_sessions.EXERCISE_REGISTRY,
                    self.active_sessions.USER_DATA,
                    self.active_sessions.BODYMASS_LOG,
                    p.to_dict(),
                )
                processor.validate_data()
                processor.write_headers()
                processor.process_data(self.active_sessions.USER_DATA)
                processor.write_calculations()
                processor.generate_charts()
                processor.write_definitions()
                processor.write_personal_records()
                processor.write_user_profile()
                processor.save()

                self.last_generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
                QTimer.singleShot(0, lambda: self._on_log_success(filename))
            except Exception as e:
                QTimer.singleShot(0, lambda: QMessageBox.critical(self, "Error", str(e)))

        threading.Thread(target=_task, daemon=True).start()

    def _on_log_success(self, filename: str):
        self.lbl_status.setText(f"✅ Excel log created!")
        self.lbl_last_gen.setText(f"Last gen: {self.last_generated_at}")
        try:
            os.startfile(filename)
        except Exception:
            pass

    def run_plan_generator(self):
        p = self.manager.get_active_profile()
        if not p or not self.active_sessions:
            QMessageBox.warning(self, "Warning", "Select a valid profile first.")
            return

        sessions_file = getattr(p, "sessions_file", None) or os.path.join(p.sessions_dir, "sessions.py")
        user_data = getattr(self.active_sessions, "USER_DATA", {})
        N, last_day_int = detect_cycle(user_data)

        if N is None:
            QMessageBox.information(
                self,
                "Cycle Unknown",
                "Could not detect your split cycle yet.\nComplete at least one full cycle before using 'Plan Next Cycle'.",
            )
            return

        day_nums = days_to_generate(N, last_day_int)
        if not day_nums:
            QMessageBox.information(
                self, "Nothing to add", "All days in the current cycle are already planned."
            )
            return

        try:
            planned = build_planned_sessions(sessions_file, day_nums)
        except Exception as e:
            QMessageBox.critical(self, "Plan Build Error", str(e))
            return

        why = f"Starting new cycle — all {N} days" if (last_day_int or 0) >= N else f"Completing cycle of {N}"
        dialog = PySideDynamicPlanDialog(self, sessions_file, planned, title=f"Plan Next Cycle ({why})")
        if dialog.exec() and dialog.confirmed:
            self._load_recent_sessions()

    def open_latest_excel(self):
        p = self.manager.get_active_profile()
        if p and p.output_dir and os.path.exists(p.output_dir):
            import glob
            files = sorted(glob.glob(os.path.join(p.output_dir, "Training_Log_*.xlsx")), reverse=True)
            if files:
                os.startfile(files[0])
            else:
                QMessageBox.information(self, "Notice", "No Excel files found.")

    def edit_sessions(self):
        p = self.manager.get_active_profile()
        if p and p.sessions_dir:
            f = os.path.join(p.sessions_dir, "sessions.py")
            if os.path.exists(f):
                os.startfile(f)

    def open_output(self):
        p = self.manager.get_active_profile()
        if p and p.output_dir and os.path.exists(p.output_dir):
            os.startfile(p.output_dir)

    def show_exercise_library(self):
        p = self.manager.get_active_profile()
        sex = getattr(p, "sex", "male") if p else "male"
        mass = getattr(p, "mass", 80.0) if p else 80.0
        dlg = PySideStandardsDialog(self, user_sex=sex, user_mass=mass)
        dlg.exec()

    def show_split_details(self):
        if hasattr(self, "cached_stats"):
            dlg = PySideSplitDetailsDialog(self, self.cached_stats)
            dlg.exec()


def run_pyside_app():
    app = QApplication(sys.argv)
    window = IronLogPySideApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run_pyside_app()
