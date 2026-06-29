#!/usr/bin/env python3
"""按行号精确定位所有section的边界"""
from pathlib import Path

html_file = Path("C:/Users/33051/Desktop/BinixOvO_正式版2.0.0/index.html")
with open(html_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 找到每行的行号和内容中 data-section 的位置
print("查找所有 data-section 标记:")
for i, line in enumerate(lines):
    if 'data-section="' in line:
        # 提取 section 名称
        import re
        m = re.search(r'data-section="([^"]+)"', line)
        if m:
            print(f"  Line {i+1}: {m.group(1)}  | {line.strip()[:80]}")

print(f"\n总共 {len(lines)} 行")

# 查找 <!-- 设置搜索框 -->
for i, line in enumerate(lines):
    if '设置搜索框' in line:
        print(f"\n搜索框起始: Line {i+1}")

# 查找 </aside>
for i, line in enumerate(lines):
    if '</aside>' in line:
        print(f"aside闭合: Line {i+1}")

# 查找所有 setting-content 的行
print("\n查找所有 setting-content 闭合 (+ sub-settings 边界):")
for i, line in enumerate(lines):
    stripped = line.strip()
    if stripped == '<!-- 设置搜索框 -->':
        print(f"  Line {i+1}: 设置搜索框注释")
    if 'setting-search-wrap' in stripped:
        print(f"  Line {i+1}: 搜索框 wrap")
    if 'setting-section' in stripped and 'data-section' in stripped:
        print(f"  Line {i+1}: [SECTION START] {stripped[:100]}")
    if stripped == '<div class="setting-content">':
        print(f"  Line {i+1}: content start")
    if stripped == '</div>' and i > 100:
        # 看看前后 context 判断这是什么闭合
        prev_line = lines[i-1].strip() if i > 0 else ""
        next_line = lines[i+1].strip() if i+1 < len(lines) else ""
        if prev_line.startswith('</div>') or next_line.startswith('</div>') or next_line.startswith('<div class="setting-section"'):
            print(f"  Line {i+1}: [POTENTIAL CLOSE] prev={prev_line[:60]} | next={next_line[:60]}")