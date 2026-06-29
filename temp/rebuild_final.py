#!/usr/bin/env python3
"""
精确重构设置面板 - 基于手动提取和映射
"""
from pathlib import Path
import re

# 读取原始文件
html_file = Path("C:/Users/33051/Desktop/BinixOvO_正式版2.0.0/index.html")
with open(html_file, 'r', encoding='utf-8') as f:
    original = f.read()

# 提取标记之间内容的辅助函数
def extract_between(content, start_marker, end_marker, include_markers=True):
    """提取两个标记之间的内容"""
    s = content.find(start_marker)
    if s == -1:
        return ""
    if not include_markers:
        s += len(start_marker)
    e = content.find(end_marker, s)
    if e == -1:
        return ""
    if include_markers:
        e += len(end_marker)
    return content[s:e]

def extract_until_next_sub_or_section(content, start_marker):
    """从标记开始提取直到下一个 sub-settings 或 section 结束"""
    s = content.find(start_marker)
    if s == -1:
        return ""
    
    # 找到最近的下一个 <div class="sub-settings" 或 </div>
    next_sub = content.find('<div class="sub-settings"', s + len(start_marker))
    next_sub_end = content.find('</div>\n                        </div>\n                    </div>', s + len(start_marker))
    
    candidates = []
    if next_sub != -1:
        candidates.append(next_sub)
    if next_sub_end != -1:
        candidates.append(next_sub_end)
    
    if not candidates:
        return content[s:]
    
    end = min(candidates)
    return content[s:end]

# 第一步: 提取原有的所有 sub-settings 块
# 我将使用更精确的方法 - 找到特定标记

sub_blocks = {}

# 方法: 对每个标题，找到它在原始HTML中的位置并提取完整块
titles_to_extract = [
    # appearance-theme
    "背景模式",
    "画面滤镜与形变",
    "桌面时钟",
    "鼠标跟随光斑",
    "全局物理模拟",
    # tile-desktop
    "磁贴图标源 (Favicon API)",
    "桌面行为控制",
    "磁贴样式定制",
    # fold-view-mode
    "📚 长条书签视图",
    "长条书签样式",
    # shortcuts-interact
    "基础快捷键映射",
    "搜索引擎管理与 1~9 快捷键",
    "桌面行为",
    "默认翻译引擎设置",
    # search-bar
    "功能与翻译 (Alt+Enter)",
    "外观与尺寸",
    # system-tools
    "气象与定位",
    "右下角工具台",
    "闲散功能",
    "🌙 夜间免打扰模式",
    "性能与省电",
    # content-manage
    "快速添加内容",
    "📚 批量导入与高级编辑",
    # media-sound
    "背景音乐播放器",
    "闹钟/计时器铃声库",
]

for title in titles_to_extract:
    # 在原始HTML中找到标题
    # 需要构建合适的搜索模式
    if title in original:
        # 找到包含此标题的 sub-settings 块
        # 向前搜索 <div class="sub-settings
        title_pos = original.find(title)
        if title_pos == -1:
            print(f"未找到: {title}")
            continue
        
        # 向前搜索 <div class="sub-settings
        search_start = max(0, title_pos - 5000)
        chunk = original[search_start:title_pos+len(title)]
        
        # 找到最后一个 <div class="sub-settings 的位置
        last_sub_start = chunk.rfind('<div class="sub-settings')
        if last_sub_start == -1:
            print(f"未找到sub-settings包装: {title}")
            continue
        
        block_start = search_start + last_sub_start
        
        # 现在从 block_start 开始计数div深度找到匹配的 </div>
        pos = block_start
        depth = 0
        in_tag = False
        while pos < len(original):
            if original[pos:pos+4] == '<div':
                depth += 1
                pos += 4
                continue
            elif original[pos:pos+5] == '</div':
                depth -= 1
                if depth == 0:
                    # 找到匹配的闭合
                    pos += 6
                    break
                pos += 5
                continue
            pos += 1
        
        block = original[block_start:pos]
        sub_blocks[title] = block
        print(f"✓ 提取: {title} (长度: {len(block)})")

# 第二步: 构建新的设置面板
# 注意: 有几种特殊类型:
# 1. 标准 sub-settings 块: 直接放入
# 2. 嵌套伪标题: 需要从父块中提取并独立成块
# 3. 无包装 config-group: 需要包装成 sub-settings

