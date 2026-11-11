#!/usr/bin/env python3
"""
Inspect all historical training splits duration and exercises in the terminal,
with automatic movement slot clustering and substitution detection.
Usage:
    python scripts/show_splits.py
"""

import os
import sys
from collections import Counter, defaultdict
from datetime import datetime

# Ensure project root is on path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.models import Log
from core.plan_generator import get_deload_dates
from core.profile_manager import ProfileManager
from core.standards import EXERCISE_STANDARDS


def clean_ex_name(slug: str) -> str:
    """Format canonical slug or variable to clean human-readable title."""
    if slug in EXERCISE_STANDARDS:
        return EXERCISE_STANDARDS[slug].get("name", slug.replace("_", " ").replace("-", " ").title())
    return slug.replace("_", " ").replace("-", " ").title()


def resolve_day_slots(sessions_list: list) -> tuple:
    """
    Cluster exercises into fixed workout movement slots based on execution
    order, frequency, and mutual exclusivity to identify substitutions.

    :param sessions_list: List of sessions, where each session is an ordered list of exercise names.
    :return: Tuple of (slots_list, unassigned_list) where slots_list is [(primary_name, [alt_names])].
    """
    total = len(sessions_list)
    if total == 0:
        return [], []

    ex_counts = Counter()
    ex_pos = defaultdict(list)
    for s in sessions_list:
        n = len(s)
        for idx, ex in enumerate(s):
            ex_counts[ex] += 1
            rel_pos = idx / max(1, n - 1) if n > 1 else 0.5
            ex_pos[ex].append(rel_pos)

    ex_avg_pos = {ex: sum(pos) / len(pos) for ex, pos in ex_pos.items()}

    # Primary exercises: those appearing in >= 40% of sessions
    primary = [e for e, c in ex_counts.items() if (c / total) >= 0.40]
    if not primary:
        primary = [e for e, _ in ex_counts.most_common(6)]

    # Collapse alternating primaries (e.g. 50/50 Week A / Week B rotation) that never co-occur in the same slot
    primary_by_freq = sorted(primary, key=lambda e: (-ex_counts[e], list(ex_counts.keys()).index(e)))
    anchors = []
    slot_alts = defaultdict(list)

    for cand in primary_by_freq:
        best_anchor = None
        best_dist = 999.0
        for anch in anchors:
            co_occur = sum(1 for s in sessions_list if anch in s and cand in s)
            if co_occur == 0:
                dist = abs(ex_avg_pos[anch] - ex_avg_pos[cand])
                if dist < 0.35 and dist < best_dist:
                    best_dist = dist
                    best_anchor = anch
        if best_anchor:
            slot_alts[best_anchor].append(cand)
        else:
            anchors.append(cand)

    # Sort slot anchors by average execution order in the workout
    anchors.sort(key=lambda e: ex_avg_pos[e])

    # Detect substitutes from remaining less-frequent exercises
    remaining = [e for e in ex_counts.keys() if e not in primary]
    unassigned = []

    for other in remaining:
        best_prim = None
        best_dist = 999.0
        for prim in anchors:
            # Check mutual exclusivity (exercises that replace each other rarely co-occur in the same session)
            co_occur = sum(1 for s in sessions_list if prim in s and other in s)
            if co_occur == 0:
                dist = abs(ex_avg_pos[prim] - ex_avg_pos[other])
                if dist < 0.35 and dist < best_dist:
                    best_dist = dist
                    best_prim = prim
        if best_prim:
            slot_alts[best_prim].append(other)
        else:
            unassigned.append(other)

    results = []
    for prim in anchors:
        alts = slot_alts.get(prim, [])
        results.append((prim, alts))

    return results, unassigned


