# Iron Log - Technical Documentation

This document contains developer execution guides, utility script references, sheet structure layouts, and calculation formulas for **Iron Log**.

---

## Developer Execution (Running from Source)

### 0. Setup
Install Python dependencies inside your environment:
```bash
pip install -r requirements.txt
```

### 1. Generation & Dashboard
Launch the Iron Log dashboard:
```bash
python main.py
```

<img src="../media/ui_user_menu.png" width="700" alt="GUI Dashboard Overview">

The dashboard provides a modern GUI to:
* **🚀 Generate Excel Log**: Processes `sessions.py`, calculates standards, layers in the benchmarks, and launches the Excel report.
* **📅 Plan Next Cycle**: Analyzes recent history to write the upcoming training progression block to your log.
* **⚡ Run Scraper**: Refreshes strength standard databases.
* **📚 Exercise Library**: Instant access to copy supported exercise IDs.

### 2. Session Logging Format
Data is maintained in `sessions.py` using Python dictionaries.

**Tracking bodymass and measurements:**
```python
BODYMASS_LOG = {
    "2026-03-01": 80.5, # Weight only
    "2026-03-08": {"mass": 81.0, "biceps": 38.0, "waist": 85.5}, # Full composition metrics
}
```

**Tracking training sessions:**
```python
USER_DATA = {
    "2026-03-12": { 
        "day": 1,                          # Cycle day/split metadata
        SQ: Log([5, 5, 5], [80, 80, 80]),  # 3 sets of squat: 80kg x 5 reps
        PU: Log([10, 8, 6], [0, 0, 0]),    # Non-uniform reps for bodyweight
    },
}
```

---

## Workbook Sheet Structure

* **Progress_Charts**: Visual performance trends layered with personal milestone backgrounds and benchmark standard tiers.
* **Data_Log**: A comprehensive chronological history of daily volume, relative intensity, and set consistency (Stdev).
* **Personal_Records**: A tracking log of all-time heaviest lifts with their corresponding achieved standard tier colored dynamically.
* **User_Profile**: Biographic profile details, age, sex, and options.
* **Definitions & Calculations**: Technical sheets mapping the formulas and color schemes.

---

## Calculation & Plotting Logic

* **1RM Estimation (Brzycki Formula)**:
  $$\text{Est. 1RM} = \text{Mass} \times \frac{36}{37 - \text{Reps}}$$
  For bodyweight exercises, maximum reps are tracked instead.
* **Auto-Zoom & Target Y-Axis Scaling**: Y-axis scales are adjusted with a 15% margin on maximums. If the next milestone tier is close, the chart auto-extends to make the target line visible.
* **Standards Slopes**: Standard levels are calculated continuously for each logged weight point to create smooth slopes across training sessions.

---

## Utility Scripts

Located in the `scripts/` directory:
* `generate_readme_charts.py`: Generates the SVG images for documentation using mock data by default (or run with `--real` for personal data).
  
  The script generates a comprehensive set of 10 charts inside the `media/` directory:
  - **Overall Strength Overview** (`media/overall_strength_overview.svg`)
  - **Body Composition Trends** (`media/body_composition_trends.svg`)
  - **Weekly Training Consistency** (`media/weekly_training_consistency.svg`)
  - **Exercise Progress (Barbell)** (`media/bench_press_max_mass.svg`, `media/squat_max_mass.svg`)
  - **Exercise Progress (Bodyweight/Reps)** (`media/pullups_max_reps.svg`, `media/abdominals_progress.svg`)
  - **Reps Evolution** (`media/bench_press_reps_evolution.svg`, `media/squat_reps_evolution.svg`, `media/pullups_reps_evolution.svg`)
* `batch_scraper.py`: Discovers and scrapes strength standards globally from Strength Level.
* `parse_standards.py`: A GUI tool to add or tweak standards manually.

---

## Architectural History (Overhaul Changelog)

* **90-Degree Transitions**: Clean background vertical walls for milestones.
* **Infinite Height Filling**: Baseline scaling set to 1,000,000.
* **Retroactive Achievements**: background fills from the start of the timeline based on highest lifetime achievement.
* **Plasma Palette**: Harmonious colors for milestones.
* **Custom transparency**: 90-95% background transparency.
* **Rotated date labels**: -45 degree label orientation.
* **Error bars**: Standard deviation variance visualizer for mass and rep stability.
