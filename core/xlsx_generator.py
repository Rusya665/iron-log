from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Callable, Dict, List

import xlsxwriter
import statistics

from core.standards import get_exercise_standard
from core.models import Exercise, Log


@dataclass
class Metric:
    name: str
    func: Callable[[Log], float]
    fmt_str: str = "0.0"
    is_plottable: bool = False
    is_helper: bool = False


def calc_vol(d: Log) -> float:
    return sum(r * m for r, m in zip(d.reps, d.mass))


def calc_avg_mass(d: Log) -> float:
    return statistics.mean(d.mass) if d.mass else 0


def calc_stdev(d: Log) -> float:
    return statistics.stdev(d.mass) if len(d.mass) > 1 else 0


def calc_brzycki(d: Log) -> float:
    if not d.reps:
        return 0
    if d.mass and max(d.mass) == 0:
        return max(d.reps)

    one_rms = [m * (36 / (37 - r)) if r < 37 else m for r, m in zip(d.reps, d.mass)]
    return max(one_rms) if one_rms else 0


METRICS_CONFIG: List[Metric] = [
    Metric("Avg Reps", lambda d: statistics.mean(d.reps), "0.00"),
    Metric("Avg Mass", calc_avg_mass, "0.00"),
    Metric("Volume", calc_vol, "#,##0"),
    Metric("Est 1RM", calc_brzycki, "0.00"),
    Metric("Stdev Mass", calc_stdev, "0.00", is_helper=True),
    Metric(
        "Stdev Reps",
        lambda d: statistics.stdev(d.reps) if len(d.reps) > 1 else 0,
        "0.00",
        is_helper=True,
    ),
    Metric("Std (Beg)", lambda d: 0, "0.00", is_helper=True),
    Metric("Std (Nov)", lambda d: 0, "0.00", is_helper=True),
    Metric("Std (Int)", lambda d: 0, "0.00", is_helper=True),
    Metric("Std (Adv)", lambda d: 0, "0.00", is_helper=True),
    Metric("Std (Eli)", lambda d: 0, "0.00", is_helper=True),
    Metric("Bg (Unt)", lambda d: 0, "0", is_helper=True),
    Metric("Bg (Beg)", lambda d: 0, "0", is_helper=True),
    Metric("Bg (Nov)", lambda d: 0, "0", is_helper=True),
    Metric("Bg (Int)", lambda d: 0, "0", is_helper=True),
    Metric("Bg (Adv)", lambda d: 0, "0", is_helper=True),
    Metric("Bg (Eli)", lambda d: 0, "0", is_helper=True),
]

CHART_CONFIG = {
    "summary": {"width": 1000, "height": 500},
    "pie": {"width": 600, "height": 450},
    "column": {"width": 600, "height": 350},
    "individual": {"width": 800, "height": 450},
}


