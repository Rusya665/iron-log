import os
import re
import time

import requests
from bs4 import BeautifulSoup

# Correct paths relative to script location
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STANDARDS_FILE = os.path.join(BASE_DIR, "core", "standards.py")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

EXERCISE_LIBRARY_ACCUMULATOR = {}


def reset_standards_file():
    """Resets standards.py to only contain the core routing function and header."""
    content = r"""import re

def get_exercise_standard(exercise_id: str, target_date_str: str, bodymass_log: dict, level: str = "Intermediate", sex: str = None) -> int:
    \"\"\"
    Retrieves the exercise standard from the consolidated EXERCISE_STANDARDS dictionary.
    Requires an exact match on the exercise_id (slug) or normalized display name.
    \"\"\"
    if sex is None:
        try:
            import sessions
            sex = sessions.USER_SEX
        except (ImportError, AttributeError):
            sex = "male" # Fallback

    if not bodymass_log or not exercise_id:
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
    
    # Strict lookup
    found_slug = None
    target_norm = exercise_id.lower().strip().replace(' ', '-')
    
    if target_norm in EXERCISE_STANDARDS:
        found_slug = target_norm
    else:
        for slug, info in EXERCISE_STANDARDS.items():
            if info.get('name', '').lower().strip().replace(' ', '-') == target_norm:
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

# Consolidate exercise standards database
EXERCISE_STANDARDS = {
"""
    with open(STANDARDS_FILE, "w", encoding="utf-8") as f:
        f.write(content)
    print("Reset standards.py to core logic and header.")


def get_all_exercise_slugs():
    """Scrapes the sitemap to find all unique exercise slugs."""
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

    slugs = set()
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


def scrape_standards(slug: str) -> dict:
    """Scrapes a specific exercise page for name and both male/female kg standards."""
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

    gender_data = {"name": display_name, "male": None, "female": None}

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


def parse_table(table) -> dict:
    """Parses a standards table into a dict."""
    if not hasattr(table, "find_all"):
        return None
    headers_text = [th.text.strip().lower() for th in table.find_all("th")]

    if len(headers_text) < 6 or "bw" not in headers_text:
        return None

    parsed_data = {}
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

                levels = {}
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


def finalize_standards_file():
    """Closes the EXERCISE_STANDARDS dictionary and generates constants in the same file."""
    lines = ["}\n", "\n# --- Exercise Constants for Autocomplete ---\n"]

    for slug, name in sorted(EXERCISE_LIBRARY_ACCUMULATOR.items()):
        # Create a clean variable name: "Bench Press" -> "BENCH_PRESS"
        var_name = re.sub(r"[^A-Z0-9\s]", "", name.upper())
        var_name = var_name.strip().replace(" ", "_")
        var_name = re.sub(r"_+", "_", var_name)
        lines.append(f"{var_name} = '{slug}'")

    with open(STANDARDS_FILE, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Finalized standards.py with {len(EXERCISE_LIBRARY_ACCUMULATOR)} constants.")


def append_to_standards_dict(slug: str, gender_results: dict):
    """Appends the exercise entry to the EXERCISE_STANDARDS dictionary and tracks for library."""
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

    with open(STANDARDS_FILE, "a", encoding="utf-8") as f:
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
    print("\nScrape Finished!")
    print(f"Success: {success_count}")
    print(f"Failed: {fail_count}")