# 从 📚 长条书签视图 块中提取 ⏱️ 顶部组件独立尺寸
if "📚 长条书签视图" in sub_blocks:
    fold_block = sub_blocks["📚 长条书签视图"]
    # 找到 ⏱️ 顶部组件独立尺寸 的标题位置
    marker = '⏱️ 顶部组件独立尺寸 (时钟与搜索栏)'
    if marker in fold_block:
        idx = fold_block.find(marker)
        # 向前找 <div class="sub-settings-title" 或直接从此处开始
        # 提取从 divider 行到这个块结束前的内容
        divider_marker = '<div style="height: 1px; background: rgba(255,255,255,0.08); margin: 15px 0;"></div>'
        if divider_marker in fold_block:
            div_pos = fold_block.rfind(divider_marker, 0, idx)
            if div_pos != -1:
                # 提取从 divider 到 block 结束之前的内容
                # 这是顶部组件尺寸部分
                top_comp_content = fold_block[div_pos + len(divider_marker):]
                # 去掉末尾的 </div> 和其他闭合标签
                # 找到所有内容直到最后一个 </div> 之前
                # 我们需要一个干净的块
                # 包装成 sub-settings
                sub_blocks["⏱️ 顶部组件独立尺寸 (时钟与搜索栏)"] = (
                    '<div class="sub-settings">\n'
                    f'                                <div class="sub-settings-title" style="color: #6ee7b7;">{marker}</div>\n'
                    + top_comp_content
                )
                print("✓ 提取嵌套块: 顶部组件独立尺寸")

# 从 长条书签样式 块中提取 ➗ 列分割线定制
if "长条书签样式" in sub_blocks:
    style_block = sub_blocks["长条书签样式"]
    marker = '➗ 列分割线定制'
    if marker in style_block:
        idx = style_block.find(marker)
        divider_marker = '<div style="height: 1px; background: rgba(255,255,255,0.08); margin: 15px 0;"></div>'
        if divider_marker in style_block:
            div_pos = style_block.rfind(divider_marker, 0, idx)
            if div_pos != -1:
                sep_content = style_block[div_pos + len(divider_marker):]
                sub_blocks["➗ 列分割线定制"] = (
                    '<div class="sub-settings">\n'
                    f'                                <div class="sub-settings-title" style="color: #6ee7b7;">{marker}</div>\n'
                    + sep_content
                )
                print("✓ 提取嵌套块: 列分割线定制")

# 从 搜索引擎管理 块中提取 ➕ 添加自定义搜索引擎
if "搜索引擎管理与 1~9 快捷键" in sub_blocks:
    eng_block = sub_blocks["搜索引擎管理与 1~9 快捷键"]
    marker = '➕ 添加自定义搜索引擎'
    if marker in eng_block:
        idx = eng_block.find(marker)
        divider_marker = '<div style="height: 1px; background: rgba(255,255,255,0.08); margin: 15px 0;"></div>'
        if divider_marker in eng_block:
            div_pos = eng_block.rfind(divider_marker, 0, idx)
            if div_pos != -1:
                custom_eng_content = eng_block[div_pos + len(divider_marker):]
                sub_blocks["➕ 添加自定义搜索引擎"] = (
                    '<div class="sub-settings">\n'
                    f'                                <div class="sub-settings-title">{marker}</div>\n'
                    + custom_eng_content
                )
                print("✓ 提取嵌套块: 添加自定义搜索引擎")

# 第三步: 从原始HTML截断长条书签视图和长条书签样式块，移除嵌套内容
if "📚 长条书签视图" in sub_blocks:
    block = sub_blocks["📚 长条书签视图"]
    marker = '⏱️ 顶部组件独立尺寸'
    # 找到 <div style="height: 1px;... 分割线 并截断
    divider = '<div style="height: 1px; background: rgba(255,255,255,0.08); margin: 15px 0;"></div>'
    idx = block.find(marker)
    if idx != -1:
        div_pos = block.rfind(divider, 0, idx)
        if div_pos != -1:
            # 截断 - 保留分割线之前的全部内容，然后加上闭合
            truncated = block[:div_pos + len(divider)]
            # 确保有正确的闭合
            if truncated[-6:] == '</div>':
                sub_blocks["📚 长条书签视图"] = truncated
            else:
                sub_blocks["📚 长条书签视图"] = truncated
            print("✓ 截断长条书签视图块")

if "长条书签样式" in sub_blocks:
    block = sub_blocks["长条书签样式"]
    marker = '➗ 列分割线定制'
    divider = '<div style="height: 1px; background: rgba(255,255,255,0.08); margin: 15px 0;"></div>'
    idx = block.find(marker)
    if idx != -1:
        div_pos = block.rfind(divider, 0, idx)
        if div_pos != -1:
            truncated = block[:div_pos + len(divider)]
            sub_blocks["长条书签样式"] = truncated
            print("✓ 截断长条书签样式块")

if "搜索引擎管理与 1~9 快捷键" in sub_blocks:
    block = sub_blocks["搜索引擎管理与 1~9 快捷键"]
    marker = '➕ 添加自定义搜索引擎'
    divider = '<div style="height: 1px; background: rgba(255,255,255,0.08); margin: 15px 0;"></div>'
    idx = block.find(marker)
    if idx != -1:
        div_pos = block.rfind(divider, 0, idx)
        if div_pos != -1:
            truncated = block[:div_pos + len(divider)]
            sub_blocks["搜索引擎管理与 1~9 快捷键"] = truncated
            print("✓ 截断搜索引擎管理块")

