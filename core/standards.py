import re

BENCH_PRESS_STANDARDS_KG = {
    50: {"Beginner": 24, "Novice": 38, "Intermediate": 57, "Advanced": 79, "Elite": 103},
    55: {"Beginner": 29, "Novice": 45, "Intermediate": 64, "Advanced": 87, "Elite": 113},
    60: {"Beginner": 34, "Novice": 51, "Intermediate": 72, "Advanced": 96, "Elite": 123},
    65: {"Beginner": 39, "Novice": 57, "Intermediate": 79, "Advanced": 104, "Elite": 132},
    70: {"Beginner": 44, "Novice": 62, "Intermediate": 85, "Advanced": 112, "Elite": 141},
    75: {"Beginner": 49, "Novice": 68, "Intermediate": 92, "Advanced": 119, "Elite": 149},
    80: {"Beginner": 53, "Novice": 74, "Intermediate": 98, "Advanced": 127, "Elite": 157},
    85: {"Beginner": 58, "Novice": 79, "Intermediate": 105, "Advanced": 134, "Elite": 165},
    90: {"Beginner": 62, "Novice": 84, "Intermediate": 111, "Advanced": 141, "Elite": 172},
    95: {"Beginner": 67, "Novice": 89, "Intermediate": 116, "Advanced": 147, "Elite": 180},
    100: {"Beginner": 71, "Novice": 94, "Intermediate": 122, "Advanced": 153, "Elite": 187},
    105: {"Beginner": 75, "Novice": 99, "Intermediate": 128, "Advanced": 160, "Elite": 194},
    110: {"Beginner": 80, "Novice": 104, "Intermediate": 133, "Advanced": 166, "Elite": 200},
    115: {"Beginner": 84, "Novice": 109, "Intermediate": 138, "Advanced": 172, "Elite": 207},
    120: {"Beginner": 88, "Novice": 113, "Intermediate": 143, "Advanced": 177, "Elite": 213},
    125: {"Beginner": 92, "Novice": 118, "Intermediate": 148, "Advanced": 183, "Elite": 219},
    130: {"Beginner": 95, "Novice": 122, "Intermediate": 153, "Advanced": 188, "Elite": 225},
    135: {"Beginner": 99, "Novice": 126, "Intermediate": 158, "Advanced": 194, "Elite": 231},
    140: {"Beginner": 103, "Novice": 130, "Intermediate": 163, "Advanced": 199, "Elite": 236},
}

SQUAT_STANDARDS_KG = {
    50: {"Beginner": 33, "Novice": 52, "Intermediate": 76, "Advanced": 104, "Elite": 136},
    55: {"Beginner": 40, "Novice": 60, "Intermediate": 86, "Advanced": 116, "Elite": 149},
    60: {"Beginner": 47, "Novice": 68, "Intermediate": 95, "Advanced": 127, "Elite": 161},
    65: {"Beginner": 53, "Novice": 76, "Intermediate": 104, "Advanced": 137, "Elite": 173},
    70: {"Beginner": 59, "Novice": 83, "Intermediate": 113, "Advanced": 147, "Elite": 184},
    75: {"Beginner": 66, "Novice": 91, "Intermediate": 122, "Advanced": 157, "Elite": 195},
    80: {"Beginner": 72, "Novice": 98, "Intermediate": 130, "Advanced": 166, "Elite": 205},
    85: {"Beginner": 78, "Novice": 105, "Intermediate": 138, "Advanced": 175, "Elite": 215},
    90: {"Beginner": 83, "Novice": 112, "Intermediate": 146, "Advanced": 184, "Elite": 225},
    95: {"Beginner": 89, "Novice": 118, "Intermediate": 153, "Advanced": 192, "Elite": 234},
    100: {"Beginner": 95, "Novice": 125, "Intermediate": 160, "Advanced": 201, "Elite": 243},
    105: {"Beginner": 100, "Novice": 131, "Intermediate": 168, "Advanced": 209, "Elite": 252},
    110: {"Beginner": 106, "Novice": 137, "Intermediate": 174, "Advanced": 216, "Elite": 260},
    115: {"Beginner": 111, "Novice": 143, "Intermediate": 181, "Advanced": 224, "Elite": 269},
    120: {"Beginner": 116, "Novice": 149, "Intermediate": 188, "Advanced": 231, "Elite": 277},
    125: {"Beginner": 121, "Novice": 155, "Intermediate": 194, "Advanced": 238, "Elite": 284},
    130: {"Beginner": 126, "Novice": 160, "Intermediate": 201, "Advanced": 245, "Elite": 292},
    135: {"Beginner": 131, "Novice": 166, "Intermediate": 207, "Advanced": 252, "Elite": 299},
    140: {"Beginner": 136, "Novice": 171, "Intermediate": 213, "Advanced": 259, "Elite": 307},
}

DEADLIFT_STANDARDS_KG = {
    50: {"Beginner": 44, "Novice": 65, "Intermediate": 93, "Advanced": 125, "Elite": 160},
    55: {"Beginner": 51, "Novice": 74, "Intermediate": 103, "Advanced": 137, "Elite": 174},
    60: {"Beginner": 58, "Novice": 83, "Intermediate": 114, "Advanced": 149, "Elite": 187},
    65: {"Beginner": 66, "Novice": 92, "Intermediate": 124, "Advanced": 160, "Elite": 200},
    70: {"Beginner": 73, "Novice": 100, "Intermediate": 133, "Advanced": 171, "Elite": 212},
    75: {"Beginner": 79, "Novice": 108, "Intermediate": 142, "Advanced": 182, "Elite": 224},
    80: {"Beginner": 86, "Novice": 116, "Intermediate": 151, "Advanced": 192, "Elite": 235},
    85: {"Beginner": 93, "Novice": 123, "Intermediate": 160, "Advanced": 201, "Elite": 245},
    90: {"Beginner": 99, "Novice": 131, "Intermediate": 168, "Advanced": 211, "Elite": 256},
    95: {"Beginner": 105, "Novice": 138, "Intermediate": 176, "Advanced": 220, "Elite": 266},
    100: {"Beginner": 111, "Novice": 145, "Intermediate": 184, "Advanced": 228, "Elite": 275},
    105: {"Beginner": 117, "Novice": 151, "Intermediate": 192, "Advanced": 237, "Elite": 284},
    110: {"Beginner": 123, "Novice": 158, "Intermediate": 199, "Advanced": 245, "Elite": 293},
    115: {"Beginner": 129, "Novice": 164, "Intermediate": 206, "Advanced": 253, "Elite": 302},
    120: {"Beginner": 134, "Novice": 171, "Intermediate": 213, "Advanced": 261, "Elite": 311},
    125: {"Beginner": 140, "Novice": 177, "Intermediate": 220, "Advanced": 268, "Elite": 319},
    130: {"Beginner": 145, "Novice": 183, "Intermediate": 227, "Advanced": 276, "Elite": 327},
    135: {"Beginner": 150, "Novice": 188, "Intermediate": 233, "Advanced": 283, "Elite": 335},
    140: {"Beginner": 155, "Novice": 194, "Intermediate": 240, "Advanced": 290, "Elite": 342},
}

OVERHEAD_PRESS_STANDARDS_KG = {
    50: {"Beginner": 15, "Novice": 25, "Intermediate": 38, "Advanced": 53, "Elite": 71},
    55: {"Beginner": 18, "Novice": 29, "Intermediate": 42, "Advanced": 59, "Elite": 77},
    60: {"Beginner": 21, "Novice": 32, "Intermediate": 47, "Advanced": 64, "Elite": 84},
    65: {"Beginner": 24, "Novice": 36, "Intermediate": 52, "Advanced": 70, "Elite": 90},
    70: {"Beginner": 27, "Novice": 40, "Intermediate": 56, "Advanced": 75, "Elite": 95},
    75: {"Beginner": 30, "Novice": 43, "Intermediate": 60, "Advanced": 80, "Elite": 101},
    80: {"Beginner": 33, "Novice": 47, "Intermediate": 64, "Advanced": 84, "Elite": 106},
    85: {"Beginner": 36, "Novice": 50, "Intermediate": 68, "Advanced": 89, "Elite": 111},
    90: {"Beginner": 39, "Novice": 54, "Intermediate": 72, "Advanced": 93, "Elite": 116},
    95: {"Beginner": 41, "Novice": 57, "Intermediate": 76, "Advanced": 97, "Elite": 121},
    100: {"Beginner": 44, "Novice": 60, "Intermediate": 79, "Advanced": 102, "Elite": 125},
    105: {"Beginner": 47, "Novice": 63, "Intermediate": 83, "Advanced": 106, "Elite": 130},
    110: {"Beginner": 49, "Novice": 66, "Intermediate": 86, "Advanced": 109, "Elite": 134},
    115: {"Beginner": 52, "Novice": 69, "Intermediate": 90, "Advanced": 113, "Elite": 138},
    120: {"Beginner": 54, "Novice": 72, "Intermediate": 93, "Advanced": 117, "Elite": 142},
    125: {"Beginner": 57, "Novice": 75, "Intermediate": 96, "Advanced": 120, "Elite": 146},
    130: {"Beginner": 59, "Novice": 77, "Intermediate": 99, "Advanced": 124, "Elite": 150},
    135: {"Beginner": 61, "Novice": 80, "Intermediate": 102, "Advanced": 127, "Elite": 154},
    140: {"Beginner": 64, "Novice": 83, "Intermediate": 105, "Advanced": 131, "Elite": 157},
}

BICEP_CURLS_STANDARDS_KG = {
    50: {"Beginner": 9, "Novice": 18, "Intermediate": 30, "Advanced": 46, "Elite": 64},
    55: {"Beginner": 11, "Novice": 20, "Intermediate": 34, "Advanced": 50, "Elite": 69},
    60: {"Beginner": 13, "Novice": 23, "Intermediate": 37, "Advanced": 54, "Elite": 73},
    65: {"Beginner": 14, "Novice": 25, "Intermediate": 40, "Advanced": 58, "Elite": 78},
    70: {"Beginner": 16, "Novice": 27, "Intermediate": 43, "Advanced": 61, "Elite": 82},
    75: {"Beginner": 18, "Novice": 30, "Intermediate": 45, "Advanced": 64, "Elite": 85},
    80: {"Beginner": 19, "Novice": 32, "Intermediate": 48, "Advanced": 67, "Elite": 89},
    85: {"Beginner": 21, "Novice": 34, "Intermediate": 50, "Advanced": 70, "Elite": 93},
    90: {"Beginner": 23, "Novice": 36, "Intermediate": 53, "Advanced": 73, "Elite": 96},
    95: {"Beginner": 24, "Novice": 38, "Intermediate": 55, "Advanced": 76, "Elite": 99},
    100: {"Beginner": 26, "Novice": 40, "Intermediate": 58, "Advanced": 79, "Elite": 102},
    105: {"Beginner": 27, "Novice": 42, "Intermediate": 60, "Advanced": 82, "Elite": 105},
    110: {"Beginner": 29, "Novice": 43, "Intermediate": 62, "Advanced": 84, "Elite": 108},
    115: {"Beginner": 30, "Novice": 45, "Intermediate": 64, "Advanced": 87, "Elite": 111},
    120: {"Beginner": 32, "Novice": 47, "Intermediate": 66, "Advanced": 89, "Elite": 114},
    125: {"Beginner": 33, "Novice": 49, "Intermediate": 68, "Advanced": 91, "Elite": 116},
    130: {"Beginner": 34, "Novice": 50, "Intermediate": 70, "Advanced": 94, "Elite": 119},
    135: {"Beginner": 36, "Novice": 52, "Intermediate": 72, "Advanced": 96, "Elite": 121},
    140: {"Beginner": 37, "Novice": 54, "Intermediate": 74, "Advanced": 98, "Elite": 124},
}

PULL_UPS_STANDARDS_KG = {
    50: {'Beginner': 1, 'Novice': 5, 'Intermediate': 15, 'Advanced': 27, 'Elite': 40},
    55: {'Beginner': 1, 'Novice': 6, 'Intermediate': 15, 'Advanced': 26, 'Elite': 39},
    60: {'Beginner': 1, 'Novice': 6, 'Intermediate': 15, 'Advanced': 26, 'Elite': 37},
    65: {'Beginner': 1, 'Novice': 6, 'Intermediate': 15, 'Advanced': 25, 'Elite': 36},
    70: {'Beginner': 1, 'Novice': 6, 'Intermediate': 14, 'Advanced': 24, 'Elite': 35},
    75: {'Beginner': 1, 'Novice': 6, 'Intermediate': 14, 'Advanced': 24, 'Elite': 34},
    80: {'Beginner': 1, 'Novice': 6, 'Intermediate': 14, 'Advanced': 23, 'Elite': 33},
    85: {'Beginner': 1, 'Novice': 6, 'Intermediate': 13, 'Advanced': 22, 'Elite': 32},
    90: {'Beginner': 1, 'Novice': 6, 'Intermediate': 13, 'Advanced': 21, 'Elite': 30},
    95: {'Beginner': 1, 'Novice': 6, 'Intermediate': 12, 'Advanced': 21, 'Elite': 29},
    100: {'Beginner': 1, 'Novice': 6, 'Intermediate': 12, 'Advanced': 20, 'Elite': 28},
    105: {'Beginner': 1, 'Novice': 5, 'Intermediate': 11, 'Advanced': 19, 'Elite': 27},
    110: {'Beginner': 1, 'Novice': 5, 'Intermediate': 11, 'Advanced': 18, 'Elite': 26},
    115: {'Beginner': 1, 'Novice': 5, 'Intermediate': 10, 'Advanced': 18, 'Elite': 25},
    120: {'Beginner': 1, 'Novice': 4, 'Intermediate': 10, 'Advanced': 17, 'Elite': 25},
    125: {'Beginner': 1, 'Novice': 4, 'Intermediate': 10, 'Advanced': 16, 'Elite': 24},
    130: {'Beginner': 1, 'Novice': 4, 'Intermediate': 9, 'Advanced': 16, 'Elite': 23},
    135: {'Beginner': 1, 'Novice': 4, 'Intermediate': 9, 'Advanced': 15, 'Elite': 22},
    140: {'Beginner': 1, 'Novice': 3, 'Intermediate': 9, 'Advanced': 15, 'Elite': 21}
}

DUMBBELL_BENCH_PRESS_STANDARDS_KG = {
    50: {"Beginner": 8, "Novice": 15, "Intermediate": 26, "Advanced": 39, "Elite": 54},
    55: {"Beginner": 10, "Novice": 18, "Intermediate": 29, "Advanced": 42, "Elite": 58},
    60: {"Beginner": 11, "Novice": 20, "Intermediate": 32, "Advanced": 46, "Elite": 62},
    65: {"Beginner": 13, "Novice": 22, "Intermediate": 34, "Advanced": 49, "Elite": 66},
    70: {"Beginner": 15, "Novice": 24, "Intermediate": 37, "Advanced": 52, "Elite": 69},
    75: {"Beginner": 16, "Novice": 26, "Intermediate": 39, "Advanced": 55, "Elite": 73},
    80: {"Beginner": 18, "Novice": 28, "Intermediate": 42, "Advanced": 58, "Elite": 76},
    85: {"Beginner": 19, "Novice": 30, "Intermediate": 44, "Advanced": 61, "Elite": 79},
    90: {"Beginner": 21, "Novice": 32, "Intermediate": 46, "Advanced": 63, "Elite": 82},
    95: {"Beginner": 22, "Novice": 34, "Intermediate": 49, "Advanced": 66, "Elite": 85},
    100: {"Beginner": 24, "Novice": 36, "Intermediate": 51, "Advanced": 69, "Elite": 88},
    105: {"Beginner": 25, "Novice": 38, "Intermediate": 53, "Advanced": 71, "Elite": 91},
    110: {"Beginner": 27, "Novice": 39, "Intermediate": 55, "Advanced": 73, "Elite": 93},
    115: {"Beginner": 28, "Novice": 41, "Intermediate": 57, "Advanced": 76, "Elite": 96},
    120: {"Beginner": 29, "Novice": 43, "Intermediate": 59, "Advanced": 78, "Elite": 98},
    125: {"Beginner": 31, "Novice": 44, "Intermediate": 61, "Advanced": 80, "Elite": 101},
    130: {"Beginner": 32, "Novice": 46, "Intermediate": 63, "Advanced": 82, "Elite": 103},
    135: {"Beginner": 33, "Novice": 47, "Intermediate": 64, "Advanced": 84, "Elite": 105},
    140: {"Beginner": 35, "Novice": 49, "Intermediate": 66, "Advanced": 86, "Elite": 108},
}

def get_exercise_standard(exercise_id: str, target_date_str: str, bodymass_log: dict, level: str = "Intermediate") -> int:
    """
    Dynamically routes an exercise to its corresponding standards table.
    Uses fuzzy matching to find the best table in the global namespace.
    """
    if not bodymass_log:
        return 0
        
    dates = sorted(bodymass_log.keys())
    if not dates:
        return 0
        
    applicable_date = dates[0]
    for d in dates:
        if d <= target_date_str:
            applicable_date = d
        else:
            break
            
    bm_data = bodymass_log[applicable_date]
    current_bm = bm_data if isinstance(bm_data, (int, float)) else bm_data.get("mass", 0)
    
    if not current_bm:
        return 0
        
    rounded_bm = int(round(current_bm / 5.0) * 5.0)
    rounded_bm = max(50, min(rounded_bm, 140))
    
    # 1. Cleanse Exercise ID for comparison
    clean_id = exercise_id.lower().replace('-', ' ').strip()
    # Remove common filler words/parentheses
    clean_id = re.sub(r'\(|\)|\[|\]', '', clean_id)
    parts = set(clean_id.split())

    # Add synonyms to parts to broaden matching
    synonym_map = {
        "overhead": "shoulder",
        "shoulder": "overhead",
        "lat": "pull", # lat pulldown <-> pull downs
        "pulldown": "pull downs",
        "pulldowns": "pull downs"
    }
    
    extra_parts = set()
    for p in parts:
        if p in synonym_map:
            extra_parts.update(synonym_map[p].split())
    parts.update(extra_parts)

    # 2. Search for matching tables in global namespace
    # We look for variables ending in _STANDARDS_KG
    available_tables = {k: v for k, v in globals().items() if k.endswith("_STANDARDS_KG")}
    
    best_match_table = None
    best_score = -1

    for table_name, table_data in available_tables.items():
        # Clean table name for comparison: DUMBBELL_BENCH_PRESS_STANDARDS_KG -> dumbbell bench press
        base_table_name = table_name.replace('_STANDARDS_KG', '').replace('_', ' ').lower()
        table_parts = set(base_table_name.split())
        
        # Scoring logic:
        # - Exact match: 100
        # - Subset match (all parts of table are in id): 50 + len(table_parts)
        # - Partial match: len(intersection)
        
        if base_table_name == clean_id:
            score = 100
        elif table_parts.issubset(parts):
            # Prioritize longer/more specific table names (e.g. "dumbbell bench press" over "bench press")
            score = 50 + len(table_parts)
        else:
            intersection = parts.intersection(table_parts)
            score = len(intersection) if intersection else 0
            
        if score > best_score and score >= 1: # Require at least one word match
            best_score = score
            best_match_table = table_data

    if best_match_table is None or rounded_bm not in best_match_table:
        return 0
        
    return best_match_table[rounded_bm].get(level, 0)

# Added via GUI on 2026-03-12 15:23:44
PULL_DOWNS_STANDARDS_KG = {
    50: {'Beginner': 25, 'Novice': 39, 'Intermediate': 58, 'Advanced': 81, 'Elite': 105},
    55: {'Beginner': 28, 'Novice': 43, 'Intermediate': 63, 'Advanced': 86, 'Elite': 112},
    60: {'Beginner': 31, 'Novice': 47, 'Intermediate': 67, 'Advanced': 92, 'Elite': 118},
    65: {'Beginner': 34, 'Novice': 51, 'Intermediate': 72, 'Advanced': 97, 'Elite': 124},
    70: {'Beginner': 37, 'Novice': 54, 'Intermediate': 76, 'Advanced': 101, 'Elite': 129},
    75: {'Beginner': 39, 'Novice': 57, 'Intermediate': 80, 'Advanced': 106, 'Elite': 134},
    80: {'Beginner': 42, 'Novice': 61, 'Intermediate': 84, 'Advanced': 110, 'Elite': 139},
    85: {'Beginner': 45, 'Novice': 64, 'Intermediate': 87, 'Advanced': 115, 'Elite': 144},
    90: {'Beginner': 47, 'Novice': 67, 'Intermediate': 91, 'Advanced': 119, 'Elite': 149},
    95: {'Beginner': 50, 'Novice': 70, 'Intermediate': 94, 'Advanced': 122, 'Elite': 153},
    100: {'Beginner': 52, 'Novice': 72, 'Intermediate': 97, 'Advanced': 126, 'Elite': 157},
    105: {'Beginner': 54, 'Novice': 75, 'Intermediate': 101, 'Advanced': 130, 'Elite': 161},
    110: {'Beginner': 57, 'Novice': 78, 'Intermediate': 104, 'Advanced': 133, 'Elite': 165},
    115: {'Beginner': 59, 'Novice': 80, 'Intermediate': 107, 'Advanced': 137, 'Elite': 169},
    120: {'Beginner': 61, 'Novice': 83, 'Intermediate': 110, 'Advanced': 140, 'Elite': 172},
    125: {'Beginner': 63, 'Novice': 85, 'Intermediate': 112, 'Advanced': 143, 'Elite': 176},
    130: {'Beginner': 65, 'Novice': 88, 'Intermediate': 115, 'Advanced': 146, 'Elite': 179},
    135: {'Beginner': 67, 'Novice': 90, 'Intermediate': 118, 'Advanced': 149, 'Elite': 183},
    140: {'Beginner': 69, 'Novice': 92, 'Intermediate': 120, 'Advanced': 152, 'Elite': 186}
}

