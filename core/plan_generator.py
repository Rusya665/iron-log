"""Plan generator — cycle-aware session planning.

Public API
----------
detect_cycle(user_data)         -> (N, last_day) | (None, None)
days_to_generate(N, last_day)   -> list[int]
build_planned_sessions(path, day_numbers) -> list[PlannedSession]
write_planned_sessions(path, sessions)
create_initial_sessions_py(path, owner_name, sex, sessions)
"""

import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

# ---------------------------------------------------------------------------
# Data structures returned to the UI
# ---------------------------------------------------------------------------


@dataclass
class PlannedExercise:
    var_name: str  # Python variable name in sessions.py  (e.g. "squat")
    display_name: str  # Human-readable (e.g. "Squat")
    sets: int
    reps: str  # comma-separated reps, e.g. "6" or "6, 6, 6" or "10, 8, 6"
    mass: str  # comma-separated mass, e.g. "100.0" or "100.0, 97.5"
    comment: str = ""  # optional user comment (written as  # "text")


@dataclass
class PlannedSession:
    day_number: int  # e.g. 3
    date_str: str  # "YYYY-MM-DD" placeholder or suggested date
    exercises: List[PlannedExercise] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Cycle detection
# ---------------------------------------------------------------------------


def detect_cycle(user_data: dict) -> Tuple[Optional[int], Optional[int]]:
    """Scan USER_DATA for Day(int) sessions and determine the split cycle.

    Algorithm
    ---------
    Collect all integer day values in chronological order.
    Walk backward: when we see prev > current, that jump is the cycle boundary.
    The larger value = N (cycle length).

    Returns
    -------
    (N, last_day)  — both ints, or (None, None) when not enough data.
    """
    int_days: List[int] = []
    for date_str in sorted(user_data.keys()):
        val = user_data[date_str].get("day")
        if isinstance(val, int):
            int_days.append(val)

    if len(int_days) < 2:
        res = int_days[-1] if int_days else None
        return res, res

    last_day = int_days[-1]

    for i in range(len(int_days) - 1, 0, -1):
        if int_days[i - 1] > int_days[i]:
            return int_days[i - 1], last_day  # (N, last_day)

    # All ascending — no cycle boundary found yet.
    # Return max day as a guessed N so the user can still plan the next cycle.
    return int_days[-1], last_day


def days_to_generate(N: int, last_day: int) -> List[int]:
    """Given cycle length N and the last completed day, return day numbers to plan.

    - last_day >= N  →  full new cycle:  [1, 2, ..., N]
    - last_day < N   →  complete current: [last_day+1, ..., N]
    """
    if last_day >= N:
        return list(range(1, N + 1))
    return list(range(last_day + 1, N + 1))


# ---------------------------------------------------------------------------
# Get last planned / session date
# ---------------------------------------------------------------------------


def _next_date_after(user_data: dict, n_sessions: int) -> List[str]:
    """Return n_sessions placeholder dates starting 2 days after the last entry."""
    if not user_data:
        base = datetime.today()
    else:
        last = max(user_data.keys())
        base = datetime.strptime(last, "%Y-%m-%d")

    dates = []
    candidate = base + timedelta(days=2)
    while len(dates) < n_sessions:
        dates.append(candidate.strftime("%Y-%m-%d"))
        candidate += timedelta(days=2)
    return dates


# ---------------------------------------------------------------------------
# Parse sessions.py to build PlannedSession objects (no file write)
# ---------------------------------------------------------------------------