class TrainingLogProcessor:
    def __init__(self, output_path: str, exercises: List[Exercise], user_data: Dict[str, Dict[str, Log]], bodymass_log: dict, user_profile: dict = None):
        self.output_path = output_path
        self.exercises = exercises
        self.user_data = user_data
        self.bodymass_log = bodymass_log
        self.user_profile = user_profile or {}
        self.metrics = METRICS_CONFIG

        if not self.bodymass_log:
            import sys
            print("CRITICAL ERROR: 'BODYMASS_LOG' is empty.")
            sys.exit(1)

        self.wb = xlsxwriter.Workbook(self.output_path)
        self.ws_charts = self.wb.add_worksheet("Progress_Charts")
        self.ws_data = self.wb.add_worksheet("Data_Log")
        self.ws_definitions = self.wb.add_worksheet("Definitions")
        self.ws_calculations = self.wb.add_worksheet("Calculations")
        self.ws_user_profile = self.wb.add_worksheet("User_Profile")
        self.ws_personal_records = self.wb.add_worksheet("Personal_Records")

        self.row_cursor = 0
        self.chart_row_cursor = 0
        self.col_map: Dict[str, Dict[str, int]] = {}
        self.exercise_volumes = {ex.id: 0.0 for ex in self.exercises}
        self.weekly_sessions: Dict[str, int] = {}

        self.bw_rows = 0
        self.measurement_cols = 0

        self.levels = [
            ("Beginner", "Beg", "#0d0887"),
            ("Novice", "Nov", "#7e03a8"),
            ("Intermediate", "Int", "#cb4679"),
            ("Advanced", "Adv", "#f89441"),
            ("Elite", "Eli", "#f0f921")
        ]
        self.bg_levels = [
            ("Bg (Unt)", "#FFFFFF", 100),
            ("Bg (Beg)", "#0d0887", 90),
            ("Bg (Nov)", "#7e03a8", 90),
            ("Bg (Int)", "#cb4679", 90),
            ("Bg (Adv)", "#f89441", 90),
            ("Bg (Eli)", "#f0f921", 90)
        ]

        self._init_styles()

    def _init_styles(self):
        self.style_header_main = self.wb.add_format({"bold": True, "align": "center", "valign": "vcenter", "bg_color": "#D7E4BC", "border": 1})
        self.style_header_sub = self.wb.add_format({"bold": True, "align": "center", "bg_color": "#DAEEF3", "border": 1, "font_size": 9})
        self.style_center_across = self.wb.add_format({"bold": True, "align": "center", "valign": "vcenter", "bg_color": "#D7E4BC", "border": 1})
        self.style_center_across.set_center_across()
        self.style_def_header = self.wb.add_format({"bold": True, "font_size": 12, "bottom": 2})
        self.style_def_text = self.wb.add_format({"text_wrap": True, "align": "left", "valign": "top"})
        self.style_date = self.wb.add_format({"num_format": "yyyy-mm-dd", "border": 1, "align": "left"})

        self.num_styles = {}
        for m in self.metrics:
            self.num_styles[m.name] = self.wb.add_format({"num_format": m.fmt_str, "border": 1, "align": "center"})

        self.level_styles = {
            "Untrained": self.wb.add_format({"align": "left"}),
            "Beginner": self.wb.add_format({"bg_color": "#0d0887", "font_color": "#FFFFFF", "align": "left"}),
            "Novice": self.wb.add_format({"bg_color": "#7e03a8", "font_color": "#FFFFFF", "align": "left"}),
            "Intermediate": self.wb.add_format({"bg_color": "#cb4679", "font_color": "#FFFFFF", "align": "left"}),
            "Advanced": self.wb.add_format({"bg_color": "#f89441", "align": "left"}),
            "Elite": self.wb.add_format({"bg_color": "#f0f921", "align": "left"})
        }

    def validate_data(self):
        """Check for mismatched reps and masses in user data."""
        for date_str, exercises in self.user_data.items():
            for ex_id, log in exercises.items():
                if len(log.reps) != len(log.mass):
                    ex_name = next((e.display_name for e in self.exercises if e.id == ex_id), ex_id)
                    raise ValueError(
                        f"Data Error on {date_str} ({ex_name}):\n"
                        f"Found {len(log.reps)} reps but {len(log.mass)} masses.\n"
                        f"Each set must have both a rep count and a mass value."
                    )

    def write_headers(self):
        self.ws_data.write(0, 0, "Date", self.style_header_main)
        self.ws_data.write(1, 0, "", self.style_header_main)
        self.ws_data.set_column(0, 0, 12)

        self.ws_data.write(0, 1, "Daily Summary", self.style_center_across)
        self.ws_data.write_blank(0, 2, "", self.style_center_across)
        self.ws_data.write_blank(0, 3, "", self.style_center_across)

        self.ws_data.write(1, 1, "Volume", self.style_header_sub)
        self.ws_data.write(1, 2, "Reps", self.style_header_sub)
        self.ws_data.write(1, 3, "Intensity", self.style_header_sub)

        self.ws_data.set_column(1, 1, 10)
        self.ws_data.set_column(2, 2, 8)
        self.ws_data.set_column(3, 3, 9)

        current_col = 4
        for ex in self.exercises:
            self.col_map[ex.id] = {}
            self.ws_data.write(
                0, current_col, ex.display_name, self.style_center_across
            )
            for i in range(1, len(self.metrics)):
                self.ws_data.write_blank(
                    0, current_col + i, "", self.style_center_across
                )

            for m in self.metrics:
                self.ws_data.write(1, current_col, m.name, self.style_header_sub)
                self.ws_data.set_column(
                    current_col, current_col, 10 if not m.is_helper else 2
                )
                self.col_map[ex.id][m.name] = current_col
                current_col += 1

        self.ws_data.freeze_panes(2, 1)
        self.row_cursor = 2

    def write_definitions(self):
        self.ws_definitions.set_column(0, 0, 25)
        self.ws_definitions.set_column(1, 1, 80)

        self.ws_definitions.write(0, 0, "Metric", self.style_def_header)
        self.ws_definitions.write(0, 1, "Description", self.style_def_header)

        definitions = [
            (
                "Est 1RM",
                "Estimated 1 Rep Max using Brzycki formula: Mass * (36 / (37 - Reps)). Represents the theoretical maximum mass you could lift for one rep based on the set performed. For body mass exercises (0 mass), this calculates 'Max Reps' instead.",
            ),
            (
                "Daily Volume",
                "Total tonnage lifted during the workout. Calculated as the sum of (Reps * Mass) for every set performed that day.",
            ),
            (
                "Daily Reps",
                "Total number of repetitions performed across all exercises during the workout.",
            ),
            (
                "Daily Intensity",
                "Daily Average Relative Intensity. This measures the average 'effort' of your sets relative to your daily capacity. For mass-based exercises, it is (Set Mass / Daily Est 1RM). For body mass exercises, it is (Set Reps / Daily Max Reps). A value of 100% means every set was a max effort set. 70-85% is typical for hypertrophy training.",
            ),
            (
                "Weekly Consistency",
                "Number of training sessions recorded in a given calendar week.",
            ),
            (
                "Total Volume Distribution",
                "A breakdown of which exercises account for the most total volume (tonnage) lifted over the entire logged period.",
            ),
            (
                "Avg Mass",
                "The average mass used across all sets for a specific exercise in a session.",
            ),
            (
                "Avg Reps",
                "The average number of reps performed per set for a specific exercise in a session.",
            ),
        ]

        for i, (metric, desc) in enumerate(definitions, start=1):
            self.ws_definitions.write(i, 0, metric, self.style_def_text)
            self.ws_definitions.write(i, 1, desc, self.style_def_text)

    def process_data(self, data: Dict[str, Dict[str, Log]]):
        if not data:
            return

        sorted_dates = sorted(data.keys())
        
        significant_dates = set(self.bodymass_log.keys())
        if sorted_dates:
            significant_dates.add(sorted_dates[0])
            significant_dates.add(sorted_dates[-1])

        # Fill missing calendar dates to ensure color background transitions are vertical
        min_date_dt = datetime.strptime(sorted_dates[0], "%Y-%m-%d")
        max_date_dt = datetime.strptime(sorted_dates[-1], "%Y-%m-%d")
        
        all_dates = []
        curr = min_date_dt
        while curr <= max_date_dt:
            all_dates.append(curr.strftime("%Y-%m-%d"))
            curr += timedelta(days=1)

        LEVEL_MAP = {-1: "Bg (Unt)", 0: "Bg (Beg)", 1: "Bg (Nov)", 2: "Bg (Int)", 3: "Bg (Adv)", 4: "Bg (Eli)"}
        max_level_so_far = {ex.id: -1 for ex in self.exercises}
        sex = self.user_profile.get("sex", "male")

        for date_str in all_dates:
            self.ws_data.write(self.row_cursor, 0, date_str, self.style_date)
            
            day_data = data.get(date_str, {})
            is_workout_day = bool(day_data)

            if is_workout_day:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                year, week_num, _ = dt.isocalendar()
                week_key = f"{year}-W{week_num:02d}"
                self.weekly_sessions[week_key] = self.weekly_sessions.get(week_key, 0) + 1

                daily_vol = 0
                daily_reps = 0
                intensity_ratios = []

                for ex_id, log in day_data.items():
                    if not (log.reps and log.mass):
                        continue

                    vol = sum(r * m for r, m in zip(log.reps, log.mass))
                    daily_vol += vol
                    daily_reps += sum(log.reps)

                    if ex_id in self.exercise_volumes:
                        self.exercise_volumes[ex_id] += vol

                    capacity = 0
                    is_bodyweight = False
                    if max(log.mass) == 0:
                        is_bodyweight = True
                        capacity = max(log.reps)
                    else:
                        capacity = calc_brzycki(log)

                    if capacity > 0:
                        for r, m in zip(log.reps, log.mass):
                            ratio = r / capacity if is_bodyweight else m / capacity
                            intensity_ratios.append(ratio)

                daily_intensity = statistics.mean(intensity_ratios) if intensity_ratios else 0
                self.ws_data.write(self.row_cursor, 1, daily_vol, self.num_styles["Volume"])
                self.ws_data.write(self.row_cursor, 2, daily_reps, self.num_styles["Avg Mass"])
                self.ws_data.write(self.row_cursor, 3, daily_intensity, self.wb.add_format({"num_format": "0%", "border": 1, "align": "center"}))

            for ex in self.exercises:
                has_data = is_workout_day and ex.id in day_data and sum(day_data[ex.id].reps) > 0
                raw_input = day_data.get(ex.id) if has_data else None

                if has_data:
                    is_bodyweight = max(raw_input.mass) == 0 if raw_input.mass else False
                    cap = max(raw_input.reps) if is_bodyweight else calc_brzycki(raw_input)

                    std_beg = get_exercise_standard(ex.id, date_str, self.bodymass_log, "Beginner", sex=sex)
                    std_nov = get_exercise_standard(ex.id, date_str, self.bodymass_log, "Novice", sex=sex)
                    std_int = get_exercise_standard(ex.id, date_str, self.bodymass_log, "Intermediate", sex=sex)
                    std_adv = get_exercise_standard(ex.id, date_str, self.bodymass_log, "Advanced", sex=sex)
                    std_eli = get_exercise_standard(ex.id, date_str, self.bodymass_log, "Elite", sex=sex)

                    today_level = -1
                    if std_eli > 0 and cap >= std_eli:
                        today_level = 4
                    elif std_adv > 0 and cap >= std_adv:
                        today_level = 3
                    elif std_int > 0 and cap >= std_int:
                        today_level = 2
                    elif std_nov > 0 and cap >= std_nov:
                        today_level = 1
                    elif std_beg > 0 and cap >= std_beg:
                        today_level = 0

                    if today_level > max_level_so_far[ex.id]:
                        max_level_so_far[ex.id] = today_level

                active_bg_level = LEVEL_MAP[max_level_so_far[ex.id]]

                for m in self.metrics:
                    col_idx = self.col_map[ex.id][m.name]
                    val = None

                    if m.name.startswith("Bg ("):
                        # Plot an absurdly high number so it shoots past any visible Y-axis constraint
                        # creating a near-perfect vertical boundary line and endless height filling
                        val = 1000000 if m.name == active_bg_level else 0
                    elif m.name.startswith("Std ("):
                        if date_str in significant_dates:
                            level_str = m.name[5:8]
                            map_std = {"Beg": "Beginner", "Nov": "Novice", "Int": "Intermediate", "Adv": "Advanced", "Eli": "Elite"}
                            val = get_exercise_standard(ex.id, date_str, self.bodymass_log, map_std.get(level_str), sex=sex)
                            if val == 0:
                                val = None
                    elif has_data:
                        val = m.func(raw_input)
                        
                    if val is not None:
                        self.ws_data.write(self.row_cursor, col_idx, val, self.num_styles[m.name])
            self.row_cursor += 1

    def write_calculations(self):
        self.ws_calculations.write(0, 0, "Exercise", self.style_header_sub)
        self.ws_calculations.write(0, 1, "Total Volume", self.style_header_sub)

        row = 1
        sorted_vols = sorted(self.exercise_volumes.items(), key=lambda x: x[1], reverse=True)
        self.calc_vol_rows = len(sorted_vols)

        for ex_id, vol in sorted_vols:
            display = ex_id
            for ex in self.exercises:
                if ex.id == ex_id:
                    display = ex.display_name
                    break
            self.ws_calculations.write(row, 0, display)
            self.ws_calculations.write(row, 1, vol)
            row += 1

        self.ws_calculations.write(0, 3, "Week", self.style_header_sub)
        self.ws_calculations.write(0, 4, "Sessions", self.style_header_sub)

        row = 1
        sorted_weeks = sorted(self.weekly_sessions.items())
        self.calc_week_rows = len(sorted_weeks)

        for week, count in sorted_weeks:
            self.ws_calculations.write(row, 3, week)
            self.ws_calculations.write(row, 4, count)
            row += 1

        self.ws_calculations.write(0, 6, "Date", self.style_header_sub)
        self.ws_calculations.write(0, 7, "Mass (kg)", self.style_header_sub)

        measurement_keys = set()
        for data in self.bodymass_log.values():
            if isinstance(data, dict):
                measurement_keys.update([k for k in data.keys() if k.lower() not in ("mass", "weight")])
                
        m_keys = sorted(list(measurement_keys))
        for i, k in enumerate(m_keys):
            self.ws_calculations.write(0, 8 + i, f"{k.capitalize()} (cm)", self.style_header_sub)
            
        row = 1
        sorted_dates = sorted(self.bodymass_log.keys())
        self.bw_rows = len(sorted_dates)
        self.measurement_cols = len(m_keys)
        
        for d_str in sorted_dates:
            data = self.bodymass_log[d_str]
            mass = data if isinstance(data, (int, float)) else data.get("mass", data.get("weight", None))
            
            self.ws_calculations.write(row, 6, d_str)
            if mass is not None:
                self.ws_calculations.write(row, 7, mass)
                
            if isinstance(data, dict):
                for i, k in enumerate(m_keys):
                    val = data.get(k)
                    if val is not None:
                        self.ws_calculations.write(row, 8 + i, val)
            row += 1

    def write_personal_records(self):
        self.ws_personal_records.set_column(0, 0, 25)
        self.ws_personal_records.set_column(1, 3, 15)
        self.ws_personal_records.write(0, 0, "Exercise", self.style_header_main)
        self.ws_personal_records.write(0, 1, "PR Mass (kg)", self.style_header_main)
        self.ws_personal_records.write(0, 2, "Date Achieved", self.style_header_main)
        self.ws_personal_records.write(0, 3, "Strength Level", self.style_header_main)
        row = 1
        
        for ex in self.exercises:
            max_mass = 0
            pr_date = None
            for date_str, day_data in self.user_data.items():
                if ex.id in day_data:
                    log = day_data[ex.id]
                    if log.mass:
                        current_max = max(log.mass)
                        if current_max > max_mass:
                            max_mass = current_max
                            pr_date = date_str
            
            if pr_date:
                levels_to_check = [lvl[0] for lvl in reversed(self.levels)]
                reached_level = "Untrained"
                
                for level in levels_to_check:
                    std_val = get_exercise_standard(
                        ex.id, 
                        pr_date, 
                        self.bodymass_log, 
                        level, 
                        sex=self.user_profile.get("sex")
                    )
                    if std_val > 0 and max_mass >= std_val:
                        reached_level = level
                        break
                
                self.ws_personal_records.write(row, 0, ex.display_name)
                self.ws_personal_records.write(row, 1, max_mass)
                self.ws_personal_records.write(row, 2, pr_date)
                
                style = self.level_styles.get(reached_level, self.style_def_text)
                self.ws_personal_records.write(row, 3, reached_level, style)
                row += 1

    def _create_summary_chart(self, metric_key: str, chart_title: str, y_axis_label: str, cell_position: str):
        width = CHART_CONFIG["summary"]["width"]
        height = CHART_CONFIG["summary"]["height"]

        chart = self.wb.add_chart({"type": "line"})
        chart.set_title({"name": chart_title})
        chart.set_size({"width": width, "height": height})
        chart.set_x_axis({"date_axis": True})
        chart.set_y_axis({"name": y_axis_label, "major_gridlines": {"visible": True}})
        chart.show_blanks_as("span")

        for ex in self.exercises:
            if metric_key in self.col_map[ex.id]:
                col_idx = self.col_map[ex.id][metric_key]
                chart.add_series({
                    "name": ex.display_name,
                    "categories": ["Data_Log", 2, 0, self.row_cursor - 1, 0],
                    "values": ["Data_Log", 2, col_idx, self.row_cursor - 1, col_idx],
                    "marker": {"type": "none"},
                    "line": {"width": 2},
                })

        self.ws_charts.insert_chart(cell_position, chart)

    def _create_body_comp_chart(self, cell_position: str) -> int:
        if self.bw_rows == 0:
            return 0
            
        chart = self.wb.add_chart({"type": "line"})
        chart.set_title({"name": "Body Composition Progression"})
        chart.set_size({"width": CHART_CONFIG["summary"]["width"], "height": CHART_CONFIG["summary"]["height"]})
        chart.set_x_axis({"name": "Date", "date_axis": True})
        chart.set_y_axis({"name": "Mass (kg)", "major_gridlines": {"visible": True}})
        
        chart.add_series({
            "name": "Body Mass",
            "categories": ["Calculations", 1, 6, self.bw_rows, 6],
            "values": ["Calculations", 1, 7, self.bw_rows, 7],
            "line": {"color": "#000000", "width": 2.5},
            "marker": {"type": "none"}
        })
        
        if self.measurement_cols > 0:
            chart.set_y2_axis({"name": "Measurements (cm)"})
            colors = ["#FF5733", "#33FF57", "#3357FF", "#F333FF"]
            for i in range(self.measurement_cols):
                chart.add_series({
                    "name": ["Calculations", 0, 8 + i],
                    "categories": ["Calculations", 1, 6, self.bw_rows, 6],
                    "values": ["Calculations", 1, 8 + i, self.bw_rows, 8 + i],
                    "y2_axis": True,
                    "line": {"color": colors[i % len(colors)], "width": 2, "dash_type": "dash"},
                    "marker": {"type": "none"}
                })
                
        chart.show_blanks_as("span")
        self.ws_charts.insert_chart(cell_position, chart)
        return self._pixels_to_rows(CHART_CONFIG["summary"]["height"]) + 2

    def _pixels_to_rows(self, pixels: int) -> int:
        return int(pixels / 20) + 1

    def _pixels_to_cols(self, pixels: int) -> int:
        return int(round(pixels / 64))

    def generate_charts(self):
        w_summary = CHART_CONFIG["summary"]["width"]
        h_summary = CHART_CONFIG["summary"]["height"]
        w_pie = CHART_CONFIG["pie"]["width"]
        h_pie = CHART_CONFIG["pie"]["height"]
        w_col = CHART_CONFIG["column"]["width"]
        h_col = CHART_CONFIG["column"]["height"]
        w_indiv = CHART_CONFIG["individual"]["width"]
        h_indiv = CHART_CONFIG["individual"]["height"]

        left_col_idx = 1  
        left_col_letter = xlsxwriter.utility.xl_col_to_name(left_col_idx)
        cursor_left = 1  

        right_col_idx = left_col_idx + self._pixels_to_cols(w_summary) + 0
        right_col_letter = xlsxwriter.utility.xl_col_to_name(right_col_idx)
        cursor_right = 1  

        cursor_left += self._create_body_comp_chart(f"{left_col_letter}{cursor_left + 1}")

        self._create_summary_chart("Est 1RM", "Total Strength Overview (Est. 1RM)", "1RM (kg)", f"{left_col_letter}{cursor_left + 1}")
        cursor_left += self._pixels_to_rows(h_summary) + 2

        self._create_summary_chart("Avg Mass", "Average Mass Overview", "Mass (kg)", f"{left_col_letter}{cursor_left + 1}")
        cursor_left += self._pixels_to_rows(h_summary) + 2

        self._create_summary_chart("Avg Reps", "Average Reps Overview", "Reps", f"{left_col_letter}{cursor_left + 1}")
        cursor_left += self._pixels_to_rows(h_summary) + 2

        vol_chart = self.wb.add_chart({"type": "line"})
        vol_chart.set_title({"name": "Daily Total Volume"})
        vol_chart.set_size({"width": w_summary, "height": h_summary})
        vol_chart.set_x_axis({"date_axis": True})
        vol_chart.set_y_axis({"name": "Volume", "major_gridlines": {"visible": True}})
        vol_chart.show_blanks_as("span")
        vol_chart.add_series({
            "name": "Daily Volume",
            "categories": ["Data_Log", 2, 0, self.row_cursor - 1, 0],  
            "values": ["Data_Log", 2, 1, self.row_cursor - 1, 1],  
            "line": {"color": "#4F81BD", "width": 2.25},
            "marker": {"type": "none"},
        })
        self.ws_charts.insert_chart(f"{left_col_letter}{cursor_left + 1}", vol_chart)

        vol_chart_row = cursor_left
        cursor_left += self._pixels_to_rows(h_summary) + 2

        pie_chart = self.wb.add_chart({"type": "pie"})
        pie_chart.set_title({"name": "Total Volume Distribution"})
        pie_chart.set_size({"width": w_pie, "height": h_pie})
        if self.calc_vol_rows > 0:
            pie_chart.add_series({
                "name": "Volume",
                "categories": ["Calculations", 1, 0, self.calc_vol_rows, 0],
                "values": ["Calculations", 1, 1, self.calc_vol_rows, 1],
                "data_labels": {"percentage": True},
            })
        self.ws_charts.insert_chart(f"{right_col_letter}{cursor_right + 1}", pie_chart)
        cursor_right += self._pixels_to_rows(h_pie) + 2

        col_chart = self.wb.add_chart({"type": "column"})
        col_chart.set_title({"name": "Weekly Consistency (Sessions)"})
        col_chart.set_size({"width": w_col, "height": h_col})
        col_chart.set_y_axis({"name": "Sessions", "major_gridlines": {"visible": True}, "min": 0})
        col_chart.set_legend({"none": True})
        if self.calc_week_rows > 0:
            col_chart.add_series({
                "name": "Sessions",
                "categories": ["Calculations", 1, 3, self.calc_week_rows, 3],
                "values": ["Calculations", 1, 4, self.calc_week_rows, 4],
                "fill": {"color": "#9BBB59"},
            })
        self.ws_charts.insert_chart(f"{right_col_letter}{cursor_right + 1}", col_chart)
        cursor_right += self._pixels_to_rows(h_col) + 2

        target_row = max(cursor_right, vol_chart_row)

        int_chart = self.wb.add_chart({"type": "line"})
        int_chart.set_title({"name": "Daily Relative Intensity (Avg Effort)"})
        int_chart.set_size({"width": w_summary, "height": h_summary})
        int_chart.set_x_axis({"date_axis": True})
        int_chart.set_y_axis({"name": "Intensity (%)", "major_gridlines": {"visible": True}, "min": 0, "max": 1.0})
        int_chart.show_blanks_as("span")
        int_chart.add_series({
            "name": "Daily Intensity",
            "categories": ["Data_Log", 2, 0, self.row_cursor - 1, 0],  
            "values": ["Data_Log", 2, 3, self.row_cursor - 1, 3],  
            "line": {"color": "#C0504D", "width": 2.25},
            "marker": {"type": "none"},
        })
        self.ws_charts.insert_chart(f"{right_col_letter}{target_row + 1}", int_chart)

        max_cursor = max(cursor_left, cursor_right)
        max_cursor = max(max_cursor, target_row + self._pixels_to_rows(h_summary) + 1)
        chart_pos_y = max_cursor + 5

        for ex in self.exercises:
            # We must calculate Y-axis max early so we can strictly bind the primary axis.
            all_mass_vals = []
            col_mass = self.col_map[ex.id]["Avg Mass"]
            col_1rm = self.col_map[ex.id]["Est 1RM"]

            for d_data in self.user_data.values():
                if ex.id in d_data:
                    log = d_data[ex.id]
                    if log.mass and sum(log.mass) > 0:
                        m_mean = statistics.mean(log.mass)
                        m_stdev = statistics.stdev(log.mass) if len(log.mass) > 1 else 0
                        # Include both Avg Mass (with error) and Est 1RM in bounds calculation
                        all_mass_vals.append(m_mean - m_stdev)
                        all_mass_vals.append(m_mean + m_stdev)
                        
                        # Use calc_brzycki logic to ensure we account for the PR line in zoom
                        m_1rm = calc_brzycki(log)
                        if m_1rm > 0:
                            all_mass_vals.append(m_1rm)

            if all_mass_vals:
                min_mass = min(all_mass_vals)
                max_mass = max(all_mass_vals)
                # Ensure we have some breathing room (15%) for the PR line and benchmarks
                y_min = max(0, int(min_mass * 0.9))
                y_max = int(max_mass * 1.15)
                if y_max <= y_min:
                    y_max = y_min + 10
            else:
                y_min = 0
                y_max = 10

            is_bodyweight = True
            for d_data in self.user_data.values():
                if ex.id in d_data:
                    log_entry = d_data[ex.id]
                    if log_entry.mass and max(log_entry.mass) > 0:
                        is_bodyweight = False
                        break

            series_2_name = "Max Reps" if is_bodyweight else "Est 1RM"
            y_axis_name = "Max Reps" if is_bodyweight else "Mass (kg)"

            # 1. CREATE AREA BACKGROUND CHART FIRST (Becomes Primary Chart)
            bg_chart = self.wb.add_chart({"type": "area", "subtype": "stacked"})
            bg_chart.set_x_axis({"date_axis": True, "num_font": {"rotation": -45}})
            bg_chart.show_blanks_as("span")

            show_milestones = self.user_profile.get("show_milestones", True)
            if show_milestones:
                for bg_key, bg_color, trans in self.bg_levels:
                    if bg_key in self.col_map[ex.id]:
                        col_bg = self.col_map[ex.id][bg_key]
                        bg_chart.add_series({
                            "name": bg_key,
                            "categories": ["Data_Log", 2, 0, self.row_cursor - 1, 0],
                            "values": ["Data_Log", 2, col_bg, self.row_cursor - 1, col_bg],
                            "fill": {"color": bg_color, "transparency": trans},
                            "line": {"none": True},
                        })

            # 2. CREATE LINE CHART SECOND (Becomes Secondary Combined Chart)
            mass_chart = self.wb.add_chart({"type": "line"})
            
            col_mass = self.col_map[ex.id]["Avg Mass"]
            col_1rm = self.col_map[ex.id]["Est 1RM"]
            col_mass_err = self.col_map[ex.id]["Stdev Mass"]

            start_cell = xlsxwriter.utility.xl_rowcol_to_cell(2, col_mass_err, row_abs=True, col_abs=True)
            end_cell = xlsxwriter.utility.xl_rowcol_to_cell(self.row_cursor - 1, col_mass_err, row_abs=True, col_abs=True)
            mass_err_ref = f"='Data_Log'!{start_cell}:{end_cell}"

            mass_chart.add_series({
                "name": f"{ex.display_name} Avg Mass",
                "categories": ["Data_Log", 2, 0, self.row_cursor - 1, 0],
                "values": ["Data_Log", 2, col_mass, self.row_cursor - 1, col_mass],
                "line": {"color": "#203764", "width": 2.25},
                "marker": {"type": "none"},
                "y_error_bars": {
                    "type": "custom",
                    "plus_values": mass_err_ref,
                    "minus_values": mass_err_ref,
                    "direction": "both",
                    "end_style": "end",
                    "line": {"color": "#B4C6E7", "width": 1.5},
                },
            })

            if self.user_profile.get("show_pr", True):
                mass_chart.add_series({
                    "name": series_2_name,
                    "categories": ["Data_Log", 2, 0, self.row_cursor - 1, 0],
                    "values": ["Data_Log", 2, col_1rm, self.row_cursor - 1, col_1rm],
                    "line": {"color": "#C0504D", "width": 1.5, "dash_type": "dash"},
                    "marker": {"type": "none"},
                })

            if self.user_profile.get("show_standards", True):
                for m_key, m_label, m_color in self.levels:
                    std_key = f"Std ({m_label})"
                    if std_key in self.col_map[ex.id]:
                        col_std = self.col_map[ex.id][std_key]
                        mass_chart.add_series({
                            "name": m_label,
                            "categories": ["Data_Log", 2, 0, self.row_cursor - 1, 0],
                            "values": ["Data_Log", 2, col_std, self.row_cursor - 1, col_std],
                            "line": {"color": m_color, "width": 1.25}, 
                            "marker": {"type": "none"},
                        })

            # 3. COMBINE AND CLAMP AXIS
            bg_chart.combine(mass_chart)
            
            bg_chart.set_y_axis({"name": y_axis_name, "major_gridlines": {"visible": True}, "min": y_min, "max": y_max})
            bg_chart.set_title({"name": f"{ex.display_name} - Progress ({y_axis_name})"})
            bg_chart.set_size({"width": w_indiv, "height": h_indiv})
            
            # Hide the 6 background area series from the legend
            bg_chart.set_legend({"position": "bottom", "delete_series": [0, 1, 2, 3, 4, 5]})

            self.ws_charts.insert_chart(f"{left_col_letter}{chart_pos_y}", bg_chart)

            col_reps = self.col_map[ex.id]["Avg Reps"]
            col_reps_err = self.col_map[ex.id]["Stdev Reps"]
            reps_col_idx = 1 + self._pixels_to_cols(w_indiv) + 1
            reps_col_letter = xlsxwriter.utility.xl_col_to_name(reps_col_idx)

            start_cell_reps = xlsxwriter.utility.xl_rowcol_to_cell(2, col_reps_err, row_abs=True, col_abs=True)
            end_cell_reps = xlsxwriter.utility.xl_rowcol_to_cell(self.row_cursor - 1, col_reps_err, row_abs=True, col_abs=True)
            reps_err_ref = f"='Data_Log'!{start_cell_reps}:{end_cell_reps}"

            reps_chart = self.wb.add_chart({"type": "line"})
            reps_chart.set_x_axis({"date_axis": True, "num_font": {"rotation": -45}})
            reps_chart.show_blanks_as("span")
            reps_chart.set_legend({"position": "bottom"})

            reps_chart.add_series({
                "name": "Avg Reps",
                "categories": ["Data_Log", 2, 0, self.row_cursor - 1, 0],
                "values": ["Data_Log", 2, col_reps, self.row_cursor - 1, col_reps],
                "line": {"color": "#8064A2", "width": 2},
                "marker": {"type": "none"},
                "y_error_bars": {
                    "type": "custom",
                    "plus_values": reps_err_ref,
                    "minus_values": reps_err_ref,
                    "direction": "both",
                    "end_style": "end",
                    "line": {"color": "#CCC0DA", "width": 1.5},
                },
            })

            reps_chart.set_title({"name": f"{ex.display_name} - Reps Consistency"})
            reps_chart.set_size({"width": w_indiv, "height": h_indiv})

            all_reps_vals = []
            for d_data in self.user_data.values():
                if ex.id in d_data:
                    log = d_data[ex.id]
                    if log.reps and sum(log.reps) > 0:
                        r_mean = statistics.mean(log.reps)
                        r_stdev = statistics.stdev(log.reps) if len(log.reps) > 1 else 0
                        all_reps_vals.append(r_mean - r_stdev)

            if all_reps_vals:
                min_reps = min(all_reps_vals)
                y_min_reps = max(0, int(min_reps * 0.8))
            else:
                y_min_reps = 0

            reps_chart.set_y_axis({"name": "Reps", "major_gridlines": {"visible": True}, "min": y_min_reps})
            self.ws_charts.insert_chart(f"{reps_col_letter}{chart_pos_y}", reps_chart)

            chart_pos_y += self._pixels_to_rows(h_indiv) + 2

    def write_user_profile(self):
        self.ws_user_profile.set_column(0, 0, 20)
        self.ws_user_profile.set_column(1, 1, 40)

        self.ws_user_profile.write(0, 0, "Personal Data", self.style_def_header)
        self.ws_user_profile.write(0, 1, "", self.style_def_header)

        latest_mass = self.user_profile.get("mass", 0)
        if (latest_mass == 0 or latest_mass is None) and self.bodymass_log:
            sorted_dates = sorted(self.bodymass_log.keys(), reverse=True)
            for d in sorted_dates:
                entry = self.bodymass_log[d]
                m = entry if isinstance(entry, (int, float)) else entry.get("mass", entry.get("weight"))
                if m is not None:
                    latest_mass = m
                    break

        fields = [
            ("Name", self.user_profile.get("name", "N/A")),
            ("Age", self.user_profile.get("age", "N/A") or "N/A"),
            ("Sex", self.user_profile.get("sex", "N/A")),
            ("Last Known Mass", f"{latest_mass} kg"),
            ("Report Date", datetime.now().strftime("%Y-%m-%d")),
        ]

        for i, (label, value) in enumerate(fields, start=1):
            self.ws_user_profile.write(i, 0, label, self.style_def_text)
            self.ws_user_profile.write(i, 1, value, self.style_def_text)

    def save(self):
        self.write_personal_records()
        self.write_user_profile()
        try:
            self.wb.close()
            print(f"Log generated: {self.output_path}")
        except Exception as e:
            print(f"Error saving: {e}")
