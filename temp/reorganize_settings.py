#!/usr/bin/env python3
"""
重构设置面板脚本
按照新的8个分类重组设置项
"""

import re
from pathlib import Path

# 读取原始HTML文件
html_file = Path("C:/Users/33051/Desktop/BinixOvO_正式版2.0.0/index.html")
with open(html_file, 'r', encoding='utf-8') as f:
    content = f.read()

# 找到设置面板的开始和结束位置
# 设置面板从 <!-- 设置搜索框 --> 开始，到 </div> (sideDrawer闭合) 为止
start_marker = "<!-- 设置搜索框 -->"
end_marker = "</div>\n            </div>\n        </aside>"  # sideDrawer闭合

start_idx = content.find(start_marker)
if start_idx == -1:
    print("错误：找不到设置搜索框标记")
    exit(1)

# 找到sideDrawer闭合的位置
# 我们需要找到包含所有设置section的div的闭合
# 先找到开始位置附近的<div class="side-drawer">
side_drawer_start = content.find('<div class="side-drawer">', start_idx)
if side_drawer_start == -1:
    side_drawer_start = content.find('<div class="side-drawer"', start_idx)

# 找到对应的闭合
def find_matching_close(content, start_pos):
    """找到与开始标签匹配的闭合标签位置"""
    pos = start_pos
    depth = 0
    in_quotes = False
    quote_char = None
    
    while pos < len(content):
        char = content[pos]
        
        # 处理引号内的内容
        if char in ('"', "'") and (pos == 0 or content[pos-1] != '\\'):
            if not in_quotes:
                in_quotes = True
                quote_char = char
            elif quote_char == char:
                in_quotes = False
                quote_char = None
        
        if not in_quotes:
            if content[pos:pos+4] == '<div':
                # 检查是否是自闭合标签
                next_chars = content[pos:pos+100]
                if '/>' in next_chars and next_chars.find('/>') < next_chars.find('>'):
                    # 自闭合标签，跳过
                    pos = content.find('>', pos) + 1
                    continue
                depth += 1
            elif content[pos:pos+5] == '</div':
                depth -= 1
                if depth == 0:
                    return content.find('>', pos) + 1
        
        pos += 1
    
    return -1

# 提取设置面板内容
if side_drawer_start != -1:
    side_drawer_end = find_matching_close(content, side_drawer_start)
    if side_drawer_end != -1:
        settings_content = content[side_drawer_start:side_drawer_end]
        print(f"成功提取设置面板内容，长度: {len(settings_content)} 字符")
    else:
        print("错误：找不到sideDrawer的闭合标签")
        exit(1)
else:
    # 回退方案：从开始标记到文件末尾，然后手动截断
    temp_content = content[start_idx:]
    # 找到最后一个设置section的闭合
    # 查找所有设置section
    sections = re.findall(r'<div class="setting-section"[^>]*>.*?</div>\s*</div>', temp_content, re.DOTALL)
    if sections:
        # 找到最后一个section的结束位置
        last_section = sections[-1]
        last_section_end_in_temp = temp_content.rfind(last_section) + len(last_section)
        # 向前找到包含所有section的div的闭合
        # 从最后一个section结束位置开始向前查找</div>直到找到匹配的深度
        settings_content = temp_content[:last_section_end_in_temp]
        print(f"回退方案提取设置面板内容，长度: {len(settings_content)} 字符")
    else:
        print("错误：找不到任何设置section")
        exit(1)

# 解析现有的设置section
section_pattern = r'<div class="setting-section"[^>]*data-section="([^"]*)"[^>]*>.*?<div class="setting-title">(.*?)</div>.*?<div class="setting-content">(.*?)</div>\s*</div>'
sections = re.findall(section_pattern, settings_content, re.DOTALL)

print(f"找到 {len(sections)} 个设置section:")
for i, (data_section, title, content_html) in enumerate(sections):
    print(f"{i+1}. data-section: {data_section}, 标题: {title.strip()}")

# 新的8个分类映射
new_categories = {
    "appearance-theme": {
        "title": "🎨 外观与主题",
        "subsections": [
            "背景模式",
            "画面滤镜与形变", 
            "桌面时钟",
            "鼠标跟随光斑",
            "全局物理模拟"
        ]
    },
    "tile-desktop": {
        "title": "📐 磁贴与桌面",
        "subsections": [
            "磁贴图标源 (Favicon API)",
            "桌面行为控制",
            "磁贴样式定制"
        ]
    },
    "search-bar": {
        "title": "🔍 搜索栏",
        "subsections": [
            "功能与翻译 (Alt+Enter)",
            "外观与尺寸"
        ]
    },
    "fold-view-mode": {
        "title": "🗂️ 折叠窗口模式",
        "subsections": [
            "📚 长条书签视图",
            "⏱️ 顶部组件独立尺寸 (时钟与搜索栏)",
            "长条书签样式",
            "➗ 列分割线定制"
        ]
    },
    "shortcuts-interact": {
        "title": "⌨️ 快捷键与交互",
        "subsections": [
            "基础快捷键映射",
            "搜索引擎管理与 1~9 快捷键",
            "➕ 添加自定义搜索引擎",
            "桌面行为",
            "历史记录点击后行为",
            "默认直译引擎",
            "默认翻译引擎设置"
        ]
    },
    "system-tools": {
        "title": "⚙️ 系统工具",
        "subsections": [
            "气象与定位",
            "右下角工具台",
            "闲散功能",
            "🌙 夜间免打扰模式",
            "性能与省电"
        ]
    },
    "content-manage": {
        "title": "📦 内容管理",
        "subsections": [
            "快速添加内容",
            "📚 批量导入与高级编辑"
        ]
    },
    "media-sound": {
        "title": "🎵 媒体与声音",
        "subsections": [
            "背景音乐播放器",
            "闹钟/计时器铃声库"
        ]
    }
}