# Scraped on 2026-03-12
BARBELL_CURL_STANDARDS_KG = {
    50: {'Beginner': 9, 'Novice': 18, 'Intermediate': 30, 'Advanced': 46, 'Elite': 64},
    55: {'Beginner': 11, 'Novice': 20, 'Intermediate': 34, 'Advanced': 50, 'Elite': 69},
    60: {'Beginner': 13, 'Novice': 23, 'Intermediate': 37, 'Advanced': 54, 'Elite': 73},
    65: {'Beginner': 14, 'Novice': 25, 'Intermediate': 40, 'Advanced': 58, 'Elite': 78},
    70: {'Beginner': 16, 'Novice': 27, 'Intermediate': 43, 'Advanced': 61, 'Elite': 82},
    75: {'Beginner': 18, 'Novice': 30, 'Intermediate': 45, 'Advanced': 64, 'Elite': 85},
    80: {'Beginner': 19, 'Novice': 32, 'Intermediate': 48, 'Advanced': 67, 'Elite': 89},
    85: {'Beginner': 21, 'Novice': 34, 'Intermediate': 50, 'Advanced': 70, 'Elite': 93},
    90: {'Beginner': 23, 'Novice': 36, 'Intermediate': 53, 'Advanced': 73, 'Elite': 96},
    95: {'Beginner': 24, 'Novice': 38, 'Intermediate': 55, 'Advanced': 76, 'Elite': 99},
    100: {'Beginner': 26, 'Novice': 40, 'Intermediate': 58, 'Advanced': 79, 'Elite': 102},
    105: {'Beginner': 27, 'Novice': 42, 'Intermediate': 60, 'Advanced': 82, 'Elite': 105},
    110: {'Beginner': 29, 'Novice': 43, 'Intermediate': 62, 'Advanced': 84, 'Elite': 108},
    115: {'Beginner': 30, 'Novice': 45, 'Intermediate': 64, 'Advanced': 87, 'Elite': 111},
    120: {'Beginner': 32, 'Novice': 47, 'Intermediate': 66, 'Advanced': 89, 'Elite': 114},
    125: {'Beginner': 33, 'Novice': 49, 'Intermediate': 68, 'Advanced': 91, 'Elite': 116},
    130: {'Beginner': 34, 'Novice': 50, 'Intermediate': 70, 'Advanced': 94, 'Elite': 119},
    135: {'Beginner': 36, 'Novice': 52, 'Intermediate': 72, 'Advanced': 96, 'Elite': 121},
    140: {'Beginner': 37, 'Novice': 54, 'Intermediate': 74, 'Advanced': 98, 'Elite': 124}
}

# Scraped on 2026-03-12
BARBELL_SHRUG_STANDARDS_KG = {
    50: {'Beginner': 17, 'Novice': 38, 'Intermediate': 69, 'Advanced': 108, 'Elite': 155},
    55: {'Beginner': 22, 'Novice': 46, 'Intermediate': 79, 'Advanced': 122, 'Elite': 171},
    60: {'Beginner': 28, 'Novice': 54, 'Intermediate': 90, 'Advanced': 135, 'Elite': 186},
    65: {'Beginner': 34, 'Novice': 62, 'Intermediate': 100, 'Advanced': 147, 'Elite': 201},
    70: {'Beginner': 40, 'Novice': 70, 'Intermediate': 110, 'Advanced': 159, 'Elite': 215},
    75: {'Beginner': 46, 'Novice': 78, 'Intermediate': 120, 'Advanced': 171, 'Elite': 228},
    80: {'Beginner': 52, 'Novice': 85, 'Intermediate': 129, 'Advanced': 182, 'Elite': 241},
    85: {'Beginner': 58, 'Novice': 93, 'Intermediate': 139, 'Advanced': 193, 'Elite': 254},
    90: {'Beginner': 64, 'Novice': 100, 'Intermediate': 148, 'Advanced': 204, 'Elite': 266},
    95: {'Beginner': 70, 'Novice': 108, 'Intermediate': 156, 'Advanced': 214, 'Elite': 278},
    100: {'Beginner': 75, 'Novice': 115, 'Intermediate': 165, 'Advanced': 224, 'Elite': 289},
    105: {'Beginner': 81, 'Novice': 122, 'Intermediate': 173, 'Advanced': 234, 'Elite': 300},
    110: {'Beginner': 87, 'Novice': 129, 'Intermediate': 181, 'Advanced': 243, 'Elite': 311},
    115: {'Beginner': 92, 'Novice': 135, 'Intermediate': 189, 'Advanced': 253, 'Elite': 321},
    120: {'Beginner': 98, 'Novice': 142, 'Intermediate': 197, 'Advanced': 262, 'Elite': 332},
    125: {'Beginner': 103, 'Novice': 148, 'Intermediate': 205, 'Advanced': 270, 'Elite': 341},
    130: {'Beginner': 108, 'Novice': 155, 'Intermediate': 212, 'Advanced': 279, 'Elite': 351},
    135: {'Beginner': 113, 'Novice': 161, 'Intermediate': 220, 'Advanced': 287, 'Elite': 360},
    140: {'Beginner': 119, 'Novice': 167, 'Intermediate': 227, 'Advanced': 295, 'Elite': 370}
}

# Scraped on 2026-03-12
BENT_OVER_ROW_STANDARDS_KG = {
    50: {'Beginner': 21, 'Novice': 34, 'Intermediate': 51, 'Advanced': 71, 'Elite': 94},
    55: {'Beginner': 25, 'Novice': 39, 'Intermediate': 57, 'Advanced': 79, 'Elite': 102},
    60: {'Beginner': 29, 'Novice': 44, 'Intermediate': 63, 'Advanced': 86, 'Elite': 110},
    65: {'Beginner': 33, 'Novice': 49, 'Intermediate': 69, 'Advanced': 93, 'Elite': 118},
    70: {'Beginner': 37, 'Novice': 54, 'Intermediate': 75, 'Advanced': 99, 'Elite': 126},
    75: {'Beginner': 41, 'Novice': 59, 'Intermediate': 80, 'Advanced': 106, 'Elite': 133},
    80: {'Beginner': 45, 'Novice': 63, 'Intermediate': 86, 'Advanced': 112, 'Elite': 140},
    85: {'Beginner': 49, 'Novice': 68, 'Intermediate': 91, 'Advanced': 118, 'Elite': 146},
    90: {'Beginner': 52, 'Novice': 72, 'Intermediate': 96, 'Advanced': 123, 'Elite': 153},
    95: {'Beginner': 56, 'Novice': 76, 'Intermediate': 101, 'Advanced': 129, 'Elite': 159},
    100: {'Beginner': 60, 'Novice': 80, 'Intermediate': 106, 'Advanced': 134, 'Elite': 165},
    105: {'Beginner': 63, 'Novice': 84, 'Intermediate': 110, 'Advanced': 139, 'Elite': 170},
    110: {'Beginner': 66, 'Novice': 88, 'Intermediate': 115, 'Advanced': 144, 'Elite': 176},
    115: {'Beginner': 70, 'Novice': 92, 'Intermediate': 119, 'Advanced': 149, 'Elite': 181},
    120: {'Beginner': 73, 'Novice': 96, 'Intermediate': 123, 'Advanced': 154, 'Elite': 187},
    125: {'Beginner': 76, 'Novice': 100, 'Intermediate': 128, 'Advanced': 159, 'Elite': 192},
    130: {'Beginner': 79, 'Novice': 103, 'Intermediate': 132, 'Advanced': 163, 'Elite': 197},
    135: {'Beginner': 83, 'Novice': 107, 'Intermediate': 136, 'Advanced': 168, 'Elite': 202},
    140: {'Beginner': 86, 'Novice': 110, 'Intermediate': 139, 'Advanced': 172, 'Elite': 206}
}

# Scraped on 2026-03-12
BODYWEIGHT_SQUAT_STANDARDS_KG = {
    50: {'Beginner': 1, 'Novice': 12, 'Intermediate': 62, 'Advanced': 131, 'Elite': 215},
    55: {'Beginner': 1, 'Novice': 14, 'Intermediate': 61, 'Advanced': 127, 'Elite': 205},
    60: {'Beginner': 1, 'Novice': 15, 'Intermediate': 61, 'Advanced': 122, 'Elite': 197},
    65: {'Beginner': 1, 'Novice': 16, 'Intermediate': 60, 'Advanced': 119, 'Elite': 189},
    70: {'Beginner': 1, 'Novice': 16, 'Intermediate': 59, 'Advanced': 115, 'Elite': 181},
    75: {'Beginner': 1, 'Novice': 17, 'Intermediate': 58, 'Advanced': 111, 'Elite': 175},
    80: {'Beginner': 1, 'Novice': 17, 'Intermediate': 56, 'Advanced': 108, 'Elite': 169},
    85: {'Beginner': 1, 'Novice': 17, 'Intermediate': 55, 'Advanced': 105, 'Elite': 163},
    90: {'Beginner': 1, 'Novice': 17, 'Intermediate': 54, 'Advanced': 102, 'Elite': 157},
    95: {'Beginner': 1, 'Novice': 17, 'Intermediate': 53, 'Advanced': 99, 'Elite': 152},
    100: {'Beginner': 1, 'Novice': 17, 'Intermediate': 52, 'Advanced': 96, 'Elite': 148},
    105: {'Beginner': 1, 'Novice': 17, 'Intermediate': 51, 'Advanced': 94, 'Elite': 143},
    110: {'Beginner': 1, 'Novice': 17, 'Intermediate': 50, 'Advanced': 91, 'Elite': 139},
    115: {'Beginner': 1, 'Novice': 17, 'Intermediate': 49, 'Advanced': 89, 'Elite': 135},
    120: {'Beginner': 1, 'Novice': 16, 'Intermediate': 48, 'Advanced': 87, 'Elite': 132},
    125: {'Beginner': 1, 'Novice': 16, 'Intermediate': 47, 'Advanced': 85, 'Elite': 128},
    130: {'Beginner': 1, 'Novice': 16, 'Intermediate': 46, 'Advanced': 83, 'Elite': 125},
    135: {'Beginner': 1, 'Novice': 16, 'Intermediate': 45, 'Advanced': 81, 'Elite': 122},
    140: {'Beginner': 1, 'Novice': 15, 'Intermediate': 44, 'Advanced': 79, 'Elite': 119}
}

# Scraped on 2026-03-12
CHEST_PRESS_STANDARDS_KG = {
    50: {'Beginner': 17, 'Novice': 35, 'Intermediate': 59, 'Advanced': 90, 'Elite': 126},
    55: {'Beginner': 21, 'Novice': 39, 'Intermediate': 65, 'Advanced': 98, 'Elite': 135},
    60: {'Beginner': 24, 'Novice': 44, 'Intermediate': 71, 'Advanced': 105, 'Elite': 143},
    65: {'Beginner': 27, 'Novice': 48, 'Intermediate': 77, 'Advanced': 112, 'Elite': 151},
    70: {'Beginner': 31, 'Novice': 53, 'Intermediate': 82, 'Advanced': 118, 'Elite': 159},
    75: {'Beginner': 34, 'Novice': 57, 'Intermediate': 87, 'Advanced': 124, 'Elite': 166},
    80: {'Beginner': 37, 'Novice': 61, 'Intermediate': 92, 'Advanced': 130, 'Elite': 173},
    85: {'Beginner': 40, 'Novice': 65, 'Intermediate': 97, 'Advanced': 136, 'Elite': 179},
    90: {'Beginner': 43, 'Novice': 68, 'Intermediate': 102, 'Advanced': 142, 'Elite': 186},
    95: {'Beginner': 46, 'Novice': 72, 'Intermediate': 106, 'Advanced': 147, 'Elite': 192},
    100: {'Beginner': 49, 'Novice': 76, 'Intermediate': 111, 'Advanced': 152, 'Elite': 198},
    105: {'Beginner': 51, 'Novice': 79, 'Intermediate': 115, 'Advanced': 157, 'Elite': 203},
    110: {'Beginner': 54, 'Novice': 83, 'Intermediate': 119, 'Advanced': 162, 'Elite': 209},
    115: {'Beginner': 57, 'Novice': 86, 'Intermediate': 123, 'Advanced': 166, 'Elite': 214},
    120: {'Beginner': 60, 'Novice': 89, 'Intermediate': 127, 'Advanced': 171, 'Elite': 219},
    125: {'Beginner': 62, 'Novice': 92, 'Intermediate': 130, 'Advanced': 175, 'Elite': 224},
    130: {'Beginner': 65, 'Novice': 95, 'Intermediate': 134, 'Advanced': 179, 'Elite': 229},
    135: {'Beginner': 67, 'Novice': 98, 'Intermediate': 138, 'Advanced': 184, 'Elite': 233},
    140: {'Beginner': 70, 'Novice': 101, 'Intermediate': 141, 'Advanced': 188, 'Elite': 238}
}

# Scraped on 2026-03-12
CHIN_UPS_STANDARDS_KG = {
    50: {'Beginner': 1, 'Novice': 6, 'Intermediate': 15, 'Advanced': 26, 'Elite': 37},
    55: {'Beginner': 1, 'Novice': 7, 'Intermediate': 15, 'Advanced': 25, 'Elite': 36},
    60: {'Beginner': 1, 'Novice': 7, 'Intermediate': 15, 'Advanced': 25, 'Elite': 35},
    65: {'Beginner': 1, 'Novice': 7, 'Intermediate': 15, 'Advanced': 24, 'Elite': 34},
    70: {'Beginner': 1, 'Novice': 7, 'Intermediate': 14, 'Advanced': 23, 'Elite': 33},
    75: {'Beginner': 1, 'Novice': 7, 'Intermediate': 14, 'Advanced': 23, 'Elite': 32},
    80: {'Beginner': 1, 'Novice': 7, 'Intermediate': 14, 'Advanced': 22, 'Elite': 31},
    85: {'Beginner': 1, 'Novice': 7, 'Intermediate': 13, 'Advanced': 21, 'Elite': 29},
    90: {'Beginner': 1, 'Novice': 7, 'Intermediate': 13, 'Advanced': 20, 'Elite': 28},
    95: {'Beginner': 1, 'Novice': 6, 'Intermediate': 12, 'Advanced': 20, 'Elite': 27},
    100: {'Beginner': 1, 'Novice': 6, 'Intermediate': 12, 'Advanced': 19, 'Elite': 26},
    105: {'Beginner': 1, 'Novice': 6, 'Intermediate': 11, 'Advanced': 18, 'Elite': 26},
    110: {'Beginner': 1, 'Novice': 6, 'Intermediate': 11, 'Advanced': 18, 'Elite': 25},
    115: {'Beginner': 1, 'Novice': 5, 'Intermediate': 10, 'Advanced': 17, 'Elite': 24},
    120: {'Beginner': 1, 'Novice': 5, 'Intermediate': 10, 'Advanced': 16, 'Elite': 23},
    125: {'Beginner': 1, 'Novice': 5, 'Intermediate': 10, 'Advanced': 16, 'Elite': 22},
    130: {'Beginner': 1, 'Novice': 4, 'Intermediate': 9, 'Advanced': 15, 'Elite': 21},
    135: {'Beginner': 1, 'Novice': 4, 'Intermediate': 9, 'Advanced': 14, 'Elite': 21},
    140: {'Beginner': 1, 'Novice': 4, 'Intermediate': 9, 'Advanced': 14, 'Elite': 20}
}

# Scraped on 2026-03-12
CLEAN_STANDARDS_KG = {
    50: {'Beginner': 31, 'Novice': 45, 'Intermediate': 62, 'Advanced': 82, 'Elite': 103},
    55: {'Beginner': 35, 'Novice': 50, 'Intermediate': 68, 'Advanced': 89, 'Elite': 111},
    60: {'Beginner': 39, 'Novice': 55, 'Intermediate': 74, 'Advanced': 95, 'Elite': 118},
    65: {'Beginner': 44, 'Novice': 60, 'Intermediate': 79, 'Advanced': 101, 'Elite': 125},
    70: {'Beginner': 47, 'Novice': 64, 'Intermediate': 84, 'Advanced': 107, 'Elite': 132},
    75: {'Beginner': 51, 'Novice': 69, 'Intermediate': 89, 'Advanced': 113, 'Elite': 138},
    80: {'Beginner': 55, 'Novice': 73, 'Intermediate': 94, 'Advanced': 119, 'Elite': 144},
    85: {'Beginner': 59, 'Novice': 77, 'Intermediate': 99, 'Advanced': 124, 'Elite': 150},
    90: {'Beginner': 62, 'Novice': 81, 'Intermediate': 104, 'Advanced': 129, 'Elite': 156},
    95: {'Beginner': 66, 'Novice': 85, 'Intermediate': 108, 'Advanced': 134, 'Elite': 161},
    100: {'Beginner': 69, 'Novice': 89, 'Intermediate': 112, 'Advanced': 138, 'Elite': 166},
    105: {'Beginner': 72, 'Novice': 92, 'Intermediate': 116, 'Advanced': 143, 'Elite': 171},
    110: {'Beginner': 75, 'Novice': 96, 'Intermediate': 120, 'Advanced': 147, 'Elite': 176},
    115: {'Beginner': 78, 'Novice': 99, 'Intermediate': 124, 'Advanced': 152, 'Elite': 181},
    120: {'Beginner': 81, 'Novice': 103, 'Intermediate': 128, 'Advanced': 156, 'Elite': 185},
    125: {'Beginner': 84, 'Novice': 106, 'Intermediate': 132, 'Advanced': 160, 'Elite': 190},
    130: {'Beginner': 87, 'Novice': 109, 'Intermediate': 135, 'Advanced': 164, 'Elite': 194},
    135: {'Beginner': 90, 'Novice': 112, 'Intermediate': 139, 'Advanced': 168, 'Elite': 198},
    140: {'Beginner': 93, 'Novice': 115, 'Intermediate': 142, 'Advanced': 171, 'Elite': 202}
}

# Scraped on 2026-03-12
CLEAN_AND_JERK_STANDARDS_KG = {
    50: {'Beginner': 25, 'Novice': 41, 'Intermediate': 60, 'Advanced': 84, 'Elite': 110},
    55: {'Beginner': 29, 'Novice': 45, 'Intermediate': 66, 'Advanced': 91, 'Elite': 118},
    60: {'Beginner': 33, 'Novice': 50, 'Intermediate': 72, 'Advanced': 98, 'Elite': 126},
    65: {'Beginner': 37, 'Novice': 55, 'Intermediate': 77, 'Advanced': 104, 'Elite': 133},
    70: {'Beginner': 40, 'Novice': 59, 'Intermediate': 83, 'Advanced': 110, 'Elite': 140},
    75: {'Beginner': 44, 'Novice': 63, 'Intermediate': 88, 'Advanced': 116, 'Elite': 146},
    80: {'Beginner': 47, 'Novice': 67, 'Intermediate': 92, 'Advanced': 121, 'Elite': 152},
    85: {'Beginner': 51, 'Novice': 71, 'Intermediate': 97, 'Advanced': 126, 'Elite': 158},
    90: {'Beginner': 54, 'Novice': 75, 'Intermediate': 101, 'Advanced': 132, 'Elite': 164},
    95: {'Beginner': 57, 'Novice': 79, 'Intermediate': 106, 'Advanced': 136, 'Elite': 169},
    100: {'Beginner': 60, 'Novice': 83, 'Intermediate': 110, 'Advanced': 141, 'Elite': 175},
    105: {'Beginner': 63, 'Novice': 86, 'Intermediate': 114, 'Advanced': 146, 'Elite': 180},
    110: {'Beginner': 66, 'Novice': 90, 'Intermediate': 118, 'Advanced': 150, 'Elite': 185},
    115: {'Beginner': 69, 'Novice': 93, 'Intermediate': 122, 'Advanced': 155, 'Elite': 190},
    120: {'Beginner': 72, 'Novice': 96, 'Intermediate': 126, 'Advanced': 159, 'Elite': 194},
    125: {'Beginner': 75, 'Novice': 99, 'Intermediate': 129, 'Advanced': 163, 'Elite': 199},
    130: {'Beginner': 77, 'Novice': 102, 'Intermediate': 133, 'Advanced': 167, 'Elite': 203},
    135: {'Beginner': 80, 'Novice': 105, 'Intermediate': 136, 'Advanced': 171, 'Elite': 207},
    140: {'Beginner': 82, 'Novice': 108, 'Intermediate': 139, 'Advanced': 174, 'Elite': 211}
}

