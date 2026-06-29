#!/usr/bin/env python3
"""
最终版 v6 - 正确处理嵌套伪标题
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
# 策略：找到所有 sub-settings-title，按唯一的 sub-settings wrapper 去重
# ============================================================

sub_pattern = re.compile(r'<div\s+class="sub-settings(?!-)[^"]*"[^>]*>')
title_pattern = re.compile(r'<div\s+class="sub-settings-title"[^>]*>(.*?)</div>', re.DOTALL)

all_subs = {}

for sec_name, sec_text in section_html.items():
    # 找到所有 sub-settings wrapper
    all_wrappers = list(sub_pattern.finditer(sec_text))
    
    # 找到所有 sub-settings-title
    all_titles = list(title_pattern.finditer(sec_text))
    
    # 为每个 wrapper 找到第一个 title
    wrapper_to_title = {}  # wrapper_index -> (title_text, title_match)
    title_to_wrapper = {}  # title_text -> wrapper_index
    
    for i, wrp in enumerate(all_wrappers):
        for j, ttl in enumerate(all_titles):
            if ttl.start() > wrp.start():
                wrapper_to_title[i] = (ttl.group(1).strip(), ttl)
                title_to_wrapper[ttl.group(1).strip()] = i
                break
    
    # 为每个 wrapper 提取块内容（到下一个 wrapper 或匹配的闭合标签）
    for i, wrp in enumerate(all_wrappers):
        if i not in wrapper_to_title:
            continue
            
        title_text, _ = wrapper_to_title[i]
        
        if i + 1 < len(all_wrappers):
            block_end = all_wrappers[i + 1].start()
        else:
            # 找到匹配的闭合
            pos = wrp.end()
            depth = 1
            while pos < len(sec_text):
                if sec_text[pos:pos+4] == '<div':
                    depth += 1
                elif sec_text[pos:pos+5] == '</div':
                    depth -= 1
                    if depth == 0:
                        block_end = pos + 6
                        break
                pos += 1
            else:
                block_end = len(sec_text)
        
        block = sec_text[wrp.start():block_end]
        all_subs[title_text] = block

# ============================================================
# 处理嵌套的伪标题（分割线之后的 sub-settings-title）
# ============================================================

def wrap_in_sub_settings(content, title_html):
    return (
        '<div class="sub-settings">\n'
        + title_html + '\n'
        + content + '\n'
        + '                            </div>'
    )

# 检查每个块内部是否有分割线后面跟着的 sub-settings-title
for key in list(all_subs.keys()):
    block = all_subs[key]
    
    # 找所有分割线 + sub-settings-title 模式
    divider_titles = re.findall(
        r'<div style="height: 1px;.*?</div>\s*\n\s*(<div\s+class="sub-settings-title"[^>]*>.*?</div>)',
        block, re.DOTALL
    )
    
    for title_tag in divider_titles:
        title_match = re.search(r'<div\s+class="sub-settings-title"[^>]*>(.*?)</div>', title_tag, re.DOTALL)
        if not title_match:
            continue
        child_title = title_match.group(1).strip()
        
        # 找到这个标题在block中的完整位置
        title_full_start = block.find(title_tag)
        if title_full_start == -1:
            continue
        
        # 找最近的闭合</div>在标题之前 (作为截断点)
        truncate_pos = block.rfind('</div>', 0, title_full_start)
        if truncate_pos == -1:
            continue
        
        # 截断后的后半部分 = 从截断点开始的内容
        child_content = block[truncate_pos:]
        
        # 确定标题颜色
        if '⏱️' in child_title or '➗' in child_title:
            style = ' style="color: #6ee7b7;"'
        elif '➕' in child_title:
            style = ''
        else:
            style = ''
        
        title_html_full = f'                                <div class="sub-settings-title"{style}>{child_title}</div>'
        
        new_key = child_title
        all_subs[new_key] = wrap_in_sub_settings(child_content, title_html_full)
        
        # 截断原块
        all_subs[key] = block[:truncate_pos]
        
        print(f"  分割: {child_title} from {key}")

# ============================================================
# 提取历史记录点击后行为和默认直译引擎
# 这些是 interaction section 中裸露的 config-group（不在任何 sub-settings 内）
# ============================================================
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
                    all_subs[key_name] = (
                        '<div class="sub-settings">\n'
                        f'                                <div class="sub-settings-title">{key_name}</div>\n'
                        + block + '\n'
                        + '                            </div>'
                    )
                    print(f"  + {key_name}")

# 从"桌面行为"块中移除裸露的 config-group (避免重复)
if "桌面行为" in all_subs:
    behavior_block = all_subs["桌面行为"]
    # 找到 "历史记录点击后行为" 出现的位置，从那里往前截断
    cut_pos = behavior_block.find("历史记录点击后行为")
    if cut_pos != -1:
        # 向上找，把对应的裸露结构移除
        # 裸 config-group 从这行 "<div class="config-group">" 开始
        pre_text = behavior_block[:cut_pos]
        cfg_tag_pos = pre_text.rfind('<div class="config-group"')
        if cfg_tag_pos != -1:
            all_subs["桌面行为"] = behavior_block[:cfg_tag_pos].rstrip()
            print("  ✂ 已修剪 桌面行为 (移除尾部裸露 config-group)")

# ============================================================
# Debug: 检查提取结果
# ============================================================
print(f"\n提取了 {len(all_subs)} 个sub-settings块:")
for k, v in sorted(all_subs.items()):
    marker = "⚠️" if len(v) < 200 else "  "
    print(f"  {marker} [{len(v):5d} chars] {k}")

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
            # 块已包含原始缩进，直接插入
            new_panel += block + '\n'
        else:
            print(f"  ❌ 缺失: [{cat_info['title']}] {sub_title}")
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

backup_path = Path("C:/Users/33051/Desktop/BinixOvO_正式版2.0.0/index.html.backup_v6")
with open(backup_path, 'w', encoding='utf-8') as f:
    f.write(''.join(lines))

output_path = Path("C:/Users/33051/Desktop/BinixOvO_正式版2.0.0/index_reconstructed.html")
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(new_html)

print(f"✅ 输出: {output_path}")
print(f"文件大小: {len(new_html)} 字符")
print(f"缺失数量: {sum(1 for cat in new_categories.values() for sub in cat['subs'] if sub not in all_subs)}")