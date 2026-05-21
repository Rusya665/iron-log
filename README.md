# Iron Log

Built with ⚡ **Vibe Coding** and **Google Antigravity IDE**.

Iron Log is a local, Python-based training tracking tool. It operates without subscriptions or cloud dependencies. The tool converts manual workout entries (sets, reps, and mass) from a Python dictionary into a formatted Excel workbook with dynamic charts. Strength standards are overlaid onto the charts and adjust automatically based on logged body mass.

---

## Visual Tour

### Strength & Progress Tracking

Charts track your estimated maximum strength and actual mass used. The next benchmark tier (e.g., Novice, Intermediate) is displayed as a target line to keep you focused on the next goal. Backgrounds utilize a Plasma color palette to indicate milestone achievements.

<img src="media/overall_strength_overview.svg" width="800" alt="Overall Strength Overview">

*Example: A bird's-eye view of all major lifts tracked against Est. 1RM / Max Reps.*

<img src="media/bench_press_max_mass.svg" width="600" alt="Bench Press Progress">

*Example: Tracking Bench Press PRs with shifting standard benchmarks.*

<img src="media/squat_max_mass.svg" width="600" alt="Squat Progress">

*Example: Seeing the next target line on Squat progression.*

### Reps & Consistency

Focus extends beyond the heaviest mass. Average reps and rep evolution are tracked to monitor efficiency and volume. Standard deviation error bars indicate set variance. A consistency chart logs weekly training frequency.

<img src="media/squat_reps_evolution.svg" width="600" alt="Squat Reps">

*Tracking rep efficiency and volume over time.*

<img src="media/weekly_training_consistency.svg" width="400" alt="Weekly Consistency">

*A bar chart tracking weekly training frequency.*

### Body Composition & Body-Mass Exercises

Additional metrics are tracked alongside body mass. Measurements such as waist and biceps are supported. The tool also handles body-mass exercises (like pull-ups) by tracking reps instead of mass.

<img src="media/body_composition_trends.svg" width="600" alt="Body Composition">

*Correlating body mass changes with physical measurements.*

<img src="media/pullups_max_reps.svg" width="600" alt="Pull-ups Max Reps">

*Example: Tracking progress on exercises where reps are the primary metric.*

---

## Key Features

- **Adaptive Strength Benchmarks**: Benchmark lines (`Beginner` to `Elite`) recalculate for every session based on your sex and your logged body mass.
- **Retroactive Milestone Backgrounds**: Chart backgrounds fill with the highest strength tier you have *ever* achieved — retroactively across the full date range.
- **Persistent Feature Toggles**: Control your chart's complexity (toggle PRs, Standards, or Milestones) directly from the Settings menu.
- **Intelligent Cycle Planning**: Automatically detects your split, pre-fills the next block of days, and provides quick-action buttons to adjust progression.

---

## Installation

The easiest way to use Iron Log is to download the standalone Windows installer:

1. Go to the [Releases](https://github.com/Rusya665/iron-log/releases) page on GitHub.
2. Download the latest `IronLog_Setup_vX.X.X.exe` file.
3. Run the installer to install the application and create a Start Menu shortcut. 
*(No Python installation or dependencies required!)*

---

## For Developers & Power Users

For developer guides, running from source code, custom workout dictionary formatting, or detailed math calculations, please refer to the:

👉 **[Technical & Developer Documentation](docs/technical.md)**