# Scraped on 2026-03-12
CLOSE_GRIP_BENCH_PRESS_STANDARDS_KG = {
    50: {'Beginner': 22, 'Novice': 35, 'Intermediate': 50, 'Advanced': 68, 'Elite': 88},
    55: {'Beginner': 28, 'Novice': 41, 'Intermediate': 57, 'Advanced': 77, 'Elite': 98},
    60: {'Beginner': 33, 'Novice': 47, 'Intermediate': 65, 'Advanced': 85, 'Elite': 107},
    65: {'Beginner': 38, 'Novice': 53, 'Intermediate': 72, 'Advanced': 93, 'Elite': 116},
    70: {'Beginner': 43, 'Novice': 59, 'Intermediate': 78, 'Advanced': 101, 'Elite': 125},
    75: {'Beginner': 48, 'Novice': 65, 'Intermediate': 85, 'Advanced': 108, 'Elite': 133},
    80: {'Beginner': 52, 'Novice': 70, 'Intermediate': 91, 'Advanced': 116, 'Elite': 141},
    85: {'Beginner': 57, 'Novice': 76, 'Intermediate': 98, 'Advanced': 123, 'Elite': 149},
    90: {'Beginner': 62, 'Novice': 81, 'Intermediate': 104, 'Advanced': 129, 'Elite': 157},
    95: {'Beginner': 67, 'Novice': 86, 'Intermediate': 110, 'Advanced': 136, 'Elite': 164},
    100: {'Beginner': 71, 'Novice': 92, 'Intermediate': 116, 'Advanced': 143, 'Elite': 171},
    105: {'Beginner': 76, 'Novice': 97, 'Intermediate': 121, 'Advanced': 149, 'Elite': 178},
    110: {'Beginner': 80, 'Novice': 101, 'Intermediate': 127, 'Advanced': 155, 'Elite': 184},
    115: {'Beginner': 84, 'Novice': 106, 'Intermediate': 132, 'Advanced': 161, 'Elite': 191},
    120: {'Beginner': 88, 'Novice': 111, 'Intermediate': 137, 'Advanced': 167, 'Elite': 197},
    125: {'Beginner': 93, 'Novice': 116, 'Intermediate': 143, 'Advanced': 172, 'Elite': 203},
    130: {'Beginner': 97, 'Novice': 120, 'Intermediate': 148, 'Advanced': 178, 'Elite': 209},
    135: {'Beginner': 101, 'Novice': 125, 'Intermediate': 153, 'Advanced': 183, 'Elite': 215},
    140: {'Beginner': 105, 'Novice': 129, 'Intermediate': 157, 'Advanced': 189, 'Elite': 221}
}

# Scraped on 2026-03-12
CRUNCHES_STANDARDS_KG = {
    50: {'Beginner': 1, 'Novice': 15, 'Intermediate': 57, 'Advanced': 111, 'Elite': 176},
    55: {'Beginner': 1, 'Novice': 17, 'Intermediate': 57, 'Advanced': 109, 'Elite': 170},
    60: {'Beginner': 1, 'Novice': 19, 'Intermediate': 57, 'Advanced': 106, 'Elite': 164},
    65: {'Beginner': 1, 'Novice': 20, 'Intermediate': 57, 'Advanced': 104, 'Elite': 158},
    70: {'Beginner': 1, 'Novice': 20, 'Intermediate': 56, 'Advanced': 101, 'Elite': 153},
    75: {'Beginner': 1, 'Novice': 21, 'Intermediate': 55, 'Advanced': 99, 'Elite': 148},
    80: {'Beginner': 1, 'Novice': 21, 'Intermediate': 55, 'Advanced': 96, 'Elite': 144},
    85: {'Beginner': 1, 'Novice': 21, 'Intermediate': 54, 'Advanced': 94, 'Elite': 139},
    90: {'Beginner': 1, 'Novice': 22, 'Intermediate': 53, 'Advanced': 91, 'Elite': 135},
    95: {'Beginner': 1, 'Novice': 22, 'Intermediate': 52, 'Advanced': 89, 'Elite': 131},
    100: {'Beginner': 1, 'Novice': 22, 'Intermediate': 51, 'Advanced': 87, 'Elite': 128},
    105: {'Beginner': 1, 'Novice': 21, 'Intermediate': 50, 'Advanced': 85, 'Elite': 124},
    110: {'Beginner': 1, 'Novice': 21, 'Intermediate': 49, 'Advanced': 83, 'Elite': 121},
    115: {'Beginner': 2, 'Novice': 21, 'Intermediate': 48, 'Advanced': 81, 'Elite': 118},
    120: {'Beginner': 2, 'Novice': 21, 'Intermediate': 47, 'Advanced': 79, 'Elite': 115},
    125: {'Beginner': 2, 'Novice': 21, 'Intermediate': 46, 'Advanced': 78, 'Elite': 112},
    130: {'Beginner': 2, 'Novice': 20, 'Intermediate': 46, 'Advanced': 76, 'Elite': 110},
    135: {'Beginner': 2, 'Novice': 20, 'Intermediate': 45, 'Advanced': 74, 'Elite': 107},
    140: {'Beginner': 3, 'Novice': 20, 'Intermediate': 44, 'Advanced': 73, 'Elite': 105}
}

# Scraped on 2026-03-12
DECLINE_BENCH_PRESS_STANDARDS_KG = {
    50: {'Beginner': 24, 'Novice': 39, 'Intermediate': 58, 'Advanced': 82, 'Elite': 107},
    55: {'Beginner': 30, 'Novice': 46, 'Intermediate': 67, 'Advanced': 91, 'Elite': 119},
    60: {'Beginner': 35, 'Novice': 52, 'Intermediate': 75, 'Advanced': 101, 'Elite': 129},
    65: {'Beginner': 40, 'Novice': 59, 'Intermediate': 82, 'Advanced': 110, 'Elite': 139},
    70: {'Beginner': 46, 'Novice': 66, 'Intermediate': 90, 'Advanced': 118, 'Elite': 149},
    75: {'Beginner': 51, 'Novice': 72, 'Intermediate': 97, 'Advanced': 127, 'Elite': 159},
    80: {'Beginner': 56, 'Novice': 78, 'Intermediate': 105, 'Advanced': 135, 'Elite': 168},
    85: {'Beginner': 61, 'Novice': 84, 'Intermediate': 112, 'Advanced': 143, 'Elite': 177},
    90: {'Beginner': 66, 'Novice': 90, 'Intermediate': 118, 'Advanced': 151, 'Elite': 185},
    95: {'Beginner': 71, 'Novice': 96, 'Intermediate': 125, 'Advanced': 158, 'Elite': 193},
    100: {'Beginner': 76, 'Novice': 101, 'Intermediate': 131, 'Advanced': 165, 'Elite': 201},
    105: {'Beginner': 81, 'Novice': 107, 'Intermediate': 137, 'Advanced': 172, 'Elite': 209},
    110: {'Beginner': 86, 'Novice': 112, 'Intermediate': 144, 'Advanced': 179, 'Elite': 216},
    115: {'Beginner': 90, 'Novice': 117, 'Intermediate': 150, 'Advanced': 186, 'Elite': 224},
    120: {'Beginner': 95, 'Novice': 122, 'Intermediate': 155, 'Advanced': 192, 'Elite': 231},
    125: {'Beginner': 99, 'Novice': 128, 'Intermediate': 161, 'Advanced': 198, 'Elite': 238},
    130: {'Beginner': 104, 'Novice': 132, 'Intermediate': 167, 'Advanced': 204, 'Elite': 244},
    135: {'Beginner': 108, 'Novice': 137, 'Intermediate': 172, 'Advanced': 210, 'Elite': 251},
    140: {'Beginner': 112, 'Novice': 142, 'Intermediate': 177, 'Advanced': 216, 'Elite': 257}
}

# Scraped on 2026-03-12
DIAMOND_PUSH_UPS_STANDARDS_KG = {
    50: {'Beginner': 1, 'Novice': 6, 'Intermediate': 21, 'Advanced': 41, 'Elite': 63},
    55: {'Beginner': 1, 'Novice': 7, 'Intermediate': 22, 'Advanced': 41, 'Elite': 62},
    60: {'Beginner': 1, 'Novice': 8, 'Intermediate': 23, 'Advanced': 41, 'Elite': 61},
    65: {'Beginner': 1, 'Novice': 9, 'Intermediate': 23, 'Advanced': 41, 'Elite': 60},
    70: {'Beginner': 1, 'Novice': 9, 'Intermediate': 24, 'Advanced': 41, 'Elite': 59},
    75: {'Beginner': 1, 'Novice': 10, 'Intermediate': 24, 'Advanced': 40, 'Elite': 58},
    80: {'Beginner': 1, 'Novice': 10, 'Intermediate': 24, 'Advanced': 40, 'Elite': 57},
    85: {'Beginner': 1, 'Novice': 10, 'Intermediate': 24, 'Advanced': 39, 'Elite': 55},
    90: {'Beginner': 1, 'Novice': 11, 'Intermediate': 24, 'Advanced': 38, 'Elite': 54},
    95: {'Beginner': 1, 'Novice': 11, 'Intermediate': 23, 'Advanced': 38, 'Elite': 53},
    100: {'Beginner': 2, 'Novice': 11, 'Intermediate': 23, 'Advanced': 37, 'Elite': 52},
    105: {'Beginner': 2, 'Novice': 11, 'Intermediate': 23, 'Advanced': 36, 'Elite': 51},
    110: {'Beginner': 2, 'Novice': 11, 'Intermediate': 22, 'Advanced': 36, 'Elite': 50},
    115: {'Beginner': 2, 'Novice': 11, 'Intermediate': 22, 'Advanced': 35, 'Elite': 48},
    120: {'Beginner': 2, 'Novice': 11, 'Intermediate': 22, 'Advanced': 34, 'Elite': 47},
    125: {'Beginner': 2, 'Novice': 10, 'Intermediate': 21, 'Advanced': 33, 'Elite': 46},
    130: {'Beginner': 2, 'Novice': 10, 'Intermediate': 21, 'Advanced': 33, 'Elite': 45},
    135: {'Beginner': 2, 'Novice': 10, 'Intermediate': 20, 'Advanced': 32, 'Elite': 44},
    140: {'Beginner': 2, 'Novice': 10, 'Intermediate': 20, 'Advanced': 31, 'Elite': 43}
}

# Scraped on 2026-03-12
DIPS_STANDARDS_KG = {
    50: {'Beginner': 1, 'Novice': 7, 'Intermediate': 19, 'Advanced': 34, 'Elite': 50},
    55: {'Beginner': 1, 'Novice': 8, 'Intermediate': 20, 'Advanced': 34, 'Elite': 50},
    60: {'Beginner': 1, 'Novice': 9, 'Intermediate': 20, 'Advanced': 34, 'Elite': 49},
    65: {'Beginner': 1, 'Novice': 9, 'Intermediate': 20, 'Advanced': 33, 'Elite': 47},
    70: {'Beginner': 1, 'Novice': 9, 'Intermediate': 20, 'Advanced': 33, 'Elite': 46},
    75: {'Beginner': 1, 'Novice': 10, 'Intermediate': 20, 'Advanced': 32, 'Elite': 45},
    80: {'Beginner': 1, 'Novice': 10, 'Intermediate': 20, 'Advanced': 32, 'Elite': 44},
    85: {'Beginner': 2, 'Novice': 10, 'Intermediate': 20, 'Advanced': 31, 'Elite': 43},
    90: {'Beginner': 2, 'Novice': 10, 'Intermediate': 19, 'Advanced': 30, 'Elite': 42},
    95: {'Beginner': 2, 'Novice': 10, 'Intermediate': 19, 'Advanced': 29, 'Elite': 41},
    100: {'Beginner': 2, 'Novice': 9, 'Intermediate': 18, 'Advanced': 29, 'Elite': 40},
    105: {'Beginner': 2, 'Novice': 9, 'Intermediate': 18, 'Advanced': 28, 'Elite': 39},
    110: {'Beginner': 2, 'Novice': 9, 'Intermediate': 18, 'Advanced': 27, 'Elite': 38},
    115: {'Beginner': 2, 'Novice': 9, 'Intermediate': 17, 'Advanced': 27, 'Elite': 37},
    120: {'Beginner': 2, 'Novice': 9, 'Intermediate': 17, 'Advanced': 26, 'Elite': 36},
    125: {'Beginner': 2, 'Novice': 9, 'Intermediate': 16, 'Advanced': 25, 'Elite': 35},
    130: {'Beginner': 2, 'Novice': 9, 'Intermediate': 16, 'Advanced': 25, 'Elite': 34},
    135: {'Beginner': 2, 'Novice': 8, 'Intermediate': 15, 'Advanced': 24, 'Elite': 33},
    140: {'Beginner': 2, 'Novice': 8, 'Intermediate': 15, 'Advanced': 23, 'Elite': 32}
}

# Scraped on 2026-03-12
DUMBBELL_BULGARIAN_SPLIT_SQUAT_STANDARDS_KG = {
    50: {'Beginner': 5, 'Novice': 11, 'Intermediate': 20, 'Advanced': 31, 'Elite': 45},
    55: {'Beginner': 6, 'Novice': 13, 'Intermediate': 22, 'Advanced': 34, 'Elite': 48},
    60: {'Beginner': 7, 'Novice': 14, 'Intermediate': 24, 'Advanced': 37, 'Elite': 51},
    65: {'Beginner': 8, 'Novice': 16, 'Intermediate': 26, 'Advanced': 39, 'Elite': 54},
    70: {'Beginner': 9, 'Novice': 17, 'Intermediate': 28, 'Advanced': 41, 'Elite': 56},
    75: {'Beginner': 10, 'Novice': 19, 'Intermediate': 30, 'Advanced': 43, 'Elite': 59},
    80: {'Beginner': 12, 'Novice': 20, 'Intermediate': 31, 'Advanced': 45, 'Elite': 61},
    85: {'Beginner': 13, 'Novice': 21, 'Intermediate': 33, 'Advanced': 47, 'Elite': 63},
    90: {'Beginner': 14, 'Novice': 23, 'Intermediate': 35, 'Advanced': 49, 'Elite': 66},
    95: {'Beginner': 14, 'Novice': 24, 'Intermediate': 36, 'Advanced': 51, 'Elite': 68},
    100: {'Beginner': 15, 'Novice': 25, 'Intermediate': 38, 'Advanced': 53, 'Elite': 70},
    105: {'Beginner': 16, 'Novice': 26, 'Intermediate': 39, 'Advanced': 55, 'Elite': 72},
    110: {'Beginner': 17, 'Novice': 27, 'Intermediate': 41, 'Advanced': 56, 'Elite': 74},
    115: {'Beginner': 18, 'Novice': 29, 'Intermediate': 42, 'Advanced': 58, 'Elite': 76},
    120: {'Beginner': 19, 'Novice': 30, 'Intermediate': 43, 'Advanced': 59, 'Elite': 77},
    125: {'Beginner': 20, 'Novice': 31, 'Intermediate': 45, 'Advanced': 61, 'Elite': 79},
    130: {'Beginner': 21, 'Novice': 32, 'Intermediate': 46, 'Advanced': 62, 'Elite': 81},
    135: {'Beginner': 22, 'Novice': 33, 'Intermediate': 47, 'Advanced': 64, 'Elite': 82},
    140: {'Beginner': 22, 'Novice': 34, 'Intermediate': 48, 'Advanced': 65, 'Elite': 84}
}

# Scraped on 2026-03-12
DUMBBELL_CURL_STANDARDS_KG = {
    50: {'Beginner': 3, 'Novice': 8, 'Intermediate': 16, 'Advanced': 27, 'Elite': 39},
    55: {'Beginner': 4, 'Novice': 9, 'Intermediate': 18, 'Advanced': 29, 'Elite': 42},
    60: {'Beginner': 5, 'Novice': 10, 'Intermediate': 19, 'Advanced': 30, 'Elite': 44},
    65: {'Beginner': 5, 'Novice': 11, 'Intermediate': 21, 'Advanced': 32, 'Elite': 46},
    70: {'Beginner': 6, 'Novice': 12, 'Intermediate': 22, 'Advanced': 34, 'Elite': 48},
    75: {'Beginner': 7, 'Novice': 13, 'Intermediate': 23, 'Advanced': 35, 'Elite': 50},
    80: {'Beginner': 7, 'Novice': 14, 'Intermediate': 24, 'Advanced': 37, 'Elite': 51},
    85: {'Beginner': 8, 'Novice': 15, 'Intermediate': 26, 'Advanced': 38, 'Elite': 53},
    90: {'Beginner': 9, 'Novice': 16, 'Intermediate': 27, 'Advanced': 40, 'Elite': 55},
    95: {'Beginner': 9, 'Novice': 17, 'Intermediate': 28, 'Advanced': 41, 'Elite': 56},
    100: {'Beginner': 10, 'Novice': 18, 'Intermediate': 29, 'Advanced': 42, 'Elite': 58},
    105: {'Beginner': 10, 'Novice': 19, 'Intermediate': 30, 'Advanced': 44, 'Elite': 59},
    110: {'Beginner': 11, 'Novice': 19, 'Intermediate': 31, 'Advanced': 45, 'Elite': 61},
    115: {'Beginner': 12, 'Novice': 20, 'Intermediate': 32, 'Advanced': 46, 'Elite': 62},
    120: {'Beginner': 12, 'Novice': 21, 'Intermediate': 33, 'Advanced': 47, 'Elite': 63},
    125: {'Beginner': 13, 'Novice': 22, 'Intermediate': 34, 'Advanced': 48, 'Elite': 65},
    130: {'Beginner': 13, 'Novice': 22, 'Intermediate': 34, 'Advanced': 49, 'Elite': 66},
    135: {'Beginner': 14, 'Novice': 23, 'Intermediate': 35, 'Advanced': 50, 'Elite': 67},
    140: {'Beginner': 14, 'Novice': 24, 'Intermediate': 36, 'Advanced': 51, 'Elite': 68}
}

# Scraped on 2026-03-12
DUMBBELL_FLY_STANDARDS_KG = {
    50: {'Beginner': 3, 'Novice': 7, 'Intermediate': 15, 'Advanced': 26, 'Elite': 38},
    55: {'Beginner': 3, 'Novice': 9, 'Intermediate': 17, 'Advanced': 28, 'Elite': 41},
    60: {'Beginner': 4, 'Novice': 10, 'Intermediate': 18, 'Advanced': 30, 'Elite': 43},
    65: {'Beginner': 5, 'Novice': 11, 'Intermediate': 20, 'Advanced': 32, 'Elite': 46},
    70: {'Beginner': 6, 'Novice': 12, 'Intermediate': 22, 'Advanced': 34, 'Elite': 48},
    75: {'Beginner': 6, 'Novice': 13, 'Intermediate': 23, 'Advanced': 36, 'Elite': 50},
    80: {'Beginner': 7, 'Novice': 14, 'Intermediate': 24, 'Advanced': 37, 'Elite': 52},
    85: {'Beginner': 8, 'Novice': 15, 'Intermediate': 26, 'Advanced': 39, 'Elite': 54},
    90: {'Beginner': 8, 'Novice': 16, 'Intermediate': 27, 'Advanced': 41, 'Elite': 56},
    95: {'Beginner': 9, 'Novice': 17, 'Intermediate': 28, 'Advanced': 42, 'Elite': 58},
    100: {'Beginner': 10, 'Novice': 18, 'Intermediate': 29, 'Advanced': 44, 'Elite': 60},
    105: {'Beginner': 11, 'Novice': 19, 'Intermediate': 31, 'Advanced': 45, 'Elite': 61},
    110: {'Beginner': 11, 'Novice': 20, 'Intermediate': 32, 'Advanced': 46, 'Elite': 63},
    115: {'Beginner': 12, 'Novice': 21, 'Intermediate': 33, 'Advanced': 48, 'Elite': 64},
    120: {'Beginner': 13, 'Novice': 22, 'Intermediate': 34, 'Advanced': 49, 'Elite': 66},
    125: {'Beginner': 13, 'Novice': 23, 'Intermediate': 35, 'Advanced': 50, 'Elite': 67},
    130: {'Beginner': 14, 'Novice': 23, 'Intermediate': 36, 'Advanced': 52, 'Elite': 69},
    135: {'Beginner': 14, 'Novice': 24, 'Intermediate': 37, 'Advanced': 53, 'Elite': 70},
    140: {'Beginner': 15, 'Novice': 25, 'Intermediate': 38, 'Advanced': 54, 'Elite': 72}
}

