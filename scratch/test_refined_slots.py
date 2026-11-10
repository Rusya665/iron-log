import sys
sys.path.append('c:/Users/runiza/GoogleProjects/iron-log')
import importlib.util
from collections import Counter, defaultdict

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
    total = len(sessions_list)
    if total == 0:
        return []
        
    ex_counts = Counter()
    ex_pos = defaultdict(list)
    for s in sessions_list:
        n = len(s)
        for idx, ex in enumerate(s):
            ex_counts[ex] += 1
            rel_pos = idx / max(1, n - 1) if n > 1 else 0.5
            ex_pos[ex].append(rel_pos)
            
    ex_avg_pos = {ex: sum(pos)/len(pos) for ex, pos in ex_pos.items()}
    
    # Primary exercises: those appearing in >= 40% of sessions
    # (or top N most frequent if all are lower)
    primary = [e for e, c in ex_counts.items() if (c / total) >= 0.40]
    if not primary:
        primary = [e for e, _ in ex_counts.most_common(6)]
        
    # Sort primaries by average workout position
    primary.sort(key=lambda e: ex_avg_pos[e])
    
    # Identify alternatives from remaining exercises
    remaining = [e for e in ex_counts.keys() if e not in primary]
    
    # For each remaining, find best matching primary:
    # 1. Never or rarely co-occurs in same workout
    # 2. Closest in average position
    slot_alts = defaultdict(list)
    unassigned = []
    
    for other in remaining:
        best_prim = None
        best_dist = 999.0
        for prim in primary:
            co_occur = sum(1 for s in sessions_list if prim in s and other in s)
            if co_occur == 0:
                dist = abs(ex_avg_pos[prim] - ex_avg_pos[other])
                if dist < 0.25 and dist < best_dist:
                    best_dist = dist
                    best_prim = prim
        if best_prim:
            slot_alts[best_prim].append(other)
        else:
            unassigned.append(other)
            
    results = []
    for prim in primary:
        alts = slot_alts.get(prim, [])
        results.append((prim, alts))
        
    return results, unassigned

for split_idx, sdates in enumerate(training_splits, 1):
    print(f"\n============================================================")
    print(f"SPLIT {split_idx} ({sdates[0]} to {sdates[-1]})")
    print(f"============================================================")
    days_data = defaultdict(list)
    for d in sdates:
        dv = user_data[d].get('day')
        if isinstance(dv, int):
            ex_list = [clean_ex_name(k) for k, v in user_data[d].items() if isinstance(v, Log)]
            days_data[dv].append(ex_list)
            
    for dn in sorted(days_data.keys()):
        print(f"\n  Day {dn}:")
        slots, unassigned = resolve_day_slots(days_data[dn])
        for prim, alts in slots:
            alt_text = f" [Alt: {', '.join(alts)}]" if alts else ""
            print(f"    - {prim}{alt_text}")
        if unassigned:
            print(f"    (Occasional: {', '.join(unassigned)})")

