#!/usr/bin/env python3
"""
创建新的设置面板，按照8个分类重新组织
"""
from pathlib import Path
import re

# 读取提取的sub-settings块
with open(Path("C:/Users/33051/Desktop/BinixOvO_正式版2.0.0/temp/all_subs.txt"), 'r', encoding='utf-8') as f:
    content = f.read()

# 解析所有块
blocks = []
current_block = []
in_block = False
current_title = ""

for line in content.split('\n'):
    if line.startswith('========= #'):
        if current_block and current_title:
            blocks.append((current_title, '\n'.join(current_block)))
        # 解析新标题
        match = re.search(r'#\d+: (.*) =========', line)
        if match:
            current_title = match.group(1).strip()
            current_block = []
            in_block = True
    elif in_block:
        current_block.append(line)

# 添加最后一个块
if current_block and current_title:
    blocks.append((current_title, '\n'.join(current_block)))

print(f"解析了 {len(blocks)} 个块:")
for i, (title, _) in enumerate(blocks):
    print(f"{i+1}. {title}")

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

# 创建标题到块的映射
title_to_block = {}
for title, block in blocks:
    title_clean = title.strip()
    title_to_block[title_clean] = block

# 创建新的设置面板HTML
new_panel = '''                    <!-- 设置搜索框 -->
                    <div class="setting-search-wrap">
                        <input type="text" id="setting-search" class="ui-input setting-search-input" placeholder="搜索设置项...">
                    </div>\n'''

# 为每个新分类创建section
for category_id, category_info in new_categories.items():
    new_panel += f'\n                    <div class="setting-section" data-section="{category_id}">\n'
    new_panel += f'                        <div class="setting-title">{category_info["title"]}</div>\n'
    new_panel += '                        <div class="setting-content">\n'
    
    # 添加对应的sub-settings
    for sub_title in category_info["subsections"]:
        # 尝试精确匹配
        if sub_title in title_to_block:
            new_panel += f'                            {title_to_block[sub_title]}\n'
        else:
            # 尝试模糊匹配
            found = False
            for key in title_to_block.keys():
                if sub_title in key or key in sub_title:
                    new_panel += f'                            {title_to_block[key]}\n'
                    found = True
                    print(f"模糊匹配: {sub_title} -> {key}")
                    break
            
            if not found:
                print(f"警告: 未找到子设置: {sub_title}")
                # 添加一个占位符
                new_panel += f'                            <div class="sub-settings">\n'
                new_panel += f'                                <div class="sub-settings-title">{sub_title}</div>\n'
                new_panel += f'                                <div class="config-group">\n'
                new_panel += f'                                    <p style="color: rgba(255,255,255,0.5); font-size: 12px;">设置项将在重构后添加</p>\n'
                new_panel += f'                                </div>\n'
                new_panel += f'                            </div>\n'
    
    new_panel += '                        </div>\n'
    new_panel += '                    </div>\n'

# 保存新面板
with open(Path("C:/Users/33051/Desktop/BinixOvO_正式版2.0.0/temp/new_panel_final.html"), 'w', encoding='utf-8') as f:
    f.write(new_panel)

print(f"\n新设置面板已保存到: new_panel_final.html")
print(f"长度: {len(new_panel)} 字符")

# 现在需要将新面板插入到原始HTML中
with open(Path("C:/Users/33051/Desktop/BinixOvO_正式版2.0.0/index.html"), 'r', encoding='utf-8') as f:
    original = f.read()

# 找到设置面板的开始和结束
start_marker = '<!-- 设置搜索框 -->'
end_marker = '</div>\n            </div>\n        </aside>'

start_idx = original.find(start_marker)
if start_idx == -1:
    print("错误: 找不到开始标记")
    exit(1)

# 找到结束位置
# 从开始位置查找 </aside>
aside_start = original.find('</aside>', start_idx)
if aside_start == -1:
    print("错误: 找不到 </aside>")
    exit(1)

# 找到包含所有设置section的div的闭合
# 向前查找匹配的 </div>
pos = aside_start
while pos > start_idx:
    if original[pos:pos+6] == '</div>':
        # 检查前面是否有足够的空格和换行
        # 我们期望的是: </div>\n            </div>\n        </aside>
        if original[pos:pos+50].startswith('</div>\n            </div>\n        </aside>'):
            end_idx = pos + len('</div>\n            </div>\n        </aside>')
            break
    pos -= 1
else:
    print("错误: 找不到结束标记")
    exit(1)

print(f"找到替换范围: {start_idx} 到 {end_idx}")

# 创建新文件
new_html = original[:start_idx] + new_panel + original[end_idx:]

# 保存备份
with open(Path("C:/Users/33051/Desktop/BinixOvO_正式版2.0.0/index.html.backup2"), 'w', encoding='utf-8') as f:
    f.write(original)

# 保存新文件
with open(Path("C:/Users/33051\Desktop\BinixOvO_正式版2.0.0/index_new2.html"), 'w', encoding='utf-8') as f:
    f.write(new_html)

print(f"原始文件备份到: index.html.backup2")
print(f"新HTML文件保存到: index_new2.html")