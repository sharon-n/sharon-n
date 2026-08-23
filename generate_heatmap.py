"""
generate_heatmap.py

Pulls your real public contribution calendar from GitHub's public,
no-auth-required contributions HTML endpoint, and renders it as an
animated SVG (boxes slide in diagonally, colored by contribution level).

Usage:
    pip install requests --break-system-packages
    python generate_heatmap.py sharon-n contrib-heatmap.svg

Meant to be run daily by the GitHub Action in
.github/workflows/update-heatmap.yml so the README stays fresh.
"""

import re
import sys
import requests

CELL = 11
GAP = 3
COLORS = {
    0: "#161b22",
    1: "#0e4429",
    2: "#006d32",
    3: "#26a641",
    4: "#39d353",
}


def fetch_contributions(username):
    url = f"https://github.com/users/{username}/contributions"
    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    html = resp.text

    # Each day cell is a <td> or <rect> with data-date and data-level (or a
    # fill class). GitHub's markup has shifted over time between <rect> and
    # <td>, so match both.
    days = []
    for m in re.finditer(
        r'data-date="([\d-]+)"[^>]*(?:data-level="(\d)"|)', html
    ):
        date, level = m.group(1), m.group(2)
        days.append((date, int(level) if level else 0))

    if not days:
        raise RuntimeError(
            "No contribution cells found — GitHub may have changed its markup."
        )
    return days


def build_svg(days):
    weeks = [days[i:i + 7] for i in range(0, len(days), 7)]
    width = len(weeks) * (CELL + GAP) + GAP
    height = 7 * (CELL + GAP) + GAP

    style_rules = []
    rects = []
    delay_step = 0.012

    idx = 0
    for w, week in enumerate(weeks):
        for d, (date, level) in enumerate(week):
            x = w * (CELL + GAP) + GAP
            y = d * (CELL + GAP) + GAP
            delay = round(idx * delay_step, 3)
            cls = f"c{idx}"
            style_rules.append(
                f".{cls} {{ animation-delay: {delay}s; }}"
            )
            rects.append(
                f'  <rect x="{x - 4}" y="{y - 4}" width="{CELL}" height="{CELL}" '
                f'rx="2" fill="{COLORS[level]}" class="cell {cls}">'
                f'<title>{date}: level {level}</title></rect>'
            )
            idx += 1

    svg = f'''<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
  <style>
    svg {{ background: #0d1117; }}
    .cell {{
      opacity: 0;
      transform: translate(-6px, -6px);
      animation: slideIn 0.35s ease-out forwards;
    }}
    @keyframes slideIn {{
      to {{ opacity: 1; transform: translate(0, 0); }}
    }}
    {chr(10).join(style_rules)}
  </style>
{chr(10).join(rects)}
</svg>'''
    return svg


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python generate_heatmap.py <github_username> <output_svg>")
        sys.exit(1)

    username, out_path = sys.argv[1], sys.argv[2]
    days = fetch_contributions(username)
    svg = build_svg(days)

    with open(out_path, "w") as f:
        f.write(svg)

    print(f"Wrote {out_path} ({len(days)} days)")
