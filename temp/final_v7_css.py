#!/usr/bin/env python3
"""
最终 v7: 处理CSS + 修复 block 中需要横向标题行的部分
"""
from pathlib import Path
import re

html_file = Path("C:/Users/33051/Desktop/BinixOvO_正式版2.0.0/index_reconstructed.html")
css_file = Path("C:/Users/33051/Desktop/BinixOvO_正式版2.0.0/style.css")

with open(html_file, 'r', encoding='utf-8') as f:
    html_content = f.read()

with open(css_file, 'r', encoding='utf-8') as f:
    css_content = f.read()

# ============================================================
# 1. HTML 处理: 识别 sub-settings 中有需要横向排版的标题行
# ============================================================

def add_header_row(match):
    """为 sub-settings 块添加 header 行包装"""
    block = match.group(0)
    
    # 找到标题
    title_match = re.search(r'(<div\s+class="sub-settings-title"[^>]*>.*?</div>)', block, re.DOTALL)
    if not title_match:
        return block
    
    title_tag = title_match.group(1)
    after_title = block[title_match.end():]
    before_title = block[:title_match.start()]
    
    # 找标题行后面紧邻的操作按钮 (在同一 div depth 层级)
    # 匹配: 缩进空格后紧跟的 button 元素
    btn_pattern = re.compile(r'(\s*<button[^>]*>.*?</button>)')
    
    buttons = []
    remaining = after_title
    for btn_match in btn_pattern.finditer(remaining):
        # 检查这个按钮前面是否只有空白字符和 config-group 闭合标签
        prefix = remaining[:btn_match.start()]
        # 如果在按钮之前有 config-group 或 inner-settings-group 开头标签，说明按钮属于内部内容
        if re.search(r'<(div|input|select|textarea)', prefix):
            break
        buttons.append(btn_match.group(1).strip())
    
    if not buttons:
        return block
    
    # 构建 header
    buttons_html = ''.join(buttons)
    header = f'<div class="sub-settings-header">\n{title_tag}\n{buttons_html}\n                                </div>'
    
    # 从 remaining 中移除这些按钮
    for btn in buttons:
        remaining = remaining.replace(btn, '', 1)
    
    return before_title + header + remaining

# 对每个 sub-settings 块应用 header 处理
html_content = re.sub(
    r'<div\s+class="sub-settings(?!-)[^"]*"[^>]*>.*?</div>',
    add_header_row,
    html_content,
    flags=re.DOTALL
)

# ============================================================
# 2. CSS 处理: 添加横向标题行样式
# ============================================================

css_additions = """
/* ==========================================
   🎯 Sub-settings Header Row (横向标题行)
   ========================================== */
.sub-settings-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 16px;
    border-bottom: 1px dashed transparent;
    gap: 12px;
    cursor: pointer;
    user-select: none;
    transition: background 0.3s ease, border-color 0.3s ease;
    flex-wrap: wrap;
}
.sub-settings-header:hover {
    background: rgba(255,255,255,0.04);
}
.sub-settings-header .sub-settings-title {
    padding: 0;
    border-bottom: none;
    flex: 0 0 auto;
    margin: 0;
}
.sub-settings-header .sub-settings-title::after {
    content: none;
}
.sub-settings-header button,
.sub-settings-header .ui-button,
.sub-settings-header .small-btn {
    flex: 0 0 auto;
    width: auto;
    min-width: 0;
    margin: 0;
    padding: 6px 12px;
    font-size: 11px;
    white-space: nowrap;
}

/* Responsive: small screen stacks header vertically */
@media (max-width: 480px) {
    .sub-settings-header {
        flex-direction: column;
        align-items: flex-start;
    }
    .sub-settings-header .sub-settings-title {
        margin-bottom: 8px;
    }
    .sub-settings-header button {
        width: 100%;
    }
}
"""

# 在 CSS 中 sub-settings 样式之后插入
insert_pos = css_content.find('.sub-settings {')
# 找到该块的结束 (下一个 } 后面跟空白行)
pos = insert_pos
brace_count = 0
in_block = False
for i in range(insert_pos, len(css_content)):
    if css_content[i] == '{':
        in_block = True
        brace_count += 1
    elif css_content[i] == '}':
        brace_count -= 1
        if brace_count == 0 and in_block:
            pos = i + 1
            break

# 在 sub-settings 块后插入新样式
css_content = css_content[:pos] + '\n' + css_additions + css_content[pos:]

# ============================================================
# 保存
# ============================================================
with open(html_file, 'w', encoding='utf-8') as f:
    f.write(html_content)

with open(css_file, 'w', encoding='utf-8') as f:
    f.write(css_content)

print(f"✅ HTML 更新: {html_file}")
print(f"✅ CSS 更新: {css_file}")
print(f"HTML 大小: {len(html_content)} 字符")
print(f"CSS 大小: {len(css_content)} 字符")

# 统计 sub-settings-header 数量
header_count = html_content.count('sub-settings-header')
print(f"sub-settings-header 实例: {header_count}")