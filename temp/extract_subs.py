#!/usr/bin/env python3
"""提取所有 sub-settings 块并列出其标题"""
import re
from pathlib import Path

html_file = Path("C:/Users/33051/Desktop/BinixOvO_正式版2.0.0/index.html")
with open(html_file, 'r', encoding='utf-8') as f:
    content = f.read()

# 提取从设置搜索框到 sideDrawer 闭合的内容
start = content.find('<!-- 设置搜索框 -->')
# 找到后面的 </div>\n            </div>\n        </aside>
# 先找 </aside>
aside_end = content.find('</aside>', start)
print(f"找到 </aside> 位置: {aside_end}")

# 提取设置面板内容
panel = content[start:aside_end]

# 提取所有 sub-settings 块 - 使用更精确的方法
# 找到所有 <div class="sub-settings" 位置
pos = 0
subs = []
while True:
    idx = panel.find('<div class="sub-settings"', pos)
    if idx == -1:
        break
    
    # 找到这个 sub-settings 块的结束
    # 统计 <div 和 </div> 的深度
    depth = 1
    i = idx + len('<div class="sub-settings"')
    
    # 跳过属性一直到 >
    close_bracket = panel.find('>', i)
    if close_bracket == -1:
        break
    i = close_bracket + 1
    
    # 现在统计深度
    while depth > 0 and i < len(panel):
        # 查找下一个 <div 或 </div>
        next_open = panel.find('<div', i)
        next_close = panel.find('</div>', i)
        
        if next_open == -1 and next_close == -1:
            break
        elif next_open == -1:
            next_token = next_close
            token_type = 'close'
        elif next_close == -1:
            next_token = next_open
            token_type = 'open'
        elif next_open < next_close:
            next_token = next_open
            token_type = 'open'
        else:
            next_token = next_close
            token_type = 'close'
        
        # 检查是否在字符串或注释中（简化处理，跳过）
        if token_type == 'open':
            # 检查是否是自闭合
            after_open = panel[next_token+4:]
            # 简单的自闭合检测
            depth += 1
            i = panel.find('>', next_token) + 1
        else:
            depth -= 1
            if depth == 0:
                # 找到匹配的闭合
                block_end = next_token + 6  # </div>
                block = panel[idx:block_end]
                
                # 提取标题
                title_match = re.search(r'<div class="sub-settings-title"[^>]*>(.*?)</div>', block, re.DOTALL)
                if title_match:
                    title_html = title_match.group(1).strip()
                    # 去除 style 属性，提取纯文本
                    title_clean = re.sub(r'<[^>]*>', '', title_html).strip()
                    subs.append((title_clean, block, idx))
                    print(f"✓ {title_clean}")
                else:
                    subs.append(("UNKNOWN", block, idx))
                    print(f"? UNKNOWN title at {idx}")
                
                pos = block_end
                break
            i = next_token + 6
    
    if depth > 0:
        print(f"警告：无法找到 sub-settings 的闭合标签，位置: {idx}")
        pos = idx + 1

print(f"\n总共找到 {len(subs)} 个 sub-settings 块")

# 保存提取结果
output = ""
for title, html, pos in subs:
    output += f"--- TITLE: {title} ---\n"
    output += html[:200] + "...\n\n"

with open(Path("C:/Users/33051/Desktop/BinixOvO_正式版2.0.0/temp/extracted_subs.txt"), 'w', encoding='utf-8') as f:
    f.write(output)

print("提取结果已保存到 extracted_subs.txt")