# Scraped on 2026-03-12
DUMBBELL_LATERAL_RAISE_STANDARDS_KG = {
    50: {'Beginner': 1, 'Novice': 5, 'Intermediate': 10, 'Advanced': 18, 'Elite': 27},
    55: {'Beginner': 2, 'Novice': 6, 'Intermediate': 11, 'Advanced': 19, 'Elite': 29},
    60: {'Beginner': 2, 'Novice': 6, 'Intermediate': 12, 'Advanced': 20, 'Elite': 30},
    65: {'Beginner': 3, 'Novice': 7, 'Intermediate': 13, 'Advanced': 22, 'Elite': 32},
    70: {'Beginner': 3, 'Novice': 8, 'Intermediate': 14, 'Advanced': 23, 'Elite': 33},
    75: {'Beginner': 4, 'Novice': 8, 'Intermediate': 15, 'Advanced': 24, 'Elite': 34},
    80: {'Beginner': 4, 'Novice': 9, 'Intermediate': 16, 'Advanced': 25, 'Elite': 36},
    85: {'Beginner': 4, 'Novice': 10, 'Intermediate': 17, 'Advanced': 26, 'Elite': 37},
    90: {'Beginner': 5, 'Novice': 10, 'Intermediate': 18, 'Advanced': 27, 'Elite': 38},
    95: {'Beginner': 5, 'Novice': 11, 'Intermediate': 18, 'Advanced': 28, 'Elite': 39},
    100: {'Beginner': 6, 'Novice': 11, 'Intermediate': 19, 'Advanced': 29, 'Elite': 40},
    105: {'Beginner': 6, 'Novice': 12, 'Intermediate': 20, 'Advanced': 30, 'Elite': 41},
    110: {'Beginner': 7, 'Novice': 12, 'Intermediate': 21, 'Advanced': 31, 'Elite': 42},
    115: {'Beginner': 7, 'Novice': 13, 'Intermediate': 21, 'Advanced': 32, 'Elite': 43},
    120: {'Beginner': 7, 'Novice': 13, 'Intermediate': 22, 'Advanced': 32, 'Elite': 44},
    125: {'Beginner': 8, 'Novice': 14, 'Intermediate': 23, 'Advanced': 33, 'Elite': 45},
    130: {'Beginner': 8, 'Novice': 14, 'Intermediate': 23, 'Advanced': 34, 'Elite': 46},
    135: {'Beginner': 8, 'Novice': 15, 'Intermediate': 24, 'Advanced': 35, 'Elite': 47},
    140: {'Beginner': 9, 'Novice': 15, 'Intermediate': 24, 'Advanced': 35, 'Elite': 48}
}

# Scraped on 2026-03-12
DUMBBELL_ROW_STANDARDS_KG = {
    50: {'Beginner': 7, 'Novice': 15, 'Intermediate': 25, 'Advanced': 39, 'Elite': 55},
    55: {'Beginner': 9, 'Novice': 17, 'Intermediate': 29, 'Advanced': 43, 'Elite': 59},
    60: {'Beginner': 11, 'Novice': 20, 'Intermediate': 32, 'Advanced': 47, 'Elite': 64},
    65: {'Beginner': 13, 'Novice': 22, 'Intermediate': 35, 'Advanced': 51, 'Elite': 68},
    70: {'Beginner': 15, 'Novice': 25, 'Intermediate': 38, 'Advanced': 54, 'Elite': 73},
    75: {'Beginner': 17, 'Novice': 27, 'Intermediate': 41, 'Advanced': 58, 'Elite': 77},
    80: {'Beginner': 18, 'Novice': 30, 'Intermediate': 44, 'Advanced': 61, 'Elite': 81},
    85: {'Beginner': 20, 'Novice': 32, 'Intermediate': 47, 'Advanced': 65, 'Elite': 84},
    90: {'Beginner': 22, 'Novice': 34, 'Intermediate': 49, 'Advanced': 68, 'Elite': 88},
    95: {'Beginner': 24, 'Novice': 36, 'Intermediate': 52, 'Advanced': 71, 'Elite': 91},
    100: {'Beginner': 25, 'Novice': 38, 'Intermediate': 55, 'Advanced': 74, 'Elite': 95},
    105: {'Beginner': 27, 'Novice': 40, 'Intermediate': 57, 'Advanced': 77, 'Elite': 98},
    110: {'Beginner': 29, 'Novice': 42, 'Intermediate': 59, 'Advanced': 79, 'Elite': 101},
    115: {'Beginner': 30, 'Novice': 44, 'Intermediate': 62, 'Advanced': 82, 'Elite': 104},
    120: {'Beginner': 32, 'Novice': 46, 'Intermediate': 64, 'Advanced': 85, 'Elite': 107},
    125: {'Beginner': 34, 'Novice': 48, 'Intermediate': 66, 'Advanced': 87, 'Elite': 110},
    130: {'Beginner': 35, 'Novice': 50, 'Intermediate': 68, 'Advanced': 90, 'Elite': 113},
    135: {'Beginner': 37, 'Novice': 52, 'Intermediate': 71, 'Advanced': 92, 'Elite': 115},
    140: {'Beginner': 38, 'Novice': 54, 'Intermediate': 73, 'Advanced': 95, 'Elite': 118}
}

# Scraped on 2026-03-12
DUMBBELL_SHOULDER_PRESS_STANDARDS_KG = {
    50: {'Beginner': 6, 'Novice': 11, 'Intermediate': 19, 'Advanced': 28, 'Elite': 38},
    55: {'Beginner': 8, 'Novice': 13, 'Intermediate': 21, 'Advanced': 31, 'Elite': 42},
    60: {'Beginner': 9, 'Novice': 15, 'Intermediate': 24, 'Advanced': 34, 'Elite': 46},
    65: {'Beginner': 11, 'Novice': 17, 'Intermediate': 26, 'Advanced': 37, 'Elite': 49},
    70: {'Beginner': 12, 'Novice': 19, 'Intermediate': 29, 'Advanced': 40, 'Elite': 52},
    75: {'Beginner': 14, 'Novice': 21, 'Intermediate': 31, 'Advanced': 42, 'Elite': 55},
    80: {'Beginner': 15, 'Novice': 23, 'Intermediate': 33, 'Advanced': 45, 'Elite': 58},
    85: {'Beginner': 16, 'Novice': 25, 'Intermediate': 35, 'Advanced': 47, 'Elite': 61},
    90: {'Beginner': 18, 'Novice': 26, 'Intermediate': 37, 'Advanced': 50, 'Elite': 64},
    95: {'Beginner': 19, 'Novice': 28, 'Intermediate': 39, 'Advanced': 52, 'Elite': 66},
    100: {'Beginner': 21, 'Novice': 30, 'Intermediate': 41, 'Advanced': 54, 'Elite': 69},
    105: {'Beginner': 22, 'Novice': 31, 'Intermediate': 43, 'Advanced': 57, 'Elite': 71},
    110: {'Beginner': 23, 'Novice': 33, 'Intermediate': 45, 'Advanced': 59, 'Elite': 74},
    115: {'Beginner': 25, 'Novice': 35, 'Intermediate': 47, 'Advanced': 61, 'Elite': 76},
    120: {'Beginner': 26, 'Novice': 36, 'Intermediate': 49, 'Advanced': 63, 'Elite': 78},
    125: {'Beginner': 27, 'Novice': 38, 'Intermediate': 50, 'Advanced': 65, 'Elite': 80},
    130: {'Beginner': 29, 'Novice': 39, 'Intermediate': 52, 'Advanced': 67, 'Elite': 83},
    135: {'Beginner': 30, 'Novice': 41, 'Intermediate': 54, 'Advanced': 69, 'Elite': 85},
    140: {'Beginner': 31, 'Novice': 42, 'Intermediate': 55, 'Advanced': 70, 'Elite': 87}
}

# Scraped on 2026-03-12
DUMBBELL_SHRUG_STANDARDS_KG = {
    50: {'Beginner': 6, 'Novice': 15, 'Intermediate': 28, 'Advanced': 45, 'Elite': 65},
    55: {'Beginner': 8, 'Novice': 17, 'Intermediate': 31, 'Advanced': 49, 'Elite': 70},
    60: {'Beginner': 10, 'Novice': 20, 'Intermediate': 35, 'Advanced': 54, 'Elite': 75},
    65: {'Beginner': 11, 'Novice': 22, 'Intermediate': 38, 'Advanced': 58, 'Elite': 80},
    70: {'Beginner': 13, 'Novice': 25, 'Intermediate': 41, 'Advanced': 61, 'Elite': 85},
    75: {'Beginner': 15, 'Novice': 27, 'Intermediate': 44, 'Advanced': 65, 'Elite': 89},
    80: {'Beginner': 17, 'Novice': 30, 'Intermediate': 47, 'Advanced': 69, 'Elite': 93},
    85: {'Beginner': 18, 'Novice': 32, 'Intermediate': 50, 'Advanced': 72, 'Elite': 97},
    90: {'Beginner': 20, 'Novice': 34, 'Intermediate': 53, 'Advanced': 75, 'Elite': 101},
    95: {'Beginner': 22, 'Novice': 36, 'Intermediate': 55, 'Advanced': 79, 'Elite': 105},
    100: {'Beginner': 23, 'Novice': 38, 'Intermediate': 58, 'Advanced': 82, 'Elite': 108},
    105: {'Beginner': 25, 'Novice': 40, 'Intermediate': 61, 'Advanced': 85, 'Elite': 112},
    110: {'Beginner': 27, 'Novice': 42, 'Intermediate': 63, 'Advanced': 88, 'Elite': 115},
    115: {'Beginner': 28, 'Novice': 44, 'Intermediate': 65, 'Advanced': 90, 'Elite': 118},
    120: {'Beginner': 30, 'Novice': 46, 'Intermediate': 68, 'Advanced': 93, 'Elite': 121},
    125: {'Beginner': 31, 'Novice': 48, 'Intermediate': 70, 'Advanced': 96, 'Elite': 124},
    130: {'Beginner': 33, 'Novice': 50, 'Intermediate': 72, 'Advanced': 99, 'Elite': 127},
    135: {'Beginner': 34, 'Novice': 52, 'Intermediate': 74, 'Advanced': 101, 'Elite': 130},
    140: {'Beginner': 36, 'Novice': 54, 'Intermediate': 77, 'Advanced': 104, 'Elite': 133}
}

# Scraped on 2026-03-12
EZ_BAR_CURL_STANDARDS_KG = {
    50: {'Beginner': 12, 'Novice': 20, 'Intermediate': 31, 'Advanced': 45, 'Elite': 61},
    55: {'Beginner': 14, 'Novice': 23, 'Intermediate': 34, 'Advanced': 49, 'Elite': 65},
    60: {'Beginner': 15, 'Novice': 25, 'Intermediate': 37, 'Advanced': 52, 'Elite': 69},
    65: {'Beginner': 17, 'Novice': 27, 'Intermediate': 40, 'Advanced': 55, 'Elite': 72},
    70: {'Beginner': 19, 'Novice': 29, 'Intermediate': 43, 'Advanced': 59, 'Elite': 76},
    75: {'Beginner': 21, 'Novice': 32, 'Intermediate': 45, 'Advanced': 62, 'Elite': 79},
    80: {'Beginner': 22, 'Novice': 34, 'Intermediate': 48, 'Advanced': 64, 'Elite': 83},
    85: {'Beginner': 24, 'Novice': 36, 'Intermediate': 50, 'Advanced': 67, 'Elite': 86},
    90: {'Beginner': 26, 'Novice': 38, 'Intermediate': 52, 'Advanced': 70, 'Elite': 89},
    95: {'Beginner': 27, 'Novice': 39, 'Intermediate': 55, 'Advanced': 72, 'Elite': 92},
    100: {'Beginner': 29, 'Novice': 41, 'Intermediate': 57, 'Advanced': 75, 'Elite': 94},
    105: {'Beginner': 30, 'Novice': 43, 'Intermediate': 59, 'Advanced': 77, 'Elite': 97},
    110: {'Beginner': 32, 'Novice': 45, 'Intermediate': 61, 'Advanced': 79, 'Elite': 100},
    115: {'Beginner': 33, 'Novice': 46, 'Intermediate': 63, 'Advanced': 82, 'Elite': 102},
    120: {'Beginner': 34, 'Novice': 48, 'Intermediate': 65, 'Advanced': 84, 'Elite': 104},
    125: {'Beginner': 36, 'Novice': 50, 'Intermediate': 67, 'Advanced': 86, 'Elite': 107},
    130: {'Beginner': 37, 'Novice': 51, 'Intermediate': 68, 'Advanced': 88, 'Elite': 109},
    135: {'Beginner': 38, 'Novice': 53, 'Intermediate': 70, 'Advanced': 90, 'Elite': 111},
    140: {'Beginner': 40, 'Novice': 54, 'Intermediate': 72, 'Advanced': 92, 'Elite': 113}
}

# Scraped on 2026-03-12
FRONT_SQUAT_STANDARDS_KG = {
    50: {'Beginner': 31, 'Novice': 46, 'Intermediate': 65, 'Advanced': 88, 'Elite': 113},
    55: {'Beginner': 35, 'Novice': 52, 'Intermediate': 73, 'Advanced': 97, 'Elite': 123},
    60: {'Beginner': 40, 'Novice': 58, 'Intermediate': 79, 'Advanced': 104, 'Elite': 132},
    65: {'Beginner': 45, 'Novice': 63, 'Intermediate': 86, 'Advanced': 112, 'Elite': 140},
    70: {'Beginner': 50, 'Novice': 69, 'Intermediate': 92, 'Advanced': 119, 'Elite': 148},
    75: {'Beginner': 54, 'Novice': 74, 'Intermediate': 98, 'Advanced': 126, 'Elite': 156},
    80: {'Beginner': 59, 'Novice': 79, 'Intermediate': 104, 'Advanced': 133, 'Elite': 163},
    85: {'Beginner': 63, 'Novice': 84, 'Intermediate': 110, 'Advanced': 139, 'Elite': 170},
    90: {'Beginner': 67, 'Novice': 89, 'Intermediate': 115, 'Advanced': 145, 'Elite': 177},
    95: {'Beginner': 71, 'Novice': 94, 'Intermediate': 121, 'Advanced': 151, 'Elite': 184},
    100: {'Beginner': 75, 'Novice': 98, 'Intermediate': 126, 'Advanced': 157, 'Elite': 190},
    105: {'Beginner': 79, 'Novice': 103, 'Intermediate': 131, 'Advanced': 163, 'Elite': 196},
    110: {'Beginner': 83, 'Novice': 107, 'Intermediate': 136, 'Advanced': 168, 'Elite': 202},
    115: {'Beginner': 86, 'Novice': 111, 'Intermediate': 141, 'Advanced': 173, 'Elite': 208},
    120: {'Beginner': 90, 'Novice': 115, 'Intermediate': 145, 'Advanced': 178, 'Elite': 213},
    125: {'Beginner': 94, 'Novice': 119, 'Intermediate': 150, 'Advanced': 183, 'Elite': 219},
    130: {'Beginner': 97, 'Novice': 123, 'Intermediate': 154, 'Advanced': 188, 'Elite': 224},
    135: {'Beginner': 100, 'Novice': 127, 'Intermediate': 158, 'Advanced': 193, 'Elite': 229},
    140: {'Beginner': 104, 'Novice': 131, 'Intermediate': 162, 'Advanced': 198, 'Elite': 234}
}

# Scraped on 2026-03-12
GOBLET_SQUAT_STANDARDS_KG = {
    50: {'Beginner': 8, 'Novice': 17, 'Intermediate': 30, 'Advanced': 48, 'Elite': 68},
    55: {'Beginner': 9, 'Novice': 19, 'Intermediate': 33, 'Advanced': 51, 'Elite': 72},
    60: {'Beginner': 10, 'Novice': 21, 'Intermediate': 35, 'Advanced': 54, 'Elite': 75},
    65: {'Beginner': 12, 'Novice': 22, 'Intermediate': 38, 'Advanced': 57, 'Elite': 79},
    70: {'Beginner': 13, 'Novice': 24, 'Intermediate': 40, 'Advanced': 60, 'Elite': 82},
    75: {'Beginner': 14, 'Novice': 26, 'Intermediate': 42, 'Advanced': 62, 'Elite': 85},
    80: {'Beginner': 15, 'Novice': 27, 'Intermediate': 44, 'Advanced': 65, 'Elite': 88},
    85: {'Beginner': 16, 'Novice': 29, 'Intermediate': 46, 'Advanced': 67, 'Elite': 90},
    90: {'Beginner': 17, 'Novice': 30, 'Intermediate': 48, 'Advanced': 69, 'Elite': 93},
    95: {'Beginner': 19, 'Novice': 32, 'Intermediate': 50, 'Advanced': 71, 'Elite': 96},
    100: {'Beginner': 20, 'Novice': 33, 'Intermediate': 51, 'Advanced': 73, 'Elite': 98},
    105: {'Beginner': 21, 'Novice': 35, 'Intermediate': 53, 'Advanced': 75, 'Elite': 100},
    110: {'Beginner': 22, 'Novice': 36, 'Intermediate': 55, 'Advanced': 77, 'Elite': 102},
    115: {'Beginner': 23, 'Novice': 37, 'Intermediate': 56, 'Advanced': 79, 'Elite': 105},
    120: {'Beginner': 24, 'Novice': 38, 'Intermediate': 58, 'Advanced': 81, 'Elite': 107},
    125: {'Beginner': 25, 'Novice': 40, 'Intermediate': 59, 'Advanced': 83, 'Elite': 109},
    130: {'Beginner': 25, 'Novice': 41, 'Intermediate': 61, 'Advanced': 84, 'Elite': 111},
    135: {'Beginner': 26, 'Novice': 42, 'Intermediate': 62, 'Advanced': 86, 'Elite': 113},
    140: {'Beginner': 27, 'Novice': 43, 'Intermediate': 63, 'Advanced': 88, 'Elite': 114}
}

# Scraped on 2026-03-12
HACK_SQUAT_STANDARDS_KG = {
    50: {'Beginner': 23, 'Novice': 51, 'Intermediate': 92, 'Advanced': 146, 'Elite': 209},
    55: {'Beginner': 28, 'Novice': 59, 'Intermediate': 104, 'Advanced': 161, 'Elite': 226},
    60: {'Beginner': 34, 'Novice': 68, 'Intermediate': 115, 'Advanced': 174, 'Elite': 242},
    65: {'Beginner': 40, 'Novice': 76, 'Intermediate': 125, 'Advanced': 187, 'Elite': 258},
    70: {'Beginner': 46, 'Novice': 84, 'Intermediate': 136, 'Advanced': 200, 'Elite': 272},
    75: {'Beginner': 52, 'Novice': 92, 'Intermediate': 146, 'Advanced': 212, 'Elite': 286},
    80: {'Beginner': 58, 'Novice': 100, 'Intermediate': 155, 'Advanced': 223, 'Elite': 300},
    85: {'Beginner': 64, 'Novice': 107, 'Intermediate': 165, 'Advanced': 234, 'Elite': 313},
    90: {'Beginner': 69, 'Novice': 114, 'Intermediate': 174, 'Advanced': 245, 'Elite': 325},
    95: {'Beginner': 75, 'Novice': 121, 'Intermediate': 182, 'Advanced': 256, 'Elite': 337},
    100: {'Beginner': 80, 'Novice': 128, 'Intermediate': 191, 'Advanced': 266, 'Elite': 348},
    105: {'Beginner': 86, 'Novice': 135, 'Intermediate': 199, 'Advanced': 275, 'Elite': 360},
    110: {'Beginner': 91, 'Novice': 142, 'Intermediate': 207, 'Advanced': 285, 'Elite': 370},
    115: {'Beginner': 96, 'Novice': 148, 'Intermediate': 215, 'Advanced': 294, 'Elite': 381},
    120: {'Beginner': 101, 'Novice': 155, 'Intermediate': 223, 'Advanced': 303, 'Elite': 391},
    125: {'Beginner': 106, 'Novice': 161, 'Intermediate': 230, 'Advanced': 312, 'Elite': 401},
    130: {'Beginner': 111, 'Novice': 167, 'Intermediate': 237, 'Advanced': 320, 'Elite': 410},
    135: {'Beginner': 116, 'Novice': 173, 'Intermediate': 244, 'Advanced': 328, 'Elite': 420},
    140: {'Beginner': 121, 'Novice': 179, 'Intermediate': 251, 'Advanced': 336, 'Elite': 429}
}

