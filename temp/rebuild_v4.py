#!/usr/bin/env python3
"""
基于 section 标记精确定位并重构
策略: 找到每个 data-section 的起止位置，提取完整HTML，然后重组
"""
from pathlib import Path
import re

html_file = Path("C:/Users/33051/Desktop/BinixOvO_正式版2.0.0/index.html")
with open(html_file, 'r', encoding='utf-8') as f:
    original = f.read()

# === Step 1: 找到所有 setting-section 的精确起止位置 ===
# 匹配 pattern: <div class="setting-section" data-section="xxx">
section_starts = []
for m in re.finditer(r'<div class="setting-section"\s+data-section="([^"]+)"\s*>', original):
    section_starts.append((m.group(1), m.start()))
    print(f"Found section: {m.group(1)} at position {m.start()}")

# === Step 2: 对每个section找到匹配的闭合标签 ===
def find_matching_close(text, start_pos, open_str='<div', close_str='</div>'):
    """找到匹配的闭合标签位置"""
    pos = start_pos
    depth = 0
    max_pos = len(text)
    while pos < max_pos:
        if text[pos:pos+len(open_str)] == open_str:
            depth += 1
            pos += len(open_str)
            continue
        if text[pos:pos+len(close_str)] == close_str:
            depth -= 1
            if depth == 0:
                return pos + len(close_str)
            pos += len(close_str)
            continue
        pos += 1
    return -1

sections = {}
for i, (name, start) in enumerate(section_starts):
    end = find_matching_close(original, start)
    if end != -1:
        sections[name] = original[start:end]
        print(f"  {name}: {start}-{end} ({end-start} bytes)")
    else:
        print(f"  {name}: UNCLOSED!")

# === Step 3: 提取设置搜索框和sideDrawer的其他部分 ===
search_box_start = original.find('<!-- 设置搜索框 -->')
if search_box_start == -1:
    print("ERROR: Cannot find setting search box")
    exit(1)

# section区域开始 (section_starts 是 (name, int_pos) 列表)
sections_start = min(s[1] for s in section_starts) if section_starts else 0

# 搜索框HTML
search_box_html = original[search_box_start:sections_start]
print(f"\nSearch box + preamble: {len(search_box_html)} bytes")

# Section 之后的闭合
# 找到所有section的结束位置
last_section_name = section_starts[-1][0]
last_section_start_pos = section_starts[-1][1]
# 找到最后一个 section 的闭合
last_section_end = find_matching_close(original, last_section_start_pos)
if last_section_end == -1:
    print(f"ERROR: Last section {last_section_name} is unclosed!")
    # 回退: 找到 </aside> 前最近的闭合
    aside_pos = original.find('</aside>', last_section_start_pos)
    last_section_end = aside_pos - 50  # approximate

print(f"Last section ends at: {last_section_end}")

# === Step 4: 映射关系: 旧 section name -> 每个旧section内部的sub-settings ===
# 按原顺序已知:
old_section_mapping = {
    "appearance": "🎨 外观主题",
    "tile-layout": "📐 磁贴布局",
    "fold-view": "🗂️ 折叠视图",
    "interaction": "⚙️ 交互行为",
    "search": "🔍 搜索与发现",
    "system-info": "📊 系统信息",
    "content-media": "📦 内容与媒体",
}

# 新分类映射
new_categories = {
    "appearance-theme": {
        "title": "🎨 外观与主题",
        "from_old_sources": [
            ("appearance", ["背景模式", "画面滤镜与形变", "桌面时钟", "鼠标跟随光斑", "全局物理模拟"])
        ]
    },
    "tile-desktop": {
        "title": "📐 磁贴与桌面",
        "from_old_sources": [
            ("tile-layout", ["磁贴图标源 (Favicon API)", "桌面行为控制", "磁贴样式定制"])
        ]
    },
    "search-bar": {
        "title": "🔍 搜索栏",
        "from_old_sources": [
            ("search", ["功能与翻译 (Alt+Enter)", "外观与尺寸"])
        ]
    },
    "fold-view-mode": {
        "title": "🗂️ 折叠窗口模式",
        "from_old_sources": [
            ("fold-view", ["📚 长条书签视图", "长条书签样式"])
        ]
    },
    "shortcuts-interact": {
        "title": "⌨️ 快捷键与交互",
        "from_old_sources": [
            ("interaction", ["基础快捷键映射", "搜索引擎管理与 1~9 快捷键", "桌面行为", "默认翻译引擎设置"])
        ]
    },
    "system-tools": {
        "title": "⚙️ 系统工具",
        "from_old_sources": [
            ("system-info", ["气象与定位", "右下角工具台", "闲散功能", "🌙 夜间免打扰模式", "性能与省电"])
        ]
    },
    "content-manage": {
        "title": "📦 内容管理",
        "from_old_sources": [
            ("content-media", ["快速添加内容", "📚 批量导入与高级编辑"])
        ]
    },
    "media-sound": {
        "title": "🎵 媒体与声音",
        "from_old_sources": [
            ("content-media", ["背景音乐播放器", "闹钟/计时器铃声库"])
        ]
    }
}

