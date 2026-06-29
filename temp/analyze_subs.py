#!/usr/bin/env python3
"""Analyze sub-settings blocks and their structures"""
import re
from pathlib import Path

html_file = Path(r"C:\Users\33051\Desktop\BinixOvO_正式版2.0.0\index_reconstructed.html")
with open(html_file, 'r', encoding='utf-8') as f:
    html = f.read()

# Find all section titles
sections = re.findall(r'data-section="([^"]+)".*?<div class="setting-title">([^<]+)</div>', html)
for sec, title in sections:
    print(f"\n=== {title} (data-section={sec}) ===")

# Find all sub-settings titles
subs = re.findall(r'<div class="sub-settings-title">([^<]+)</div>', html)
print(f"\n\nTotal sub-settings: {len(subs)}")
for i, s in enumerate(subs):
    print(f"  {i+1}. {s}")