import os
import re
import time
from typing import Any, Dict, List, Optional, Set

import requests
from bs4 import BeautifulSoup

# Correct paths relative to script location
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STANDARDS_FILE = os.path.join(BASE_DIR, "core", "standards.py")
STANDARDS_TMP_FILE = STANDARDS_FILE + ".tmp"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

EXERCISE_LIBRARY_ACCUMULATOR: Dict[str, str] = {}


def reset_standards_file() -> None:
    """
    Initialize temporary standards output file with core lookup routing functions.

    :return: None
    """
    content = r'''import math
import re
from typing import Any, Dict, Optional


def get_exercise_standard(
    exercise_id: str,
    target_date_str: str,
    bodymass_log: Dict[str, Any],
    level: str = "Intermediate",
    sex: Optional[str] = None,
) -> int:
    """
    Retrieve standard lifted mass target for exercise and date from standards database.

    :param exercise_id: Canonical exercise slug or display name.
    :param target_date_str: Date string formatted as YYYY-MM-DD to resolve closest body mass.
    :param bodymass_log: Dictionary mapping date strings to body mass records.
    :param level: Strength tier ("Beginner", "Novice", "Intermediate", "Advanced", "Elite").
    :param sex: Biological sex ("male" or "female").
    :return: Target lifted weight in kilograms, or 0 if unmapped.
    """
    if sex is None:
        try:
            import sessions

            sex = sessions.USER_SEX
        except (ImportError, AttributeError):
            sex = "male"

    if not bodymass_log or not exercise_id:
        return 0

    dates = sorted(bodymass_log.keys())
    if not dates:
        return 0

    applicable_date = None
    for d in reversed(dates):
        if d <= target_date_str:
            bm_data = bodymass_log[d]
            bm = bm_data if isinstance(bm_data, (int, float)) else (bm_data.get("mass") or bm_data.get("weight"))
            if bm is not None and bm > 0:
                applicable_date = d
                break

    if not applicable_date:
        for d in dates:
            bm_data = bodymass_log[d]
            bm = bm_data if isinstance(bm_data, (int, float)) else (bm_data.get("mass") or bm_data.get("weight"))
            if bm is not None and bm > 0:
                applicable_date = d
                break

    if not applicable_date:
        return 0

    bm_data = bodymass_log[applicable_date]
    current_bm = (
        bm_data if isinstance(bm_data, (int, float)) else bm_data.get("mass")
    )
    if current_bm is None:
        current_bm = bm_data.get("weight", 0) if isinstance(bm_data, dict) else 0

    if not current_bm:
        return 0

    rounded_bm = int(math.ceil(round(current_bm, 2) / 5.0) * 5)
    rounded_bm = max(50, min(rounded_bm, 140))

    target_norm = exercise_id.lower().strip().replace(" ", "-")
    found_slug = None

    if target_norm in EXERCISE_STANDARDS:
        found_slug = target_norm
    else:
        for slug, info in EXERCISE_STANDARDS.items():
            if info.get("name", "").lower().strip().replace(" ", "-") == target_norm:
                found_slug = slug
                break

    if not found_slug:
        return 0

    gender_table = EXERCISE_STANDARDS[found_slug].get(sex.lower())
    if not gender_table:
        return 0

    available_bms = sorted(gender_table.keys())
    if not available_bms:
        return 0

    clipped_bm = max(available_bms[0], min(rounded_bm, available_bms[-1]))
    return gender_table[clipped_bm].get(level, 0)


def get_tiered_standards(
    exercise_id: str,
    sex: str,
    body_mass: Optional[float] = None,
) -> Optional[Dict[int, Dict[str, int]]]:
    """
    Return dictionary of strength standards across bodyweight tiers for an exercise and sex.

    :param exercise_id: Canonical exercise slug or display name.
    :param sex: Biological sex ("male" or "female").
    :param body_mass: Optional body mass in kg to return 3 adjacent tiers around user weight class.
    :return: Dictionary mapping bodyweight tiers (kg) to tier level target weights, or None.
    """
    if not exercise_id:
        return None

    target_norm = exercise_id.lower().strip().replace(" ", "-")
    found_slug = None

    if target_norm in EXERCISE_STANDARDS:
        found_slug = target_norm
    else:
        for slug, info in EXERCISE_STANDARDS.items():
            if info.get("name", "").lower().strip().replace(" ", "-") == target_norm:
                found_slug = slug
                break

    if not found_slug:
        return None

    gender_table = EXERCISE_STANDARDS[found_slug].get(sex.lower())
    if not gender_table:
        return None

    available_bms = sorted(gender_table.keys())
    if not available_bms:
        return None

    if body_mass is None or body_mass <= 0:
        return gender_table

    rounded_bm = int(math.ceil(round(body_mass, 2) / 5.0) * 5)

    results = {}
    for offset in [-5, 0, 5]:
        target_bm = rounded_bm + offset
        clipped_bm = max(available_bms[0], min(target_bm, available_bms[-1]))
        results[target_bm] = gender_table[clipped_bm]

    return results


EXERCISE_STANDARDS = {
'''
    with open(STANDARDS_TMP_FILE, "w", encoding="utf-8") as f:
        f.write(content)
    print("Reset standards.py.tmp to core logic and header.")


