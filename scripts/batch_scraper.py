import os
import re
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# Correct paths relative to script location
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STANDARDS_FILE = os.path.join(BASE_DIR, "core", "standards.py")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def get_all_exercise_slugs():
    """Scrapes the main standards page to find all exercise slugs."""
    url = "https://strengthlevel.com/strength-standards"
    print(f"Discovering exercises from {url}...")
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"Discovery Failed: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Slugs are usually in links like /strength-standards/bench-press
    slugs = set()
    links = soup.find_all('a', href=re.compile(r'^/strength-standards/[a-z0-9-]+$'))
    
    for link in links:
        href = link.get('href')
        # Filter out generic category pages if they don't contain standards
        # Most specific exercises follow the pattern
        slug = href.split('/')[-1]
        if slug and slug not in ['strength-standards', 'kg', 'lb', 'male', 'female']:
            slugs.add(slug)
            
    print(f"Found {len(slugs)} potential exercises.")
    return sorted(list(slugs))

def scrape_standard(slug: str) -> dict:
    """Scrapes a specific exercise page for kg standards."""
    url = f"https://strengthlevel.com/strength-standards/{slug}/kg"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            return None
    except Exception:
        return None
        
    soup = BeautifulSoup(response.text, 'html.parser')
    tables = soup.find_all('table')
    target_table = None
    
    # Try finding the first table that looks like a standards table
    for table in tables:
        headers_text = [th.text.strip().lower() for th in table.find_all('th')]
        
        # Abbreviated headers found in HTML: ['BW', 'Beg.', 'Nov.', 'Int.', 'Adv.', 'Elite']
        if len(headers_text) >= 6:
            if 'bw' in headers_text and any(h in headers_text for h in ['beg.', 'nov.', 'int.']):
                target_table = table
                break
            
    if not target_table:
        return None
        
    parsed_data = {}
    tbody = target_table.find('tbody')
    rows = tbody.find_all('tr') if tbody else target_table.find_all('tr')[1:]
    
    for row in rows:
        cols = row.find_all('td')
        if len(cols) >= 6:
            try:
                # 1. Parse Bodyweight (e.g. "50 kg" or "50")
                bw_text = cols[0].text.strip().replace(',', '')
                bw_match = re.search(r'(\d+)', bw_text)
                if not bw_match: continue
                bw = int(bw_match.group(1))
                
                # 2. Parse 5 Levels
                levels = {}
                level_names = ["Beginner", "Novice", "Intermediate", "Advanced", "Elite"]
                for i, name in enumerate(level_names, 1):
                    val_text = cols[i].text.strip().replace(',', '')
                    val_match = re.search(r'(\d+)', val_text)
                    levels[name] = int(val_match.group(1)) if val_match else 0
                
                parsed_data[bw] = levels
            except (ValueError, AttributeError, IndexError):
                continue
                
    return parsed_data

def append_to_standards(slug: str, data: dict):
    """Appends the parsed data to standards.py as a new constant."""
    # Convert slug to constant name: bench-press -> BENCH_PRESS_STANDARDS_KG
    variable_name = slug.replace('-', '_').upper() + "_STANDARDS_KG"
    
    # Check if table is empty
    if not data:
        return

    # Check if already exists in file to avoid duplicates (loose check)
    with open(STANDARDS_FILE, "r", encoding="utf-8") as f:
        file_content = f.read()
    
    if variable_name in file_content:
        print(f"Skipping {variable_name} (already exists)")
        return

    dict_lines = []
    for bm, levels in sorted(data.items()):
        levels_str = ", ".join([f"'{k}': {v}" for k, v in levels.items()])
        dict_lines.append(f"    {bm}: {{{levels_str}}}")
    
    formatted_dict = variable_name + " = {\n" + ",\n".join(dict_lines) + "\n}\n"
    
    with open(STANDARDS_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n# Scraped on {datetime.now().strftime('%Y-%m-%d')}\n")
        f.write(formatted_dict)
    print(f"Saved: {variable_name}")

if __name__ == "__main__":
    slugs = get_all_exercise_slugs()
    
    # For safety/verification, maybe we don't start with ALL 400+ immediately
    # But the user asked for "ALL exercises"
    
    success_count = 0
    fail_count = 0
    
    for i, slug in enumerate(slugs, 1):
        print(f"[{i}/{len(slugs)}] Scraping {slug}...", end=" ", flush=True)
        data = scrape_standard(slug)
        if data:
            append_to_standards(slug, data)
            success_count += 1
            print("OK")
        else:
            fail_count += 1
            print("FAILED (No table)")
            
        # Throttling to be polite to the server
        time.sleep(1.5)
        
    print(f"\nScrape Finished!")
    print(f"Success: {success_count}")
    print(f"Failed: {fail_count}")
