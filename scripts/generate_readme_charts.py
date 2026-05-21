import os
import sys
import json
import statistics
import math
import argparse
from datetime import datetime, timedelta

# Force Matplotlib to run in headless mode
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.colors as mcolors

# Add project root to python path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.standards import get_exercise_standard
from core.models import Log

# Setup output media directory
MEDIA_DIR = os.path.join(PROJECT_ROOT, "media")
os.makedirs(MEDIA_DIR, exist_ok=True)

# Central styling palette
OFFICE_COLORS = [
    "#4F81BD", "#C0504D", "#9BBB59", "#8064A2", "#4BACC6", "#F79646",
    "#3C679A", "#9D3D3A", "#7D9844", "#664E83", "#388CA2", "#CB7833"
]

MILESTONE_INFO = [
    ("Bg (Unt)", "Untrained", "#E8E8E8", 0.05),
    ("Bg (Beg)", "Beginner", "#0d0887", 0.1),
    ("Bg (Nov)", "Novice", "#7e03a8", 0.1),
    ("Bg (Int)", "Intermediate", "#cb4679", 0.1),
    ("Bg (Adv)", "Advanced", "#f89441", 0.1),
    ("Bg (Eli)", "Elite", "#f0f921", 0.1)
]

LEVELS_ORDER = ["Beginner", "Novice", "Intermediate", "Advanced", "Elite"]

# Global placeholders for the selected data source
USER_DATA = {}
BODYMASS_LOG = {}
global_start_date = None
global_end_date = None
min_date = None
max_date = None

# Configurations
user_sex = "male"
show_pr = True
show_standards = True
show_milestones = True

def generate_mock_data():
    """Generates deterministic, high-quality, realistic gym tracking dummy data."""
    start_date = datetime(2026, 1, 5)
    end_date = datetime(2026, 5, 15)
    
    bodymass_log = {}
    user_data = {}
    
    curr = start_date
    while curr <= end_date:
        date_str = curr.strftime("%Y-%m-%d")
        days_elapsed = (curr - start_date).days
        total_days = (end_date - start_date).days
        fraction = days_elapsed / total_days if total_days > 0 else 0.0
        
        # Base weight cut from 85.0kg down to 79.5kg
        base_weight = 85.0 - 5.5 * fraction
        is_measurement_day = (curr.weekday() == 6)  # Sunday
        
        if is_measurement_day:
            bodymass_log[date_str] = {
                "mass": round(base_weight + 0.2 * math.sin(days_elapsed / 7.0), 1),
                "chest": round(106.0 - 2.0 * fraction, 1),
                "waist": round(92.0 - 8.0 * fraction, 1),
                "ass": round(102.0 - 4.0 * fraction, 1),
                "arms": round(38.5 - 0.3 * fraction, 1),
                "legs": round(59.0 - 1.5 * fraction, 1)
            }
        else:
            if curr.weekday() in (2, 4):  # Wed, Fri daily weight check-ins
                bodymass_log[date_str] = round(base_weight + 0.3 * math.cos(days_elapsed / 3.0), 1)
                
        curr += timedelta(days=1)
        
    # Generate workouts (3x/week split: Mon, Wed, Fri)
    curr = start_date
    session_counter = 0
    while curr <= end_date:
        date_str = curr.strftime("%Y-%m-%d")
        weekday = curr.weekday()
        days_elapsed = (curr - start_date).days
        total_days = (end_date - start_date).days
        fraction = days_elapsed / total_days if total_days > 0 else 0.0
        
        if weekday in (0, 2, 4):
            day_data = {}
            day_data["day"] = (session_counter % 3) + 1
            session_counter += 1
            
            def make_log(base_mass, end_mass, reps_pattern, is_bw=False):
                current_mass = base_mass + (end_mass - base_mass) * fraction
                rounded_mass = round(current_mass / 2.5) * 2.5
                masses = [0.0 if is_bw else rounded_mass] * len(reps_pattern)
                reps = list(reps_pattern)
                # Introduce slight fatigue set-to-set variance for error bar realism
                if len(reps) > 1 and fraction < 0.8:
                    fatigue = int((days_elapsed % 3) == 0)
                    if fatigue > 0:
                        reps[-1] = max(1, reps[-1] - fatigue)
                return Log(reps, masses)

            # Mon: Day 1
            if weekday == 0:
                day_data['squat'] = make_log(65.0, 95.0, [5, 5, 5])
                day_data['bench-press'] = make_log(50.0, 72.5, [5, 5, 5])
                day_data['lat-pulldown'] = make_log(40.0, 60.0, [8, 8, 8])
                day_data['dumbbell-curl'] = make_log(12.5, 17.5, [10, 10, 10])
                
            # Wed: Day 2
            elif weekday == 2:
                day_data['deadlift'] = make_log(80.0, 125.0, [5])
                day_data['shoulder-press'] = make_log(30.0, 45.0, [5, 5, 5])
                pullups_reps = [int(5 + 5 * fraction), int(4 + 5 * fraction), int(3 + 5 * fraction)]
                day_data['pull-ups'] = make_log(0.0, 0.0, pullups_reps, is_bw=True)
                crunches_reps = [int(12 + 10 * fraction), int(12 + 8 * fraction), int(10 + 8 * fraction)]
                day_data['crunches'] = make_log(0.0, 0.0, crunches_reps, is_bw=True)
                
            # Fri: Day 3
            elif weekday == 4:
                day_data['squat'] = make_log(65.0, 95.0, [5, 5, 5])
                day_data['dumbbell-bench-press'] = make_log(16.0, 24.0, [8, 8, 8])
                day_data['barbell-curl'] = make_log(25.0, 35.0, [8, 8, 8])
                day_data['dumbbell-shoulder-press'] = make_log(12.5, 17.5, [8, 8, 8])
                day_data['incline-bench-press'] = make_log(40.0, 57.5, [6, 6, 6])
                
            user_data[date_str] = day_data
            
        curr += timedelta(days=1)
        
    return user_data, bodymass_log

