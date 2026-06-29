#!/usr/bin/env python3
"""按行号精确提取各section并重构"""
from pathlib import Path

html_file = Path("C:/Users/33051/Desktop/BinixOvO_正式版2.0.0/index.html")
with open(html_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 从行号分析得到的精确section边界 (1-indexed -> 0-indexed)
sections = {
    "appearance":    (105, 267),   # lines 106-267 inclusive -> indices 105-266
    "tile-layout":   (267, 372),   # lines 268-372
    "fold-view":     (372, 560),   # lines 373-560
    "interaction":   (560, 632),   # lines 561-632
    "search":        (632, 687),   # lines 633-687
    "system-info":   (687, 759),   # lines 688-759
    "content-media": (759, 811),   # lines 760-811
}

# 提取每个section的行
section_lines = {}
for name, (start, end) in sections.items():
    section_lines[name] = lines[start:end]
    print(f"{name}: lines {start+1}-{end} ({len(section_lines[name])} lines)")

# 验证每个section开头的行
for name, slines in section_lines.items():
    first = slines[0].strip()
    last = slines[-1].strip()
    print(f"  {name}: first='{first[:80]}' last='{last[:60]}'")

# 设置搜索框 (lines 101-104, indices 100-103)
search_box = ''.join(lines[100:104])
print(f"\n搜索框: {len(search_box)} chars")

# 现在构建新面板
# 出口部分: lines 812+ (index 811+)
tail = ''.join(lines[811:])  # includes </aside> and everything after

print(f"尾部: {len(tail)} chars, starts with: {tail[:60].strip()}")