# 从原始内容中提取所有sub-settings
# 首先，我们需要从每个section中提取sub-settings
all_subsections = {}

# 解析每个section的sub-settings
for data_section, title, content_html in sections:
    # 提取所有sub-settings
    sub_pattern = r'<div class="sub-settings"[^>]*>.*?<div class="sub-settings-title">(.*?)</div>(.*?)</div>\s*(?=<div class="sub-settings"|</div>\s*</div>)'
    subs = re.findall(sub_pattern, content_html, re.DOTALL)
    
    for sub_title, sub_content in subs:
        sub_title_clean = sub_title.strip()
        # 处理一些特殊情况
        if "style=" in sub_title_clean:
            # 提取实际的标题文本
            match = re.search(r'>(.*?)<', sub_title_clean)
            if match:
                sub_title_clean = match.group(1).strip()
        
        # 存储完整的sub-settings HTML
        full_html = f'<div class="sub-settings">\n<div class="sub-settings-title">{sub_title_clean}</div>\n{sub_content}\n</div>'
        all_subsections[sub_title_clean] = full_html
        print(f"提取子设置: {sub_title_clean}")

# 现在我们需要按照新的分类重新组织
# 首先创建新的设置面板HTML
new_settings_html = '''                    <!-- 设置搜索框 -->
                    <div class="setting-search-wrap">
                        <input type="text" id="setting-search" class="ui-input setting-search-input" placeholder="搜索设置项...">
                    </div>\n'''

# 为每个新分类创建section
for category_id, category_info in new_categories.items():
    new_settings_html += f'\n                    <div class="setting-section" data-section="{category_id}">\n'
    new_settings_html += f'                        <div class="setting-title">{category_info["title"]}</div>\n'
    new_settings_html += '                        <div class="setting-content">\n'
    
    # 添加对应的sub-settings
    for sub_title in category_info["subsections"]:
        if sub_title in all_subsections:
            new_settings_html += f'                            {all_subsections[sub_title]}\n'
        else:
            # 尝试模糊匹配
            found = False
            for key in all_subsections.keys():
                if sub_title in key or key in sub_title:
                    new_settings_html += f'                            {all_subsections[key]}\n'
                    found = True
                    print(f"模糊匹配: {sub_title} -> {key}")
                    break
            
            if not found:
                print(f"警告: 未找到子设置: {sub_title}")
                # 添加一个占位符
                new_settings_html += f'                            <div class="sub-settings">\n'
                new_settings_html += f'                                <div class="sub-settings-title">{sub_title}</div>\n'
                new_settings_html += f'                                <div class="config-group">\n'
                new_settings_html += f'                                    <p style="color: rgba(255,255,255,0.5); font-size: 12px;">设置项将在重构后添加</p>\n'
                new_settings_html += f'                                </div>\n'
                new_settings_html += f'                            </div>\n'
    
    new_settings_html += '                        </div>\n'
    new_settings_html += '                    </div>\n'

print("\n新设置面板HTML已生成")

# 保存新设置面板到文件
output_file = Path("C:/Users/33051/Desktop/BinixOvO_正式版2.0.0/temp/new_settings.html")
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(new_settings_html)

print(f"新设置面板已保存到: {output_file}")

# 现在需要将新设置面板插入到原始HTML中
# 首先找到原始设置面板的位置并替换
if side_drawer_start != -1 and side_drawer_end != -1:
    new_content = content[:side_drawer_start] + new_settings_html + content[side_drawer_end:]
else:
    # 使用回退方案
    new_content = content.replace(settings_content, new_settings_html)

# 保存备份
backup_file = Path("C:/Users/33051/Desktop/BinixOvO_正式版2.0.0/index.html.backup")
with open(backup_file, 'w', encoding='utf-8') as f:
    f.write(content)

# 保存新文件
new_html_file = Path("C:/Users/33051/Desktop/BinixOvO_正式版2.0.0/index_new.html")
with open(new_html_file, 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f"原始文件备份到: {backup_file}")
print(f"新HTML文件保存到: {new_html_file}")
print("\n注意: 新文件名为 index_new.html，请检查确认后重命名为 index.html")