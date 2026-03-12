import statistics
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Dict, List

import xlsxwriter
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
    Metric(
        "Stdev Mass",
        lambda d: statistics.stdev(d.mass) if len(d.mass) > 1 else 0,
        "0.00",
        is_helper=True,
    ),
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
]

CHART_CONFIG = {
    "summary": {"width": 1000, "height": 500},
    "pie": {"width": 600, "height": 450},
    "column": {"width": 600, "height": 350},
    "individual": {"width": 600, "height": 350},
}


class TrainingLogProcessor:
    def __init__(self, output_path: str, exercises: List[Exercise], user_data: Dict[str, Dict[str, Log]], bodyweight_log: dict):
        self.output_path = output_path
        self.exercises = exercises
        self.user_data = user_data
        self.bodyweight_log = bodyweight_log
        self.metrics = METRICS_CONFIG

        if not self.bodyweight_log:
            import sys
            print("CRITICAL ERROR: 'BODYWEIGHT_LOG' in 'sessions.py' is empty.")
            print("Please add at least one entry (e.g., '2025-01-01': 80.0) to track standards.")
            input("Press Enter to exit...")
            sys.exit(1)

        self.wb = xlsxwriter.Workbook(self.output_path)
        self.ws_data = self.wb.add_worksheet("Data_Log")
        self.ws_charts = self.wb.add_worksheet("Progress_Charts")
        self.ws_definitions = self.wb.add_worksheet("Definitions")
        self.ws_calculations = self.wb.add_worksheet("Calculations")

        self.row_cursor = 0
        self.chart_row_cursor = 0
        self.col_map: Dict[str, Dict[str, int]] = {}
        self.exercise_volumes = {ex.id: 0.0 for ex in self.exercises}
        self.weekly_sessions: Dict[str, int] = {}

        self.bw_rows = 0
        self.measurement_cols = 0

        self._init_styles()

    def _init_styles(self):
        self.style_header_main = self.wb.add_format(
            {
                "bold": True,
                "align": "center",
                "valign": "vcenter",
                "bg_color": "#D7E4BC",
                "border": 1,
            }
        )
        self.style_header_sub = self.wb.add_format(
            {
                "bold": True,
                "align": "center",
                "bg_color": "#DAEEF3",
                "border": 1,
                "font_size": 9,
            }
        )
        self.style_center_across = self.wb.add_format(
            {
                "bold": True,
                "align": "center",
                "valign": "vcenter",
                "bg_color": "#D7E4BC",
                "border": 1,
            }
        )
        self.style_center_across.set_center_across()

        self.style_def_header = self.wb.add_format(
            {"bold": True, "font_size": 12, "bottom": 2}
        )
        self.style_def_text = self.wb.add_format(
            {"text_wrap": True, "align": "left", "valign": "top"}
        )

        self.style_date = self.wb.add_format(
            {"num_format": "yyyy-mm-dd", "border": 1, "align": "left"}
        )

        self.num_styles = {}
        for m in self.metrics:
            self.num_styles[m.name] = self.wb.add_format(
                {"num_format": m.fmt_str, "border": 1, "align": "center"}
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
                "Estimated 1 Rep Max using Brzycki formula: Mass * (36 / (37 - Reps)). Represents the theoretical maximum weight you could lift for one rep based on the set performed. For bodyweight exercises (0 mass), this calculates 'Max Reps' instead.",
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
                "Daily Average Relative Intensity. This measures the average 'effort' of your sets relative to your daily capacity. For weighted exercises, it is (Set Mass / Daily Est 1RM). For bodyweight exercises, it is (Set Reps / Daily Max Reps). A value of 100% means every set was a max effort set. 70-85% is typical for hypertrophy training.",
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
                "The average weight used across all sets for a specific exercise in a session.",
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
        sorted_dates = sorted(data.keys())
        for date_str in sorted_dates:
            self.ws_data.write(self.row_cursor, 0, date_str, self.style_date)
            day_data = data[date_str]

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
                        if is_bodyweight:
                            ratio = r / capacity
                        else:
                            ratio = m / capacity
                        intensity_ratios.append(ratio)

            daily_intensity = (
                statistics.mean(intensity_ratios) if intensity_ratios else 0
            )

            self.ws_data.write(self.row_cursor, 1, daily_vol, self.num_styles["Volume"])
            self.ws_data.write(
                self.row_cursor, 2, daily_reps, self.num_styles["Avg Mass"]
            )
            self.ws_data.write(
                self.row_cursor,
                3,
                daily_intensity,
                self.wb.add_format(
                    {"num_format": "0%", "border": 1, "align": "center"}
                ),
            )

            for ex in self.exercises:
                has_data = ex.id in day_data and sum(day_data[ex.id].reps) > 0
                raw_input = day_data.get(ex.id)
                
                for m in self.metrics:
                    col_idx = self.col_map[ex.id][m.name]
                    val = None
                    if m.name.startswith("Std ("):
                        level_map = {
                            "Std (Beg)": "Beginner",
                            "Std (Nov)": "Novice",
                            "Std (Int)": "Intermediate",
                            "Std (Adv)": "Advanced",
                            "Std (Eli)": "Elite"
                        }
                        level = level_map.get(m.name)
                        val = get_exercise_standard(ex.id, date_str, self.bodyweight_log, level)
                        if val == 0:
                            val = None
                    elif has_data:
                        val = m.func(raw_input)
                        
                    if val is not None:
                        self.ws_data.write(
                            self.row_cursor, col_idx, val, self.num_styles[m.name]
                        )
            self.row_cursor += 1

    def write_calculations(self):
        self.ws_calculations.write(0, 0, "Exercise", self.style_header_sub)
        self.ws_calculations.write(0, 1, "Total Volume", self.style_header_sub)

        row = 1
        sorted_vols = sorted(
            self.exercise_volumes.items(), key=lambda x: x[1], reverse=True
        )
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
        self.ws_calculations.write(0, 7, "Weight (kg)", self.style_header_sub)

        measurement_keys = set()
        for data in self.bodyweight_log.values():
            if isinstance(data, dict):
                measurement_keys.update([k for k in data.keys() if k.lower() != "weight"])
                
        m_keys = sorted(list(measurement_keys))
        for i, k in enumerate(m_keys):
            self.ws_calculations.write(0, 8 + i, f"{k.capitalize()} (cm)", self.style_header_sub)
            
        row = 1
        sorted_dates = sorted(self.bodyweight_log.keys())
        self.bw_rows = len(sorted_dates)
        self.measurement_cols = len(m_keys)
        
        for d_str in sorted_dates:
            data = self.bodyweight_log[d_str]
            weight = data if isinstance(data, (int, float)) else data.get("weight", None)
            
            self.ws_calculations.write(row, 6, d_str)
            if weight is not None:
                self.ws_calculations.write(row, 7, weight)
                
            if isinstance(data, dict):
                for i, k in enumerate(m_keys):
                    val = data.get(k)
                    if val is not None:
                        self.ws_calculations.write(row, 8 + i, val)
            row += 1

    def _create_summary_chart(
        self, metric_key: str, chart_title: str, y_axis_label: str, cell_position: str
    ):
        width = CHART_CONFIG["summary"]["width"]
        height = CHART_CONFIG["summary"]["height"]

        chart = self.wb.add_chart({"type": "line"})
        chart.set_title({"name": chart_title})
        chart.set_size({"width": width, "height": height})
        chart.set_x_axis({"name": "Date", "num_font": {"rotation": -45}})
        chart.set_y_axis({"name": y_axis_label, "major_gridlines": {"visible": True}})
        chart.set_legend({"position": "bottom", "font": {"size": 9}})

        chart.show_blanks_as("span")

        for ex in self.exercises:
            if metric_key in self.col_map[ex.id]:
                col_idx = self.col_map[ex.id][metric_key]
                chart.add_series(
                    {
                        "name": ex.display_name,
                        "categories": ["Data_Log", 2, 0, self.row_cursor - 1, 0],
                        "values": [
                            "Data_Log",
                            2,
                            col_idx,
                            self.row_cursor - 1,
                            col_idx,
                        ],
                        "marker": {"type": "circle", "size": 5},
                        "line": {"width": 2},
                    }
                )

        self.ws_charts.insert_chart(cell_position, chart)

    def _create_body_comp_chart(self, cell_position: str) -> int:
        if self.bw_rows == 0:
            return 0
            
        chart = self.wb.add_chart({"type": "line"})
        chart.set_title({"name": "Body Composition Progression"})
        chart.set_size({"width": CHART_CONFIG["summary"]["width"], "height": CHART_CONFIG["summary"]["height"]})
        
        chart.set_x_axis({"name": "Date", "num_font": {"rotation": -45}})
        chart.set_y_axis({"name": "Mass (kg)", "major_gridlines": {"visible": True}})
        chart.set_legend({"position": "bottom", "font": {"size": 9}})
        
        chart.add_series({
            "name": "Bodyweight",
            "categories": ["Calculations", 1, 6, self.bw_rows, 6],
            "values": ["Calculations", 1, 7, self.bw_rows, 7],
            "line": {"color": "#000000", "width": 2.5},
            "marker": {"type": "square", "size": 6}
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
                    "marker": {"type": "circle", "size": 5}
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

        self._create_summary_chart(
            "Est 1RM",
            "Total Strength Overview (Est. 1RM)",
            "1RM (kg)",
            f"{left_col_letter}{cursor_left + 1}",
        )
        cursor_left += self._pixels_to_rows(h_summary) + 2

        self._create_summary_chart(
            "Avg Mass",
            "Average Mass Overview",
            "Mass (kg)",
            f"{left_col_letter}{cursor_left + 1}",
        )
        cursor_left += self._pixels_to_rows(h_summary) + 2

        self._create_summary_chart(
            "Avg Reps",
            "Average Reps Overview",
            "Reps",
            f"{left_col_letter}{cursor_left + 1}",
        )
        cursor_left += self._pixels_to_rows(h_summary) + 2

        vol_chart = self.wb.add_chart({"type": "line"})
        vol_chart.set_title({"name": "Daily Total Volume"})
        vol_chart.set_size({"width": w_summary, "height": h_summary})
        vol_chart.set_x_axis({"name": "Date", "num_font": {"rotation": -45}})
        vol_chart.set_y_axis(
            {"name": "Volume (kg)", "major_gridlines": {"visible": True}}
        )
        vol_chart.set_legend({"position": "bottom", "font": {"size": 9}})
        vol_chart.show_blanks_as("span")

        vol_chart.add_series(
            {
                "name": "Daily Volume",
                "categories": ["Data_Log", 2, 0, self.row_cursor - 1, 0],  
                "values": [
                    "Data_Log",
                    2,
                    1,
                    self.row_cursor - 1,
                    1,
                ],  
                "line": {"color": "#4F81BD", "width": 2.25},
                "marker": {"type": "circle", "size": 5},
            }
        )
        self.ws_charts.insert_chart(f"{left_col_letter}{cursor_left + 1}", vol_chart)

        vol_chart_row = cursor_left
        cursor_left += self._pixels_to_rows(h_summary) + 2

        pie_chart = self.wb.add_chart({"type": "pie"})
        pie_chart.set_title({"name": "Total Volume Distribution"})
        pie_chart.set_size({"width": w_pie, "height": h_pie})

        if self.calc_vol_rows > 0:
            pie_chart.add_series(
                {
                    "name": "Volume",
                    "categories": ["Calculations", 1, 0, self.calc_vol_rows, 0],
                    "values": ["Calculations", 1, 1, self.calc_vol_rows, 1],
                    "data_labels": {"percentage": True},
                }
            )
        self.ws_charts.insert_chart(f"{right_col_letter}{cursor_right + 1}", pie_chart)
        cursor_right += self._pixels_to_rows(h_pie) + 2

        col_chart = self.wb.add_chart({"type": "column"})
        col_chart.set_title({"name": "Weekly Consistency (Sessions)"})
        col_chart.set_size({"width": w_col, "height": h_col})
        col_chart.set_y_axis(
            {"name": "Sessions", "major_gridlines": {"visible": True}, "min": 0}
        )
        col_chart.set_legend({"none": True})

        if self.calc_week_rows > 0:
            col_chart.add_series(
                {
                    "name": "Sessions",
                    "categories": ["Calculations", 1, 3, self.calc_week_rows, 3],
                    "values": ["Calculations", 1, 4, self.calc_week_rows, 4],
                    "fill": {"color": "#9BBB59"},
                }
            )
        self.ws_charts.insert_chart(f"{right_col_letter}{cursor_right + 1}", col_chart)
        cursor_right += self._pixels_to_rows(h_col) + 2

        target_row = max(cursor_right, vol_chart_row)

        int_chart = self.wb.add_chart({"type": "line"})
        int_chart.set_title({"name": "Daily Relative Intensity (Avg Effort)"})
        int_chart.set_size({"width": w_summary, "height": h_summary})
        int_chart.set_x_axis({"name": "Date", "num_font": {"rotation": -45}})
        int_chart.set_y_axis(
            {
                "name": "Intensity (%)",
                "major_gridlines": {"visible": True},
                "min": 0,
                "max": 1.0,  
            }
        )
        int_chart.set_legend({"position": "bottom", "font": {"size": 9}})
        int_chart.show_blanks_as("span")

        int_chart.add_series(
            {
                "name": "Daily Intensity",
                "categories": ["Data_Log", 2, 0, self.row_cursor - 1, 0],  
                "values": [
                    "Data_Log",
                    2,
                    3,
                    self.row_cursor - 1,
                    3,
                ],  
                "line": {"color": "#C0504D", "width": 2.25},
                "marker": {"type": "diamond", "size": 5},
            }
        )
        self.ws_charts.insert_chart(f"{right_col_letter}{target_row + 1}", int_chart)

        max_cursor = max(cursor_left, cursor_right)
        max_cursor = max(max_cursor, target_row + self._pixels_to_rows(h_summary) + 1)

        chart_pos_y = max_cursor + 5

        for ex in self.exercises:
            is_bodyweight = True
            for d_data in self.user_data.values():
                if ex.id in d_data:
                    log_entry = d_data[ex.id]
                    if log_entry.mass and max(log_entry.mass) > 0:
                        is_bodyweight = False
                        break

            series_2_name = "Max Reps" if is_bodyweight else "Est 1RM"
            y_axis_name = "Max Reps" if is_bodyweight else "Mass (kg)"

            mass_chart = self.wb.add_chart({"type": "line"})
            mass_chart.show_blanks_as("span")
            mass_chart.set_x_axis({"name": "Date", "num_font": {"rotation": -45}})
            mass_chart.set_legend({"position": "bottom", "font": {"size": 9}})

            col_mass = self.col_map[ex.id]["Avg Mass"]
            col_mass_err = self.col_map[ex.id]["Stdev Mass"]
            col_1rm = self.col_map[ex.id]["Est 1RM"]

            start_cell = xlsxwriter.utility.xl_rowcol_to_cell(
                2, col_mass_err, row_abs=True, col_abs=True
            )
            end_cell = xlsxwriter.utility.xl_rowcol_to_cell(
                self.row_cursor - 1, col_mass_err, row_abs=True, col_abs=True
            )
            mass_err_ref = f"='Data_Log'!{start_cell}:{end_cell}"

            mass_chart.add_series(
                {
                    "name": "Avg Mass",
                    "categories": ["Data_Log", 2, 0, self.row_cursor - 1, 0],
                    "values": ["Data_Log", 2, col_mass, self.row_cursor - 1, col_mass],
                    "line": {"color": "#203764", "width": 2.25},
                    "marker": {
                        "type": "circle",
                        "size": 5,
                        "fill": {"color": "white"},
                        "border": {"color": "#203764"},
                    },
                    "y_error_bars": {
                        "type": "custom",
                        "plus_values": mass_err_ref,  
                        "minus_values": mass_err_ref,  
                        "direction": "both",
                        "end_style": "end",
                        "line": {"color": "#B4C6E7", "width": 1.5},
                    },
                }
            )

            mass_chart.add_series(
                {
                    "name": series_2_name,
                    "categories": ["Data_Log", 2, 0, self.row_cursor - 1, 0],
                    "values": ["Data_Log", 2, col_1rm, self.row_cursor - 1, col_1rm],
                    "line": {"color": "#C0504D", "width": 1.5, "dash_type": "dash"},
                    "marker": {"type": "none"},
                }
            )

            levels = [
                ("Std (Beg)", "Beg", "#FFFF00"), 
                ("Std (Nov)", "Nov", "#FFC000"), 
                ("Std (Int)", "Int", "#00B050"), 
                ("Std (Adv)", "Adv", "#0070C0"), 
                ("Std (Eli)", "Eli", "#7030A0")  
            ]
            
            for m_key, m_label, m_color in levels:
                if m_key in self.col_map[ex.id]:
                    col_std = self.col_map[ex.id][m_key]
                    mass_chart.add_series(
                        {
                            "name": m_label,
                            "categories": ["Data_Log", 2, 0, self.row_cursor - 1, 0],
                            "values": ["Data_Log", 2, col_std, self.row_cursor - 1, col_std],
                            "line": {"color": m_color, "width": 1.25}, 
                            "marker": {"type": "none"},
                        }
                    )

            mass_chart.set_title(
                {"name": f"{ex.display_name} - Progress ({y_axis_name})"}
            )
            mass_chart.set_size({"width": w_indiv, "height": h_indiv})

            all_mass_vals = []
            
            for d_data in self.user_data.values():
                if ex.id in d_data:
                    log = d_data[ex.id]
                    if log.mass and sum(log.mass) > 0:
                        m_mean = statistics.mean(log.mass)
                        m_stdev = statistics.stdev(log.mass) if len(log.mass) > 1 else 0
                        all_mass_vals.append(m_mean - m_stdev)
                        all_mass_vals.append(m_mean + m_stdev)



            if all_mass_vals:
                curr_max = max(all_mass_vals)
                
                # Include the first standard level that is above the curr_max to provide a "target"
                next_std = None
                level_map_rev = {
                    "Beg": "Beginner",
                    "Nov": "Novice",
                    "Int": "Intermediate",
                    "Adv": "Advanced",
                    "Eli": "Elite"
                }
                for _, m_label, _ in levels:
                    std_level = level_map_rev.get(m_label)
                    # Check the standard at the latest date
                    latest_date = sorted(self.user_data.keys())[-1]
                    val = get_exercise_standard(ex.id, latest_date, self.bodyweight_log, std_level)
                    if val > curr_max:
                        next_std = val
                        break
                
                if next_std:
                    all_mass_vals.append(next_std)
                
                # Re-calculate with the target included
                y_min = max(0, int(min(all_mass_vals) * 0.95))
                y_max = int(max(all_mass_vals) * 1.05)
                
                # Ensure at least 15 units of range for better perspective
                if y_max - y_min < 15:
                    center = (y_min + y_max) / 2
                    y_min = max(0, int(center - 7.5))
                    y_max = int(center + 7.5)
            else:
                y_min = 0
                y_max = None

            mass_chart.set_y_axis(
                {
                    "name": y_axis_name,
                    "major_gridlines": {"visible": True},
                    "min": y_min,
                    "max": y_max,
                }
            )

            self.ws_charts.insert_chart(f"{left_col_letter}{chart_pos_y}", mass_chart)

            col_reps = self.col_map[ex.id]["Avg Reps"]
            col_reps_err = self.col_map[ex.id]["Stdev Reps"]

            reps_col_idx = 1 + self._pixels_to_cols(w_indiv) + 1
            reps_col_letter = xlsxwriter.utility.xl_col_to_name(reps_col_idx)

            start_cell_reps = xlsxwriter.utility.xl_rowcol_to_cell(
                2, col_reps_err, row_abs=True, col_abs=True
            )
            end_cell_reps = xlsxwriter.utility.xl_rowcol_to_cell(
                self.row_cursor - 1, col_reps_err, row_abs=True, col_abs=True
            )
            reps_err_ref = f"='Data_Log'!{start_cell_reps}:{end_cell_reps}"

            reps_chart = self.wb.add_chart({"type": "line"})
            reps_chart.show_blanks_as("span")
            reps_chart.set_x_axis({"name": "Date", "num_font": {"rotation": -45}})
            reps_chart.set_legend({"position": "bottom", "font": {"size": 9}})

            reps_chart.add_series(
                {
                    "name": "Avg Reps",
                    "categories": ["Data_Log", 2, 0, self.row_cursor - 1, 0],
                    "values": ["Data_Log", 2, col_reps, self.row_cursor - 1, col_reps],
                    "line": {"color": "#8064A2", "width": 2},
                    "marker": {
                        "type": "diamond",
                        "size": 5,
                        "fill": {"color": "white"},
                        "border": {"color": "#8064A2"},
                    },
                    "y_error_bars": {
                        "type": "custom",
                        "plus_values": reps_err_ref,
                        "minus_values": reps_err_ref,
                        "direction": "both",
                        "end_style": "end",
                        "line": {"color": "#CCC0DA", "width": 1.5},
                    },
                }
            )

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

            reps_chart.set_y_axis(
                {
                    "name": "Reps",
                    "major_gridlines": {"visible": True},
                    "min": y_min_reps,
                }
            )

            self.ws_charts.insert_chart(f"{reps_col_letter}{chart_pos_y}", reps_chart)

            chart_pos_y += self._pixels_to_rows(h_indiv) + 2

    def save(self):
        try:
            self.wb.close()
            print(f"Log generated: {self.output_path}")
        except Exception as e:
            print(f"Error saving: {e}")