def initialize_data_source(use_real):
    global USER_DATA, BODYMASS_LOG, min_date, max_date, global_start_date, global_end_date
    global user_sex, show_pr, show_standards, show_milestones
    
    if use_real:
        print("Using real data from user's sessions.py...")
        PROFILES_FILE = os.path.join(PROJECT_ROOT, "profiles.json")
        sessions_dir = PROJECT_ROOT
        if os.path.exists(PROFILES_FILE):
            try:
                with open(PROFILES_FILE, "r", encoding="utf-8") as f:
                    profiles_data = json.load(f)
                    idx = profiles_data.get("active_profile_index", 0)
                    profiles = profiles_data.get("profiles", [])
                    if 0 <= idx < len(profiles):
                        active_profile = profiles[idx]
                        sessions_dir = active_profile.get("sessions_dir", PROJECT_ROOT)
                        user_sex = active_profile.get("sex", "male")
                        show_pr = active_profile.get("show_pr", True)
                        show_standards = active_profile.get("show_standards", True)
                        show_milestones = active_profile.get("show_milestones", True)
            except Exception as e:
                print(f"Warning: could not load profiles.json: {e}")

        if sessions_dir not in sys.path:
            sys.path.insert(0, sessions_dir)

        try:
            import sessions
            USER_DATA = sessions.USER_DATA
            BODYMASS_LOG = sessions.BODYMASS_LOG
        except ImportError:
            print(f"CRITICAL ERROR: Could not import 'sessions.py' from {sessions_dir}")
            sys.exit(1)
    else:
        print("Using generated dummy/mock data for README charts (sandbox/privacy mode)...")
        user_sex = "male"
        show_pr = True
        show_standards = True
        show_milestones = True
        USER_DATA, BODYMASS_LOG = generate_mock_data()

    if not USER_DATA:
        print("CRITICAL ERROR: USER_DATA is empty. Cannot generate charts.")
        sys.exit(1)

    sorted_dates = sorted(USER_DATA.keys())
    min_date = datetime.strptime(sorted_dates[0], "%Y-%m-%d")
    max_date = datetime.strptime(sorted_dates[-1], "%Y-%m-%d")
    global_start_date = min_date - timedelta(days=2)
    global_end_date = max_date + timedelta(days=2)

def get_body_mass_on_date(date_str):
    """Finds body mass for a given date in BODYMASS_LOG, falling back to the last available record."""
    dates = sorted(BODYMASS_LOG.keys())
    if not dates:
        return 0.0
    applicable_date = dates[0]
    for d in dates:
        if d <= date_str:
            applicable_date = d
        else:
            break
    entry = BODYMASS_LOG[applicable_date]
    if isinstance(entry, (int, float)):
        return float(entry)
    return float(entry.get("mass", entry.get("weight", 0.0)))

