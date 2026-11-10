import sys
sys.path.append('c:/Users/runiza/GoogleProjects/iron-log')
import importlib.util
from collections import Counter, defaultdict
from statistics import median

spec = importlib.util.spec_from_file_location('sessions', 'g:/My Drive/2025 Health/sessions.py')
sess = importlib.util.module_from_spec(spec)
sys.modules['sessions'] = sess
spec.loader.exec_module(sess)

from core.models import Log
from core.standards import EXERCISE_STANDARDS
from core.plan_generator import get_deload_dates

def clean_ex_name(slug: str) -> str:
    if slug in EXERCISE_STANDARDS:
        return EXERCISE_STANDARDS[slug].get("name", slug.replace("_", " ").replace("-", " ").title())
    return slug.replace("_", " ").replace("-", " ").title()

user_data = sess.USER_DATA
deload_dates = get_deload_dates('g:/My Drive/2025 Health/sessions.py')

sorted_dates = sorted(user_data.keys())

# Segment sessions into training splits
training_splits = []
current_sessions = []

for d in sorted_dates:
    if d in ["2026-01-09", "2026-03-12"] or d in deload_dates:
        if current_sessions:
            training_splits.append(current_sessions)
            current_sessions = []
        continue
    current_sessions.append(d)

if current_sessions:
    training_splits.append(current_sessions)

def resolve_day_slots(sessions_list):
    """
    sessions_list: list of lists, where each inner list is [ex1, ex2, ex3...] in workout order
    returns: list of (primary_ex, [alts])
    """
    if not sessions_list:
        return []
    
    # 1. Overall frequency of each exercise across all sessions of this day
    total_sessions = len(sessions_list)
    ex_counts = Counter()
    for s in sessions_list:
        for ex in s:
            ex_counts[ex] += 1
            
    # 2. Typical number of exercises per session (median)
    lengths = [len(s) for s in sessions_list]
    k = int(round(median(lengths)))
    
    # 3. For each session, track which slot position each exercise occupied
    # Map ex -> average relative position (0.0 to 1.0)
    ex_pos = defaultdict(list)
    for s in sessions_list:
        n = len(s)
        for idx, ex in enumerate(s):
            rel_pos = idx / max(1, n - 1) if n > 1 else 0.5
            ex_pos[ex].append(rel_pos)
            
    ex_avg_pos = {ex: sum(pos)/len(pos) for ex, pos in ex_pos.items()}
    
    # Sort all exercises by their average relative position in the workout
    sorted_by_pos = sorted(ex_counts.keys(), key=lambda e: ex_avg_pos[e])
    
    # Identify primary exercises vs substitutes
    # An exercise is "Primary" if it appears in at least 40% of sessions
    # If two exercises appear at very close relative position, and their combined frequency is high,
    # the less frequent one is an alternative to the more frequent one.
    
    # Let's see: we can cluster adjacent exercises by position if they are mutually exclusive in workouts
    slots = []
    used_as_alt = set()
    
    for i, ex in enumerate(sorted_by_pos):
        if ex in used_as_alt:
            continue
        
        freq = ex_counts[ex]
        pct = (freq / total_sessions) * 100
        
        # Look for potential substitutes:
        # Exercises close in position that NEVER or rarely occur in the same workout with `ex`
        alts = []
        for other in sorted_by_pos:
            if other == ex or other in used_as_alt:
                continue
            # check co-occurrence in sessions
            co_occur = sum(1 for s in sessions_list if ex in s and other in s)
            if co_occur == 0:
                # Check position proximity
                if abs(ex_avg_pos[ex] - ex_avg_pos[other]) < 0.25:
                    # other is an alternative to ex (or vice-versa)
                    if ex_counts[ex] >= ex_counts[other]:
                        alts.append(other)
                        used_as_alt.add(other)
                    
        slots.append((ex, pct, alts))
        
    return slots

for split_idx, sdates in enumerate(training_splits, 1):
    print(f"\n=== SPLIT {split_idx} ===")
    days_data = defaultdict(list)
    for d in sdates:
        dv = user_data[d].get('day')
        if isinstance(dv, int):
            ex_list = [clean_ex_name(k) for k, v in user_data[d].items() if isinstance(v, Log)]
            days_data[dv].append(ex_list)
            
    for dn in sorted(days_data.keys()):
        print(f"  Day {dn} ({len(days_data[dn])} sessions):")
        resolved = resolve_day_slots(days_data[dn])
        for prim, pct, alts in resolved:
            alt_str = f" [Alt: {', '.join(alts)}]" if alts else ""
            print(f"    - {prim}{alt_str} ({pct:.0f}%)")

