#!/usr/bin/env python3
"""
v2: 通过行级别扫描提取所有 sub-settings 块，正确处理任意嵌套深度
"""
from pathlib import Path
import re

html_file = Path("C:/Users/33051/Desktop/BinixOvO_正式版2.0.0/index.html")
with open(html_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 找到设置面板范围 (行号)
start_line = None
end_line = None

for i, line in enumerate(lines):
    if '<!-- 设置搜索框 -->' in line:
        start_line = i
    if '</aside>' in line and start_line is not None and end_line is None:
        end_line = i
        break

print(f"设置面板: 行 {start_line+1} 到 {end_line+1}")

# 提取面板内容
panel_lines = lines[start_line:end_line+1]
panel_text = ''.join(panel_lines)

# 找到所有 <div class="sub-settings" 的位置
positions = []
idx = 0
while True:
    p = panel_text.find('<div class="sub-settings"', idx)
    if p == -1:
        break
    # 找到 > 的位置
    gt = panel_text.find('>', p)
    positions.append(p)
    idx = p + 10

print(f"找到 {len(positions)} 个 sub-settings 起始位置")

# 对于每个起始位置，找到匹配的 </div> 闭合
def find_matching_close(text, start_pos):
    """从 start_pos 开始(已在 > 之后)，找到匹配的 </div>"""
    i = start_pos
    depth = 1
    
    # 先跳到 > 之后
    gt = text.find('>', start_pos)
    if gt == -1:
        return -1
    i = gt + 1
    
    while i < len(text) and depth > 0:
        # 查找下一个标签
        next_open = text.find('<div', i)
        next_close = text.find('</div>', i)
        
        # 跳过注释
        next_comment = text.find('<!--', i)
        
        if next_open == -1 and next_close == -1:
            break
        
        # 选择最近的那个
        candidates = []
        if next_open != -1:
            candidates.append((next_open, 'open'))
        if next_close != -1:
            candidates.append((next_close, 'close'))
        if next_comment != -1:
            candidates.append((next_comment, 'comment'))
        
        candidates.sort()
        
        for pos, typ in candidates:
            if typ == 'open':
                depth += 1
                i = text.find('>', pos) + 1
            elif typ == 'close':
                depth -= 1
                if depth == 0:
                    return pos + 6  # 包含 </div>
                i = pos + 6
            elif typ == 'comment':
                end_comment = text.find('-->', pos)
                if end_comment != -1:
                    i = end_comment + 3
                else:
                    i = pos + 4
            break  # 只处理最近的一个
    
    return -1

# 提取每个 sub-settings 块
sub_blocks = []
for pos in positions:
    end = find_matching_close(panel_text, pos)
    if end != -1:
        block = panel_text[pos:end]
        # 提取标题
        title_match = re.search(r'<div class="sub-settings-title"[^>]*>(.*?)</div>', block, re.DOTALL)
        if title_match:
            title_html = title_match.group(1).strip()
            # 如果有 style，提取纯文本
            if 'style="' in title_html:
                inner = re.sub(r'<[^>]*>', '', title_html).strip()
            else:
                inner = title_html
            title_clean = re.sub(r'<[^>]*>', '', inner).strip()
            sub_blocks.append((title_clean, block))
            print(f"✓ [{len(sub_blocks)}] {title_clean} (长度: {len(block)})")
        else:
            sub_blocks.append(("???", block))
            print(f"✓ [{len(sub_blocks)}] ??? (长度: {len(block)})")
    else:
        print(f"✗ 无法找到闭合")

print(f"\n成功提取 {len(sub_blocks)} 个 sub-settings")

# 保存到文件以便检查
with open(Path("C:/Users/33051/Desktop/BinixOvO_正式版2.0.0/temp/all_subs.txt"), 'w', encoding='utf-8') as f:
    for i, (title, block) in enumerate(sub_blocks):
        f.write(f"========= #{i+1}: {title} =========\n")
        f.write(block)
        f.write("\n\n")

print("已保存到 all_subs.txt")