def calc_brzycki(log_entry):
    """Calculates Estimated 1RM using the Brzycki formula, or returns max reps for bodyweight."""
    if not log_entry.reps:
        return 0.0
    if log_entry.mass and max(log_entry.mass) == 0:
        valid_reps = [r for r in log_entry.reps if r > 0]
        return max(valid_reps) if valid_reps else 0.0
    one_rms = [
        m * (36 / (37 - r)) if r < 37 else m
        for r, m in zip(log_entry.reps, log_entry.mass)
        if r > 0
    ]
    return max(one_rms) if one_rms else 0.0

def apply_common_styling(ax, title, y_label):
    """Applies modern clean typography and grids."""
    ax.set_title(title, fontsize=12, fontweight='bold', pad=10)
    ax.set_ylabel(y_label, fontsize=10)
    ax.grid(True, linestyle='--', alpha=0.5, color='#D9D9D9')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#868686')
    ax.spines['bottom'].set_color('#868686')
    ax.tick_params(axis='both', colors='#333333', labelsize=9)

def format_date_axis(ax):
    """Formats date axis with -45 degree labels."""
    ax.set_xlim(global_start_date, global_end_date)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    plt.setp(ax.get_xticklabels(), rotation=-45, ha='left')

# Chart 1: overall_strength_overview.svg
def generate_overall_strength_overview():
    print("Generating overall_strength_overview.svg...")
    ex_mapping = {
        'lat-pulldown': 'Pull-downs',
        'squat': 'Squat',
        'shoulder-press': 'Overhead Press (Barbell)',
        'incline-bench-press': 'Bench press inclined (Barbell)',
        'bench-press': 'Bench Press (Barbell)',
        'dumbbell-bench-press': 'Bench Press (Dumbbell)',
        'pull-ups': 'Pull-ups',
        'deadlift': 'Deadlift',
        'barbell-curl': 'Bicep Curls (Barbell)',
        'dumbbell-curl': 'Bicep Curls (Dumbbell)',
        'dumbbell-shoulder-press': 'Overhead Press (Dumbbell)',
        'crunches': 'Abdominals'
    }

    fig, ax = plt.subplots(figsize=(10, 5), dpi=100)
    
    for idx, (ex_id, display_name) in enumerate(ex_mapping.items()):
        dates_list = []
        vals_list = []
        for date_str, day_data in USER_DATA.items():
            if ex_id in day_data:
                log = day_data[ex_id]
                if isinstance(log, Log) and log.reps:
                    dt = datetime.strptime(date_str, "%Y-%m-%d")
                    dates_list.append(dt)
                    vals_list.append(calc_brzycki(log))
        
        if dates_list:
            combined = sorted(zip(dates_list, vals_list))
            x_vals = [c[0] for c in combined]
            y_vals = [c[1] for c in combined]
            
            color = OFFICE_COLORS[idx % len(OFFICE_COLORS)]
            ax.plot(x_vals, y_vals, label=display_name, color=color, linewidth=1.5, marker='o', markersize=4)

    apply_common_styling(ax, "Overall Strength Overview (Est. 1RM or Reps)", "Est. 1RM (kg) / Max Reps")
    format_date_axis(ax)
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.2), ncol=3, frameon=False, fontsize=8)
    
    output_path = os.path.join(MEDIA_DIR, "overall_strength_overview.svg")
    fig.savefig(output_path, format='svg', bbox_inches='tight')
    plt.close(fig)
    print(f"Saved: {output_path}")

