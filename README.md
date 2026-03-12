# Iron Log

[Iron Log](https://github.com/Rusya665/iron-log) is a local, Python-based training tracking tool. It operates without subscriptions or cloud dependencies. The tool converts manual workout entries (sets, reps, and mass) from a Python dictionary into a formatted Excel workbook with dynamic charts. Strength standards are overlaid onto the charts and adjust automatically based on logged body mass.

## Visual Tour

### Strength & Progress Tracking

Charts track your estimated maximum strength and actual mass used. The next benchmark tier (e.g., Novice, Intermediate) is displayed as a target line to keep you focused on the next goal.

<img src="media/overall_strength_overview.svg" width="800" alt="Overall Strength Overview">

Example: A birds-eye view of all major lifts tracked against Est. 1RM.

<img src="media/bench_press_max_mass.svg" width="600" alt="Bench Press Progress">

Example: Tracking Bench Press PRs with shifting standard benchmarks.

<img src="media/squat_max_mass.svg" width="600" alt="Squat Progress">

Example: Seeing the next target line on Squat progression.

### Reps & Consistency

Focus extends beyond the heaviest mass. Average reps and rep evolution are tracked to monitor efficiency and volume. A consistency chart logs weekly training frequency.

<img src="media/squat_reps_evolution.svg" width="600" alt="Squat Reps">

Tracking rep efficiency and volume over time.

<img src="media/weekly_training_consistency.svg" width="400" alt="Weekly Consistency">

A bar chart tracking weekly training frequency.

### Body Composition & Body-Mass Exercises

Additional metrics are tracked alongside body mass. Measurements such as waist and biceps are supported. The tool also handles body-mass exercises (like pull-ups) by tracking reps instead of mass.

<img src="media/body_composition_trends.svg" width="600" alt="Body Composition">

Correlating body mass changes with physical measurements.

<img src="media/pullups_max_reps.svg" width="600" alt="Pull-ups Max Reps">

Example: Tracking progress on exercises where reps are the primary metric.

## Features

*   **Data Log**: A chronological table of workouts, including daily volume and intensity.
*   **Time-Scaled Charts**: The X-axis utilizes standard date scaling. Gaps in training are visually represented.
*   **Dynamic Benchmarks**: Standard lifts feature target lines from Beginner to Elite. Benchmark lines adjust based on the logged body mass for the specific date.
*   **Massive Standards Database**: Includes benchmarks for 60+ exercises automatically discovered and updated.
*   **Intelligent Routing**: Uses fuzzy matching and synonym handling (e.g., "Overhead Press" maps to "Shoulder Press") to find the correct benchmarks regardless of naming preference.

## Calculation Logic

*   **1RM Estimation**: The [Brzycki formula](https://en.wikipedia.org/wiki/One-repetition_maximum) calculates estimated maximum strength. For body-mass exercises, maximum reps are tracked instead.
*   **Target Padding**: Charts are configured to display a minimum 15kg range to prevent flat visualization during periods of consistent mass.
*   **Automatic Interpolation**: Benchmark lines interpolate smoothly between logged body mass entries.

## Execution

### 0. Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

### 1. Generation

Run the primary script:

```bash
python main.py
```

Upon initial execution, prompts will request the output directory for Excel files and the location of `sessions.py`. Paths are saved in `config.json`. To modify paths, execute:

```bash
python main.py --reconfigure
```

### 2. Session Logging

Data is maintained in `sessions.py`. Dictionaries are updated manually.

**Tracking mass:**

```python
BODYMASS_LOG = {
    "2026-03-01": 80.5, # Mass only
    "2026-03-08": {"mass": 81.0, "biceps": 38.0, "waist": 85.5}, # Full metrics
}
```

**Tracking workouts:**

```python
USER_DATA = {
    "2026-03-12": { 
        SQ: Log([5, 3, 1], [80, 90, 100]), # 3 sets: 80kg x 5, 90kg x 3, 100kg x 1
        PU: Log([8, 7, 6], [0, 0, 0]),     # Use 0 mass for body-mass exercises
    },
}
```

### 3. Registering Exercises

Before you can log a new exercise, you must add it to the `EXERCISE_REGISTRY` in `sessions.py`. This ensures it appears consistently in the data log and charts.

```python
# Create a unique ID/Constant
LP = "Leg Press"

# Add it to the registry list
EXERCISE_REGISTRY = [
    Exercise(LP, "Leg Press"), # ID and optional display name
    Exercise(SQ),               # Defaults to ID as name
]
```

### 4. Managing Standards

The project uses a massive database of exercise standards. You can manage these using the provided scripts:

*   **Global Update**: To refresh the entire collection of 60+ exercises from [strengthlevel.com](https://strengthlevel.com):
    ```bash
    python scripts/batch_scraper.py
    ```
*   **Manual Entry**: To add a specific exercise via text copying (GUI):
    ```bash
    python scripts/parse_standards.py
    ```

## Utility Scripts

Located in the `scripts/` directory, these tools assist with data and asset management:

*   `batch_scraper.py`: Discovers and scrapes all available strength standards globally.
*   `parse_standards.py`: A GUI utility for manually adding missing standards via copy-paste.
*   `patch_svgs.py`: Ensures exported SVGs are compatible with dark-mode environments by adjusting color schemes and transparency.

## Contributing

Contributions are welcome! If you have suggestions for new features, benchmarks, or logic improvements, feel free to open an issue or submit a pull request.

## License

This project is licensed under the [MIT License](LICENSE).