def get_all_exercise_slugs() -> List[str]:
    """
    Discover all unique exercise slugs by scraping the strengthlevel sitemap XML.

    :return: Sorted list of discovered unique exercise slugs.
    """
    url = "https://strengthlevel.com/sitemap.xml"
    print(f"Discovering all exercises from {url}...")

    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"Discovery Failed: {e}")
        return []

    locs = re.findall(
        r"<loc>(https://strengthlevel.com/strength-standards/([^<]+))</loc>",
        response.text,
    )

    slugs: Set[str] = set()
    for full_url, path in locs:
        parts = path.strip("/").split("/")
        slug = parts[0]
        if "-vs-" in slug:
            continue
        if slug in ["strength-standards", "kg", "lb", "male", "female", "all"]:
            continue
        slugs.add(slug)

    print(f"Found {len(slugs)} unique exercise slugs via sitemap.")
    return sorted(list(slugs))


def scrape_standards(slug: str) -> Dict[str, Any]:
    """
    Scrape male and female strength standards tables in kilograms for given exercise slug.

    :param slug: Canonical exercise slug.
    :return: Dictionary containing display name and parsed male and female standards tables.
    """
    url = f"https://strengthlevel.com/strength-standards/{slug}/kg"

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            return {}
    except Exception:
        return {}

    soup = BeautifulSoup(response.text, "html.parser")

    # Get Display Name
    name_tag = soup.find("h1")
    raw_name = name_tag.text.strip() if name_tag else slug.replace("-", " ").title()
    # Clean name: "Bench Press Standards (kg)" -> "Bench Press"
    display_name = re.sub(
        r"\s+Standards(\s*\(kg\))?", "", raw_name, flags=re.IGNORECASE
    ).strip()

    gender_data: Dict[str, Any] = {"name": display_name, "male": None, "female": None}

    headers = soup.find_all(["h2", "h3"])

    for h in headers:
        text = h.text.lower()
        gender = None
        if "male" in text and "female" not in text:
            gender = "male"
        elif "female" in text:
            gender = "female"

        if gender and gender_data[gender] is None:
            curr = h
            while curr:
                if curr.name == "table":
                    data = parse_table(curr)
                    if data:
                        gender_data[gender] = data
                        break

                if hasattr(curr, "find"):
                    t = curr.find("table")
                    if t:
                        data = parse_table(t)
                        if data:
                            gender_data[gender] = data
                            break

                next_node = curr.next_sibling
                if not next_node:
                    if curr.parent and curr.parent.name != "[document]":
                        next_node = curr.parent.next_sibling
                    else:
                        break

                if next_node and hasattr(next_node, "text"):
                    nt = next_node.text.upper()
                    if ("MALE" in nt or "FEMALE" in nt) and next_node.name in [
                        "h2",
                        "h3",
                    ]:
                        break

                curr = next_node

    return gender_data


