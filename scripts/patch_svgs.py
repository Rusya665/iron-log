import glob
import os
import re
import sys

def patch_svg_for_dark_mode(filepath: str):
    """
    Patches an SVG file to be dark-mode safe by:
    1. Making white backgrounds transparent.
    2. Injecting CSS to invert common black/gray strokes and text in dark mode.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        svg_content = f.read()

    # Remove hardcoded white backgrounds
    svg_content = re.sub(r'fill="#[Ff]{6}"', 'fill="transparent"', svg_content)
    svg_content = re.sub(r'fill:\s*#[Ff]{6};?', 'fill: transparent;', svg_content)
    svg_content = re.sub(r'background-color:\s*#[Ff]{6};?', 'background-color: transparent;', svg_content)

    # CSS to invert black text/lines and dim gray gridlines in dark mode
    dark_mode_styles = """
    <style>
        @media (prefers-color-scheme: dark) {
            text { fill: #E5E7EB !important; }
            path[stroke="#000000"], path[stroke="#000"], 
            line[stroke="#000000"], line[stroke="#000"] { stroke: #E5E7EB !important; }
            /* Target common Excel export grays for gridlines */
            path[stroke="#D9D9D9"], path[stroke="#d9d9d9"],
            line[stroke="#D9D9D9"], line[stroke="#d9d9d9"],
            path[stroke="#BFBFBF"], line[stroke="#BFBFBF"],
            path[stroke="#868686"], line[stroke="#868686"] { stroke: #374151 !important; }
        }
    </style>
    """

    # Inject styles immediately after the opening <svg> tag
    if '@media (prefers-color-scheme: dark)' not in svg_content:
        svg_content = re.sub(r'(<svg[^>]*>)', r'\1\n' + dark_mode_styles, svg_content, count=1)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(svg_content)
    print(f"Patched: {filepath}")

if __name__ == "__main__":
    # Target the media directory by default, or accept a CLI argument
    target_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "media")
    
    if not os.path.exists(target_dir):
        print(f"Directory not found: {target_dir}")
        sys.exit(1)

    svgs = glob.glob(os.path.join(target_dir, "*.svg"))
    for svg in svgs:
        patch_svg_for_dark_mode(svg)
