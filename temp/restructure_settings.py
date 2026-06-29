#!/usr/bin/env python3
"""
Restructure sub-settings blocks: move title and top-level action buttons
into a header row, wrap remaining content in a body.
"""
import re
from pathlib import Path

html_file = Path(r"C:\Users\33051\Desktop\BinixOvO_正式版2.0.0\index_reconstructed.html")
with open(html_file, 'r', encoding='utf-8') as f:
    html = f.read()

def extract_sub_settings_blocks(html):
    """Find all <div class="sub-settings"...> blocks with their full content."""
    pattern = re.compile(r'<div\s+class="sub-settings[^"]*"[^>]*>(.*?)</div>\s*(?=\n\s*(?:<div|$))', re.DOTALL)
    blocks = []
    for m in pattern.finditer(html):
        blocks.append({
            'full': m.group(0),
            'start': m.start(),
            'end': m.end(),
            'tag': re.match(r'<div[^>]*>', m.group(0)).group(0),
            'content': m.group(1),
        })
    return blocks

def process_block(block_html):
    """Process a single sub-settings block, extracting title and creating header."""
    # Find the title
    title_match = re.search(r'<div\s+class="sub-settings-title">([^<]*)</div>', block_html)
    if not title_match:
        return block_html
    
    title_text = title_match.group(1)
    title_tag = title_match.group(0)
    
    # Get content before and after title
    before = block_html[:title_match.start()]
    after = block_html[title_match.end():]
    
    # Find the outer tag and closing
    outer_tag = re.match(r'(<div[^>]*>)', block_html).group(1)
    closing = '</div>'
    
    # Determine what goes into header vs body
    # Look for bg-mode-selector or action buttons near the top
    header_extras = []
    body_start = after
    
    # Case 1: bg-mode-selector immediately follows title
    mode_selector_match = re.search(r'^\s*(<div\s+class="config-group"[^>]*>\s*<div\s+class="bg-mode-selector"[^>]*>.*?</div>\s*</div>)', after, re.DOTALL)
    if mode_selector_match:
        header_extras.append(mode_selector_match.group(1).strip())
        body_start = after[mode_selector_match.end():]
    
    # Case 2: standalone ui-button or small-btn right after title (before any config-group)
    btn_pattern = re.compile(r'(\s*<(?:button|div)[^>]*class="[^"]*(?:ui-button|small-btn|refresh-btn|add-btn)[^"]*"[^>]*>.*?</(?:button|div)>)')
    remaining = body_start
    while btn_pattern.match(remaining):
        m = btn_pattern.match(remaining)
        header_extras.append(m.group(1).strip())
        remaining = remaining[m.end():]
        body_start = remaining
    
    # Build header
    extras_html = '\n'.join(header_extras)
    header_html = f'                <div class="sub-settings-header">\n                    {title_tag}\n                    {extras_html}\n                </div>'
    
    # Build body
    if body_start.strip():
        body_inner = body_start.strip()
        # Remove the closing </div> from original and build new
        # Find the last </div> that closes the sub-settings
        result = outer_tag + '\n' + header_html + '\n                <div class="sub-settings-body">\n' + body_inner + '\n                </div>\n' + closing
    else:
        result = outer_tag + '\n' + header_html + '\n' + closing
    
    return result

# Process all blocks
blocks = extract_sub_settings_blocks(html)

new_html = html
offset = 0
for block in blocks:
    original = block['full']
    processed = process_block(original)
    start = block['start'] + offset
    end = block['end'] + offset
    new_html = new_html[:start] + processed + new_html[end:]
    offset += len(processed) - len(original)

output = Path(r"C:\Users\33051\Desktop\BinixOvO_正式版2.0.0\index.html")
with open(output, 'w', encoding='utf-8') as f:
    f.write(new_html)

header_count = new_html.count('sub-settings-header')
body_count = new_html.count('sub-settings-body')
print(f"Done: {len(new_html)} chars")
print(f"Headers: {header_count}, Bodies: {body_count}")