# 第四步: 提取历史记录点击后行为和默认直译引擎 (作为 config-group 包装)
# 搜索原始HTML中这两个配置
for cfg_title, cfg_id in [("历史记录点击后行为", "history-action-selector"),
                           ("默认直译引擎", "quick-trans-selector")]:
    selector_pos = original.find(f'id="{cfg_id}"')
    if selector_pos != -1:
        # 向前找到最近的 <div class="config-group" 或标签开始
        search_back = max(0, selector_pos - 2000)
        chunk = original[search_back:selector_pos]
        
        # 找到最接近的 <div class="config-group" 
        last_cfg = chunk.rfind('<div class="config-group"')
        if last_cfg == -1:
            # maybe it's not in a config-group
            print(f"未找到{cfg_title}的config-group包装")
            continue
        
        block_start = search_back + last_cfg
        
        # 向前找闭合
        pos = block_start
        depth = 0
        while pos < len(original):
            if original[pos:pos+4] == '<div':
                depth += 1
                pos += 4
                continue
            elif original[pos:pos+5] == '</div':
                depth -= 1
                if depth == 0:
                    pos += 6
                    break
                pos += 5
                continue
            pos += 1
        
        block = original[block_start:pos]
        sub_blocks[cfg_title] = (
            '<div class="sub-settings">\n'
            f'                                <div class="sub-settings-title">{cfg_title}</div>\n'
            + block + '\n'
            + '                            </div>'
        )
        print(f"✓ 包装: {cfg_title}")

# 第五步: 构建新的8个分类
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
new_panel = '''                    <!-- 设置搜索框 -->
                    <div class="setting-search-wrap">
                        <input type="text" id="setting-search" class="ui-input setting-search-input" placeholder="搜索设置项...">
                    </div>\n'''

for cat_id, cat_info in new_categories.items():
    new_panel += f'\n                    <div class="setting-section" data-section="{cat_id}">\n'
    new_panel += f'                        <div class="setting-title">{cat_info["title"]}</div>\n'
    new_panel += '                        <div class="setting-content">\n'
    
    for sub_title in cat_info["subs"]:
        if sub_title in sub_blocks:
            block = sub_blocks[sub_title]
            new_panel += f'                            {block}\n'
        else:
            print(f"⚠️ 缺失: {sub_title}")
            new_panel += f'                            <div class="sub-settings">\n'
            new_panel += f'                                <div class="sub-settings-title">{sub_title}</div>\n'
            new_panel += f'                                <div class="config-group"><p style="color: rgba(255,255,255,0.4); font-size: 12px;">设置项提取失败，请手动检查</p></div>\n'
            new_panel += f'                            </div>\n'
    
    new_panel += '                        </div>\n'
    new_panel += '                    </div>\n'

# 保存新面板
with open(Path("C:/Users/33051/Desktop/BinixOvO_正式版2.0.0/temp/new_panel_v3.html"), 'w', encoding='utf-8') as f:
    f.write(new_panel)

print(f"\n新面板长度: {len(new_panel)} 字符")
print(f"已有块: {list(sub_blocks.keys())}")

# 第六步: 替换原始HTML
start_marker = '<!-- 设置搜索框 -->'
start_idx = original.find(start_marker)
if start_idx == -1:
    print("错误: 找不到开始标记")
    exit(1)

# 找到sideDrawer闭合
# 从start_idx向后找</aside>
aside_idx = original.find('</aside>', start_idx)
if aside_idx == -1:
    print("错误: 找不到</aside>")
    exit(1)

# 往前找对应的闭合标签链
pos = aside_idx
while pos > start_idx:
    # 期望: </div>\n            </div>\n        </aside>
    snippet = original[pos:pos+60]
    if snippet.startswith('</div>\n            </div>\n        </aside>'):
        end_idx = pos + len('</div>\n            </div>\n        </aside>')
        break
    pos -= 1
else:
    print("错误: 找不到结束标记")
    exit(1)

print(f"替换范围: {start_idx} -> {end_idx}")

# 备份
with open(Path("C:/Users/33051/Desktop/BinixOvO_正式版2.0.0/index.html.backup_v3"), 'w', encoding='utf-8') as f:
    f.write(original)

# 生成新文件
new_html = original[:start_idx] + new_panel + original[end_idx:]
with open(Path("C:/Users/33051/Desktop/BinixOvO_正式版2.0.0/index_rebuilt.html"), 'w', encoding='utf-8') as f:
    f.write(new_html)

print("完成！新文件: index_rebuilt.html")