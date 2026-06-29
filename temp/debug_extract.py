#!/usr/bin/env python3
"""调试: 检查提取的块大小"""
from pathlib import Path

html_file = Path("C:/Users/33051/Desktop/BinixOvO_正式版2.0.0/index.html")
with open(html_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

section_boundaries = {
    "appearance":    (105, 267),
    "tile-layout":   (267, 372),
    "fold-view":     (372, 560),
    "interaction":   (560, 632),
    "search":        (632, 687),
    "system-info":   (687, 759),
    "content-media": (759, 811),
}

section_html = {}
for name, (start, end) in section_boundaries.items():
    section_html[name] = ''.join(lines[start:end])

def extract_sub_by_title_debug(section_text, title):
    title_pos = section_text.find(title)
    if title_pos == -1:
        print(f"    NOT FOUND: '{title}'")
        return None
    
    search_chunk = section_text[:title_pos]
    sub_start = search_chunk.rfind('<div class="sub-settings')
    
    print(f"    title_pos={title_pos}, sub_start={sub_start}")
    
    if sub_start == -1:
        print(f"    No <div class=\"sub-settings\" found before title")
        return None
    
    pos = sub_start
    depth = 0
    iteration = 0
    while pos < len(section_text):
        iteration += 1
        if section_text[pos:pos+4] == '<div':
            depth += 1
        elif section_text[pos:pos+5] == '</div':
            depth -= 1
            if depth == 0:
                block = section_text[sub_start:pos+6]
                print(f"    result: {len(block)} chars, {iteration} iterations, depth 0 at pos {pos}")
                return block
        pos += 1
        if iteration > 100000:
            print(f"    TIMEOUT at pos={pos}, depth={depth}")
            break
    
    print(f"    FAILED: depth={depth} at end")
    return None

# Test with first block
print("Testing extract_sub_by_title with '背景模式':")
block = extract_sub_by_title_debug(section_html["appearance"], "背景模式")

# Also test with a block from system-info
print("\nTesting with '气象与定位':")
block2 = extract_sub_by_title_debug(section_html["system-info"], "气象与定位")