def build_planned_sessions(
    sessions_file_path: str, day_numbers: List[int]
) -> List[PlannedSession]:
    """Read sessions.py and construct PlannedSession objects for the given day numbers.

    Reads the *last* occurrence of each Day-N block to get the most recent
    progression baseline, then applies a simple +2.5 kg / same-reps progression.

    Returns
    -------
    list[PlannedSession] — one per requested day, pre-filled with suggested values.
    The caller (UI dialog) lets the user edit before writing.
    """
    from core.standards import EXERCISE_STANDARDS

    with open(sessions_file_path, "r", encoding="utf-8") as f:
        content = f.read()
        lines = content.splitlines()

    # Attempt to load sessions module to get USER_DATA + EXERCISE_REGISTRY
    import importlib
    import sys

    sessions_dir = str(__import__("pathlib").Path(sessions_file_path).parent)
    if sessions_dir not in sys.path:
        sys.path.insert(0, sessions_dir)
    import sessions as sess_mod

    importlib.reload(sess_mod)

    # Build display-name lookup from EXERCISE_STANDARDS
    id_to_name = {
        slug: info.get("name", slug) for slug, info in EXERCISE_STANDARDS.items()
    }

    # Build var_name → exercise_id lookup from sessions module
    var_to_id: dict[str, str] = {}
    for attr in dir(sess_mod):
        val = getattr(sess_mod, attr)
        if (
            isinstance(val, str)
            and attr not in ("SESSIONS_OWNER", "USER_SEX")
            and not attr.startswith("_")
        ):
            var_to_id[attr] = val  # e.g. "squat" → "squat" (the slug)

    from core.models import Log

    # Find the most recent session for each requested day number
    sorted_dates = sorted(sess_mod.USER_DATA.keys(), reverse=True)
    baseline: dict[int, dict] = {}  # day_number → day_data dict

    for date_str in sorted_dates:
        day_data = sess_mod.USER_DATA[date_str]
        day_obj = day_data.get("day")
        if not isinstance(day_obj, int):
            # not a numbered training day — skip
            continue
        dn = day_obj
        if dn in day_numbers and dn not in baseline:
            baseline[dn] = day_data

    if len(baseline) < len(day_numbers):
        # Only match uncommented block openers — commented-out sessions are
        # intentionally excluded.  detect_cycle() already derives N from
        # USER_DATA (which never contains commented entries), so the cycle
        # length is always inferred from real, active sessions.
        pattern = re.compile(
            r'^([ \t]*)"(\d{4})-[^"]+"\s*:\s*\{[^{]*#\s*[Dd]ay\s*(\d+)'
        )
        parsed_blocks: dict[int, list] = {}
        last_seen_year: dict[int, str] = {}
        line_idx = 0
        while line_idx < len(lines):
            line = lines[line_idx]
            match = pattern.match(line)
            if match:
                indent = match.group(1)
                year = match.group(2)
                dn = int(match.group(3))
                block_lines = []
                idx2 = line_idx + 1
                while idx2 < len(lines):
                    l2 = lines[idx2]
                    if l2.startswith(indent + "}") or l2.strip() == "},":
                        parsed_blocks[dn] = block_lines
                        last_seen_year[dn] = year
                        break
                    else:
                        stripped = l2.split("#")[0].rstrip()
                        if stripped.strip() and not l2.strip().startswith("#"):
                            block_lines.append(stripped)
                    idx2 += 1
                line_idx = idx2
            else:
                line_idx += 1

        for dn in day_numbers:
            if dn not in baseline and dn in parsed_blocks:
                baseline[dn] = {"_raw_lines": parsed_blocks[dn]}

    suggested_dates = _next_date_after(sess_mod.USER_DATA, len(day_numbers))

    planned: List[PlannedSession] = []
    for idx, dn in enumerate(day_numbers):
        session = PlannedSession(
            day_number=dn,
            date_str=suggested_dates[idx],
        )
        day_data = baseline.get(dn, {})

        if "_raw_lines" in day_data:
            # Legacy parsing path: parse raw "    var: Log([r], [m])," strings
            log_pat = re.compile(
                r"\s*(\w+)\s*:\s*Log\(\s*\[([^\]]+)\]\s*,\s*\[([^\]]+)\]\s*\)"
            )
            for raw_line in day_data["_raw_lines"]:
                m = log_pat.match(raw_line)
                if not m:
                    continue
                var_name = m.group(1)
                reps_list = [float(x.strip()) for x in m.group(2).split(",")]
                mass_list = [float(x.strip()) for x in m.group(3).split(",")]
                ex_id = var_to_id.get(var_name, var_name)
                display = id_to_name.get(ex_id, var_name.replace("_", " ").title())
                progression = _suggest_progression(reps_list, mass_list)
                session.exercises.append(
                    PlannedExercise(
                        var_name=var_name,
                        display_name=display,
                        **progression,
                    )
                )
        else:
            for key, val in day_data.items():
                if not isinstance(val, Log):
                    continue
                ex_id = key.replace("-", "_")

                # Exclude uppercase constants imported from core.standards by preferring lowercase vars
                matches = [
                    v for v, eid in var_to_id.items() if eid.lower() == ex_id.lower()
                ]
                var_name = ex_id
                if matches:
                    # Prefer lowercase variables (e.g. 'dips' instead of 'DIPS')
                    lower_matches = [m for m in matches if m.islower()]
                    var_name = lower_matches[0] if lower_matches else matches[0]

                display = (
                    id_to_name.get(ex_id)
                    or id_to_name.get(ex_id.lower())
                    or var_name.replace("_", " ").title()
                )
                progression = _suggest_progression(val.reps, val.mass)
                session.exercises.append(
                    PlannedExercise(
                        var_name=var_name,
                        display_name=display,
                        **progression,
                    )
                )

        planned.append(session)

    return planned


