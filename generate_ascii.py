"""
generate_ascii.py

Turns a photo into a monochrome ASCII-art SVG that "types itself in" row by row
using CSS animation-delay. GitHub strips <script> tags from README-embedded
SVGs but still runs CSS keyframes / SMIL, so the animation is done purely in CSS.

Usage:
    pip install pillow --break-system-packages
    python generate_ascii.py your_photo.jpg avi-ascii.svg

Then embed the output in your README with:
    <img src="avi-ascii.svg" width="320" alt="ascii portrait"/>
"""

import sys
from PIL import Image

# Characters ordered from "empty" to "dense" — pick based on brightness
ASCII_CHARS = "@%#*+=-:. "[::-1]

CHAR_WIDTH = 6      # px per character cell in the output SVG
CHAR_HEIGHT = 10
COLS = 80            # ASCII art width in characters


def image_to_ascii_rows(path, cols=COLS):
    img = Image.open(path).convert("L")  # grayscale
    aspect_correct = 0.55  # monospace chars are taller than wide
    w, h = img.size
    new_h = int(cols * (h / w) * aspect_correct)
    img = img.resize((cols, new_h))

    pixels = img.getdata()
    chars = [ASCII_CHARS[pixel * (len(ASCII_CHARS) - 1) // 255] for pixel in pixels]

    rows = []
    for i in range(0, len(chars), cols):
        rows.append("".join(chars[i:i + cols]))
    return rows


def escape(s):
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def build_svg(rows, row_delay=0.05):
    width = COLS * CHAR_WIDTH
    height = len(rows) * CHAR_HEIGHT

    style_rules = []
    text_elements = []

    for i, row in enumerate(rows):
        delay = round(i * row_delay, 3)
        style_rules.append(
            f".r{i} {{ animation-delay: {delay}s; }}"
        )
        y = (i + 1) * CHAR_HEIGHT
        text_elements.append(
            f'  <text x="0" y="{y}" class="row r{i}">{escape(row)}</text>'
        )

    svg = f'''<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
  <style>
    svg {{ background: #0d1117; }}
    text {{
      font-family: 'Courier New', monospace;
      font-size: {CHAR_HEIGHT - 1}px;
      fill: #7ee787;
      white-space: pre;
    }}
    /* Visible by default — safe fallback if the animation doesn't
       run (image proxies, reduced-motion settings, some renderers).
       The typing effect below is a progressive enhancement only. */
    .row {{
      opacity: 1;
    }}
    @media (prefers-reduced-motion: no-preference) {{
      .row {{
        opacity: 0;
        animation: fadeIn 0.3s ease-out forwards;
      }}
      @keyframes fadeIn {{
        to {{ opacity: 1; }}
      }}
      {chr(10).join(style_rules)}
    }}
  </style>
{chr(10).join(text_elements)}
</svg>'''
    return svg


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python generate_ascii.py <input_photo> <output_svg>")
        sys.exit(1)

    rows = image_to_ascii_rows(sys.argv[1])
    svg = build_svg(rows)

    with open(sys.argv[2], "w") as f:
        f.write(svg)

    print(f"Wrote {sys.argv[2]} ({len(rows)} rows, {COLS} cols)")