# === Step 5: 从每个旧section中提取sub-settings块 ===
def extract_subs(text, titles):
    """从section文本中提取指定标题的sub-settings块"""
    results = {}
    for title in titles:
        # 找到标题位置
        title_pos = text.find(title)
        if title_pos == -1:
            print(f"  WARN: title '{title}' not found in section")
            results[title] = None
            continue
        
        # 向前搜索最近的 <div class="sub-settings
        search_chunk = text[:title_pos]
        sub_start = search_chunk.rfind('<div class="sub-settings')
        if sub_start == -1:
            # 尝试 <div class="sub-settings anything>
            sub_start = search_chunk.rfind('<div class="sub-settings')
            if sub_start == -1:
                print(f"  WARN: no sub-settings wrapper for '{title}'")
                results[title] = None
                continue
        
        # 从这个sub-settings开始找闭合
        depth = 0
        pos = sub_start
        end_pos = -1
        while pos < len(text):
            if text[pos:pos+4] == '<div':
                depth += 1
                pos += 4
            elif text[pos:pos+5] == '</div':
                depth -= 1
                if depth == 0:
                    end_pos = pos + 6
                    break
                pos += 5
            else:
                pos += 1
        
        if end_pos == -1:
            print(f"  WARN: unclosed sub-settings for '{title}'")
            results[title] = None
            continue
        
        block = text[sub_start:end_pos]
        results[title] = block
        print(f"  ✓ '{title}': {len(block)} bytes")
    
    return results

# 为每个旧section提取sub-settings
all_subs = {}
for old_name, html in sections.items():
    print(f"\n--- Processing section: {old_name} ---")
    # 找出这个section对应的新分类中的sub-settings
    for cat_id, cat_info in new_categories.items():
        for src_section, sub_titles in cat_info["from_old_sources"]:
            if src_section == old_name:
                subs = extract_subs(html, sub_titles)
                for k, v in subs.items():
                    all_subs[k] = v

# === Step 6: 处理特殊嵌套项 ===
# fold-view 中的 ⏱️ 顶部组件独立尺寸 和 ➗ 列分割线定制
# interaction 中的 ➕ 添加自定义搜索引擎、历史记录点击后行为、默认直译引擎

# 从长条书签视图中提取顶部组件
if "📚 长条书签视图" in all_subs and all_subs["📚 长条书签视图"]:
    block = all_subs["📚 长条书签视图"]
    marker = '⏱️ 顶部组件独立尺寸'
    if marker in block:
        idx = block.find(marker)
        # 找分割线
        divider = '<div style="height: 1px; background: rgba(255,255,255,0.08); margin: 15px 0;"></div>'
        div_pos = block.rfind(divider, 0, idx)
        if div_pos != -1:
            # 提取后半部分
            sub_block = block[div_pos:]
            all_subs["⏱️ 顶部组件独立尺寸 (时钟与搜索栏)"] = sub_block
            # 截断原块
            all_subs["📚 长条书签视图"] = block[:div_pos]
            print("✓ Split: ⏱️ 顶部组件独立尺寸 from 长条书签视图")

# 从长条书签样式中提取列分割线
if "长条书签样式" in all_subs and all_subs["长条书签样式"]:
    block = all_subs["长条书签样式"]
    marker = '➗ 列分割线定制'
    if marker in block:
        idx = block.find(marker)
        divider = '<div style="height: 1px; background: rgba(255,255,255,0.08); margin: 15px 0;"></div>'
        div_pos = block.rfind(divider, 0, idx)
        if div_pos != -1:
            all_subs["➗ 列分割线定制"] = block[div_pos:]
            all_subs["长条书签样式"] = block[:div_pos]
            print("✓ Split: ➗ 列分割线定制 from 长条书签样式")