def _suggest_progression(reps: list, mass: list) -> dict:
    """Return an exact baseline copy from the previous session."""
    n_sets = len(reps)

    def _fmt_rep(r):
        """Format a rep value: whole-number floats become ints (6.0 → 6)."""
        if isinstance(r, float) and r.is_integer():
            return str(int(r))
        return str(r)

    reps_str = ", ".join(_fmt_rep(r) for r in reps)
    mass_str = ", ".join(f"{m:g}" if m > 0 else "0" for m in mass)

    # Simplify to single number if all sets are identical
    if len(set(reps)) == 1:
        reps_str = _fmt_rep(reps[0])
    if len(set(mass)) == 1:
        mass_str = f"{mass[0]:g}" if mass[0] > 0 else "0"

    return {"sets": n_sets, "reps": reps_str, "mass": mass_str}


# ---------------------------------------------------------------------------
# Pre-deload baseline: skip deload sessions and read the last clean cycle
# ---------------------------------------------------------------------------

_DELOAD_COMMENT_RE = re.compile(r"#.*deload", re.IGNORECASE)
_LOG_LINE_RE = re.compile(
    r"\s*(\w+)\s*:\s*Log\(\s*\[([^\]]+)\]\s*,\s*\[([^\]]+)\]\s*\)"
)
# Matches the opening line of a session block:  "2026-05-05": {  # Day 1
_BLOCK_OPEN_RE = re.compile(
    r'^([ \t]*)"(\d{4}-\d{2}-[^"]+)"\s*:\s*\{[^{]*#\s*[Dd]ay\s*(\d+)'
)


def _is_deload_block(block_lines: list[str]) -> bool:
    """Return True if any exercise line in the block carries a 'deload' comment."""
    return any(_DELOAD_COMMENT_RE.search(ln) for ln in block_lines)


