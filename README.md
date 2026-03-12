# Iron Log 🏋️‍♂️

A completely local, Python-based tool to log workouts, track body measurements, and generate detailed Excel reports charting your strength progress against established community standards. No subscriptions, no cloud databases—just your data and pure analytical insight.

## What It Does

Iron Log takes your manual workout entries (sets, reps, and weights) and bodyweight measurements from a simple Python dictionary, processes the numbers, and outputs a formatted Excel workbook.

The Excel report includes:

*   **Data Log**: A clean, day-by-day table of your workouts including daily volume, total reps, and relative intensity.
*   **Progress Charts**: Visualizations of your progress. The X-axis correctly scales to the actual dates of your workouts (so a missed week shows as a visual gap).
*   **Body Composition**: Tracks your bodyweight alongside any other measurements (e.g., biceps, waist) you log.
*   **Summary Analytics**: Daily volume distribution, relative intensity, and weekly consistency.
*   **Exercise-Specific Charts**: Individual line charts for every exercise tracking your Average Mass and Estimated 1RM (or Max Reps for bodyweight movements).
*   **Strength Standards**: For the major lifts (Squat, Bench Press, Deadlift, Overhead Press, Bicep Curls, Pull-ups), the charts overlay standard benchmark lines (Beginner to Elite). These benchmarks adjust dynamically based on the bodyweight you log on that specific date.

## The Math Under the Hood

Iron Log uses standard formulas to calculate performance metrics:

*   **Volume**: Sum of (Reps * Mass) for every set in a session.
*   **Estimated 1RM (One-Rep Max)**: Calculated using the Brzycki formula: `Mass * (36 / (37 - Reps))`. The tool finds the 1RM for each set and reports the maximum value achieved in that session.
    *   *Note*: If the exercise uses 0 mass (like pull-ups), the tool calculates and charts the maximum number of reps achieved in a single set instead.
*   **Relative Intensity**: Measures the average 'effort' of your sets relative to your daily capacity.
    *   For weighted exercises: `(Set Mass / Daily Est 1RM)`
    *   For bodyweight exercises: `(Set Reps / Daily Max Reps)`
*   **Dynamic Standard Benchmarks**: When plotting your lifts against strength standards, the tool rounds your logged bodyweight to the nearest 5kg to match the look-up tables. It automatically includes the "Next Level" (e.g., Novice if you are currently at Beginner) as a target on your charts, providing both a "zoomed" view and future context. The X-axis correctly handles irregular gaps in logging, showing your real progress over time.

## How to Use It

### 0. Install Requirements

Before running, ensure you have the necessary libraries installed:

```bash
pip install -r requirements.txt
```

### 1. Initial Setup

Run the main script to generate your first report:

```bash
python main.py
```

On the first run, a GUI dialog will pop up asking you to select two directories:

1.  **Excel Output Folder**: Where the generated `.xlsx` files will be saved.
2.  **Sessions Folder**: The location of your `sessions.py` file (defaults to searching for `2025 Health` in your Google Drive or local directories).

If you ever need to change these paths, run:

```bash
python main.py --reconfigure
```

### 2. Logging Your Workouts (`sessions.py`)

All your data lives in `sessions.py`. You update this file manually.

#### Tracking Bodyweight & Measurements
At the top of the file, maintain the `BODYWEIGHT_LOG`.

```python
BODYWEIGHT_LOG = {
    "2026-03-01": 80.5, # Simple weight entry
    "2026-03-08": {"weight": 81.0, "biceps": 38.0, "waist": 85.5}, # Advanced tracking
}
```

#### Tracking Workouts
Add a new dictionary entry for each workout day in `USER_DATA`.

```python
USER_DATA = {
    "2026-03-12": { 
        SQ: Log([5, 3, 1], [80, 90, 100]), # 3 sets: 80kg for 5, 90kg for 3, 100kg for 1
        PU: Log([8, 7, 6], [0, 0, 0]),     # Bodyweight exercises use 0 for mass
    },
}
```

### 3. Adding New Strength Standards

If you want to track a new exercise against community benchmarks, you can use the built-in parsing utility.

1.  Find the standards table for your exercise on [strengthlevel.com](https://strengthlevel.com).
2.  Run the parser:
    ```bash
    python scripts/parse_standards.py
    ```
3.  Use the GUI dropdown to select the exercise ID from your registry.
4.  Copy the raw table text from the website and paste it into the parser box.
5.  Click **PARSE & SAVE**. The tool will automatically clean the data and append the new dictionary to `core/standards.py`.