#!/usr/bin/env python3
"""
V2: Properly extract sub-settings blocks using depth counting,
then move title and top-level action buttons into header row.
"""
import re
from pathlib import Path

html_file = Path(r"C:\Users\33051\Desktop\BinixOvO_正式版2.0.0\index_reconstructed.html")
with open(html_file, 'r', encoding='utf-8') as f:
    html = f.read()

def find_sub_settings_blocks(html):
    """Find all sub-settings div blocks using depth counting."""
    blocks = []
    pattern = re.compile(r'<div\s+class="sub-settings[^"]*"')
    
    pos = 0
    while True:
        m = pattern.search(html, pos)
        if not m:
            break
        
        start = m.start()
        # Count depth from this opening tag
        depth = 1
        i = m.end()
        tag_pattern = re.compile(r'<(/?)(div|section|article|nav|main|aside|header|footer|form|fieldset)\b')
        
        while i < len(html) and depth > 0:
            tag = tag_pattern.search(html, i)
            if not tag:
                break
            if tag.group(1) == '/':
                depth -= 1
                if depth == 0:
                    end = tag.end()
                    blocks.append((start, end, html[start:end]))
                    break
            else:
                depth += 1
            i = tag.end()
        
        if depth > 0:
            # Couldn't find matching closing tag
            blocks.append((start, len(html), html[start:]))
            break
        
        pos = end
    
    return blocks

blocks = find_sub_settings_blocks(html)
print(f"Found {len(blocks)} sub-settings blocks")

# Process each block
new_html = html
offset = 0

for start, end, block_html in blocks:
    title_match = re.search(r'<div\s+class="sub-settings-title">([^<]*)</div>', block_html)
    if not title_match:
        continue
    
    title_text = title_match.group(1)
    title_tag = title_match.group(0)
    
    # Content after title (inside the block, not including outer tags)
    inner_start = block_html.index('>') + 1
    inner_end = block_html.rindex('</div>')
    inner_html = block_html[inner_start:inner_end]
    
    after_title = inner_html[title_match.end():]
    
    # Extract header extras: bg-mode-selector or ui-button/small-btn
    header_extras = []
    body_html = after_title
    
    # Case 1: bg-mode-selector follows title
    ms_match = re.match(
        r'\s*(<div\s+class="config-group"[^>]*>\s*<div\s+class="bg-mode-selector"[^>]*>.*?</div>\s*</div>)',
        after_title, re.DOTALL
    )
    if ms_match:
        header_extras.append(ms_match.group(1).strip())
        body_html = after_title[ms_match.end():]
    
    # Case 2: Top-level buttons (ui-button, small-btn, etc.) before any config-group
    btn_re = re.compile(
        r'^\s*(<(?:button|div)\s[^>]*class="[^"]*(?:ui-button|small-btn)[^"]*"[^>]*>.*?</(?:button|div)>)',
        re.DOTALL
    )
    while body_html and btn_re.match(body_html):
        m = btn_re.match(body_html)
        header_extras.append(m.group(1).strip())
        body_html = body_html[m.end():]
    
    # Build new block
    outer_tag = re.match(r'<div[^>]*>', block_html).group(0)
    extras_str = '\n'.join(header_extras)
    
    header = f'<div class="sub-settings-header">\n{title_tag}\n{extras_str}\n</div>'
    
    if body_html.strip():
        new_block = f'{outer_tag}\n{header}\n<div class="sub-settings-body">\n{body_html.strip()}\n</div>\n</div>'
    else:
        new_block = f'{outer_tag}\n{header}\n</div>'
    
    actual_start = start + offset
    actual_end = end + offset
    new_html = new_html[:actual_start] + new_block + new_html[actual_end:]
    offset += len(new_block) - (end - start)
    
    print(f"  {title_text}: {len(header_extras)} extras")

header_count = new_html.count('sub-settings-header')
body_count = new_html.count('sub-settings-body')
print(f"\nDone: {len(new_html)} chars, Headers: {header_count}, Bodies: {body_count}")

output = Path(r"C:\Users\33051\Desktop\BinixOvO_正式版2.0.0\index.html")
with open(output, 'w', encoding='utf-8') as f:
    f.write(new_html)