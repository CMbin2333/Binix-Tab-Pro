#!/usr/bin/env python3
"""Check which sub-settings blocks are not being matched"""
import re
from pathlib import Path

html_file = Path(r"C:\Users\33051\Desktop\BinixOvO_正式版2.0.0\index_reconstructed.html")
with open(html_file, 'r', encoding='utf-8') as f:
    html = f.read()

# Find all titles
titles = re.findall(r'<div class="sub-settings-title">([^<]+)</div>', html)
print(f"Total titles in HTML: {len(titles)}")
for t in titles:
    print(f"  - {t}")

# Find class names of all blocks
classes = re.findall(r'<div class="(sub-settings[^"]*)"', html)
print(f"\nBlock classes found: {len(classes)}")
for c in classes:
    print(f"  {c}")