def build_pre_deload_baseline(
    sessions_file_path: str,
    day_numbers: List[int],
    scale_pct: float,
) -> List["PlannedSession"]:
    """Build PlannedSession objects from the *last non-deload* cycle.

    Algorithm
    ---------
    1. Parse sessions.py raw text into ordered ``(date, day_number, block_lines)``
       tuples — most-recent first.
    2. A block is considered a *deload block* if any exercise line contains
       the word "deload" in its inline comment.
    3. Walk backward; for each requested day number, take the **first block that
       is NOT a deload block** as the pre-deload baseline.
    4. Scale every mass by ``scale_pct / 100``, round to nearest 2.5 kg.
    5. Preserve reps/sets exactly; reset comments to e.g. ``"85% of pre-deload"``.

    Parameters
    ----------
    sessions_file_path:
        Path to sessions.py.
    day_numbers:
        Day numbers to plan (e.g. ``[1, 2, 3]`` for a full 3-day cycle).
    scale_pct:
        Percentage of the pre-deload max to target (e.g. ``85`` for 85%).

    Returns
    -------
    list[PlannedSession]
    """
    from core.standards import EXERCISE_STANDARDS

    with open(sessions_file_path, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    # -- load module for display-name + var_name resolution ------------------
    import importlib, sys

    sessions_dir = str(__import__("pathlib").Path(sessions_file_path).parent)
    if sessions_dir not in sys.path:
        sys.path.insert(0, sessions_dir)
    import sessions as sess_mod
    importlib.reload(sess_mod)

    id_to_name = {
        slug: info.get("name", slug) for slug, info in EXERCISE_STANDARDS.items()
    }
    var_to_id: dict[str, str] = {}
    for attr in dir(sess_mod):
        val = getattr(sess_mod, attr)
        if (
            isinstance(val, str)
            and attr not in ("SESSIONS_OWNER", "USER_SEX")
            and not attr.startswith("_")
        ):
            var_to_id[attr] = val

    # -- parse raw blocks in chronological order then reverse ----------------
    # Each entry: (date_str, day_number, raw_block_lines)
    all_blocks: list[tuple[str, int, list[str]]] = []

    line_idx = 0
    while line_idx < len(lines):
        line = lines[line_idx]
        m = _BLOCK_OPEN_RE.match(line)
        if m:
            indent = m.group(1)
            date_str = m.group(2)
            dn = int(m.group(3))
            block_lines: list[str] = []
            idx2 = line_idx + 1
            while idx2 < len(lines):
                l2 = lines[idx2]
                if l2.startswith(indent + "}") or l2.strip() == "},":
                    all_blocks.append((date_str, dn, block_lines))
                    break
                block_lines.append(l2)
                idx2 += 1
            line_idx = idx2
        else:
            line_idx += 1

    # Walk newest-first
    all_blocks_rev = list(reversed(all_blocks))

    # For each requested day, find the most recent NON-deload block
    baseline: dict[int, list[str]] = {}
    for date_str, dn, block_lines in all_blocks_rev:
        if dn in day_numbers and dn not in baseline:
            if not _is_deload_block(block_lines):
                baseline[dn] = block_lines

    suggested_dates = _next_date_after(sess_mod.USER_DATA, len(day_numbers))
    label = "restored" if scale_pct == 100.0 else f"{scale_pct:g}% of pre-deload"

    planned: List[PlannedSession] = []
    for idx, dn in enumerate(day_numbers):
        session = PlannedSession(
            day_number=dn,
            date_str=suggested_dates[idx],
        )
        block_lines = baseline.get(dn, [])
        for raw_ln in block_lines:
            lm = _LOG_LINE_RE.match(raw_ln)
            if not lm:
                continue
            var_name = lm.group(1)
            if var_name == "day":
                continue
            reps_list = [float(x.strip()) for x in lm.group(2).split(",")]
            mass_list = [float(x.strip()) for x in lm.group(3).split(",")]

            # Scale + round to nearest 2.5 kg (keep 0 as 0)
            factor = scale_pct / 100.0
            scaled_mass = [
                round(m * factor / 2.5) * 2.5 if m > 0 else 0.0
                for m in mass_list
            ]

            ex_id = var_to_id.get(var_name, var_name)
            display = id_to_name.get(ex_id, var_name.replace("_", " ").title())
            prog = _suggest_progression(reps_list, scaled_mass)

            session.exercises.append(
                PlannedExercise(
                    var_name=var_name,
                    display_name=display,
                    comment=label,
                    **prog,
                )
            )
        planned.append(session)

    return planned


# ---------------------------------------------------------------------------
# Write planned sessions back into sessions.py
# ---------------------------------------------------------------------------


def write_planned_sessions(
    sessions_file_path: str, planned: List[PlannedSession]
) -> None:
    """Inject the confirmed planned sessions into sessions.py.

    If any exercise variable is missing from the file entirely, it will automatically
    define the variable and insert it into EXERCISE_REGISTRY.
    """
    import os

    with open(sessions_file_path, "r", encoding="utf-8") as f:
        file_content = f.read()
        lines = file_content.splitlines()

    # Collect missing exercises
    missing_exercises = []
    seen = set()
    for ps in planned:
        for ex in ps.exercises:
            if ex.var_name not in seen:
                seen.add(ex.var_name)
                # Quick check if it's defined anywhere in the file as `var_name = ...` or `var_name:`
                if not re.search(rf"\b{ex.var_name}\b", file_content):
                    missing_exercises.append(ex.var_name)

    # If missing, we inject definitions just before USER_DATA
    if missing_exercises:
        user_data_start = next(
            (i for i, l in enumerate(lines) if l.startswith("USER_DATA")), -1
        )
        if user_data_start != -1:
            defs = []
            has_header = any(
                "# Automatically added exercises:" in line for line in lines
            )
            if not has_header:
                defs.append("# Automatically added exercises:")

            for mx in missing_exercises:
                slug = re.sub(r"\W+", "_", mx.lower()).strip("_")
                if not slug:
                    slug = "exercise"
                if slug[0].isdigit():
                    slug = "_" + slug
                defs.append(f'{slug} = "{slug}"')

            if not has_header:
                defs.append("")

            # Now insert into EXERCISE_REGISTRY
            reg_end = next(
                (i for i in range(user_data_start - 1, -1, -1) if "]" in lines[i]), -1
            )
            if reg_end != -1:
                for mx in missing_exercises:
                    slug = re.sub(r"\W+", "_", mx.lower()).strip("_")
                    if not slug:
                        slug = "exercise"
                    if slug[0].isdigit():
                        slug = "_" + slug
                    lines.insert(reg_end, f"    Exercise({slug}),")

                # Insert the constants before EXERCISE_REGISTRY
                reg_start = next(
                    (
                        i
                        for i in range(reg_end, -1, -1)
                        if lines[i].startswith("EXERCISE_REGISTRY")
                    ),
                    -1,
                )
                if reg_start != -1:
                    lines[reg_start:reg_start] = defs
            else:
                lines[user_data_start:user_data_start] = defs

        # Rewrite we need file_content updated to re-format the lines
        # we will just continue using `lines` object

    injection_lines: List[str] = []
    for ps in planned:
        reps_mass_comment = []
        for ex in ps.exercises:
            # Recompute slug if we had space
            slug = re.sub(r"\W+", "_", ex.var_name.lower()).strip("_")
            if not slug:
                slug = "exercise"
            if slug[0].isdigit():
                slug = "_" + slug
            r_str = (
                ex.reps
                if "," in str(ex.reps)
                else ", ".join(str(ex.reps) for _ in range(ex.sets))
            )
            m_str = (
                ex.mass
                if "," in str(ex.mass)
                else ", ".join(str(ex.mass) for _ in range(ex.sets))
            )
            comment_part = f"  # {ex.comment}" if ex.comment.strip() else "  #"
            reps_mass_comment.append(
                f"        {slug}: Log([{r_str}], [{m_str}]),{comment_part}"
            )

        injection_lines.append("")
        injection_lines.append(f'    "{ps.date_str}": {{  # Day {ps.day_number}')
        injection_lines.append(f"        day: {ps.day_number},")
        injection_lines.extend(reps_mass_comment)
        injection_lines.append("    },")

    # Proceed to find USER_DATA closing
    user_data_start = next(
        (i for i, l in enumerate(lines) if l.startswith("USER_DATA = {")), -1
    )
    if user_data_start == -1:
        raise ValueError("Could not find 'USER_DATA = {' in sessions.py")

    user_data_end = -1
    for i in range(user_data_start + 1, len(lines)):
        if lines[i] == "}":
            user_data_end = i

    if user_data_end == -1:
        raise ValueError("Could not find closing '}' for USER_DATA")

    lines[user_data_end:user_data_end] = injection_lines

    with open(sessions_file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def create_initial_sessions_py(
    sessions_file_path: str, owner_name: str, sex: str, planned: List[PlannedSession]
) -> None:
    """Create a completely new sessions.py file for a new user with the first cycle."""
    import os

    lines = [
        "from core.models import Exercise, Log",
        "from core.standards import *",
        "",
        f'SESSIONS_OWNER = "{owner_name}"',
        f'USER_SEX = "{sex}"',
        "",
        "BODYMASS_LOG = {",
        "}",
        "",
        "day = 'day'",
        "",
        "# Dynamically imported exercises:",
    ]

    # Collect unique exercises across all planned sessions
    exercises = []
    exercise_ids = set()
    for ps in planned:
        for ex in ps.exercises:
            slug = re.sub(r"\W+", "_", ex.var_name.lower()).strip("_")
            if not slug:
                slug = "exercise"
            if slug[0].isdigit():
                slug = "_" + slug

            if slug not in exercise_ids:
                exercises.append(slug)
                exercise_ids.add(slug)

    # Write constants for them (assuming default to slug format uppercase or just string)
    for ex in exercises:
        lines.append(f'{ex} = "{ex}"')

    lines.append("")
    lines.append("EXERCISE_REGISTRY = [")
    for ex in exercises:
        lines.append(f"    Exercise({ex}),")
    lines.append("]")
    lines.append("")

    lines.append("USER_DATA = {")

    # Write the planned sessions
    from datetime import datetime

    for ps in planned:
        lines.append(f'    "{ps.date_str}": {{  # Day {ps.day_number}')
        lines.append(f"        day: {ps.day_number},")
        for ex in ps.exercises:
            slug = re.sub(r"\W+", "_", ex.var_name.lower()).strip("_")
            if not slug:
                slug = "exercise"
            if slug[0].isdigit():
                slug = "_" + slug

            r_str = (
                ex.reps
                if "," in str(ex.reps)
                else ", ".join(str(ex.reps) for _ in range(ex.sets))
            )
            m_str = (
                ex.mass
                if "," in str(ex.mass)
                else ", ".join(str(ex.mass) for _ in range(ex.sets))
            )
            comment = f"  # {ex.comment}" if ex.comment.strip() else "  #"
            lines.append(f"        {slug}: Log([{r_str}], [{m_str}]),{comment}")
        lines.append("    },")

    lines.append("}")

    os.makedirs(os.path.dirname(os.path.abspath(sessions_file_path)), exist_ok=True)
    with open(sessions_file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def detect_sessions_owner(file_path: str) -> Optional[str]:
    """
    Safely extract the SESSIONS_OWNER value from a sessions.py file
    using regex to avoid side-effects from importing the file.
    """
    if not os.path.exists(file_path):
        return None
    try:
        import re

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            match = re.search(
                r'^SESSIONS_OWNER\s*=\s*[\'"](.*?)[\'"]', content, re.MULTILINE
            )
            if match:
                return match.group(1)
    except Exception:
        pass
    return None