# Scraped on 2026-03-12
HAMMER_CURL_STANDARDS_KG = {
    50: {'Beginner': 4, 'Novice': 8, 'Intermediate': 14, 'Advanced': 22, 'Elite': 31},
    55: {'Beginner': 5, 'Novice': 9, 'Intermediate': 16, 'Advanced': 24, 'Elite': 33},
    60: {'Beginner': 6, 'Novice': 11, 'Intermediate': 17, 'Advanced': 26, 'Elite': 36},
    65: {'Beginner': 7, 'Novice': 12, 'Intermediate': 19, 'Advanced': 28, 'Elite': 38},
    70: {'Beginner': 8, 'Novice': 13, 'Intermediate': 21, 'Advanced': 30, 'Elite': 41},
    75: {'Beginner': 9, 'Novice': 15, 'Intermediate': 22, 'Advanced': 32, 'Elite': 43},
    80: {'Beginner': 10, 'Novice': 16, 'Intermediate': 24, 'Advanced': 34, 'Elite': 45},
    85: {'Beginner': 10, 'Novice': 17, 'Intermediate': 26, 'Advanced': 36, 'Elite': 47},
    90: {'Beginner': 11, 'Novice': 18, 'Intermediate': 27, 'Advanced': 38, 'Elite': 49},
    95: {'Beginner': 12, 'Novice': 19, 'Intermediate': 28, 'Advanced': 39, 'Elite': 51},
    100: {'Beginner': 13, 'Novice': 21, 'Intermediate': 30, 'Advanced': 41, 'Elite': 53},
    105: {'Beginner': 14, 'Novice': 22, 'Intermediate': 31, 'Advanced': 42, 'Elite': 55},
    110: {'Beginner': 15, 'Novice': 23, 'Intermediate': 32, 'Advanced': 44, 'Elite': 57},
    115: {'Beginner': 16, 'Novice': 24, 'Intermediate': 34, 'Advanced': 45, 'Elite': 58},
    120: {'Beginner': 17, 'Novice': 25, 'Intermediate': 35, 'Advanced': 47, 'Elite': 60},
    125: {'Beginner': 18, 'Novice': 26, 'Intermediate': 36, 'Advanced': 48, 'Elite': 61},
    130: {'Beginner': 18, 'Novice': 27, 'Intermediate': 37, 'Advanced': 50, 'Elite': 63},
    135: {'Beginner': 19, 'Novice': 28, 'Intermediate': 39, 'Advanced': 51, 'Elite': 65},
    140: {'Beginner': 20, 'Novice': 29, 'Intermediate': 40, 'Advanced': 52, 'Elite': 66}
}

# Scraped on 2026-03-12
HEX_BAR_DEADLIFT_STANDARDS_KG = {
    50: {'Beginner': 55, 'Novice': 78, 'Intermediate': 107, 'Advanced': 141, 'Elite': 178},
    55: {'Beginner': 62, 'Novice': 87, 'Intermediate': 118, 'Advanced': 154, 'Elite': 192},
    60: {'Beginner': 70, 'Novice': 96, 'Intermediate': 128, 'Advanced': 165, 'Elite': 205},
    65: {'Beginner': 77, 'Novice': 104, 'Intermediate': 138, 'Advanced': 176, 'Elite': 217},
    70: {'Beginner': 84, 'Novice': 112, 'Intermediate': 147, 'Advanced': 186, 'Elite': 228},
    75: {'Beginner': 90, 'Novice': 120, 'Intermediate': 156, 'Advanced': 196, 'Elite': 239},
    80: {'Beginner': 97, 'Novice': 128, 'Intermediate': 165, 'Advanced': 206, 'Elite': 250},
    85: {'Beginner': 103, 'Novice': 135, 'Intermediate': 173, 'Advanced': 215, 'Elite': 260},
    90: {'Beginner': 110, 'Novice': 142, 'Intermediate': 181, 'Advanced': 224, 'Elite': 270},
    95: {'Beginner': 116, 'Novice': 149, 'Intermediate': 189, 'Advanced': 233, 'Elite': 279},
    100: {'Beginner': 121, 'Novice': 156, 'Intermediate': 196, 'Advanced': 241, 'Elite': 288},
    105: {'Beginner': 127, 'Novice': 162, 'Intermediate': 203, 'Advanced': 249, 'Elite': 297},
    110: {'Beginner': 133, 'Novice': 168, 'Intermediate': 210, 'Advanced': 257, 'Elite': 306},
    115: {'Beginner': 138, 'Novice': 175, 'Intermediate': 217, 'Advanced': 264, 'Elite': 314},
    120: {'Beginner': 143, 'Novice': 180, 'Intermediate': 224, 'Advanced': 272, 'Elite': 322},
    125: {'Beginner': 149, 'Novice': 186, 'Intermediate': 230, 'Advanced': 279, 'Elite': 330},
    130: {'Beginner': 154, 'Novice': 192, 'Intermediate': 236, 'Advanced': 286, 'Elite': 337},
    135: {'Beginner': 159, 'Novice': 197, 'Intermediate': 243, 'Advanced': 292, 'Elite': 344},
    140: {'Beginner': 164, 'Novice': 203, 'Intermediate': 249, 'Advanced': 299, 'Elite': 351}
}

# Scraped on 2026-03-12
HIP_ADDUCTION_STANDARDS_KG = {
    50: {'Beginner': 16, 'Novice': 39, 'Intermediate': 74, 'Advanced': 121, 'Elite': 175},
    55: {'Beginner': 20, 'Novice': 44, 'Intermediate': 81, 'Advanced': 129, 'Elite': 186},
    60: {'Beginner': 23, 'Novice': 49, 'Intermediate': 88, 'Advanced': 138, 'Elite': 195},
    65: {'Beginner': 26, 'Novice': 54, 'Intermediate': 94, 'Advanced': 146, 'Elite': 205},
    70: {'Beginner': 29, 'Novice': 59, 'Intermediate': 100, 'Advanced': 153, 'Elite': 214},
    75: {'Beginner': 33, 'Novice': 63, 'Intermediate': 106, 'Advanced': 160, 'Elite': 222},
    80: {'Beginner': 36, 'Novice': 68, 'Intermediate': 112, 'Advanced': 167, 'Elite': 230},
    85: {'Beginner': 39, 'Novice': 72, 'Intermediate': 117, 'Advanced': 174, 'Elite': 238},
    90: {'Beginner': 42, 'Novice': 76, 'Intermediate': 122, 'Advanced': 180, 'Elite': 245},
    95: {'Beginner': 45, 'Novice': 80, 'Intermediate': 127, 'Advanced': 186, 'Elite': 252},
    100: {'Beginner': 48, 'Novice': 84, 'Intermediate': 132, 'Advanced': 192, 'Elite': 259},
    105: {'Beginner': 50, 'Novice': 87, 'Intermediate': 137, 'Advanced': 198, 'Elite': 266},
    110: {'Beginner': 53, 'Novice': 91, 'Intermediate': 141, 'Advanced': 203, 'Elite': 272},
    115: {'Beginner': 56, 'Novice': 95, 'Intermediate': 146, 'Advanced': 208, 'Elite': 278},
    120: {'Beginner': 59, 'Novice': 98, 'Intermediate': 150, 'Advanced': 213, 'Elite': 284},
    125: {'Beginner': 61, 'Novice': 101, 'Intermediate': 154, 'Advanced': 218, 'Elite': 290},
    130: {'Beginner': 64, 'Novice': 105, 'Intermediate': 158, 'Advanced': 223, 'Elite': 295},
    135: {'Beginner': 66, 'Novice': 108, 'Intermediate': 162, 'Advanced': 228, 'Elite': 301},
    140: {'Beginner': 69, 'Novice': 111, 'Intermediate': 166, 'Advanced': 232, 'Elite': 306}
}

# Scraped on 2026-03-12
HIP_THRUST_STANDARDS_KG = {
    50: {'Beginner': 15, 'Novice': 38, 'Intermediate': 73, 'Advanced': 120, 'Elite': 176},
    55: {'Beginner': 20, 'Novice': 46, 'Intermediate': 85, 'Advanced': 135, 'Elite': 194},
    60: {'Beginner': 26, 'Novice': 55, 'Intermediate': 96, 'Advanced': 149, 'Elite': 211},
    65: {'Beginner': 32, 'Novice': 63, 'Intermediate': 107, 'Advanced': 163, 'Elite': 227},
    70: {'Beginner': 38, 'Novice': 71, 'Intermediate': 118, 'Advanced': 176, 'Elite': 242},
    75: {'Beginner': 44, 'Novice': 79, 'Intermediate': 128, 'Advanced': 188, 'Elite': 257},
    80: {'Beginner': 50, 'Novice': 87, 'Intermediate': 138, 'Advanced': 201, 'Elite': 271},
    85: {'Beginner': 56, 'Novice': 95, 'Intermediate': 148, 'Advanced': 213, 'Elite': 285},
    90: {'Beginner': 61, 'Novice': 103, 'Intermediate': 158, 'Advanced': 224, 'Elite': 298},
    95: {'Beginner': 67, 'Novice': 110, 'Intermediate': 167, 'Advanced': 235, 'Elite': 311},
    100: {'Beginner': 73, 'Novice': 118, 'Intermediate': 176, 'Advanced': 246, 'Elite': 324},
    105: {'Beginner': 79, 'Novice': 125, 'Intermediate': 185, 'Advanced': 257, 'Elite': 336},
    110: {'Beginner': 85, 'Novice': 132, 'Intermediate': 194, 'Advanced': 267, 'Elite': 347},
    115: {'Beginner': 90, 'Novice': 139, 'Intermediate': 202, 'Advanced': 277, 'Elite': 359},
    120: {'Beginner': 96, 'Novice': 146, 'Intermediate': 211, 'Advanced': 286, 'Elite': 370},
    125: {'Beginner': 101, 'Novice': 153, 'Intermediate': 219, 'Advanced': 296, 'Elite': 380},
    130: {'Beginner': 107, 'Novice': 160, 'Intermediate': 227, 'Advanced': 305, 'Elite': 391},
    135: {'Beginner': 112, 'Novice': 166, 'Intermediate': 234, 'Advanced': 314, 'Elite': 401},
    140: {'Beginner': 118, 'Novice': 173, 'Intermediate': 242, 'Advanced': 323, 'Elite': 411}
}

# Scraped on 2026-03-12
HORIZONTAL_LEG_PRESS_STANDARDS_KG = {
    50: {'Beginner': 36, 'Novice': 72, 'Intermediate': 122, 'Advanced': 185, 'Elite': 258},
    55: {'Beginner': 44, 'Novice': 83, 'Intermediate': 136, 'Advanced': 202, 'Elite': 278},
    60: {'Beginner': 52, 'Novice': 93, 'Intermediate': 149, 'Advanced': 218, 'Elite': 297},
    65: {'Beginner': 59, 'Novice': 103, 'Intermediate': 162, 'Advanced': 234, 'Elite': 314},
    70: {'Beginner': 67, 'Novice': 113, 'Intermediate': 174, 'Advanced': 248, 'Elite': 331},
    75: {'Beginner': 74, 'Novice': 122, 'Intermediate': 186, 'Advanced': 262, 'Elite': 347},
    80: {'Beginner': 82, 'Novice': 132, 'Intermediate': 197, 'Advanced': 276, 'Elite': 363},
    85: {'Beginner': 89, 'Novice': 141, 'Intermediate': 208, 'Advanced': 289, 'Elite': 378},
    90: {'Beginner': 96, 'Novice': 149, 'Intermediate': 219, 'Advanced': 301, 'Elite': 392},
    95: {'Beginner': 102, 'Novice': 158, 'Intermediate': 229, 'Advanced': 313, 'Elite': 406},
    100: {'Beginner': 109, 'Novice': 166, 'Intermediate': 239, 'Advanced': 325, 'Elite': 419},
    105: {'Beginner': 116, 'Novice': 174, 'Intermediate': 249, 'Advanced': 336, 'Elite': 432},
    110: {'Beginner': 122, 'Novice': 182, 'Intermediate': 258, 'Advanced': 347, 'Elite': 444},
    115: {'Beginner': 129, 'Novice': 190, 'Intermediate': 267, 'Advanced': 358, 'Elite': 456},
    120: {'Beginner': 135, 'Novice': 198, 'Intermediate': 276, 'Advanced': 368, 'Elite': 468},
    125: {'Beginner': 141, 'Novice': 205, 'Intermediate': 285, 'Advanced': 378, 'Elite': 479},
    130: {'Beginner': 147, 'Novice': 212, 'Intermediate': 293, 'Advanced': 388, 'Elite': 490},
    135: {'Beginner': 153, 'Novice': 219, 'Intermediate': 302, 'Advanced': 397, 'Elite': 501},
    140: {'Beginner': 158, 'Novice': 226, 'Intermediate': 310, 'Advanced': 407, 'Elite': 511}
}

# Scraped on 2026-03-12
INCLINE_BENCH_PRESS_STANDARDS_KG = {
    50: {'Beginner': 22, 'Novice': 34, 'Intermediate': 49, 'Advanced': 67, 'Elite': 87},
    55: {'Beginner': 27, 'Novice': 40, 'Intermediate': 56, 'Advanced': 76, 'Elite': 97},
    60: {'Beginner': 32, 'Novice': 46, 'Intermediate': 63, 'Advanced': 83, 'Elite': 106},
    65: {'Beginner': 36, 'Novice': 51, 'Intermediate': 70, 'Advanced': 91, 'Elite': 114},
    70: {'Beginner': 41, 'Novice': 57, 'Intermediate': 76, 'Advanced': 98, 'Elite': 122},
    75: {'Beginner': 45, 'Novice': 62, 'Intermediate': 82, 'Advanced': 105, 'Elite': 130},
    80: {'Beginner': 50, 'Novice': 67, 'Intermediate': 88, 'Advanced': 112, 'Elite': 138},
    85: {'Beginner': 54, 'Novice': 73, 'Intermediate': 94, 'Advanced': 119, 'Elite': 145},
    90: {'Beginner': 59, 'Novice': 78, 'Intermediate': 100, 'Advanced': 125, 'Elite': 152},
    95: {'Beginner': 63, 'Novice': 82, 'Intermediate': 105, 'Advanced': 131, 'Elite': 159},
    100: {'Beginner': 67, 'Novice': 87, 'Intermediate': 111, 'Advanced': 137, 'Elite': 165},
    105: {'Beginner': 71, 'Novice': 92, 'Intermediate': 116, 'Advanced': 143, 'Elite': 172},
    110: {'Beginner': 75, 'Novice': 96, 'Intermediate': 121, 'Advanced': 149, 'Elite': 178},
    115: {'Beginner': 79, 'Novice': 101, 'Intermediate': 126, 'Advanced': 154, 'Elite': 184},
    120: {'Beginner': 83, 'Novice': 105, 'Intermediate': 131, 'Advanced': 160, 'Elite': 190},
    125: {'Beginner': 87, 'Novice': 110, 'Intermediate': 136, 'Advanced': 165, 'Elite': 196},
    130: {'Beginner': 91, 'Novice': 114, 'Intermediate': 141, 'Advanced': 170, 'Elite': 201},
    135: {'Beginner': 94, 'Novice': 118, 'Intermediate': 145, 'Advanced': 175, 'Elite': 207},
    140: {'Beginner': 98, 'Novice': 122, 'Intermediate': 150, 'Advanced': 180, 'Elite': 212}
}

# Scraped on 2026-03-12
INCLINE_DUMBBELL_BENCH_PRESS_STANDARDS_KG = {
    50: {'Beginner': 10, 'Novice': 16, 'Intermediate': 24, 'Advanced': 33, 'Elite': 44},
    55: {'Beginner': 12, 'Novice': 18, 'Intermediate': 27, 'Advanced': 37, 'Elite': 48},
    60: {'Beginner': 14, 'Novice': 21, 'Intermediate': 30, 'Advanced': 40, 'Elite': 51},
    65: {'Beginner': 16, 'Novice': 23, 'Intermediate': 32, 'Advanced': 43, 'Elite': 55},
    70: {'Beginner': 17, 'Novice': 25, 'Intermediate': 35, 'Advanced': 46, 'Elite': 59},
    75: {'Beginner': 19, 'Novice': 28, 'Intermediate': 38, 'Advanced': 49, 'Elite': 62},
    80: {'Beginner': 21, 'Novice': 30, 'Intermediate': 40, 'Advanced': 52, 'Elite': 65},
    85: {'Beginner': 23, 'Novice': 32, 'Intermediate': 43, 'Advanced': 55, 'Elite': 68},
    90: {'Beginner': 25, 'Novice': 34, 'Intermediate': 45, 'Advanced': 58, 'Elite': 71},
    95: {'Beginner': 26, 'Novice': 36, 'Intermediate': 47, 'Advanced': 60, 'Elite': 74},
    100: {'Beginner': 28, 'Novice': 38, 'Intermediate': 49, 'Advanced': 63, 'Elite': 77},
    105: {'Beginner': 30, 'Novice': 40, 'Intermediate': 52, 'Advanced': 65, 'Elite': 80},
    110: {'Beginner': 31, 'Novice': 42, 'Intermediate': 54, 'Advanced': 68, 'Elite': 82},
    115: {'Beginner': 33, 'Novice': 43, 'Intermediate': 56, 'Advanced': 70, 'Elite': 85},
    120: {'Beginner': 34, 'Novice': 45, 'Intermediate': 58, 'Advanced': 72, 'Elite': 87},
    125: {'Beginner': 36, 'Novice': 47, 'Intermediate': 60, 'Advanced': 74, 'Elite': 90},
    130: {'Beginner': 37, 'Novice': 49, 'Intermediate': 62, 'Advanced': 76, 'Elite': 92},
    135: {'Beginner': 39, 'Novice': 50, 'Intermediate': 64, 'Advanced': 79, 'Elite': 94},
    140: {'Beginner': 40, 'Novice': 52, 'Intermediate': 65, 'Advanced': 81, 'Elite': 96}
}

# Scraped on 2026-03-12
LAT_PULLDOWN_STANDARDS_KG = {
    50: {'Beginner': 25, 'Novice': 39, 'Intermediate': 58, 'Advanced': 81, 'Elite': 105},
    55: {'Beginner': 28, 'Novice': 43, 'Intermediate': 63, 'Advanced': 86, 'Elite': 112},
    60: {'Beginner': 31, 'Novice': 47, 'Intermediate': 67, 'Advanced': 92, 'Elite': 118},
    65: {'Beginner': 34, 'Novice': 51, 'Intermediate': 72, 'Advanced': 97, 'Elite': 124},
    70: {'Beginner': 37, 'Novice': 54, 'Intermediate': 76, 'Advanced': 101, 'Elite': 129},
    75: {'Beginner': 39, 'Novice': 57, 'Intermediate': 80, 'Advanced': 106, 'Elite': 134},
    80: {'Beginner': 42, 'Novice': 61, 'Intermediate': 84, 'Advanced': 110, 'Elite': 139},
    85: {'Beginner': 45, 'Novice': 64, 'Intermediate': 87, 'Advanced': 115, 'Elite': 144},
    90: {'Beginner': 47, 'Novice': 67, 'Intermediate': 91, 'Advanced': 119, 'Elite': 149},
    95: {'Beginner': 50, 'Novice': 70, 'Intermediate': 94, 'Advanced': 122, 'Elite': 153},
    100: {'Beginner': 52, 'Novice': 72, 'Intermediate': 97, 'Advanced': 126, 'Elite': 157},
    105: {'Beginner': 54, 'Novice': 75, 'Intermediate': 101, 'Advanced': 130, 'Elite': 161},
    110: {'Beginner': 57, 'Novice': 78, 'Intermediate': 104, 'Advanced': 133, 'Elite': 165},
    115: {'Beginner': 59, 'Novice': 80, 'Intermediate': 107, 'Advanced': 137, 'Elite': 169},
    120: {'Beginner': 61, 'Novice': 83, 'Intermediate': 110, 'Advanced': 140, 'Elite': 172},
    125: {'Beginner': 63, 'Novice': 85, 'Intermediate': 112, 'Advanced': 143, 'Elite': 176},
    130: {'Beginner': 65, 'Novice': 88, 'Intermediate': 115, 'Advanced': 146, 'Elite': 179},
    135: {'Beginner': 67, 'Novice': 90, 'Intermediate': 118, 'Advanced': 149, 'Elite': 183},
    140: {'Beginner': 69, 'Novice': 92, 'Intermediate': 120, 'Advanced': 152, 'Elite': 186}
}