# Chart 2: body_composition_trends.svg
def generate_body_composition_trends():
    print("Generating body_composition_trends.svg...")
    dates_list = []
    mass_list = []
    chest_list = []
    waist_list = []
    ass_list = []
    arms_list = []
    legs_list = []

    for date_str in sorted(BODYMASS_LOG.keys()):
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        entry = BODYMASS_LOG[date_str]
        
        mass_val = None
        chest_val = None
        waist_val = None
        ass_val = None
        arms_val = None
        legs_val = None
        
        if isinstance(entry, (int, float)):
            mass_val = float(entry)
        elif isinstance(entry, dict):
            mass_val = entry.get("mass", entry.get("weight"))
            chest_val = entry.get("chest")
            waist_val = entry.get("waist")
            ass_val = entry.get("ass")
            arms_val = entry.get("arms")
            legs_val = entry.get("legs")
            
        dates_list.append(dt)
        mass_list.append(float(mass_val) if mass_val is not None else None)
        chest_list.append(float(chest_val) if chest_val is not None else None)
        waist_list.append(float(waist_val) if waist_val is not None else None)
        ass_list.append(float(ass_val) if ass_val is not None else None)
        arms_list.append(float(arms_val) if arms_val is not None else None)
        legs_list.append(float(legs_val) if legs_val is not None else None)

    fig, ax1 = plt.subplots(figsize=(10, 5), dpi=100)
    ax2 = ax1.twinx()

    def filter_series(x_vals, y_vals):
        res = [(x, y) for x, y in zip(x_vals, y_vals) if y is not None]
        return zip(*res) if res else ([], [])

    mass_x, mass_y = filter_series(dates_list, mass_list)
    if mass_x:
        ax1.plot(mass_x, mass_y, label="Body Mass", color="#000000", linewidth=2.5, marker='o', markersize=5)
    
    measurements = [
        (chest_list, "Chest", "#4F81BD"),
        (waist_list, "Waist", "#C0504D"),
        (ass_list, "Glutes/Ass", "#9BBB59"),
        (arms_list, "Arms", "#8064A2"),
        (legs_list, "Legs", "#4BACC6")
    ]
    
    for y_list, label, color in measurements:
        mx, my = filter_series(dates_list, y_list)
        if mx:
            ax2.plot(mx, my, label=label, color=color, linewidth=2.0, linestyle='--')

    apply_common_styling(ax1, "Body Composition Trends", "Body Mass (kg)")
    ax2.set_ylabel("Measurements (cm)", fontsize=10)
    ax2.tick_params(axis='y', colors='#333333', labelsize=9)
    ax2.spines['top'].set_visible(False)
    ax2.spines['left'].set_visible(False)
    ax2.spines['right'].set_color('#868686')
    
    format_date_axis(ax1)
    
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper center', bbox_to_anchor=(0.5, -0.2), ncol=6, frameon=False, fontsize=8)

    output_path = os.path.join(MEDIA_DIR, "body_composition_trends.svg")
    fig.savefig(output_path, format='svg', bbox_inches='tight')
    plt.close(fig)
    print(f"Saved: {output_path}")

# Chart 3: weekly_training_consistency.svg
def generate_weekly_training_consistency():
    print("Generating weekly_training_consistency.svg...")
    weekly_sessions = {}
    for date_str in sorted(USER_DATA.keys()):
        day_data = USER_DATA[date_str]
        if "day" in day_data:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            year, week_num, _ = dt.isocalendar()
            week_key = f"{year}-W{week_num:02d}"
            weekly_sessions[week_key] = weekly_sessions.get(week_key, 0) + 1

    all_week_keys = []
    curr = min_date
    while curr <= max_date:
        y, w, _ = curr.isocalendar()
        week_key = f"{y}-W{w:02d}"
        if week_key not in all_week_keys:
            all_week_keys.append(week_key)
        curr += timedelta(days=7)
    
    y_last, w_last, _ = max_date.isocalendar()
    last_week_key = f"{y_last}-W{w_last:02d}"
    if last_week_key not in all_week_keys:
        all_week_keys.append(last_week_key)

    counts = [weekly_sessions.get(wk, 0) for wk in all_week_keys]
    display_labels = [wk.split("-")[1] for wk in all_week_keys]

    fig, ax = plt.subplots(figsize=(10, 5), dpi=100)
    ax.bar(display_labels, counts, color="#9BBB59", width=0.6)
    
    apply_common_styling(ax, "Weekly Training Consistency", "Workouts per Week")
    ax.set_xlabel("Calendar Week", fontsize=10)
    plt.setp(ax.get_xticklabels(), rotation=-45, ha='left')
    ax.set_ylim(0, max(counts) + 1 if counts else 5)
    
    output_path = os.path.join(MEDIA_DIR, "weekly_training_consistency.svg")
    fig.savefig(output_path, format='svg', bbox_inches='tight')
    plt.close(fig)
    print(f"Saved: {output_path}")