def build_splits_report(user_data: dict, deload_dates: set) -> str:
    """Segment workout history into chronological training splits and format plain text."""
    sorted_dates = sorted(user_data.keys())

    training_splits = []
    current_sessions = []

    for d in sorted_dates:
        # Deloads or isolated PR checks define split boundaries
        if d in ["2026-01-09", "2026-03-12"] or d in deload_dates:
            if current_sessions:
                training_splits.append(current_sessions)
                current_sessions = []
            continue

        current_sessions.append(d)

    if current_sessions:
        training_splits.append(current_sessions)

    lines = [
        "============================================================",
        "             ALL TRAINING SPLITS - HISTORICAL LOG           ",
        "============================================================",
        f"Total Training Splits Identified: {len(training_splits)}",
        "",
        "SUMMARY OVERVIEW:",
    ]

    for idx, sdates in enumerate(training_splits, 1):
        d_start = datetime.strptime(sdates[0], "%Y-%m-%d")
        d_end = datetime.strptime(sdates[-1], "%Y-%m-%d")
        days = (d_end - d_start).days
        weeks = days / 7.0
        status = " [ACTIVE]" if idx == len(training_splits) else ""
        lines.append(f"  Split {idx}: {sdates[0]} -> {sdates[-1]} ({weeks:.1f} wks, {len(sdates)} workouts){status}")

    lines.append("")
    lines.append("============================================================")
    lines.append("                  DETAILED SPLIT BREAKDOWN                  ")
    lines.append("============================================================")

    for idx, sdates in enumerate(training_splits, 1):
        d_start = datetime.strptime(sdates[0], "%Y-%m-%d")
        d_end = datetime.strptime(sdates[-1], "%Y-%m-%d")
        days = (d_end - d_start).days
        weeks = days / 7.0
        is_current = (idx == len(training_splits))
        header_title = f"SPLIT {idx}" + (" [CURRENT / ACTIVE]" if is_current else "")

        lines.append("")
        lines.append("------------------------------------------------------------")
        lines.append(header_title)
        lines.append("------------------------------------------------------------")
        lines.append(f"Date Range:  {sdates[0]} to {sdates[-1]}")
        lines.append(f"Duration:    {weeks:.1f} weeks ({days} days)")
        lines.append(f"Workouts:    {len(sdates)} completed sessions")

        # Gather ordered exercise lists per numbered training day
        days_data = defaultdict(list)
        for d in sdates:
            dv = user_data[d].get("day")
            if isinstance(dv, int):
                ex_list = [clean_ex_name(k) for k, v in user_data[d].items() if isinstance(v, Log)]
                days_data[dv].append(ex_list)

        for dn in sorted(days_data.keys()):
            slots, unassigned = resolve_day_slots(days_data[dn])
            lines.append(f"\n  Day {dn} ({len(slots)} exercises):")
            for prim, alts in slots:
                alt_text = f" [Alt: {', '.join(alts)}]" if alts else ""
                lines.append(f"    - {prim}{alt_text}")
            if unassigned:
                lines.append(f"    (Occasional: {', '.join(unassigned)})")

        lines.append("")

    lines.append("============================================================")
    lines.append("                        END OF REPORT                       ")
    lines.append("============================================================")

    return "\n".join(lines)


def main() -> None:
    # 1. Resolve sessions.py path from active profile
    pm = ProfileManager()
    profile = pm.get_active_profile()
    sessions_dir = profile.sessions_dir if profile else os.path.join("G:\\My Drive", "2025 Health")
    sessions_file = os.path.join(sessions_dir, "sessions.py")

    if not os.path.exists(sessions_file):
        sessions_file = os.path.join(PROJECT_ROOT, "sessions.py")

    if not os.path.exists(sessions_file):
        print(f"Error: sessions.py not found at {sessions_file}")
        return

    # 2. Import sessions dynamically
    import importlib.util
    spec = importlib.util.spec_from_file_location("sessions", sessions_file)
    if spec is None or spec.loader is None:
        print("Error: Could not load spec for sessions.py")
        return
    sess = importlib.util.module_from_spec(spec)
    sys.modules["sessions"] = sess
    spec.loader.exec_module(sess)

    # 3. Compute deload dates and split text
    deload_dates = get_deload_dates(sessions_file)
    full_text = build_splits_report(sess.USER_DATA, deload_dates)

    # 4. Print directly to terminal
    print(full_text)


if __name__ == "__main__":
    main()