# Scraped on 2026-03-12
LEG_EXTENSION_STANDARDS_KG = {
    50: {'Beginner': 21, 'Novice': 40, 'Intermediate': 68, 'Advanced': 102, 'Elite': 141},
    55: {'Beginner': 24, 'Novice': 45, 'Intermediate': 74, 'Advanced': 109, 'Elite': 150},
    60: {'Beginner': 27, 'Novice': 49, 'Intermediate': 79, 'Advanced': 116, 'Elite': 158},
    65: {'Beginner': 31, 'Novice': 54, 'Intermediate': 85, 'Advanced': 123, 'Elite': 165},
    70: {'Beginner': 34, 'Novice': 58, 'Intermediate': 90, 'Advanced': 129, 'Elite': 172},
    75: {'Beginner': 37, 'Novice': 62, 'Intermediate': 95, 'Advanced': 134, 'Elite': 179},
    80: {'Beginner': 40, 'Novice': 65, 'Intermediate': 99, 'Advanced': 140, 'Elite': 186},
    85: {'Beginner': 42, 'Novice': 69, 'Intermediate': 104, 'Advanced': 145, 'Elite': 192},
    90: {'Beginner': 45, 'Novice': 73, 'Intermediate': 108, 'Advanced': 150, 'Elite': 198},
    95: {'Beginner': 48, 'Novice': 76, 'Intermediate': 112, 'Advanced': 155, 'Elite': 203},
    100: {'Beginner': 51, 'Novice': 79, 'Intermediate': 116, 'Advanced': 160, 'Elite': 209},
    105: {'Beginner': 53, 'Novice': 83, 'Intermediate': 120, 'Advanced': 165, 'Elite': 214},
    110: {'Beginner': 56, 'Novice': 86, 'Intermediate': 124, 'Advanced': 169, 'Elite': 219},
    115: {'Beginner': 58, 'Novice': 89, 'Intermediate': 128, 'Advanced': 173, 'Elite': 224},
    120: {'Beginner': 61, 'Novice': 92, 'Intermediate': 131, 'Advanced': 178, 'Elite': 228},
    125: {'Beginner': 63, 'Novice': 95, 'Intermediate': 135, 'Advanced': 182, 'Elite': 233},
    130: {'Beginner': 65, 'Novice': 97, 'Intermediate': 138, 'Advanced': 186, 'Elite': 237},
    135: {'Beginner': 68, 'Novice': 100, 'Intermediate': 141, 'Advanced': 189, 'Elite': 242},
    140: {'Beginner': 70, 'Novice': 103, 'Intermediate': 144, 'Advanced': 193, 'Elite': 246}
}

# Scraped on 2026-03-12
LYING_LEG_CURL_STANDARDS_KG = {
    50: {'Beginner': 12, 'Novice': 24, 'Intermediate': 42, 'Advanced': 64, 'Elite': 91},
    55: {'Beginner': 14, 'Novice': 28, 'Intermediate': 46, 'Advanced': 70, 'Elite': 97},
    60: {'Beginner': 17, 'Novice': 31, 'Intermediate': 51, 'Advanced': 75, 'Elite': 103},
    65: {'Beginner': 19, 'Novice': 34, 'Intermediate': 55, 'Advanced': 80, 'Elite': 109},
    70: {'Beginner': 21, 'Novice': 37, 'Intermediate': 59, 'Advanced': 85, 'Elite': 115},
    75: {'Beginner': 24, 'Novice': 40, 'Intermediate': 63, 'Advanced': 90, 'Elite': 120},
    80: {'Beginner': 26, 'Novice': 43, 'Intermediate': 66, 'Advanced': 94, 'Elite': 125},
    85: {'Beginner': 28, 'Novice': 46, 'Intermediate': 70, 'Advanced': 98, 'Elite': 130},
    90: {'Beginner': 30, 'Novice': 49, 'Intermediate': 73, 'Advanced': 102, 'Elite': 135},
    95: {'Beginner': 32, 'Novice': 52, 'Intermediate': 77, 'Advanced': 106, 'Elite': 139},
    100: {'Beginner': 35, 'Novice': 54, 'Intermediate': 80, 'Advanced': 110, 'Elite': 143},
    105: {'Beginner': 37, 'Novice': 57, 'Intermediate': 83, 'Advanced': 114, 'Elite': 148},
    110: {'Beginner': 39, 'Novice': 59, 'Intermediate': 86, 'Advanced': 117, 'Elite': 152},
    115: {'Beginner': 41, 'Novice': 62, 'Intermediate': 89, 'Advanced': 121, 'Elite': 156},
    120: {'Beginner': 43, 'Novice': 64, 'Intermediate': 92, 'Advanced': 124, 'Elite': 159},
    125: {'Beginner': 45, 'Novice': 67, 'Intermediate': 94, 'Advanced': 127, 'Elite': 163},
    130: {'Beginner': 46, 'Novice': 69, 'Intermediate': 97, 'Advanced': 130, 'Elite': 167},
    135: {'Beginner': 48, 'Novice': 71, 'Intermediate': 100, 'Advanced': 133, 'Elite': 170},
    140: {'Beginner': 50, 'Novice': 73, 'Intermediate': 102, 'Advanced': 136, 'Elite': 173}
}

# Scraped on 2026-03-12
LYING_TRICEP_EXTENSION_STANDARDS_KG = {
    50: {'Beginner': 6, 'Novice': 13, 'Intermediate': 24, 'Advanced': 38, 'Elite': 54},
    55: {'Beginner': 8, 'Novice': 16, 'Intermediate': 28, 'Advanced': 42, 'Elite': 59},
    60: {'Beginner': 10, 'Novice': 19, 'Intermediate': 31, 'Advanced': 47, 'Elite': 64},
    65: {'Beginner': 12, 'Novice': 21, 'Intermediate': 35, 'Advanced': 51, 'Elite': 69},
    70: {'Beginner': 14, 'Novice': 24, 'Intermediate': 38, 'Advanced': 55, 'Elite': 74},
    75: {'Beginner': 16, 'Novice': 27, 'Intermediate': 41, 'Advanced': 59, 'Elite': 78},
    80: {'Beginner': 18, 'Novice': 29, 'Intermediate': 44, 'Advanced': 63, 'Elite': 83},
    85: {'Beginner': 20, 'Novice': 32, 'Intermediate': 48, 'Advanced': 66, 'Elite': 87},
    90: {'Beginner': 22, 'Novice': 34, 'Intermediate': 51, 'Advanced': 70, 'Elite': 91},
    95: {'Beginner': 24, 'Novice': 37, 'Intermediate': 54, 'Advanced': 73, 'Elite': 95},
    100: {'Beginner': 26, 'Novice': 39, 'Intermediate': 56, 'Advanced': 77, 'Elite': 99},
    105: {'Beginner': 28, 'Novice': 42, 'Intermediate': 59, 'Advanced': 80, 'Elite': 103},
    110: {'Beginner': 30, 'Novice': 44, 'Intermediate': 62, 'Advanced': 83, 'Elite': 106},
    115: {'Beginner': 31, 'Novice': 46, 'Intermediate': 65, 'Advanced': 86, 'Elite': 110},
    120: {'Beginner': 33, 'Novice': 48, 'Intermediate': 67, 'Advanced': 89, 'Elite': 113},
    125: {'Beginner': 35, 'Novice': 51, 'Intermediate': 70, 'Advanced': 92, 'Elite': 117},
    130: {'Beginner': 37, 'Novice': 53, 'Intermediate': 72, 'Advanced': 95, 'Elite': 120},
    135: {'Beginner': 39, 'Novice': 55, 'Intermediate': 75, 'Advanced': 98, 'Elite': 123},
    140: {'Beginner': 40, 'Novice': 57, 'Intermediate': 77, 'Advanced': 101, 'Elite': 126}
}

# Scraped on 2026-03-12
MACHINE_CALF_RAISE_STANDARDS_KG = {
    50: {'Beginner': 11, 'Novice': 37, 'Intermediate': 80, 'Advanced': 141, 'Elite': 214},
    55: {'Beginner': 15, 'Novice': 44, 'Intermediate': 91, 'Advanced': 154, 'Elite': 231},
    60: {'Beginner': 19, 'Novice': 51, 'Intermediate': 101, 'Advanced': 167, 'Elite': 247},
    65: {'Beginner': 24, 'Novice': 58, 'Intermediate': 111, 'Advanced': 180, 'Elite': 262},
    70: {'Beginner': 28, 'Novice': 65, 'Intermediate': 120, 'Advanced': 192, 'Elite': 276},
    75: {'Beginner': 33, 'Novice': 72, 'Intermediate': 129, 'Advanced': 203, 'Elite': 290},
    80: {'Beginner': 37, 'Novice': 78, 'Intermediate': 138, 'Advanced': 214, 'Elite': 303},
    85: {'Beginner': 42, 'Novice': 85, 'Intermediate': 146, 'Advanced': 225, 'Elite': 315},
    90: {'Beginner': 46, 'Novice': 91, 'Intermediate': 155, 'Advanced': 235, 'Elite': 328},
    95: {'Beginner': 50, 'Novice': 97, 'Intermediate': 163, 'Advanced': 245, 'Elite': 339},
    100: {'Beginner': 55, 'Novice': 103, 'Intermediate': 171, 'Advanced': 255, 'Elite': 350},
    105: {'Beginner': 59, 'Novice': 109, 'Intermediate': 178, 'Advanced': 264, 'Elite': 361},
    110: {'Beginner': 64, 'Novice': 115, 'Intermediate': 186, 'Advanced': 273, 'Elite': 372},
    115: {'Beginner': 68, 'Novice': 121, 'Intermediate': 193, 'Advanced': 282, 'Elite': 382},
    120: {'Beginner': 72, 'Novice': 126, 'Intermediate': 200, 'Advanced': 290, 'Elite': 392},
    125: {'Beginner': 76, 'Novice': 132, 'Intermediate': 207, 'Advanced': 299, 'Elite': 402},
    130: {'Beginner': 80, 'Novice': 137, 'Intermediate': 214, 'Advanced': 307, 'Elite': 411},
    135: {'Beginner': 84, 'Novice': 143, 'Intermediate': 220, 'Advanced': 314, 'Elite': 420},
    140: {'Beginner': 88, 'Novice': 148, 'Intermediate': 227, 'Advanced': 322, 'Elite': 429}
}

# Scraped on 2026-03-12
MACHINE_CHEST_FLY_STANDARDS_KG = {
    50: {'Beginner': 17, 'Novice': 33, 'Intermediate': 55, 'Advanced': 83, 'Elite': 114},
    55: {'Beginner': 21, 'Novice': 38, 'Intermediate': 61, 'Advanced': 90, 'Elite': 123},
    60: {'Beginner': 24, 'Novice': 43, 'Intermediate': 67, 'Advanced': 97, 'Elite': 131},
    65: {'Beginner': 28, 'Novice': 47, 'Intermediate': 73, 'Advanced': 104, 'Elite': 139},
    70: {'Beginner': 31, 'Novice': 52, 'Intermediate': 78, 'Advanced': 111, 'Elite': 146},
    75: {'Beginner': 35, 'Novice': 56, 'Intermediate': 84, 'Advanced': 117, 'Elite': 154},
    80: {'Beginner': 38, 'Novice': 60, 'Intermediate': 89, 'Advanced': 123, 'Elite': 160},
    85: {'Beginner': 41, 'Novice': 64, 'Intermediate': 94, 'Advanced': 128, 'Elite': 167},
    90: {'Beginner': 44, 'Novice': 68, 'Intermediate': 98, 'Advanced': 134, 'Elite': 173},
    95: {'Beginner': 47, 'Novice': 72, 'Intermediate': 103, 'Advanced': 139, 'Elite': 179},
    100: {'Beginner': 50, 'Novice': 76, 'Intermediate': 107, 'Advanced': 145, 'Elite': 185},
    105: {'Beginner': 53, 'Novice': 79, 'Intermediate': 112, 'Advanced': 150, 'Elite': 191},
    110: {'Beginner': 56, 'Novice': 83, 'Intermediate': 116, 'Advanced': 154, 'Elite': 196},
    115: {'Beginner': 59, 'Novice': 86, 'Intermediate': 120, 'Advanced': 159, 'Elite': 202},
    120: {'Beginner': 62, 'Novice': 90, 'Intermediate': 124, 'Advanced': 164, 'Elite': 207},
    125: {'Beginner': 65, 'Novice': 93, 'Intermediate': 128, 'Advanced': 168, 'Elite': 212},
    130: {'Beginner': 67, 'Novice': 96, 'Intermediate': 131, 'Advanced': 172, 'Elite': 217},
    135: {'Beginner': 70, 'Novice': 99, 'Intermediate': 135, 'Advanced': 177, 'Elite': 221},
    140: {'Beginner': 73, 'Novice': 102, 'Intermediate': 139, 'Advanced': 181, 'Elite': 226}
}

# Scraped on 2026-03-12
MACHINE_SHOULDER_PRESS_STANDARDS_KG = {
    50: {'Beginner': 10, 'Novice': 23, 'Intermediate': 44, 'Advanced': 71, 'Elite': 102},
    55: {'Beginner': 13, 'Novice': 28, 'Intermediate': 50, 'Advanced': 78, 'Elite': 112},
    60: {'Beginner': 16, 'Novice': 32, 'Intermediate': 56, 'Advanced': 86, 'Elite': 120},
    65: {'Beginner': 19, 'Novice': 37, 'Intermediate': 62, 'Advanced': 93, 'Elite': 129},
    70: {'Beginner': 22, 'Novice': 41, 'Intermediate': 67, 'Advanced': 100, 'Elite': 137},
    75: {'Beginner': 25, 'Novice': 45, 'Intermediate': 73, 'Advanced': 106, 'Elite': 144},
    80: {'Beginner': 28, 'Novice': 49, 'Intermediate': 78, 'Advanced': 112, 'Elite': 152},
    85: {'Beginner': 31, 'Novice': 53, 'Intermediate': 83, 'Advanced': 119, 'Elite': 159},
    90: {'Beginner': 34, 'Novice': 57, 'Intermediate': 88, 'Advanced': 124, 'Elite': 165},
    95: {'Beginner': 37, 'Novice': 61, 'Intermediate': 92, 'Advanced': 130, 'Elite': 172},
    100: {'Beginner': 40, 'Novice': 65, 'Intermediate': 97, 'Advanced': 136, 'Elite': 178},
    105: {'Beginner': 43, 'Novice': 69, 'Intermediate': 102, 'Advanced': 141, 'Elite': 184},
    110: {'Beginner': 46, 'Novice': 72, 'Intermediate': 106, 'Advanced': 146, 'Elite': 190},
    115: {'Beginner': 49, 'Novice': 76, 'Intermediate': 110, 'Advanced': 151, 'Elite': 196},
    120: {'Beginner': 52, 'Novice': 80, 'Intermediate': 115, 'Advanced': 156, 'Elite': 202},
    125: {'Beginner': 55, 'Novice': 83, 'Intermediate': 119, 'Advanced': 161, 'Elite': 207},
    130: {'Beginner': 58, 'Novice': 86, 'Intermediate': 123, 'Advanced': 166, 'Elite': 212},
    135: {'Beginner': 60, 'Novice': 90, 'Intermediate': 127, 'Advanced': 170, 'Elite': 218},
    140: {'Beginner': 63, 'Novice': 93, 'Intermediate': 131, 'Advanced': 175, 'Elite': 223}
}

# Scraped on 2026-03-12
MILITARY_PRESS_STANDARDS_KG = {
    50: {'Beginner': 15, 'Novice': 24, 'Intermediate': 36, 'Advanced': 50, 'Elite': 66},
    55: {'Beginner': 18, 'Novice': 28, 'Intermediate': 41, 'Advanced': 56, 'Elite': 73},
    60: {'Beginner': 22, 'Novice': 32, 'Intermediate': 46, 'Advanced': 62, 'Elite': 79},
    65: {'Beginner': 25, 'Novice': 36, 'Intermediate': 51, 'Advanced': 67, 'Elite': 85},
    70: {'Beginner': 28, 'Novice': 40, 'Intermediate': 55, 'Advanced': 72, 'Elite': 91},
    75: {'Beginner': 31, 'Novice': 44, 'Intermediate': 59, 'Advanced': 77, 'Elite': 97},
    80: {'Beginner': 34, 'Novice': 48, 'Intermediate': 64, 'Advanced': 82, 'Elite': 102},
    85: {'Beginner': 37, 'Novice': 51, 'Intermediate': 68, 'Advanced': 87, 'Elite': 107},
    90: {'Beginner': 40, 'Novice': 55, 'Intermediate': 72, 'Advanced': 91, 'Elite': 112},
    95: {'Beginner': 43, 'Novice': 58, 'Intermediate': 76, 'Advanced': 96, 'Elite': 117},
    100: {'Beginner': 46, 'Novice': 61, 'Intermediate': 79, 'Advanced': 100, 'Elite': 122},
    105: {'Beginner': 49, 'Novice': 65, 'Intermediate': 83, 'Advanced': 104, 'Elite': 126},
    110: {'Beginner': 52, 'Novice': 68, 'Intermediate': 87, 'Advanced': 108, 'Elite': 130},
    115: {'Beginner': 54, 'Novice': 71, 'Intermediate': 90, 'Advanced': 112, 'Elite': 135},
    120: {'Beginner': 57, 'Novice': 74, 'Intermediate': 94, 'Advanced': 116, 'Elite': 139},
    125: {'Beginner': 60, 'Novice': 77, 'Intermediate': 97, 'Advanced': 119, 'Elite': 143},
    130: {'Beginner': 62, 'Novice': 80, 'Intermediate': 100, 'Advanced': 123, 'Elite': 147},
    135: {'Beginner': 65, 'Novice': 82, 'Intermediate': 103, 'Advanced': 126, 'Elite': 151},
    140: {'Beginner': 67, 'Novice': 85, 'Intermediate': 106, 'Advanced': 130, 'Elite': 155}
}

# Scraped on 2026-03-12
MUSCLE_UPS_STANDARDS_KG = {
    50: {'Beginner': 1, 'Novice': 1, 'Intermediate': 5, 'Advanced': 11, 'Elite': 18},
    55: {'Beginner': 1, 'Novice': 1, 'Intermediate': 6, 'Advanced': 11, 'Elite': 18},
    60: {'Beginner': 1, 'Novice': 1, 'Intermediate': 6, 'Advanced': 12, 'Elite': 18},
    65: {'Beginner': 1, 'Novice': 1, 'Intermediate': 7, 'Advanced': 12, 'Elite': 18},
    70: {'Beginner': 1, 'Novice': 1, 'Intermediate': 7, 'Advanced': 12, 'Elite': 18},
    75: {'Beginner': 1, 'Novice': 2, 'Intermediate': 7, 'Advanced': 12, 'Elite': 18},
    80: {'Beginner': 1, 'Novice': 2, 'Intermediate': 7, 'Advanced': 12, 'Elite': 17},
    85: {'Beginner': 1, 'Novice': 2, 'Intermediate': 7, 'Advanced': 11, 'Elite': 17},
    90: {'Beginner': 1, 'Novice': 2, 'Intermediate': 7, 'Advanced': 11, 'Elite': 16},
    95: {'Beginner': 1, 'Novice': 2, 'Intermediate': 7, 'Advanced': 11, 'Elite': 16},
    100: {'Beginner': 1, 'Novice': 2, 'Intermediate': 7, 'Advanced': 10, 'Elite': 15},
    105: {'Beginner': 1, 'Novice': 2, 'Intermediate': 6, 'Advanced': 10, 'Elite': 15},
    110: {'Beginner': 1, 'Novice': 2, 'Intermediate': 6, 'Advanced': 10, 'Elite': 14},
    115: {'Beginner': 1, 'Novice': 2, 'Intermediate': 6, 'Advanced': 10, 'Elite': 14},
    120: {'Beginner': 1, 'Novice': 1, 'Intermediate': 6, 'Advanced': 9, 'Elite': 13},
    125: {'Beginner': 1, 'Novice': 1, 'Intermediate': 6, 'Advanced': 9, 'Elite': 13},
    130: {'Beginner': 1, 'Novice': 1, 'Intermediate': 5, 'Advanced': 9, 'Elite': 13},
    135: {'Beginner': 1, 'Novice': 1, 'Intermediate': 5, 'Advanced': 9, 'Elite': 12},
    140: {'Beginner': 1, 'Novice': 1, 'Intermediate': 5, 'Advanced': 8, 'Elite': 12}
}

# Scraped on 2026-03-12
NEUTRAL_GRIP_PULL_UPS_STANDARDS_KG = {
    50: {'Beginner': 1, 'Novice': 5, 'Intermediate': 15, 'Advanced': 29, 'Elite': 43},
    55: {'Beginner': 1, 'Novice': 6, 'Intermediate': 16, 'Advanced': 28, 'Elite': 42},
    60: {'Beginner': 1, 'Novice': 6, 'Intermediate': 16, 'Advanced': 28, 'Elite': 41},
    65: {'Beginner': 1, 'Novice': 6, 'Intermediate': 16, 'Advanced': 27, 'Elite': 40},
    70: {'Beginner': 1, 'Novice': 7, 'Intermediate': 16, 'Advanced': 27, 'Elite': 39},
    75: {'Beginner': 1, 'Novice': 7, 'Intermediate': 15, 'Advanced': 26, 'Elite': 38},
    80: {'Beginner': 1, 'Novice': 7, 'Intermediate': 15, 'Advanced': 25, 'Elite': 36},
    85: {'Beginner': 1, 'Novice': 7, 'Intermediate': 15, 'Advanced': 25, 'Elite': 35},
    90: {'Beginner': 1, 'Novice': 7, 'Intermediate': 14, 'Advanced': 24, 'Elite': 34},
    95: {'Beginner': 1, 'Novice': 6, 'Intermediate': 14, 'Advanced': 23, 'Elite': 33},
    100: {'Beginner': 1, 'Novice': 6, 'Intermediate': 13, 'Advanced': 23, 'Elite': 32},
    105: {'Beginner': 1, 'Novice': 6, 'Intermediate': 13, 'Advanced': 22, 'Elite': 31},
    110: {'Beginner': 1, 'Novice': 6, 'Intermediate': 13, 'Advanced': 21, 'Elite': 30},
    115: {'Beginner': 1, 'Novice': 6, 'Intermediate': 12, 'Advanced': 21, 'Elite': 29},
    120: {'Beginner': 1, 'Novice': 6, 'Intermediate': 12, 'Advanced': 20, 'Elite': 28},
    125: {'Beginner': 1, 'Novice': 5, 'Intermediate': 11, 'Advanced': 19, 'Elite': 27},
    130: {'Beginner': 1, 'Novice': 5, 'Intermediate': 11, 'Advanced': 19, 'Elite': 27},
    135: {'Beginner': 1, 'Novice': 5, 'Intermediate': 10, 'Advanced': 18, 'Elite': 26},
    140: {'Beginner': 1, 'Novice': 5, 'Intermediate': 10, 'Advanced': 17, 'Elite': 25}
}