# 从搜索引擎管理中提取添加自定义搜索引擎
if "搜索引擎管理与 1~9 快捷键" in all_subs and all_subs["搜索引擎管理与 1~9 快捷键"]:
    block = all_subs["搜索引擎管理与 1~9 快捷键"]
    marker = '➕ 添加自定义搜索引擎'
    if marker in block:
        idx = block.find(marker)
        divider = '<div style="height: 1px; background: rgba(255,255,255,0.08); margin: 15px 0;"></div>'
        div_pos = block.rfind(divider, 0, idx)
        if div_pos != -1:
            all_subs["➕ 添加自定义搜索引擎"] = block[div_pos:]
            all_subs["搜索引擎管理与 1~9 快捷键"] = block[:div_pos]
            print("✓ Split: ➕ 添加自定义搜索引擎 from 搜索引擎管理")

# 从interaction section提取历史记录和直译引擎
if "interaction" in sections:
    inter_html = sections["interaction"]
    for cfg_title, cfg_id in [("历史记录点击后行为", "history-action-selector"),
                               ("默认直译引擎", "quick-trans-selector")]:
        sel_pos = inter_html.find(f'id="{cfg_id}"')
        if sel_pos != -1:
            # 向前找 config-group
            chunk = inter_html[:sel_pos]
            cfg_start = chunk.rfind('<div class="config-group"')
            if cfg_start != -1:
                # 找闭合
                depth = 0
                pos = cfg_start
                while pos < len(inter_html):
                    if inter_html[pos:pos+4] == '<div':
                        depth += 1
                        pos += 4
                    elif inter_html[pos:pos+5] == '</div':
                        depth -= 1
                        if depth == 0:
                            end = pos + 6
                            break
                        pos += 5
                    else:
                        pos += 1
                else:
                    end = -1
                if end != -1:
                    all_subs[cfg_title] = inter_html[cfg_start:end]
                    print(f"✓ Extracted: {cfg_title}")

# === Step 7: 构建新面板 ===
print("\n=== Building new panel ===")

new_panel = '                    <!-- 设置搜索框 -->\n'
new_panel += '                    <div class="setting-search-wrap">\n'
new_panel += '                        <input type="text" id="setting-search" class="ui-input setting-search-input" placeholder="搜索设置项...">\n'
new_panel += '                    </div>\n'

for cat_id, cat_info in new_categories.items():
    new_panel += f'\n                    <div class="setting-section" data-section="{cat_id}">\n'
    new_panel += f'                        <div class="setting-title">{cat_info["title"]}</div>\n'
    new_panel += '                        <div class="setting-content">\n'
    
    # 收集该分类下的所有sub-settings
    for src_section, sub_titles in cat_info["from_old_sources"]:
        for title in sub_titles:
            if title in all_subs and all_subs[title]:
                new_panel += f'                            {all_subs[title]}\n'
            else:
                print(f"  MISSING: {title} (category: {cat_id})")
                new_panel += f'                            <!-- TODO: {title} -->\n'
    
    new_panel += '                        </div>\n'
    new_panel += '                    </div>\n'

# === Step 8: 替换原始HTML ===
# 开始位置
panel_start = original.find('<!-- 设置搜索框 -->')
if panel_start == -1:
    print("FATAL: Cannot find panel start")
    exit(1)

# 结束位置: </aside> 之前的闭合
aside_pos = original.find('</aside>', panel_start)
# 往前找两个 </div>
pos = aside_pos
for _ in range(2):
    pos = original.rfind('</div>', 0, pos)
# 加上 </div>\n
end_pos = original.find('\n', pos) + 1

# 验证
panel_end = end_pos
print(f"\nPanel range: {panel_start} -> {panel_end}")
print(f"Old panel content length: {panel_end - panel_start}")
print(f"New panel content length: {len(new_panel)}")

# 备份
with open(Path("C:/Users/33051/Desktop/BinixOvO_正式版2.0.0/index.html.bak"), 'w', encoding='utf-8') as f:
    f.write(original)

# 生成新文件
new_html = original[:panel_start] + new_panel + original[panel_end:]
output_path = Path("C:/Users/33051/Desktop/BinixOvO_正式版2.0.0/index_new.html")
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(new_html)

print(f"\nDone! Output: {output_path}")
print(f"New file size: {len(new_html)} bytes (original: {len(original)} bytes)")
print(f"All subs found: {len(all_subs)}")
for k in sorted(all_subs.keys()):
    print(f"  - {k}")