#!/usr/bin/env python3
"""
基于行号的精确重构
"""
from pathlib import Path

html_file = Path("C:/Users/33051/Desktop/BinixOvO_正式版2.0.0/index.html")
with open(html_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# === 1. 提取各section的完整HTML ===
# 注意: 行号是1-indexed，但Python列表是0-indexed
section_boundaries = {
    "appearance":    (105, 267),   # lines 106-267
    "tile-layout":   (267, 372),   # lines 268-372
    "fold-view":     (372, 560),   # lines 373-560
    "interaction":   (560, 632),   # lines 561-632
    "search":        (632, 687),   # lines 633-687
    "system-info":   (687, 759),   # lines 688-759
    "content-media": (759, 811),   # lines 760-811
}

# 提取每个section的完整HTML
section_html = {}
for name, (start, end) in section_boundaries.items():
    section_html[name] = ''.join(lines[start:end])
    print(f"✓ 提取 {name}: {len(section_html[name])} 字符")

# 提取搜索框
search_box_html = ''.join(lines[100:104])  # lines 101-104
print(f"✓ 搜索框: {len(search_box_html)} 字符")

# 提取尾部 (</aside> 之后的所有内容)
tail_html = ''.join(lines[811:])  # line 812+
print(f"✓ 尾部: {len(tail_html)} 字符")

# === 2. 从每个section中提取sub-settings块 ===
# 辅助函数: 提取指定标题的sub-settings块
def extract_sub_by_title(section_text, title):
    """从section文本中提取指定标题的sub-settings块"""
    # 找到标题位置
    title_pos = section_text.find(title)
    if title_pos == -1:
        return None
    
    # 向前搜索最近的 <div class="sub-settings"> (必须是独立tag，不能是 sub-settings-title)
    # 使用正则精确匹配
    import re
    search_chunk = section_text[:title_pos]
    matches = list(re.finditer(r'<div\s+class="sub-settings"[^>]*>', search_chunk))
    if not matches:
        return None
    sub_start = matches[-1].start()  # 最近的一个
    
    # 从sub_start开始找到匹配的闭合标签
    pos = sub_start
    depth = 0
    while pos < len(section_text):
        if section_text[pos:pos+4] == '<div':
            depth += 1
        elif section_text[pos:pos+5] == '</div':
            depth -= 1
            if depth == 0:
                return section_text[sub_start:pos+6]
        pos += 1
    
    return None

# 从各section提取sub-settings
sub_blocks = {}

# appearance 中的块
appearance_subs = [
    "背景模式",
    "画面滤镜与形变",
    "桌面时钟",
    "鼠标跟随光斑",
    "全局物理模拟"
]
for sub in appearance_subs:
    block = extract_sub_by_title(section_html["appearance"], sub)
    if block:
        sub_blocks[sub] = block
        print(f"  ✓ appearance: {sub}")

# tile-layout 中的块
tile_subs = [
    "磁贴图标源 (Favicon API)",
    "桌面行为控制",
    "磁贴样式定制"
]
for sub in tile_subs:
    block = extract_sub_by_title(section_html["tile-layout"], sub)
    if block:
        sub_blocks[sub] = block
        print(f"  ✓ tile-layout: {sub}")

# fold-view 中的块
fold_subs = [
    "📚 长条书签视图",
    "长条书签样式"
]
for sub in fold_subs:
    block = extract_sub_by_title(section_html["fold-view"], sub)
    if block:
        sub_blocks[sub] = block
        print(f"  ✓ fold-view: {sub}")

# interaction 中的块
interaction_subs = [
    "基础快捷键映射",
    "搜索引擎管理与 1~9 快捷键",
    "桌面行为",
    "默认翻译引擎设置"
]
for sub in interaction_subs:
    block = extract_sub_by_title(section_html["interaction"], sub)
    if block:
        sub_blocks[sub] = block
        print(f"  ✓ interaction: {sub}")

# search 中的块
search_subs = [
    "功能与翻译 (Alt+Enter)",
    "外观与尺寸"
]
for sub in search_subs:
    block = extract_sub_by_title(section_html["search"], sub)
    if block:
        sub_blocks[sub] = block
        print(f"  ✓ search: {sub}")

# system-info 中的块
system_subs = [
    "气象与定位",
    "右下角工具台",
    "闲散功能",
    "🌙 夜间免打扰模式",
    "性能与省电"
]
for sub in system_subs:
    block = extract_sub_by_title(section_html["system-info"], sub)
    if block:
        sub_blocks[sub] = block
        print(f"  ✓ system-info: {sub}")

# content-media 中的块
content_subs = [
    "快速添加内容",
    "📚 批量导入与高级编辑",
    "背景音乐播放器",
    "闹钟/计时器铃声库"
]
for sub in content_subs:
    block = extract_sub_by_title(section_html["content-media"], sub)
    if block:
        sub_blocks[sub] = block
        print(f"  ✓ content-media: {sub}")

# == 3. 提取特殊嵌套块 (在sub_blocks提取之前，修改已有块的内容) ===

def wrap_in_sub_settings(content, title_html):
    """将提取的嵌套内容包装成独立的 sub-settings 块"""
    return (
        '<div class="sub-settings">\n'
        + title_html + '\n'
        + content + '\n'
        + '                            </div>'
    )

# 从长条书签视图中提取顶部组件
if "📚 长条书签视图" in sub_blocks:
    block = sub_blocks["📚 长条书签视图"]
    marker = '⏱️ 顶部组件独立尺寸'
    if marker in block:
        idx = block.find(marker)
        divider = '<div style="height: 1px; background: rgba(255,255,255,0.08); margin: 15px 0;"></div>'
        div_pos = block.rfind(divider, 0, idx)
        if div_pos != -1:
            # 提取后半部分作为子内容
            sub_content = block[div_pos + len(divider):]
            # 去掉末尾多余的 </div> 闭合
            sub_content = sub_content.rsplit('</div>', 1)[0]
            # 包装
            sub_blocks["⏱️ 顶部组件独立尺寸 (时钟与搜索栏)"] = wrap_in_sub_settings(
                sub_content,
                '                                <div class="sub-settings-title" style="color: #6ee7b7;">⏱️ 顶部组件独立尺寸 (时钟与搜索栏)</div>'
            )
            # 截断原块
            sub_blocks["📚 长条书签视图"] = block[:div_pos + len(divider)]
            print("✓ 分割: 顶部组件独立尺寸")

# 从长条书签样式中提取列分割线
if "长条书签样式" in sub_blocks:
    block = sub_blocks["长条书签样式"]
    marker = '➗ 列分割线定制'
    if marker in block:
        idx = block.find(marker)
        divider = '<div style="height: 1px; background: rgba(255,255,255,0.08); margin: 15px 0;"></div>'
        div_pos = block.rfind(divider, 0, idx)
        if div_pos != -1:
            sub_content = block[div_pos + len(divider):]
            sub_content = sub_content.rsplit('</div>', 1)[0]
            sub_blocks["➗ 列分割线定制"] = wrap_in_sub_settings(
                sub_content,
                '                                <div class="sub-settings-title" style="color: #6ee7b7;">➗ 列分割线定制</div>'
            )
            sub_blocks["长条书签样式"] = block[:div_pos + len(divider)]
            print("✓ 分割: 列分割线定制")

# 从搜索引擎管理中提取添加自定义搜索引擎
if "搜索引擎管理与 1~9 快捷键" in sub_blocks:
    block = sub_blocks["搜索引擎管理与 1~9 快捷键"]
    marker = '➕ 添加自定义搜索引擎'
    if marker in block:
        idx = block.find(marker)
        divider = '<div style="height: 1px; background: rgba(255,255,255,0.08); margin: 15px 0;"></div>'
        div_pos = block.rfind(divider, 0, idx)
        if div_pos != -1:
            sub_content = block[div_pos + len(divider):]
            sub_content = sub_content.rsplit('</div>', 1)[0]
            sub_blocks["➕ 添加自定义搜索引擎"] = wrap_in_sub_settings(
                sub_content,
                '                                <div class="sub-settings-title">➕ 添加自定义搜索引擎</div>'
            )
            sub_blocks["搜索引擎管理与 1~9 快捷键"] = block[:div_pos + len(divider)]
            print("✓ 分割: 添加自定义搜索引擎")

# 从interaction section提取历史记录和直译引擎 (作为config-group)
if "interaction" in section_html:
    inter_text = section_html["interaction"]
    # 历史记录点击后行为
    if 'id="history-action-selector"' in inter_text:
        # 向前找最近的 <div class="config-group"
        pos = inter_text.find('id="history-action-selector"')
        chunk = inter_text[:pos]
        cfg_start = chunk.rfind('<div class="config-group"')
        if cfg_start != -1:
            # 找到闭合
            end_pos = inter_text.find('</div>', pos) + 6
            if end_pos > 5:
                block = inter_text[cfg_start:end_pos]
                sub_blocks["历史记录点击后行为"] = (
                    '<div class="sub-settings">\n'
                    '                                <div class="sub-settings-title">历史记录点击后行为</div>\n'
                    + block + '\n'
                    + '                            </div>'
                )
                print("✓ 提取: 历史记录点击后行为")
    
    # 默认直译引擎
    if 'id="quick-trans-selector"' in inter_text:
        pos = inter_text.find('id="quick-trans-selector"')
        chunk = inter_text[:pos]
        cfg_start = chunk.rfind('<div class="config-group"')
        if cfg_start != -1:
            end_pos = inter_text.find('</div>', pos) + 6
            if end_pos > 5:
                block = inter_text[cfg_start:end_pos]
                sub_blocks["默认直译引擎"] = (
                    '<div class="sub-settings">\n'
                    '                                <div class="sub-settings-title">默认直译引擎</div>\n'
                    + block + '\n'
                    + '                            </div>'
                )
                print("✓ 提取: 默认直译引擎")

# === 4. 构建新面板 ===
print(f"\n=== 构建新面板 (已提取 {len(sub_blocks)} 个块) ===")

# 新分类映射
new_categories = {
    "appearance-theme": {
        "title": "🎨 外观与主题",
        "subs": ["背景模式", "画面滤镜与形变", "桌面时钟", "鼠标跟随光斑", "全局物理模拟"]
    },
    "tile-desktop": {
        "title": "📐 磁贴与桌面",
        "subs": ["磁贴图标源 (Favicon API)", "桌面行为控制", "磁贴样式定制"]
    },
    "search-bar": {
        "title": "🔍 搜索栏",
        "subs": ["功能与翻译 (Alt+Enter)", "外观与尺寸"]
    },
    "fold-view-mode": {
        "title": "🗂️ 折叠窗口模式",
        "subs": ["📚 长条书签视图", "⏱️ 顶部组件独立尺寸 (时钟与搜索栏)", "长条书签样式", "➗ 列分割线定制"]
    },
    "shortcuts-interact": {
        "title": "⌨️ 快捷键与交互",
        "subs": ["基础快捷键映射", "搜索引擎管理与 1~9 快捷键", "➕ 添加自定义搜索引擎", "桌面行为", "历史记录点击后行为", "默认直译引擎", "默认翻译引擎设置"]
    },
    "system-tools": {
        "title": "⚙️ 系统工具",
        "subs": ["气象与定位", "右下角工具台", "闲散功能", "🌙 夜间免打扰模式", "性能与省电"]
    },
    "content-manage": {
        "title": "📦 内容管理",
        "subs": ["快速添加内容", "📚 批量导入与高级编辑"]
    },
    "media-sound": {
        "title": "🎵 媒体与声音",
        "subs": ["背景音乐播放器", "闹钟/计时器铃声库"]
    }
}

# 构建新面板HTML
new_panel = search_box_html  # starts with <!-- 设置搜索框 -->

for cat_id, cat_info in new_categories.items():
    new_panel += f'\n                    <div class="setting-section" data-section="{cat_id}">\n'
    new_panel += f'                        <div class="setting-title">{cat_info["title"]}</div>\n'
    new_panel += '                        <div class="setting-content">\n'
    
    for sub_title in cat_info["subs"]:
        if sub_title in sub_blocks:
            block = sub_blocks[sub_title]
            # 移除原有缩进 (28空格)，重新加上正确缩进
            dedented = '\n'.join(line[28:] if line.startswith(' ' * 28) else line for line in block.split('\n'))
            new_panel += f'                            {dedented}\n'
        else:
            print(f"  ⚠️  缺失: {sub_title}")
            new_panel += f'                            <div class="sub-settings">\n'
            new_panel += f'                                <div class="sub-settings-title">{sub_title}</div>\n'
            new_panel += f'                                <div class="config-group"><p style="color: rgba(255,255,255,0.4); font-size: 12px;">设置项提取失败，请手动检查</p></div>\n'
            new_panel += f'                            </div>\n'
    
    new_panel += '                        </div>\n'
    new_panel += '                    </div>\n'

print(f"新面板长度: {len(new_panel)} 字符")

# === 5. 替换并保存 ===
# 构建完整的新HTML
# 头部: lines[0:100] (前100行)
header = ''.join(lines[:100])
new_html = header + new_panel + tail_html

# 备份
backup_path = Path("C:/Users/33051/Desktop/BinixOvO_正式版2.0.0/index.html.backup_final")
with open(backup_path, 'w', encoding='utf-8') as f:
    f.write(''.join(lines))

# 保存新文件
output_path = Path("C:/Users/33051/Desktop/BinixOvO_正式版2.0.0/index_reconstructed.html")
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(new_html)

print(f"\n✅ 完成!")
print(f"原始文件备份到: {backup_path}")
print(f"新文件保存到: {output_path}")
print(f"新文件大小: {len(new_html)} 字符")
print(f"提取的块: {len(sub_blocks)} 个")
print("缺失的块:")
for cat_id, cat_info in new_categories.items():
    for sub in cat_info["subs"]:
        if sub not in sub_blocks:
            print(f"  - {sub} (在 {cat_info['title']})")