# Charts 4-7: Individual progress charts
def generate_individual_progress(ex_id, display_name, filename):
    print(f"Generating {filename} for {display_name}...")
    
    dates_list = []
    avg_mass_list = []
    stdev_mass_list = []
    est_1rm_list = []
    
    for date_str, day_data in USER_DATA.items():
        if ex_id in day_data:
            log = day_data[ex_id]
            if isinstance(log, Log) and log.reps:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                dates_list.append(dt)
                avg_mass_list.append(statistics.mean(log.mass) if log.mass else 0.0)
                stdev_mass_list.append(statistics.stdev(log.mass) if len(log.mass) > 1 else 0.0)
                est_1rm_list.append(calc_brzycki(log))

    if not dates_list:
        print(f"No data for {ex_id}, skipping progress chart.")
        return

    is_bodyweight = True
    for date_str, day_data in USER_DATA.items():
        if ex_id in day_data:
            log = day_data[ex_id]
            if log.mass and max(log.mass) > 0:
                is_bodyweight = False
                break

    y_axis_name = "Max Reps" if is_bodyweight else "Mass (kg)"
    series_2_name = "Max Reps" if is_bodyweight else "Est 1RM"

    # Precompute highest achieved level across ALL dates
    highest_lvl_idx = -1
    for date_str, day_data in USER_DATA.items():
        if ex_id in day_data:
            log = day_data[ex_id]
            if isinstance(log, Log) and log.reps:
                cap = calc_brzycki(log)
                lv = -1
                for lvl_idx, lvl_name in enumerate(LEVELS_ORDER):
                    std_val = get_exercise_standard(ex_id, date_str, BODYMASS_LOG, lvl_name, sex=user_sex)
                    if std_val > 0 and cap >= std_val:
                        lv = lvl_idx
                if lv > highest_lvl_idx:
                    highest_lvl_idx = lv

    bg_key, bg_label, bg_color, bg_alpha = MILESTONE_INFO[highest_lvl_idx + 1]

    # Bounds calculation
    all_bounds_vals = []
    for am, sd, rm in zip(avg_mass_list, stdev_mass_list, est_1rm_list):
        all_bounds_vals.append(am - sd)
        all_bounds_vals.append(am + sd)
        if rm > 0:
            all_bounds_vals.append(rm)
            
    min_val = min(all_bounds_vals)
    max_val = max(all_bounds_vals)
    y_min = max(0, int(min_val * 0.9))
    y_max = int(max_val * 1.15)
    
    last_date_str = sorted(USER_DATA.keys())[-1]
    for lvl_name in LEVELS_ORDER:
        std_val = get_exercise_standard(ex_id, last_date_str, BODYMASS_LOG, lvl_name, sex=user_sex)
        if std_val > max_val:
            y_max = max(y_max, int(std_val * 1.10))
            break
            
    if y_max <= y_min:
        y_max = y_min + 10

    # Calculate standards continuously
    full_dates = []
    std_lines = {lvl: [] for lvl in LEVELS_ORDER}
    
    curr = min_date
    while curr <= max_date:
        full_dates.append(curr)
        curr_str = curr.strftime("%Y-%m-%d")
        for lvl_name in LEVELS_ORDER:
            std_val = get_exercise_standard(ex_id, curr_str, BODYMASS_LOG, lvl_name, sex=user_sex)
            std_lines[lvl_name].append(std_val if std_val > 0 else None)
        curr += timedelta(days=1)

    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=100)

    if show_milestones:
        ax.set_facecolor(mcolors.to_rgba(bg_color, alpha=bg_alpha))

    if show_standards:
        for lvl_name in LEVELS_ORDER:
            # Filter None to plot continuous segments
            paired = [(fd, val) for fd, val in zip(full_dates, std_lines[lvl_name]) if val is not None]
            if paired:
                std_x, std_y = zip(*paired)
                lvl_color = [info[2] for info in MILESTONE_INFO if info[1] == lvl_name][0]
                ax.plot(std_x, std_y, label=lvl_name, color=lvl_color, linewidth=1.25)

    combined_data = sorted(zip(dates_list, avg_mass_list, stdev_mass_list, est_1rm_list))
    plt_dates = [c[0] for c in combined_data]
    plt_avg = [c[1] for c in combined_data]
    plt_sd = [c[2] for c in combined_data]
    plt_1rm = [c[3] for c in combined_data]

    # Primary series: Avg Mass
    ax.errorbar(plt_dates, plt_avg, yerr=plt_sd, fmt='o', color='#203764', ecolor='#B4C6E7', 
                elinewidth=1.5, capsize=3, mfc='#203764', mec='#203764', ms=5, 
                label="Avg Mass" if not is_bodyweight else "Avg Mass (0)")
    ax.plot(plt_dates, plt_avg, color='#203764', linewidth=2.25)

    # Secondary series: Est 1RM / Max Reps
    if show_pr:
        ax.plot(plt_dates, plt_1rm, label=series_2_name, color='#C0504D', linewidth=1.5, linestyle='--')

    title = f"{display_name} - Progress ({y_axis_name})"
    apply_common_styling(ax, title, y_axis_name)
    ax.set_ylim(y_min, y_max)
    format_date_axis(ax)
    
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.2), ncol=4, frameon=False, fontsize=8)

    output_path = os.path.join(MEDIA_DIR, filename)
    fig.savefig(output_path, format='svg', bbox_inches='tight')
    plt.close(fig)
    print(f"Saved: {output_path}")

