#!/usr/bin/env python3
"""
v8: 极简重构 — 保持所有块原样，只重组分类。
不做嵌套拆分。CSS添加横向标题行支持。
"""
from pathlib import Path
import re

# ============================================================
# 1. 读取原文件
# ============================================================
html_file = Path("C:/Users/33051/Desktop/BinixOvO_正式版2.0.0/index.html")
css_file = Path("C:/Users/33051/Desktop/BinixOvO_正式版2.0.0/style.css")

# 恢复原始备份
import shutil
backup = Path("C:/Users/33051/Desktop/BinixOvO_正式版2.0.0/index.html.backup_v5")
if backup.exists():
    shutil.copy(backup, html_file)
    print("✓ 恢复原始备份")

with open(html_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# ============================================================
# 2. 提取各section的完整HTML
# ============================================================
section_boundaries = {
    "appearance":    (105, 267),
    "tile-layout":   (267, 372),
    "fold-view":     (372, 560),
    "interaction":   (560, 632),
    "search":        (632, 687),
    "system-info":   (687, 759),
    "content-media": (759, 810),
}

section_html = {}
for name, (start, end) in section_boundaries.items():
    section_html[name] = ''.join(lines[start:end])
    print(f"✓ {name}: {len(section_html[name])} chars")

search_box_html = ''.join(lines[100:104])
tail_html = ''.join(lines[810:])

# ============================================================
# 3. 提取各section中的所有 sub-settings 块 (保持原样)
# ============================================================

sub_pattern = re.compile(r'<div\s+class="sub-settings(?!-)[^"]*"[^>]*>')

def extract_intact_subs(sec_text):
    """提取section中所有顶级sub-settings，保持完整不变"""
    wrappers = list(sub_pattern.finditer(sec_text))
    blocks = []
    
    for i, wrp in enumerate(wrappers):
        start = wrp.start()
        if i + 1 < len(wrappers):
            end = wrappers[i + 1].start()
        else:
            # 找匹配的闭合
            pos = wrp.end()
            depth = 1
            while pos < len(sec_text):
                if sec_text[pos:pos+4] == '<div':
                    depth += 1
                elif sec_text[pos:pos+5] == '</div':
                    depth -= 1
                    if depth == 0:
                        end = pos + 6
                        break
                pos += 1
            else:
                end = len(sec_text)
        
        blocks.append(sec_text[start:end])
    
    return blocks

# 提取所有块的标题
def get_block_title(block):
    match = re.search(r'<div\s+class="sub-settings-title"[^>]*>(.*?)</div>', block, re.DOTALL)
    if match:
        return match.group(1).strip()
    return "未命名"

# 提取
all_blocks = {}  # title -> block

for sec_name, sec_text in section_html.items():
    blocks = extract_intact_subs(sec_text)
    for block in blocks:
        title = get_block_title(block)
        if title:
            all_blocks[title] = block
            print(f"  [{sec_name}] {title} ({len(block)} chars)")
        else:
            print(f"  [{sec_name}] 无标题块 ({len(block)} chars)")

# ============================================================
# 4. 手动提取裸 config-group (不在任何 sub-settings 内)
# ============================================================

# interaction section 中裸露的 config-group
if "interaction" in section_html:
    inter_text = section_html["interaction"]
    
    for key_name, selector_id in [
        ("历史记录点击后行为", 'id="history-action-selector"'),
        ("默认直译引擎", 'id="quick-trans-selector"')
    ]:
        if selector_id in inter_text:
            pos = inter_text.find(selector_id)
            chunk = inter_text[:pos]
            cfg_start = chunk.rfind('<div class="config-group"')
            if cfg_start != -1:
                end_pos = inter_text.find('</div>', pos) + 6
                if end_pos > 5:
                    block = inter_text[cfg_start:end_pos]
                    all_blocks[key_name] = (
                        '<div class="sub-settings">\n'
                        f'                                <div class="sub-settings-title">{key_name}</div>\n'
                        + block + '\n'
                        + '                            </div>'
                    )
                    print(f"  + 裸config: {key_name}")

# 从"桌面行为"块中切除裸露的 config-group (避免ID重复)
if "桌面行为" in all_blocks:
    desk_block = all_blocks["桌面行为"]
    cut_pos = desk_block.find("历史记录点击后行为")
    if cut_pos != -1:
        pre_text = desk_block[:cut_pos]
        cfg_tag_pos = pre_text.rfind('<div class="config-group"')
        if cfg_tag_pos != -1:
            all_blocks["桌面行为"] = desk_block[:cfg_tag_pos].rstrip()
            print(f"  ✂ 已修剪 桌面行为 ({len(all_blocks['桌面行为'])} chars)")

print(f"\n总计: {len(all_blocks)} 个块")

# ============================================================
# 5. 构建新面板
# ============================================================

panel_structure = {
    "appearance-theme": {
        "title": "🎨 外观与主题",
        "blocks": [
            "背景模式", "画面滤镜与形变", "桌面时钟", "鼠标跟随光斑", "全局物理模拟"
        ]
    },
    "tile-desktop": {
        "title": "📐 磁贴与桌面",
        "blocks": [
            "磁贴图标源 (Favicon API)", "桌面行为控制", "磁贴样式定制"
        ]
    },
    "search-bar": {
        "title": "🔍 搜索栏",
        "blocks": [
            "功能与翻译 (Alt+Enter)", "外观与尺寸"
        ]
    },
    "fold-view-mode": {
        "title": "🗂️ 折叠窗口模式",
        "blocks": [
            "📚 长条书签视图", "长条书签样式"
        ]
    },
    "shortcuts-interact": {
        "title": "⌨️ 快捷键与交互",
        "blocks": [
            "基础快捷键映射", "搜索引擎管理与 1~9 快捷键", "桌面行为",
            "历史记录点击后行为", "默认直译引擎", "默认翻译引擎设置"
        ]
    },
    "system-tools": {
        "title": "⚙️ 系统工具",
        "blocks": [
            "气象与定位", "右下角工具台", "闲散功能", "🌙 夜间免打扰模式", "性能与省电"
        ]
    },
    "content-manage": {
        "title": "📦 内容管理",
        "section_attrs": ' id="setting-data-section"',
        "blocks": [
            "快速添加内容", "📚 批量导入与高级编辑"
        ]
    },
    "media-sound": {
        "title": "🎵 媒体与声音",
        "blocks": [
            "背景音乐播放器", "闹钟/计时器铃声库"
        ]
    }
}

new_panel = search_box_html

for cat_id, cat_info in panel_structure.items():
    attrs = cat_info.get("section_attrs", "")
    new_panel += f'\n                    <div class="setting-section" data-section="{cat_id}"{attrs}>\n'
    new_panel += f'                        <div class="setting-title">{cat_info["title"]}</div>\n'
    new_panel += '                        <div class="setting-content">\n'
    
    for block_title in cat_info["blocks"]:
        if block_title in all_blocks:
            block = all_blocks[block_title]
            new_panel += block + '\n'
        else:
            print(f"  ❌ 缺失: [{cat_info['title']}] {block_title}")
    
    new_panel += '                        </div>\n'
    new_panel += '                    </div>\n'

print(f"\n新面板: {len(new_panel)} chars")

# ============================================================
# 6. 合并并保存
# ============================================================
header = ''.join(lines[:100])
new_html = header + new_panel + tail_html

output_path = Path("C:/Users/33051/Desktop/BinixOvO_正式版2.0.0/index_reconstructed.html")
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(new_html)

print(f"✅ 输出: {output_path}")
print(f"文件大小: {len(new_html)} chars")

# ============================================================
# 7. 添加 CSS
# ============================================================
with open(css_file, 'r', encoding='utf-8') as f:
    css_content = f.read()

css_additions = """
/* ==========================================
   🎯 Sub-settings Header Row — 横向标题行
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
    border-color: rgba(255,255,255,0.06);
}
.sub-settings-header .sub-settings-title {
    padding: 0;
    border-bottom: none;
    flex: 0 0 auto;
    margin: 0;
    font-size: 12px;
    font-weight: 800;
    color: var(--text-b);
}
.sub-settings-header .sub-settings-title::after {
    content: none;
}
.sub-settings-header button,
.sub-settings-header .ui-button,
.sub-settings-header .small-btn {
    flex: 0 0 auto;
    width: auto;
    min-width: auto;
    margin: 0;
    padding: 6px 14px;
    font-size: 11px;
    white-space: nowrap;
    border-radius: 8px;
}

/* 响应式: 小屏纵向堆叠 */
@media (max-width: 480px) {
    .sub-settings-header {
        flex-direction: column;
        align-items: flex-start;
        gap: 8px;
    }
    .sub-settings-header .sub-settings-title {
        margin-bottom: 0;
    }
    .sub-settings-header button {
        width: 100%;
    }
}
"""

# 插入到 sub-settings 样式块之后
insert_marker = '.sub-settings:last-child'
insert_pos = css_content.find(insert_marker)
if insert_pos == -1:
    insert_pos = css_content.find('.sub-settings {')
    # 找到这个块的结束
    brace_count = 0
    for i in range(insert_pos, len(css_content)):
        if css_content[i] == '{':
            brace_count += 1
        elif css_content[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                insert_pos = i + 1
                break

css_content = css_content[:insert_pos] + '\n' + css_additions + css_content[insert_pos:]

with open(css_file, 'w', encoding='utf-8') as f:
    f.write(css_content)

print(f"✅ CSS 更新: {css_file} (+{len(css_additions)} chars)")

# ============================================================
# 8. 验证
# ============================================================
print("\n=== 验证 ===")
for cat_id, cat_info in panel_structure.items():
    found = sum(1 for b in cat_info["blocks"] if b in all_blocks)
    total = len(cat_info["blocks"])
    status = "✅" if found == total else f"⚠️ {found}/{total}"
    print(f"  {status} {cat_info['title']}")