# Scraped on 2026-03-12
ONE_ARM_PUSH_UPS_STANDARDS_KG = {
    50: {'Beginner': 1, 'Novice': 1, 'Intermediate': 8, 'Advanced': 25, 'Elite': 47},
    55: {'Beginner': 1, 'Novice': 1, 'Intermediate': 9, 'Advanced': 26, 'Elite': 46},
    60: {'Beginner': 1, 'Novice': 1, 'Intermediate': 9, 'Advanced': 26, 'Elite': 46},
    65: {'Beginner': 1, 'Novice': 1, 'Intermediate': 10, 'Advanced': 27, 'Elite': 45},
    70: {'Beginner': 1, 'Novice': 1, 'Intermediate': 11, 'Advanced': 27, 'Elite': 45},
    75: {'Beginner': 1, 'Novice': 1, 'Intermediate': 11, 'Advanced': 27, 'Elite': 44},
    80: {'Beginner': 1, 'Novice': 1, 'Intermediate': 11, 'Advanced': 26, 'Elite': 43},
    85: {'Beginner': 1, 'Novice': 1, 'Intermediate': 11, 'Advanced': 26, 'Elite': 42},
    90: {'Beginner': 1, 'Novice': 1, 'Intermediate': 12, 'Advanced': 26, 'Elite': 41},
    95: {'Beginner': 1, 'Novice': 1, 'Intermediate': 12, 'Advanced': 25, 'Elite': 41},
    100: {'Beginner': 1, 'Novice': 1, 'Intermediate': 11, 'Advanced': 25, 'Elite': 40},
    105: {'Beginner': 1, 'Novice': 1, 'Intermediate': 11, 'Advanced': 25, 'Elite': 39},
    110: {'Beginner': 1, 'Novice': 1, 'Intermediate': 11, 'Advanced': 24, 'Elite': 38},
    115: {'Beginner': 1, 'Novice': 1, 'Intermediate': 11, 'Advanced': 24, 'Elite': 37},
    120: {'Beginner': 1, 'Novice': 1, 'Intermediate': 11, 'Advanced': 23, 'Elite': 36},
    125: {'Beginner': 1, 'Novice': 1, 'Intermediate': 11, 'Advanced': 23, 'Elite': 36},
    130: {'Beginner': 1, 'Novice': 1, 'Intermediate': 11, 'Advanced': 22, 'Elite': 35},
    135: {'Beginner': 1, 'Novice': 1, 'Intermediate': 10, 'Advanced': 22, 'Elite': 34},
    140: {'Beginner': 1, 'Novice': 1, 'Intermediate': 10, 'Advanced': 21, 'Elite': 33}
}

# Scraped on 2026-03-12
POWER_CLEAN_STANDARDS_KG = {
    50: {'Beginner': 28, 'Novice': 42, 'Intermediate': 60, 'Advanced': 81, 'Elite': 104},
    55: {'Beginner': 32, 'Novice': 47, 'Intermediate': 66, 'Advanced': 88, 'Elite': 112},
    60: {'Beginner': 36, 'Novice': 52, 'Intermediate': 71, 'Advanced': 94, 'Elite': 119},
    65: {'Beginner': 40, 'Novice': 56, 'Intermediate': 77, 'Advanced': 101, 'Elite': 126},
    70: {'Beginner': 43, 'Novice': 61, 'Intermediate': 82, 'Advanced': 107, 'Elite': 133},
    75: {'Beginner': 47, 'Novice': 65, 'Intermediate': 87, 'Advanced': 112, 'Elite': 139},
    80: {'Beginner': 50, 'Novice': 69, 'Intermediate': 92, 'Advanced': 118, 'Elite': 145},
    85: {'Beginner': 54, 'Novice': 73, 'Intermediate': 96, 'Advanced': 123, 'Elite': 151},
    90: {'Beginner': 57, 'Novice': 77, 'Intermediate': 101, 'Advanced': 128, 'Elite': 157},
    95: {'Beginner': 60, 'Novice': 81, 'Intermediate': 105, 'Advanced': 133, 'Elite': 162},
    100: {'Beginner': 64, 'Novice': 84, 'Intermediate': 109, 'Advanced': 137, 'Elite': 167},
    105: {'Beginner': 67, 'Novice': 88, 'Intermediate': 113, 'Advanced': 142, 'Elite': 172},
    110: {'Beginner': 70, 'Novice': 91, 'Intermediate': 117, 'Advanced': 146, 'Elite': 177},
    115: {'Beginner': 73, 'Novice': 95, 'Intermediate': 121, 'Advanced': 151, 'Elite': 182},
    120: {'Beginner': 76, 'Novice': 98, 'Intermediate': 125, 'Advanced': 155, 'Elite': 186},
    125: {'Beginner': 78, 'Novice': 101, 'Intermediate': 128, 'Advanced': 159, 'Elite': 191},
    130: {'Beginner': 81, 'Novice': 104, 'Intermediate': 132, 'Advanced': 163, 'Elite': 195},
    135: {'Beginner': 84, 'Novice': 107, 'Intermediate': 135, 'Advanced': 166, 'Elite': 199},
    140: {'Beginner': 86, 'Novice': 110, 'Intermediate': 139, 'Advanced': 170, 'Elite': 203}
}

# Scraped on 2026-03-12
PREACHER_CURL_STANDARDS_KG = {
    50: {'Beginner': 9, 'Novice': 18, 'Intermediate': 30, 'Advanced': 46, 'Elite': 64},
    55: {'Beginner': 10, 'Novice': 20, 'Intermediate': 33, 'Advanced': 49, 'Elite': 68},
    60: {'Beginner': 12, 'Novice': 22, 'Intermediate': 36, 'Advanced': 53, 'Elite': 72},
    65: {'Beginner': 14, 'Novice': 24, 'Intermediate': 39, 'Advanced': 56, 'Elite': 76},
    70: {'Beginner': 15, 'Novice': 26, 'Intermediate': 41, 'Advanced': 59, 'Elite': 80},
    75: {'Beginner': 17, 'Novice': 28, 'Intermediate': 44, 'Advanced': 63, 'Elite': 83},
    80: {'Beginner': 18, 'Novice': 30, 'Intermediate': 46, 'Advanced': 65, 'Elite': 87},
    85: {'Beginner': 20, 'Novice': 32, 'Intermediate': 49, 'Advanced': 68, 'Elite': 90},
    90: {'Beginner': 21, 'Novice': 34, 'Intermediate': 51, 'Advanced': 71, 'Elite': 93},
    95: {'Beginner': 23, 'Novice': 36, 'Intermediate': 53, 'Advanced': 74, 'Elite': 96},
    100: {'Beginner': 24, 'Novice': 38, 'Intermediate': 55, 'Advanced': 76, 'Elite': 99},
    105: {'Beginner': 26, 'Novice': 40, 'Intermediate': 57, 'Advanced': 79, 'Elite': 102},
    110: {'Beginner': 27, 'Novice': 41, 'Intermediate': 59, 'Advanced': 81, 'Elite': 105},
    115: {'Beginner': 28, 'Novice': 43, 'Intermediate': 61, 'Advanced': 83, 'Elite': 107},
    120: {'Beginner': 30, 'Novice': 44, 'Intermediate': 63, 'Advanced': 85, 'Elite': 110},
    125: {'Beginner': 31, 'Novice': 46, 'Intermediate': 65, 'Advanced': 88, 'Elite': 112},
    130: {'Beginner': 32, 'Novice': 48, 'Intermediate': 67, 'Advanced': 90, 'Elite': 114},
    135: {'Beginner': 33, 'Novice': 49, 'Intermediate': 69, 'Advanced': 92, 'Elite': 117},
    140: {'Beginner': 35, 'Novice': 50, 'Intermediate': 70, 'Advanced': 94, 'Elite': 119}
}

# Scraped on 2026-03-12
PUSH_PRESS_STANDARDS_KG = {
    50: {'Beginner': 18, 'Novice': 31, 'Intermediate': 49, 'Advanced': 70, 'Elite': 94},
    55: {'Beginner': 22, 'Novice': 36, 'Intermediate': 55, 'Advanced': 77, 'Elite': 102},
    60: {'Beginner': 26, 'Novice': 41, 'Intermediate': 60, 'Advanced': 84, 'Elite': 110},
    65: {'Beginner': 29, 'Novice': 45, 'Intermediate': 66, 'Advanced': 90, 'Elite': 117},
    70: {'Beginner': 33, 'Novice': 50, 'Intermediate': 71, 'Advanced': 96, 'Elite': 124},
    75: {'Beginner': 36, 'Novice': 54, 'Intermediate': 76, 'Advanced': 102, 'Elite': 130},
    80: {'Beginner': 39, 'Novice': 58, 'Intermediate': 81, 'Advanced': 108, 'Elite': 137},
    85: {'Beginner': 43, 'Novice': 62, 'Intermediate': 85, 'Advanced': 113, 'Elite': 143},
    90: {'Beginner': 46, 'Novice': 66, 'Intermediate': 90, 'Advanced': 118, 'Elite': 149},
    95: {'Beginner': 49, 'Novice': 69, 'Intermediate': 94, 'Advanced': 123, 'Elite': 154},
    100: {'Beginner': 52, 'Novice': 73, 'Intermediate': 99, 'Advanced': 128, 'Elite': 160},
    105: {'Beginner': 55, 'Novice': 77, 'Intermediate': 103, 'Advanced': 133, 'Elite': 165},
    110: {'Beginner': 58, 'Novice': 80, 'Intermediate': 107, 'Advanced': 137, 'Elite': 170},
    115: {'Beginner': 61, 'Novice': 84, 'Intermediate': 111, 'Advanced': 142, 'Elite': 175},
    120: {'Beginner': 64, 'Novice': 87, 'Intermediate': 115, 'Advanced': 146, 'Elite': 180},
    125: {'Beginner': 67, 'Novice': 90, 'Intermediate': 118, 'Advanced': 150, 'Elite': 185},
    130: {'Beginner': 70, 'Novice': 93, 'Intermediate': 122, 'Advanced': 155, 'Elite': 189},
    135: {'Beginner': 72, 'Novice': 97, 'Intermediate': 126, 'Advanced': 159, 'Elite': 194},
    140: {'Beginner': 75, 'Novice': 100, 'Intermediate': 129, 'Advanced': 163, 'Elite': 198}
}

# Scraped on 2026-03-12
ROMANIAN_DEADLIFT_STANDARDS_KG = {
    50: {'Beginner': 28, 'Novice': 47, 'Intermediate': 73, 'Advanced': 103, 'Elite': 138},
    55: {'Beginner': 34, 'Novice': 55, 'Intermediate': 82, 'Advanced': 114, 'Elite': 150},
    60: {'Beginner': 40, 'Novice': 62, 'Intermediate': 90, 'Advanced': 124, 'Elite': 162},
    65: {'Beginner': 45, 'Novice': 69, 'Intermediate': 98, 'Advanced': 134, 'Elite': 173},
    70: {'Beginner': 51, 'Novice': 75, 'Intermediate': 106, 'Advanced': 143, 'Elite': 183},
    75: {'Beginner': 56, 'Novice': 82, 'Intermediate': 114, 'Advanced': 152, 'Elite': 193},
    80: {'Beginner': 61, 'Novice': 88, 'Intermediate': 122, 'Advanced': 161, 'Elite': 203},
    85: {'Beginner': 66, 'Novice': 94, 'Intermediate': 129, 'Advanced': 169, 'Elite': 212},
    90: {'Beginner': 71, 'Novice': 100, 'Intermediate': 136, 'Advanced': 177, 'Elite': 221},
    95: {'Beginner': 76, 'Novice': 106, 'Intermediate': 143, 'Advanced': 185, 'Elite': 230},
    100: {'Beginner': 81, 'Novice': 112, 'Intermediate': 149, 'Advanced': 192, 'Elite': 238},
    105: {'Beginner': 86, 'Novice': 117, 'Intermediate': 156, 'Advanced': 199, 'Elite': 246},
    110: {'Beginner': 91, 'Novice': 123, 'Intermediate': 162, 'Advanced': 207, 'Elite': 254},
    115: {'Beginner': 95, 'Novice': 128, 'Intermediate': 168, 'Advanced': 213, 'Elite': 262},
    120: {'Beginner': 100, 'Novice': 133, 'Intermediate': 174, 'Advanced': 220, 'Elite': 269},
    125: {'Beginner': 104, 'Novice': 138, 'Intermediate': 180, 'Advanced': 227, 'Elite': 276},
    130: {'Beginner': 108, 'Novice': 143, 'Intermediate': 185, 'Advanced': 233, 'Elite': 283},
    135: {'Beginner': 113, 'Novice': 148, 'Intermediate': 191, 'Advanced': 239, 'Elite': 290},
    140: {'Beginner': 117, 'Novice': 153, 'Intermediate': 196, 'Advanced': 245, 'Elite': 297}
}

# Scraped on 2026-03-12
SEATED_CABLE_ROW_STANDARDS_KG = {
    50: {'Beginner': 24, 'Novice': 38, 'Intermediate': 56, 'Advanced': 78, 'Elite': 102},
    55: {'Beginner': 27, 'Novice': 42, 'Intermediate': 62, 'Advanced': 85, 'Elite': 110},
    60: {'Beginner': 31, 'Novice': 47, 'Intermediate': 67, 'Advanced': 91, 'Elite': 117},
    65: {'Beginner': 35, 'Novice': 52, 'Intermediate': 73, 'Advanced': 97, 'Elite': 124},
    70: {'Beginner': 38, 'Novice': 56, 'Intermediate': 78, 'Advanced': 103, 'Elite': 131},
    75: {'Beginner': 42, 'Novice': 60, 'Intermediate': 83, 'Advanced': 109, 'Elite': 137},
    80: {'Beginner': 45, 'Novice': 64, 'Intermediate': 88, 'Advanced': 114, 'Elite': 143},
    85: {'Beginner': 49, 'Novice': 68, 'Intermediate': 92, 'Advanced': 120, 'Elite': 149},
    90: {'Beginner': 52, 'Novice': 72, 'Intermediate': 97, 'Advanced': 125, 'Elite': 155},
    95: {'Beginner': 55, 'Novice': 76, 'Intermediate': 101, 'Advanced': 130, 'Elite': 160},
    100: {'Beginner': 58, 'Novice': 79, 'Intermediate': 105, 'Advanced': 134, 'Elite': 166},
    105: {'Beginner': 61, 'Novice': 83, 'Intermediate': 109, 'Advanced': 139, 'Elite': 171},
    110: {'Beginner': 64, 'Novice': 86, 'Intermediate': 113, 'Advanced': 143, 'Elite': 176},
    115: {'Beginner': 67, 'Novice': 90, 'Intermediate': 117, 'Advanced': 148, 'Elite': 180},
    120: {'Beginner': 70, 'Novice': 93, 'Intermediate': 121, 'Advanced': 152, 'Elite': 185},
    125: {'Beginner': 73, 'Novice': 96, 'Intermediate': 124, 'Advanced': 156, 'Elite': 189},
    130: {'Beginner': 75, 'Novice': 99, 'Intermediate': 128, 'Advanced': 160, 'Elite': 194},
    135: {'Beginner': 78, 'Novice': 102, 'Intermediate': 131, 'Advanced': 164, 'Elite': 198},
    140: {'Beginner': 81, 'Novice': 105, 'Intermediate': 134, 'Advanced': 167, 'Elite': 202}
}

# Scraped on 2026-03-12
SEATED_DUMBBELL_SHOULDER_PRESS_STANDARDS_KG = {
    50: {'Beginner': 6, 'Novice': 11, 'Intermediate': 18, 'Advanced': 27, 'Elite': 38},
    55: {'Beginner': 7, 'Novice': 13, 'Intermediate': 21, 'Advanced': 30, 'Elite': 41},
    60: {'Beginner': 9, 'Novice': 15, 'Intermediate': 23, 'Advanced': 33, 'Elite': 45},
    65: {'Beginner': 10, 'Novice': 17, 'Intermediate': 26, 'Advanced': 36, 'Elite': 48},
    70: {'Beginner': 12, 'Novice': 19, 'Intermediate': 28, 'Advanced': 39, 'Elite': 51},
    75: {'Beginner': 13, 'Novice': 21, 'Intermediate': 30, 'Advanced': 42, 'Elite': 54},
    80: {'Beginner': 15, 'Novice': 22, 'Intermediate': 32, 'Advanced': 44, 'Elite': 57},
    85: {'Beginner': 16, 'Novice': 24, 'Intermediate': 35, 'Advanced': 47, 'Elite': 60},
    90: {'Beginner': 17, 'Novice': 26, 'Intermediate': 37, 'Advanced': 49, 'Elite': 63},
    95: {'Beginner': 19, 'Novice': 28, 'Intermediate': 39, 'Advanced': 52, 'Elite': 66},
    100: {'Beginner': 20, 'Novice': 29, 'Intermediate': 41, 'Advanced': 54, 'Elite': 68},
    105: {'Beginner': 22, 'Novice': 31, 'Intermediate': 43, 'Advanced': 56, 'Elite': 71},
    110: {'Beginner': 23, 'Novice': 33, 'Intermediate': 45, 'Advanced': 58, 'Elite': 73},
    115: {'Beginner': 24, 'Novice': 34, 'Intermediate': 46, 'Advanced': 60, 'Elite': 76},
    120: {'Beginner': 26, 'Novice': 36, 'Intermediate': 48, 'Advanced': 62, 'Elite': 78},
    125: {'Beginner': 27, 'Novice': 37, 'Intermediate': 50, 'Advanced': 64, 'Elite': 80},
    130: {'Beginner': 28, 'Novice': 39, 'Intermediate': 52, 'Advanced': 66, 'Elite': 82},
    135: {'Beginner': 29, 'Novice': 40, 'Intermediate': 53, 'Advanced': 68, 'Elite': 84},
    140: {'Beginner': 31, 'Novice': 42, 'Intermediate': 55, 'Advanced': 70, 'Elite': 86}
}

# Scraped on 2026-03-12
SEATED_LEG_CURL_STANDARDS_KG = {
    50: {'Beginner': 17, 'Novice': 33, 'Intermediate': 56, 'Advanced': 84, 'Elite': 116},
    55: {'Beginner': 20, 'Novice': 37, 'Intermediate': 60, 'Advanced': 90, 'Elite': 123},
    60: {'Beginner': 22, 'Novice': 40, 'Intermediate': 65, 'Advanced': 95, 'Elite': 130},
    65: {'Beginner': 25, 'Novice': 44, 'Intermediate': 69, 'Advanced': 101, 'Elite': 136},
    70: {'Beginner': 28, 'Novice': 47, 'Intermediate': 74, 'Advanced': 106, 'Elite': 142},
    75: {'Beginner': 30, 'Novice': 50, 'Intermediate': 78, 'Advanced': 110, 'Elite': 147},
    80: {'Beginner': 32, 'Novice': 54, 'Intermediate': 81, 'Advanced': 115, 'Elite': 152},
    85: {'Beginner': 35, 'Novice': 57, 'Intermediate': 85, 'Advanced': 119, 'Elite': 157},
    90: {'Beginner': 37, 'Novice': 60, 'Intermediate': 89, 'Advanced': 124, 'Elite': 162},
    95: {'Beginner': 39, 'Novice': 62, 'Intermediate': 92, 'Advanced': 128, 'Elite': 167},
    100: {'Beginner': 42, 'Novice': 65, 'Intermediate': 95, 'Advanced': 132, 'Elite': 171},
    105: {'Beginner': 44, 'Novice': 68, 'Intermediate': 99, 'Advanced': 135, 'Elite': 176},
    110: {'Beginner': 46, 'Novice': 70, 'Intermediate': 102, 'Advanced': 139, 'Elite': 180},
    115: {'Beginner': 48, 'Novice': 73, 'Intermediate': 105, 'Advanced': 142, 'Elite': 184},
    120: {'Beginner': 50, 'Novice': 75, 'Intermediate': 108, 'Advanced': 146, 'Elite': 188},
    125: {'Beginner': 52, 'Novice': 78, 'Intermediate': 111, 'Advanced': 149, 'Elite': 191},
    130: {'Beginner': 54, 'Novice': 80, 'Intermediate': 113, 'Advanced': 152, 'Elite': 195},
    135: {'Beginner': 55, 'Novice': 82, 'Intermediate': 116, 'Advanced': 156, 'Elite': 199},
    140: {'Beginner': 57, 'Novice': 85, 'Intermediate': 119, 'Advanced': 159, 'Elite': 202}
}

