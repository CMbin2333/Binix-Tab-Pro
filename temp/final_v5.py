#!/usr/bin/env python3
"""
最终版重构 - 处理所有边缘情况
"""
from pathlib import Path
import re

html_file = Path("C:/Users/33051/Desktop/BinixOvO_正式版2.0.0/index.html")
with open(html_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

section_boundaries = {
    "appearance":    (105, 267),
    "tile-layout":   (267, 372),
    "fold-view":     (372, 560),
    "interaction":   (560, 632),
    "search":        (632, 687),
    "system-info":   (687, 759),
    "content-media": (759, 811),
}

section_html = {}
for name, (start, end) in section_boundaries.items():
    section_html[name] = ''.join(lines[start:end])

search_box_html = ''.join(lines[100:104])
tail_html = ''.join(lines[811:])

# ============================================================
# 新的提取策略：基于 sub-settings-title 标题提取内容
# ============================================================

def extract_all_subs_by_title(section_text, section_name):
    """
    通用提取: 找到所有 sub-settings-title，向前找 enclosing <div class="sub-settings"
    """
    results = {}
    # 找到所有 sub-settings-title 标签
    title_pattern = re.compile(r'<div\s+class="sub-settings-title"[^>]*>(.*?)</div>', re.DOTALL)
    
    titles = list(title_pattern.finditer(section_text))
    
    for i, match in enumerate(titles):
        title_text = match.group(1).strip()
        title_start = match.start()
        
        # 向前搜索最近的 <div class="sub-settings" (精确匹配)
        search_chunk = section_text[:title_start]
        # 匹配各种变体: class="sub-settings", class="sub-settings add-form", class="sub-settings" style="..."
        sub_pattern = re.compile(r'<div\s+class="sub-settings[^"]*"[^>]*>')
        sub_matches = list(sub_pattern.finditer(search_chunk))
        if not sub_matches:
            print(f"  [WARN] {section_name}: no sub-settings wrapper for '{title_text}'")
            continue
        sub_start = sub_matches[-1].start()
        
        # 确定这个块的结束位置
        if i + 1 < len(titles):
            # 下一个标题的开头
            next_title_start = titles[i + 1].start()
            # 但块结束可能在下一个标题的 sub-settings wrapper 之前
            # 找到下一个标题的 sub-settings wrapper
            next_search = section_text[:next_title_start]
            next_sub_matches = list(sub_pattern.finditer(next_search))
            if next_sub_matches:
                block_end = next_sub_matches[-1].start()
            else:
                block_end = next_title_start
        else:
            # 最后一个块 - 需要找到匹配的闭合
            # 使用简化方法: 从 sub_start 开始计数
            pos = sub_start
            depth = 0
            while pos < len(section_text):
                if section_text[pos:pos+4] == '<div':
                    depth += 1
                elif section_text[pos:pos+5] == '</div':
                    depth -= 1
                    if depth == 0:
                        block_end = pos + 6
                        break
                pos += 1
            else:
                # 如果div计数失败，尝试找到下一个 </div>\n + 空行 + <div class="setting-section" 或 </div>
                block_end = len(section_text)
        
        block = section_text[sub_start:block_end]
        results[title_text] = block
    
    return results

# 提取所有section的所有sub-settings
all_subs = {}
for name, html in section_html.items():
    subs = extract_all_subs_by_title(html, name)
    for title, block in subs.items():
        key = title
        all_subs[key] = block

print(f"\n提取了 {len(all_subs)} 个sub-settings块:")
for k in sorted(all_subs.keys()):
    print(f"  [{len(all_subs[k])} chars] {k}")

# ============================================================
# 处理特殊嵌套块
# ============================================================

def wrap_in_sub_settings(content, title_html):
    return (
        '<div class="sub-settings">\n'
        + title_html + '\n'
        + content + '\n'
        + '                            </div>'
    )

# 分割规则: 如果某个块内部有嵌入的 sub-settings-title（在divider之后），提取出来
for key in list(all_subs.keys()):
    block = all_subs[key]
    # 检查是否有嵌套的 sub-settings-title (通常在height:1px分割线之后)
    nested_titles = re.findall(r'<div style="height: 1px;.*?</div>\s*\n\s*<div\s+class="sub-settings-title"[^>]*>(.*?)</div>', block, re.DOTALL)
    
    for nested_title in nested_titles:
        nested_title = nested_title.strip()
        if nested_title == key:
            continue
        
        # 找到分割线
        divider_match = re.search(r'<div style="height: 1px;.*?</div>', block)
        if not divider_match:
            continue
        div_pos = divider_match.start()
        
        # 在block中从这个分割线位置找嵌套标题
        after_divider = block[div_pos:]
        nested_match = re.search(r'<div\s+class="sub-settings-title"[^>]*>' + re.escape(nested_title) + r'</div>', after_divider)
        if nested_match:
            nested_start = div_pos + nested_match.start()
            # 从分割线开始提取
            nested_content = block[div_pos:]
            
            # 包装这个嵌套块
            title_html = f'                                <div class="sub-settings-title" style="color: #6ee7b7;">{nested_title}</div>'
            if '➗' in nested_title:
                title_html = f'                                <div class="sub-settings-title" style="color: #6ee7b7;">{nested_title}</div>'
            elif '➕' in nested_title:
                title_html = f'                                <div class="sub-settings-title">{nested_title}</div>'
            
            # 清理嵌套内容: 去掉末尾多余的闭合标签
            nested_clean = nested_content
            # 尝试移除末尾多余的 </div>
            while nested_clean.rstrip().endswith('</div>'):
                nested_clean = nested_clean.rstrip()[:-6].rstrip()
                # 最多移除2个
                if nested_content.count('</div>') - nested_clean.count('</div>') >= 2:
                    break
            
            new_key = nested_title
            all_subs[new_key] = wrap_in_sub_settings(nested_content, title_html)
            
            # 截断原块
            all_subs[key] = block[:div_pos + len(divider_match.group(0))]
            
            print(f"  分割: {new_key} from {key}")

# ============================================================
# 提取历史记录点击后行为和默认直译引擎
# ============================================================
if "interaction" in section_html:
    inter_text = section_html["interaction"]
    
    # 历史记录点击后行为
    if 'id="history-action-selector"' in inter_text:
        pos = inter_text.find('id="history-action-selector"')
        chunk = inter_text[:pos]
        cfg_start = chunk.rfind('<div class="config-group"')
        if cfg_start != -1:
            end_pos = inter_text.find('</div>', pos) + 6
            if end_pos > 5:
                block = inter_text[cfg_start:end_pos]
                all_subs["历史记录点击后行为"] = (
                    '<div class="sub-settings">\n'
                    '                                <div class="sub-settings-title">历史记录点击后行为</div>\n'
                    + block + '\n'
                    + '                            </div>'
                )
                print("  + 历史记录点击后行为")
    
    # 默认直译引擎
    if 'id="quick-trans-selector"' in inter_text:
        pos = inter_text.find('id="quick-trans-selector"')
        chunk = inter_text[:pos]
        cfg_start = chunk.rfind('<div class="config-group"')
        if cfg_start != -1:
            end_pos = inter_text.find('</div>', pos) + 6
            if end_pos > 5:
                block = inter_text[cfg_start:end_pos]
                all_subs["默认直译引擎"] = (
                    '<div class="sub-settings">\n'
                    '                                <div class="sub-settings-title">默认直译引擎</div>\n'
                    + block + '\n'
                    + '                            </div>'
                )
                print("  + 默认直译引擎")

# ============================================================
# 构建新面板
# ============================================================
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

new_panel = search_box_html

for cat_id, cat_info in new_categories.items():
    new_panel += f'\n                    <div class="setting-section" data-section="{cat_id}">\n'
    new_panel += f'                        <div class="setting-title">{cat_info["title"]}</div>\n'
    new_panel += '                        <div class="setting-content">\n'
    
    for sub_title in cat_info["subs"]:
        if sub_title in all_subs:
            block = all_subs[sub_title]
            # 移除原有缩进 (28空格)，重新加上正确缩进
            dedented = '\n'.join(line[28:] if line.startswith(' ' * 28) else line for line in block.split('\n'))
            new_panel += f'                            {dedented}\n'
        else:
            print(f"  ⚠️ 缺失: {sub_title}")
            new_panel += f'                            <div class="sub-settings">\n'
            new_panel += f'                                <div class="sub-settings-title">{sub_title}</div>\n'
            new_panel += f'                                <div class="config-group"><p style="color: rgba(255,255,255,0.4); font-size: 12px;">设置项提取失败，请手动检查</p></div>\n'
            new_panel += f'                            </div>\n'
    
    new_panel += '                        </div>\n'
    new_panel += '                    </div>\n'

print(f"\n新面板长度: {len(new_panel)} 字符")

# 生成完整文件
header = ''.join(lines[:100])
new_html = header + new_panel + tail_html

backup_path = Path("C:/Users/33051/Desktop/BinixOvO_正式版2.0.0/index.html.backup_v5")
with open(backup_path, 'w', encoding='utf-8') as f:
    f.write(''.join(lines))

output_path = Path("C:/Users/33051/Desktop/BinixOvO_正式版2.0.0/index_reconstructed.html")
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(new_html)

print(f"\n✅ 输出: {output_path}")
print(f"文件大小: {len(new_html)} 字符")