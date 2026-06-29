#!/usr/bin/env python3
"""Apply sub-settings-header wrappers and copy to index.html"""
import re
from pathlib import Path

html_file = Path(r"C:\Users\33051\Desktop\BinixOvO_正式版2.0.0\index_reconstructed.html")
with open(html_file, 'r', encoding='utf-8') as f:
    html_content = f.read()

def add_header_row(match):
    block = match.group(0)
    title_match = re.search(r'(<div\s+class="sub-settings-title"[^>]*>.*?</div>)', block, re.DOTALL)
    if not title_match:
        return block

    title_tag = title_match.group(1)
    after_title = block[title_match.end():]

    btn_pattern = re.compile(r'(\s*<button[^>]*>.*?</button>)')
    buttons = []
    remaining = after_title
    for btn_match in btn_pattern.finditer(remaining):
        prefix = remaining[:btn_match.start()]
        if re.search(r'<(div|input|select|textarea)', prefix):
            break
        buttons.append(btn_match.group(1).strip())

    if not buttons:
        return block

    buttons_html = ''.join(buttons)
    header = f'<div class="sub-settings-header">\n{title_tag}\n{buttons_html}\n                                </div>'
    for btn in buttons:
        remaining = remaining.replace(btn, '', 1)

    return block[:title_match.start()] + header + remaining

html_content = re.sub(
    r'<div\s+class="sub-settings(?!-)[^"]*"[^>]*>.*?</div>',
    add_header_row,
    html_content,
    flags=re.DOTALL
)

output = Path(r"C:\Users\33051\Desktop\BinixOvO_正式版2.0.0\index.html")
with open(output, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"Done: {len(html_content)} chars, headers: {html_content.count('sub-settings-header')}")