# Scraped on 2026-03-12
SEATED_SHOULDER_PRESS_STANDARDS_KG = {
    50: {'Beginner': 10, 'Novice': 21, 'Intermediate': 36, 'Advanced': 54, 'Elite': 76},
    55: {'Beginner': 14, 'Novice': 25, 'Intermediate': 41, 'Advanced': 61, 'Elite': 84},
    60: {'Beginner': 17, 'Novice': 30, 'Intermediate': 47, 'Advanced': 68, 'Elite': 92},
    65: {'Beginner': 20, 'Novice': 34, 'Intermediate': 53, 'Advanced': 75, 'Elite': 100},
    70: {'Beginner': 24, 'Novice': 39, 'Intermediate': 58, 'Advanced': 81, 'Elite': 107},
    75: {'Beginner': 27, 'Novice': 43, 'Intermediate': 63, 'Advanced': 88, 'Elite': 114},
    80: {'Beginner': 31, 'Novice': 47, 'Intermediate': 69, 'Advanced': 94, 'Elite': 121},
    85: {'Beginner': 34, 'Novice': 52, 'Intermediate': 74, 'Advanced': 100, 'Elite': 128},
    90: {'Beginner': 38, 'Novice': 56, 'Intermediate': 79, 'Advanced': 105, 'Elite': 134},
    95: {'Beginner': 41, 'Novice': 60, 'Intermediate': 83, 'Advanced': 111, 'Elite': 141},
    100: {'Beginner': 44, 'Novice': 64, 'Intermediate': 88, 'Advanced': 116, 'Elite': 147},
    105: {'Beginner': 47, 'Novice': 68, 'Intermediate': 93, 'Advanced': 121, 'Elite': 153},
    110: {'Beginner': 51, 'Novice': 71, 'Intermediate': 97, 'Advanced': 127, 'Elite': 158},
    115: {'Beginner': 54, 'Novice': 75, 'Intermediate': 101, 'Advanced': 132, 'Elite': 164},
    120: {'Beginner': 57, 'Novice': 79, 'Intermediate': 106, 'Advanced': 136, 'Elite': 169},
    125: {'Beginner': 60, 'Novice': 82, 'Intermediate': 110, 'Advanced': 141, 'Elite': 175},
    130: {'Beginner': 63, 'Novice': 86, 'Intermediate': 114, 'Advanced': 146, 'Elite': 180},
    135: {'Beginner': 66, 'Novice': 89, 'Intermediate': 118, 'Advanced': 150, 'Elite': 185},
    140: {'Beginner': 69, 'Novice': 93, 'Intermediate': 122, 'Advanced': 155, 'Elite': 190}
}

# Scraped on 2026-03-12
SIT_UPS_STANDARDS_KG = {
    50: {'Beginner': 1, 'Novice': 25, 'Intermediate': 69, 'Advanced': 128, 'Elite': 196},
    55: {'Beginner': 1, 'Novice': 25, 'Intermediate': 67, 'Advanced': 122, 'Elite': 185},
    60: {'Beginner': 1, 'Novice': 25, 'Intermediate': 65, 'Advanced': 117, 'Elite': 176},
    65: {'Beginner': 1, 'Novice': 25, 'Intermediate': 63, 'Advanced': 112, 'Elite': 168},
    70: {'Beginner': 1, 'Novice': 24, 'Intermediate': 61, 'Advanced': 108, 'Elite': 161},
    75: {'Beginner': 1, 'Novice': 24, 'Intermediate': 59, 'Advanced': 104, 'Elite': 154},
    80: {'Beginner': 1, 'Novice': 24, 'Intermediate': 57, 'Advanced': 100, 'Elite': 148},
    85: {'Beginner': 1, 'Novice': 23, 'Intermediate': 56, 'Advanced': 96, 'Elite': 142},
    90: {'Beginner': 1, 'Novice': 23, 'Intermediate': 54, 'Advanced': 93, 'Elite': 137},
    95: {'Beginner': 1, 'Novice': 22, 'Intermediate': 52, 'Advanced': 90, 'Elite': 132},
    100: {'Beginner': 1, 'Novice': 21, 'Intermediate': 51, 'Advanced': 87, 'Elite': 128},
    105: {'Beginner': 1, 'Novice': 21, 'Intermediate': 49, 'Advanced': 84, 'Elite': 123},
    110: {'Beginner': 1, 'Novice': 20, 'Intermediate': 48, 'Advanced': 82, 'Elite': 120},
    115: {'Beginner': 1, 'Novice': 20, 'Intermediate': 47, 'Advanced': 79, 'Elite': 116},
    120: {'Beginner': 1, 'Novice': 19, 'Intermediate': 45, 'Advanced': 77, 'Elite': 112},
    125: {'Beginner': 1, 'Novice': 19, 'Intermediate': 44, 'Advanced': 75, 'Elite': 109},
    130: {'Beginner': 1, 'Novice': 18, 'Intermediate': 43, 'Advanced': 73, 'Elite': 106},
    135: {'Beginner': 1, 'Novice': 18, 'Intermediate': 42, 'Advanced': 71, 'Elite': 103},
    140: {'Beginner': 1, 'Novice': 17, 'Intermediate': 41, 'Advanced': 69, 'Elite': 100}
}

# Scraped on 2026-03-12
SLED_LEG_PRESS_STANDARDS_KG = {
    50: {'Beginner': 40, 'Novice': 78, 'Intermediate': 132, 'Advanced': 199, 'Elite': 276},
    55: {'Beginner': 50, 'Novice': 91, 'Intermediate': 149, 'Advanced': 220, 'Elite': 300},
    60: {'Beginner': 59, 'Novice': 104, 'Intermediate': 165, 'Advanced': 239, 'Elite': 323},
    65: {'Beginner': 69, 'Novice': 117, 'Intermediate': 181, 'Advanced': 258, 'Elite': 345},
    70: {'Beginner': 78, 'Novice': 129, 'Intermediate': 196, 'Advanced': 277, 'Elite': 366},
    75: {'Beginner': 88, 'Novice': 141, 'Intermediate': 211, 'Advanced': 294, 'Elite': 386},
    80: {'Beginner': 97, 'Novice': 153, 'Intermediate': 225, 'Advanced': 311, 'Elite': 406},
    85: {'Beginner': 106, 'Novice': 164, 'Intermediate': 239, 'Advanced': 327, 'Elite': 424},
    90: {'Beginner': 115, 'Novice': 176, 'Intermediate': 252, 'Advanced': 343, 'Elite': 442},
    95: {'Beginner': 124, 'Novice': 187, 'Intermediate': 265, 'Advanced': 358, 'Elite': 459},
    100: {'Beginner': 133, 'Novice': 197, 'Intermediate': 278, 'Advanced': 373, 'Elite': 476},
    105: {'Beginner': 142, 'Novice': 208, 'Intermediate': 290, 'Advanced': 387, 'Elite': 492},
    110: {'Beginner': 150, 'Novice': 218, 'Intermediate': 302, 'Advanced': 401, 'Elite': 508},
    115: {'Beginner': 158, 'Novice': 228, 'Intermediate': 314, 'Advanced': 414, 'Elite': 523},
    120: {'Beginner': 166, 'Novice': 238, 'Intermediate': 326, 'Advanced': 427, 'Elite': 538},
    125: {'Beginner': 174, 'Novice': 247, 'Intermediate': 337, 'Advanced': 440, 'Elite': 552},
    130: {'Beginner': 182, 'Novice': 256, 'Intermediate': 348, 'Advanced': 453, 'Elite': 566},
    135: {'Beginner': 190, 'Novice': 266, 'Intermediate': 358, 'Advanced': 465, 'Elite': 579},
    140: {'Beginner': 198, 'Novice': 275, 'Intermediate': 369, 'Advanced': 477, 'Elite': 593}
}

# Scraped on 2026-03-12
SMITH_MACHINE_BENCH_PRESS_STANDARDS_KG = {
    50: {'Beginner': 27, 'Novice': 42, 'Intermediate': 62, 'Advanced': 85, 'Elite': 111},
    55: {'Beginner': 31, 'Novice': 48, 'Intermediate': 68, 'Advanced': 93, 'Elite': 120},
    60: {'Beginner': 36, 'Novice': 53, 'Intermediate': 75, 'Advanced': 101, 'Elite': 129},
    65: {'Beginner': 40, 'Novice': 59, 'Intermediate': 81, 'Advanced': 108, 'Elite': 137},
    70: {'Beginner': 45, 'Novice': 64, 'Intermediate': 88, 'Advanced': 115, 'Elite': 145},
    75: {'Beginner': 49, 'Novice': 69, 'Intermediate': 94, 'Advanced': 122, 'Elite': 152},
    80: {'Beginner': 53, 'Novice': 74, 'Intermediate': 99, 'Advanced': 128, 'Elite': 160},
    85: {'Beginner': 57, 'Novice': 79, 'Intermediate': 105, 'Advanced': 135, 'Elite': 167},
    90: {'Beginner': 61, 'Novice': 83, 'Intermediate': 110, 'Advanced': 141, 'Elite': 173},
    95: {'Beginner': 65, 'Novice': 88, 'Intermediate': 115, 'Advanced': 147, 'Elite': 180},
    100: {'Beginner': 69, 'Novice': 92, 'Intermediate': 120, 'Advanced': 152, 'Elite': 186},
    105: {'Beginner': 72, 'Novice': 96, 'Intermediate': 125, 'Advanced': 158, 'Elite': 192},
    110: {'Beginner': 76, 'Novice': 101, 'Intermediate': 130, 'Advanced': 163, 'Elite': 198},
    115: {'Beginner': 80, 'Novice': 105, 'Intermediate': 134, 'Advanced': 168, 'Elite': 204},
    120: {'Beginner': 83, 'Novice': 109, 'Intermediate': 139, 'Advanced': 173, 'Elite': 209},
    125: {'Beginner': 86, 'Novice': 112, 'Intermediate': 143, 'Advanced': 178, 'Elite': 215},
    130: {'Beginner': 90, 'Novice': 116, 'Intermediate': 148, 'Advanced': 183, 'Elite': 220},
    135: {'Beginner': 93, 'Novice': 120, 'Intermediate': 152, 'Advanced': 187, 'Elite': 225},
    140: {'Beginner': 96, 'Novice': 123, 'Intermediate': 156, 'Advanced': 192, 'Elite': 230}
}

# Scraped on 2026-03-12
SNATCH_STANDARDS_KG = {
    50: {'Beginner': 20, 'Novice': 33, 'Intermediate': 50, 'Advanced': 71, 'Elite': 94},
    55: {'Beginner': 23, 'Novice': 37, 'Intermediate': 55, 'Advanced': 77, 'Elite': 101},
    60: {'Beginner': 26, 'Novice': 40, 'Intermediate': 59, 'Advanced': 82, 'Elite': 107},
    65: {'Beginner': 29, 'Novice': 44, 'Intermediate': 64, 'Advanced': 87, 'Elite': 113},
    70: {'Beginner': 31, 'Novice': 47, 'Intermediate': 68, 'Advanced': 92, 'Elite': 118},
    75: {'Beginner': 34, 'Novice': 51, 'Intermediate': 72, 'Advanced': 97, 'Elite': 124},
    80: {'Beginner': 37, 'Novice': 54, 'Intermediate': 76, 'Advanced': 101, 'Elite': 129},
    85: {'Beginner': 39, 'Novice': 57, 'Intermediate': 79, 'Advanced': 105, 'Elite': 133},
    90: {'Beginner': 42, 'Novice': 60, 'Intermediate': 83, 'Advanced': 109, 'Elite': 138},
    95: {'Beginner': 44, 'Novice': 63, 'Intermediate': 86, 'Advanced': 113, 'Elite': 142},
    100: {'Beginner': 47, 'Novice': 66, 'Intermediate': 90, 'Advanced': 117, 'Elite': 147},
    105: {'Beginner': 49, 'Novice': 69, 'Intermediate': 93, 'Advanced': 121, 'Elite': 151},
    110: {'Beginner': 51, 'Novice': 71, 'Intermediate': 96, 'Advanced': 124, 'Elite': 155},
    115: {'Beginner': 53, 'Novice': 74, 'Intermediate': 99, 'Advanced': 128, 'Elite': 158},
    120: {'Beginner': 56, 'Novice': 76, 'Intermediate': 102, 'Advanced': 131, 'Elite': 162},
    125: {'Beginner': 58, 'Novice': 79, 'Intermediate': 105, 'Advanced': 134, 'Elite': 166},
    130: {'Beginner': 60, 'Novice': 81, 'Intermediate': 108, 'Advanced': 137, 'Elite': 169},
    135: {'Beginner': 62, 'Novice': 84, 'Intermediate': 110, 'Advanced': 140, 'Elite': 173},
    140: {'Beginner': 64, 'Novice': 86, 'Intermediate': 113, 'Advanced': 143, 'Elite': 176}
}

# Scraped on 2026-03-12
SUMO_DEADLIFT_STANDARDS_KG = {
    50: {'Beginner': 52, 'Novice': 75, 'Intermediate': 105, 'Advanced': 140, 'Elite': 178},
    55: {'Beginner': 60, 'Novice': 85, 'Intermediate': 117, 'Advanced': 154, 'Elite': 194},
    60: {'Beginner': 68, 'Novice': 95, 'Intermediate': 128, 'Advanced': 167, 'Elite': 208},
    65: {'Beginner': 76, 'Novice': 105, 'Intermediate': 139, 'Advanced': 179, 'Elite': 222},
    70: {'Beginner': 84, 'Novice': 114, 'Intermediate': 150, 'Advanced': 191, 'Elite': 235},
    75: {'Beginner': 91, 'Novice': 122, 'Intermediate': 160, 'Advanced': 202, 'Elite': 247},
    80: {'Beginner': 99, 'Novice': 131, 'Intermediate': 170, 'Advanced': 213, 'Elite': 259},
    85: {'Beginner': 106, 'Novice': 139, 'Intermediate': 179, 'Advanced': 224, 'Elite': 271},
    90: {'Beginner': 113, 'Novice': 147, 'Intermediate': 188, 'Advanced': 234, 'Elite': 282},
    95: {'Beginner': 120, 'Novice': 155, 'Intermediate': 197, 'Advanced': 244, 'Elite': 293},
    100: {'Beginner': 126, 'Novice': 162, 'Intermediate': 205, 'Advanced': 253, 'Elite': 303},
    105: {'Beginner': 133, 'Novice': 170, 'Intermediate': 214, 'Advanced': 262, 'Elite': 313},
    110: {'Beginner': 139, 'Novice': 177, 'Intermediate': 222, 'Advanced': 271, 'Elite': 323},
    115: {'Beginner': 145, 'Novice': 184, 'Intermediate': 229, 'Advanced': 280, 'Elite': 332},
    120: {'Beginner': 151, 'Novice': 191, 'Intermediate': 237, 'Advanced': 288, 'Elite': 342},
    125: {'Beginner': 157, 'Novice': 197, 'Intermediate': 244, 'Advanced': 296, 'Elite': 351},
    130: {'Beginner': 163, 'Novice': 204, 'Intermediate': 252, 'Advanced': 304, 'Elite': 359},
    135: {'Beginner': 169, 'Novice': 210, 'Intermediate': 259, 'Advanced': 312, 'Elite': 368},
    140: {'Beginner': 174, 'Novice': 217, 'Intermediate': 266, 'Advanced': 320, 'Elite': 376}
}

# Scraped on 2026-03-12
T_BAR_ROW_STANDARDS_KG = {
    50: {'Beginner': 17, 'Novice': 32, 'Intermediate': 52, 'Advanced': 77, 'Elite': 106},
    55: {'Beginner': 21, 'Novice': 37, 'Intermediate': 59, 'Advanced': 85, 'Elite': 115},
    60: {'Beginner': 25, 'Novice': 42, 'Intermediate': 65, 'Advanced': 93, 'Elite': 124},
    65: {'Beginner': 29, 'Novice': 47, 'Intermediate': 71, 'Advanced': 101, 'Elite': 133},
    70: {'Beginner': 33, 'Novice': 52, 'Intermediate': 77, 'Advanced': 108, 'Elite': 141},
    75: {'Beginner': 37, 'Novice': 57, 'Intermediate': 83, 'Advanced': 115, 'Elite': 149},
    80: {'Beginner': 40, 'Novice': 62, 'Intermediate': 89, 'Advanced': 121, 'Elite': 156},
    85: {'Beginner': 44, 'Novice': 66, 'Intermediate': 94, 'Advanced': 127, 'Elite': 164},
    90: {'Beginner': 48, 'Novice': 71, 'Intermediate': 100, 'Advanced': 134, 'Elite': 171},
    95: {'Beginner': 51, 'Novice': 75, 'Intermediate': 105, 'Advanced': 140, 'Elite': 177},
    100: {'Beginner': 55, 'Novice': 79, 'Intermediate': 110, 'Advanced': 145, 'Elite': 184},
    105: {'Beginner': 58, 'Novice': 83, 'Intermediate': 115, 'Advanced': 151, 'Elite': 190},
    110: {'Beginner': 62, 'Novice': 88, 'Intermediate': 120, 'Advanced': 156, 'Elite': 196},
    115: {'Beginner': 65, 'Novice': 92, 'Intermediate': 124, 'Advanced': 162, 'Elite': 202},
    120: {'Beginner': 68, 'Novice': 95, 'Intermediate': 129, 'Advanced': 167, 'Elite': 208},
    125: {'Beginner': 72, 'Novice': 99, 'Intermediate': 133, 'Advanced': 172, 'Elite': 214},
    130: {'Beginner': 75, 'Novice': 103, 'Intermediate': 137, 'Advanced': 177, 'Elite': 219},
    135: {'Beginner': 78, 'Novice': 107, 'Intermediate': 142, 'Advanced': 182, 'Elite': 224},
    140: {'Beginner': 81, 'Novice': 110, 'Intermediate': 146, 'Advanced': 186, 'Elite': 229}
}

# Scraped on 2026-03-12
TRICEP_PUSHDOWN_STANDARDS_KG = {
    50: {'Beginner': 7, 'Novice': 18, 'Intermediate': 35, 'Advanced': 56, 'Elite': 82},
    55: {'Beginner': 10, 'Novice': 21, 'Intermediate': 39, 'Advanced': 62, 'Elite': 89},
    60: {'Beginner': 12, 'Novice': 24, 'Intermediate': 43, 'Advanced': 67, 'Elite': 95},
    65: {'Beginner': 14, 'Novice': 27, 'Intermediate': 47, 'Advanced': 72, 'Elite': 100},
    70: {'Beginner': 16, 'Novice': 30, 'Intermediate': 51, 'Advanced': 77, 'Elite': 106},
    75: {'Beginner': 18, 'Novice': 33, 'Intermediate': 54, 'Advanced': 81, 'Elite': 111},
    80: {'Beginner': 20, 'Novice': 36, 'Intermediate': 58, 'Advanced': 85, 'Elite': 116},
    85: {'Beginner': 22, 'Novice': 39, 'Intermediate': 61, 'Advanced': 89, 'Elite': 121},
    90: {'Beginner': 24, 'Novice': 41, 'Intermediate': 65, 'Advanced': 93, 'Elite': 126},
    95: {'Beginner': 26, 'Novice': 44, 'Intermediate': 68, 'Advanced': 97, 'Elite': 130},
    100: {'Beginner': 28, 'Novice': 46, 'Intermediate': 71, 'Advanced': 101, 'Elite': 134},
    105: {'Beginner': 30, 'Novice': 49, 'Intermediate': 74, 'Advanced': 105, 'Elite': 139},
    110: {'Beginner': 32, 'Novice': 51, 'Intermediate': 77, 'Advanced': 108, 'Elite': 143},
    115: {'Beginner': 33, 'Novice': 54, 'Intermediate': 80, 'Advanced': 112, 'Elite': 147},
    120: {'Beginner': 35, 'Novice': 56, 'Intermediate': 83, 'Advanced': 115, 'Elite': 150},
    125: {'Beginner': 37, 'Novice': 58, 'Intermediate': 86, 'Advanced': 118, 'Elite': 154},
    130: {'Beginner': 39, 'Novice': 60, 'Intermediate': 88, 'Advanced': 121, 'Elite': 158},
    135: {'Beginner': 41, 'Novice': 63, 'Intermediate': 91, 'Advanced': 124, 'Elite': 161},
    140: {'Beginner': 42, 'Novice': 65, 'Intermediate': 93, 'Advanced': 127, 'Elite': 165}
}