# Charts 8-10: Individual reps evolution charts
def generate_individual_reps_evolution(ex_id, display_name, filename):
    print(f"Generating {filename} for {display_name}...")
    
    dates_list = []
    avg_reps_list = []
    stdev_reps_list = []
    
    for date_str, day_data in USER_DATA.items():
        if ex_id in day_data:
            log = day_data[ex_id]
            if isinstance(log, Log) and log.reps:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                dates_list.append(dt)
                avg_reps_list.append(statistics.mean(log.reps))
                stdev_reps_list.append(statistics.stdev(log.reps) if len(log.reps) > 1 else 0.0)

    if not dates_list:
        print(f"No data for {ex_id}, skipping reps consistency chart.")
        return

    all_reps_vals = [ar - sd for ar, sd in zip(avg_reps_list, stdev_reps_list)]
    min_reps = min(all_reps_vals)
    y_min_reps = max(0, int(min_reps * 0.8))

    combined_data = sorted(zip(dates_list, avg_reps_list, stdev_reps_list))
    plt_dates = [c[0] for c in combined_data]
    plt_avg = [c[1] for c in combined_data]
    plt_sd = [c[2] for c in combined_data]

    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=100)

    ax.errorbar(plt_dates, plt_avg, yerr=plt_sd, fmt='o', color='#8064A2', ecolor='#CCC0DA', 
                elinewidth=1.5, capsize=3, mfc='#8064A2', mec='#8064A2', ms=5, 
                label="Avg Reps")
    ax.plot(plt_dates, plt_avg, color='#8064A2', linewidth=2.0)

    title = f"{display_name} - Reps Consistency"
    apply_common_styling(ax, title, "Reps")
    ax.set_ylim(y_min_reps, None)
    format_date_axis(ax)
    
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.2), ncol=1, frameon=False, fontsize=8)

    output_path = os.path.join(MEDIA_DIR, filename)
    fig.savefig(output_path, format='svg', bbox_inches='tight')
    plt.close(fig)
    print(f"Saved: {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Generate SVG charts for README/docs.")
    parser.add_argument("--real", action="store_true", help="Use real data from sessions.py instead of dummy data.")
    args = parser.parse_args()
    
    initialize_data_source(args.real)
    
    # Generate all charts
    generate_overall_strength_overview()
    generate_body_composition_trends()
    generate_weekly_training_consistency()
    
    generate_individual_progress("bench-press", "Bench Press", "bench_press_max_mass.svg")
    generate_individual_progress("squat", "Squat", "squat_max_mass.svg")
    generate_individual_progress("pull-ups", "Pull-ups", "pullups_max_reps.svg")
    generate_individual_progress("crunches", "Abdominals", "abdominals_progress.svg")
    
    generate_individual_reps_evolution("bench-press", "Bench Press", "bench_press_reps_evolution.svg")
    generate_individual_reps_evolution("squat", "Squat", "squat_reps_evolution.svg")
    generate_individual_reps_evolution("pull-ups", "Pull-ups", "pullups_reps_evolution.svg")
    
    print("All README charts generated successfully!")

if __name__ == "__main__":
    main()
