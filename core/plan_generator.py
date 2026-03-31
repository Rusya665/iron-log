import re

def generate_next_3_days(sessions_file_path: str) -> list[int]:
    """
    Parses sessions.py, looks at the recent history to grab the last 3 days
    of workouts blocks by `# Day X` marker. Then automatically generates UP TO
    the next 3 consecutive days to complete a 3-day block, appending them to
    the USER_DATA block while dropping any comments.
    Uses 'YYYY-MM-DD' placeholder for dates.
    Returns the days that were added (e.g. [2, 3] or [3] or [1,2,3]).
    """
    with open(sessions_file_path, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    parsed_blocks = {} # maps Day number (1, 2, 3) to list of strings (block content)
    last_seen_day = None
    current_year = None
    
    line_idx = 0
    # Search for blocks
    # Pattern to match e.g.     "2026-03-15" : { # Day 1
    # or     "2026-03-22": { # Day 1
    pattern = re.compile(r'^([ \t]*)"(\d{4})-[^"]+"\s*:\s*\{\s*#\s*[Dd]ay\s*(\d+)')

    while line_idx < len(lines):
        line = lines[line_idx]
        match = pattern.match(line)
        if match:
            indent = match.group(1)
            year = match.group(2)
            day = int(match.group(3))
            
            block_lines = []
            idx2 = line_idx + 1
            while idx2 < len(lines):
                l2 = lines[idx2]
                if l2.startswith(indent + "}") or l2.strip() == "},":
                    parsed_blocks[day] = block_lines
                    last_seen_day = day
                    current_year = year
                    break
                else:
                    if not l2.strip().startswith('#'):
                        cleaned = l2.split('#')[0].rstrip()
                        if cleaned.strip():
                            block_lines.append(cleaned)
                idx2 += 1
                
            line_idx = idx2
        else:
            line_idx += 1

    if last_seen_day is None:
        raise ValueError("Could not find any '# Day X' markers in sessions.py")
        
    days_to_add = []
    if last_seen_day == 1:
        days_to_add = [2, 3]
    elif last_seen_day == 2:
        days_to_add = [3]
    elif last_seen_day == 3:
        days_to_add = [1, 2, 3]
        
    injection_lines = []
    for d in days_to_add:
        if d not in parsed_blocks:
            raise ValueError(f"Cannot generate: Could not find previous history for Day {d}")
            
        injection_lines.append("")
        injection_lines.append(f'    "{current_year}-MM-DD": {{ # Day {d}')
        injection_lines.extend(parsed_blocks[d])
        injection_lines.append('    },')
        
    # Find USER_DATA to know exactly where to insert this
    user_data_start = -1
    for i, line in enumerate(lines):
        if line.startswith("USER_DATA = {"):
            user_data_start = i
            break
            
    if user_data_start == -1:
        raise ValueError("Could not find 'USER_DATA = {' block in sessions.py")
        
    # Find the very last closing brace `}` at indentation 0 that closes USER_DATA
    user_data_end = -1
    for i in range(user_data_start + 1, len(lines)):
        if lines[i] == "}":
            user_data_end = i
            
    if user_data_end == -1:
        raise ValueError("Could not find the closing '}' for USER_DATA")
        
    # We insert our injection right before the closing brace of USER_DATA
    # For safety, ensure it doesn't break formatting
    for line in injection_lines:
        lines.insert(user_data_end, line)
        user_data_end += 1

    with open(sessions_file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
        
    return days_to_add