def parse_table(table: Any) -> Optional[Dict[int, Dict[str, int]]]:
    """
    Parse HTML table element containing bodyweight rows and tier columns.

    :param table: BeautifulSoup tag element representing the standards table.
    :return: Dictionary mapping body mass (kg) to tier weights, or None if invalid.
    """
    if not hasattr(table, "find_all"):
        return None
    headers_text = [th.text.strip().lower() for th in table.find_all("th")]

    if len(headers_text) < 6 or "bw" not in headers_text:
        return None

    parsed_data: Dict[int, Dict[str, int]] = {}
    tbody = table.find("tbody")
    rows = tbody.find_all("tr") if tbody else table.find_all("tr")[1:]

    for row in rows:
        cols = row.find_all("td")
        if len(cols) >= 6:
            try:
                bw_text = cols[0].text.strip().replace(",", "")
                bw_match = re.search(r"(\d+)", bw_text)
                if not bw_match:
                    continue
                bw = int(bw_match.group(1))

                levels: Dict[str, int] = {}
                level_names = [
                    "Beginner",
                    "Novice",
                    "Intermediate",
                    "Advanced",
                    "Elite",
                ]
                for i, name in enumerate(level_names, 1):
                    val_text = cols[i].text.strip().replace(",", "")
                    val_match = re.search(r"(\d+)", val_text)
                    levels[name] = int(val_match.group(1)) if val_match else 0

                parsed_data[bw] = levels
            except (ValueError, AttributeError, IndexError):
                continue

    return parsed_data


def finalize_standards_file() -> None:
    """
    Close the EXERCISE_STANDARDS dictionary block and append constant definitions.

    :return: None
    """
    lines = ["}\n", "\n# --- Exercise Constants for Autocomplete ---\n"]

    for slug, name in sorted(EXERCISE_LIBRARY_ACCUMULATOR.items()):
        # Create a clean variable name: "Bench Press" -> "BENCH_PRESS"
        var_name = re.sub(r"[^A-Z0-9\s]", "", name.upper())
        var_name = var_name.strip().replace(" ", "_")
        var_name = re.sub(r"_+", "_", var_name)
        lines.append(f"{var_name} = '{slug}'")

    with open(STANDARDS_TMP_FILE, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Finalized standards.py.tmp with {len(EXERCISE_LIBRARY_ACCUMULATOR)} constants.")


def append_to_standards_dict(slug: str, gender_results: Dict[str, Any]) -> None:
    """
    Format and append an exercise entry to the temporary standards file.

    :param slug: Canonical exercise slug.
    :param gender_results: Dictionary containing exercise display name and parsed gender tables.
    :return: None
    """
    if not gender_results.get("male") and not gender_results.get("female"):
        return

    name = gender_results.get("name", slug)
    EXERCISE_LIBRARY_ACCUMULATOR[slug] = name

    lines = [f"    '{slug}': {{"]
    lines.append(f"        'name': '{name}',")

    for gender in ["male", "female"]:
        data = gender_results.get(gender)
        if data:
            lines.append(f"        '{gender}': {{")
            for bm, lvls in sorted(data.items()):
                lvls_str = ", ".join([f"'{k}': {v}" for k, v in lvls.items()])
                lines.append(f"            {bm}: {{{lvls_str}}},")
            lines.append("        },")

    lines.append("    },")

    with open(STANDARDS_TMP_FILE, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Saved: {slug} ('{name}')")


if __name__ == "__main__":
    reset_standards_file()
    slugs = get_all_exercise_slugs()

    success_count = 0
    fail_count = 0

    for i, slug in enumerate(slugs, 1):
        print(f"[{i}/{len(slugs)}] Scraping {slug}...", end=" ", flush=True)
        gender_results = scrape_standards(slug)

        if gender_results.get("male") or gender_results.get("female"):
            append_to_standards_dict(slug, gender_results)
            success_count += 1
            print("OK")
        else:
            fail_count += 1
            print("FAILED (No tables found)")

        time.sleep(1.0)

    finalize_standards_file()
    if os.path.exists(STANDARDS_TMP_FILE):
        os.replace(STANDARDS_TMP_FILE, STANDARDS_FILE)
        print("Updated standards.py atomically.")
    else:
        print("Error: Temporary standards file not found. Could not update.")
    print("\nScrape Finished!")
    print(f"Success: {success_count}")
    print(f"Failed: {fail_count}")
