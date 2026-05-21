import os
import sys
import unittest
import tempfile
import shutil

# Add project root to python path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

class TestReadmeCharts(unittest.TestCase):
    def test_chart_generation(self):
        # Import target generation module
        import scripts.generate_readme_charts
        
        # Isolated output directory for testing
        temp_dir = tempfile.mkdtemp()
        original_media_dir = scripts.generate_readme_charts.MEDIA_DIR
        scripts.generate_readme_charts.MEDIA_DIR = temp_dir
        
        try:
            # Run the main generation pipeline using mock/dummy data
            scripts.generate_readme_charts.initialize_data_source(use_real=False)
            
            # Execute chart renders
            scripts.generate_readme_charts.generate_overall_strength_overview()
            scripts.generate_readme_charts.generate_body_composition_trends()
            scripts.generate_readme_charts.generate_weekly_training_consistency()
            
            scripts.generate_readme_charts.generate_individual_progress("bench-press", "Bench Press", "bench_press_max_mass.svg")
            scripts.generate_readme_charts.generate_individual_progress("squat", "Squat", "squat_max_mass.svg")
            scripts.generate_readme_charts.generate_individual_progress("pull-ups", "Pull-ups", "pullups_max_reps.svg")
            scripts.generate_readme_charts.generate_individual_progress("crunches", "Abdominals", "abdominals_progress.svg")
            
            scripts.generate_readme_charts.generate_individual_reps_evolution("bench-press", "Bench Press", "bench_press_reps_evolution.svg")
            scripts.generate_readme_charts.generate_individual_reps_evolution("squat", "Squat", "squat_reps_evolution.svg")
            scripts.generate_readme_charts.generate_individual_reps_evolution("pull-ups", "Pull-ups", "pullups_reps_evolution.svg")
            
            expected_files = [
                "overall_strength_overview.svg",
                "body_composition_trends.svg",
                "weekly_training_consistency.svg",
                "bench_press_max_mass.svg",
                "squat_max_mass.svg",
                "pullups_max_reps.svg",
                "abdominals_progress.svg",
                "bench_press_reps_evolution.svg",
                "squat_reps_evolution.svg",
                "pullups_reps_evolution.svg"
            ]
            
            # Validate existence, non-emptiness, and basic SVG format structure
            for filename in expected_files:
                file_path = os.path.join(temp_dir, filename)
                self.assertTrue(os.path.exists(file_path), f"File {filename} was not generated")
                self.assertGreater(os.path.getsize(file_path), 0, f"File {filename} is empty")
                
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    self.assertIn("<svg", content)
                    self.assertIn("</svg>", content)
                    
        finally:
            # Restore original settings and clean up test directory
            scripts.generate_readme_charts.MEDIA_DIR = original_media_dir
            shutil.rmtree(temp_dir)

if __name__ == "__main__":
    unittest.main()
