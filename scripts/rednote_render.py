#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
小红书卡片渲染脚本
将 Markdown 文件渲染为小红书风格的图片卡片，自动根据内容高度分页。

使用方法:
    python rednote_render.py <markdown_file> [options]

选项:
    --output-dir, -o     输出目录（默认为当前工作目录）
    --theme, -t          排版主题（默认: sketch）
    --width, -w          图片宽度（默认 1080）
    --height, -h         图片高度（默认 1440）
    --dpr                设备像素比（默认 2）

可用主题:
    default, playful-geometric, neo-brutalism, botanical,
    professional, retro, terminal, sketch

依赖安装:
    pip install markdown pyyaml playwright
    playwright install chromium
"""

import argparse
import asyncio
import os
import re
import sys
import tempfile
from pathlib import Path

try:
    import markdown
    import yaml
    from playwright.async_api import async_playwright
except ImportError as e:
    print(f"缺少依赖: {e}")
    print("请运行: pip install markdown pyyaml playwright && playwright install chromium")
    sys.exit(1)


# ============================================================
# 路径常量
# ============================================================

SCRIPT_DIR = Path(__file__).parent.parent          # skills/auto-redbook-skills/
ASSETS_DIR = SCRIPT_DIR / "assets"
THEMES_DIR = ASSETS_DIR / "themes"

# ============================================================
# 渲染参数
# ============================================================

DEFAULT_WIDTH = 1080
DEFAULT_HEIGHT = 1440

# 可用主题
AVAILABLE_THEMES = [
    'default',
    'playful-geometric',
    'neo-brutalism',
    'botanical',
    'professional',
    'retro',
    'terminal',
    'sketch',
    'minimalist',
]

# ============================================================
# 主题配色（按主题统一管理，消除原版中 cover/card 两处字典的重复）
# ============================================================

# 封面背景渐变（纵向，180deg）
COVER_BACKGROUNDS = {
    'default':             'linear-gradient(180deg, #f3f4f8 0%, #fdfdfc 100%)',
    'playful-geometric':   'linear-gradient(180deg, #8B5CF6 0%, #F472B6 100%)',
    'neo-brutalism':       'linear-gradient(180deg, #FF4757 0%, #FECA57 100%)',
    'botanical':           'linear-gradient(180deg, #8a9e8b 0%, #c4cfc0 100%)',
    'professional':        'linear-gradient(180deg, #dce3ed 0%, #fcfbf8 100%)',
    'retro':               'linear-gradient(180deg, #c49568 0%, #f0e0cc 100%)',
    'terminal':            'linear-gradient(180deg, #0d1117 0%, #161b22 100%)',
    'sketch':              'linear-gradient(180deg, #e0d8c8 0%, #f9f5ed 100%)',
    'minimalist':          'linear-gradient(180deg, #e8e8e5 0%, #fafaf8 100%)',
}

# 正文卡片背景渐变（斜向，135deg）
CARD_BACKGROUNDS = {
    'default':             'linear-gradient(135deg, #f3f4f8 0%, #fafaf9 100%)',
    'playful-geometric':   'linear-gradient(135deg, #8B5CF6 0%, #F472B6 100%)',
    'neo-brutalism':       'linear-gradient(135deg, #FF4757 0%, #FECA57 100%)',
    'botanical':           'linear-gradient(135deg, #a3b5a4 0%, #dce1d6 100%)',
    'professional':        'linear-gradient(135deg, #e0e6f0 0%, #f8f7f5 100%)',
    'retro':               'linear-gradient(135deg, #d4a878 0%, #f2e8d8 100%)',
    'terminal':            'linear-gradient(135deg, #0d1117 0%, #11151c 100%)',
    'sketch':              'linear-gradient(135deg, #e5ddd0 0%, #f7f2e8 100%)',
    'minimalist':          'linear-gradient(135deg, #e8e8e5 0%, #f5f5f2 100%)',
}

# 封面标题文字渐变
TITLE_GRADIENTS = {
    'default':             'linear-gradient(180deg, #1a1d22 0%, #3d4147 100%)',
    'playful-geometric':   'linear-gradient(180deg, #7C3AED 0%, #F472B6 100%)',
    'neo-brutalism':       'linear-gradient(180deg, #000000 0%, #FF4757 100%)',
    'botanical':           'linear-gradient(180deg, #3a4d3b 0%, #6b8b6c 100%)',
    'professional':        'linear-gradient(180deg, #141a24 0%, #1e4b8c 100%)',
    'retro':               'linear-gradient(180deg, #4a2810 0%, #b85c28 100%)',
    'terminal':            'linear-gradient(180deg, #3fb950 0%, #58a6ff 100%)',
    'sketch':              'linear-gradient(180deg, #3b3a38 0%, #787671 100%)',
    'minimalist':          'linear-gradient(180deg, #0a0a0a 0%, #2e2e2e 100%)',
}


# ============================================================
# Markdown 解析
# ============================================================

def parse_markdown_file(file_path: str) -> dict:
    """读取 .md 文件，返回 {'metadata': {...}, 'body': '...'}"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 匹配 YAML front matter（--- 包裹的元数据块）
    yaml_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)

    if yaml_match:
        try:
            metadata = yaml.safe_load(yaml_match.group(1)) or {}
        except yaml.YAMLError:
            metadata = {}
        body = content[yaml_match.end():]
    else:
        metadata = {}
        body = content

    return {'metadata': metadata, 'body': body.strip()}


# ============================================================
# Markdown → HTML 转换
# ============================================================

def convert_markdown_to_html(md_content: str) -> str:
    """将 Markdown 正文转为 HTML，自动识别文末 #tag 并渲染为标签"""
    # 提取文末的 #标签 行（例如 "#Python #AI #教程"）
    tags_match = re.search(
        r'((?:#[\w一-龥]+\s*)+)$',
        md_content,
        re.MULTILINE,
    )
    tags_html = ""

    if tags_match:
        tags_str = tags_match.group(1)
        md_content = md_content[:tags_match.start()].strip()
        tags = re.findall(r'#([\w一-龥]+)', tags_str)
        if tags:
            parts = ['<div class="tags-container">']
            for tag in tags:
                parts.append(f'<span class="tag">#{tag}</span>')
            parts.append('</div>')
            tags_html = ''.join(parts)

    html = markdown.markdown(
        md_content,
        extensions=['extra', 'codehilite', 'tables', 'nl2br'],
    )
    return html + tags_html


# ============================================================
# 主题 CSS 加载
# ============================================================

def load_theme_css(theme: str) -> str:
    """从 assets/themes/{theme}.css 读取主题样式，fallback 到 default.css"""
    theme_file = THEMES_DIR / f"{theme}.css"
    if theme_file.exists():
        with open(theme_file, 'r', encoding='utf-8') as f:
            return f.read()

    default_file = THEMES_DIR / "default.css"
    if default_file.exists():
        with open(default_file, 'r', encoding='utf-8') as f:
            return f.read()
    return ""


# ============================================================
# HTML 生成
# ============================================================

def generate_cover_html(metadata: dict, theme: str, width: int, height: int) -> str:
    """生成封面页 HTML——标题使用固定字号，超长时自动换行而非缩小"""
    emoji = metadata.get('emoji', '📝')
    title = metadata.get('title', '标题')
    subtitle = metadata.get('subtitle', '')

    # 固定标题字号，让长标题自然换行
    title_size = int(width * 0.095)

    bg = COVER_BACKGROUNDS.get(theme, COVER_BACKGROUNDS['default'])
    title_gradient = TITLE_GRADIENTS.get(theme, TITLE_GRADIENTS['default'])

    # 所有尺寸按比例计算，保证不同 width/height 下版面一致
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width={width}, height={height}">
    <title>小红书封面</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700;900&display=swap');

        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: 'Noto Sans SC', 'Source Han Sans CN', 'PingFang SC', 'Microsoft YaHei', sans-serif;
            width: {width}px;
            height: {height}px;
            overflow: hidden;
        }}

        .cover-container {{
            width: {width}px;
            height: {height}px;
            background: {bg};
            position: relative;
            overflow: hidden;
        }}

        .cover-inner {{
            position: absolute;
            width: {int(width * 0.88)}px;
            height: {int(height * 0.91)}px;
            left: {int(width * 0.06)}px;
            top: {int(height * 0.045)}px;
            background: #F3F3F3;
            border-radius: 25px;
            display: flex;
            flex-direction: column;
            padding: {int(width * 0.074)}px {int(width * 0.079)}px;
            overflow: hidden;
        }}

        .cover-emoji {{
            font-size: {int(width * 0.167)}px;
            line-height: 1.2;
            margin-bottom: {int(height * 0.035)}px;
            flex-shrink: 0;
        }}

        .cover-title {{
            font-weight: 900;
            font-size: {title_size}px;
            line-height: 1.35;
            background: {title_gradient};
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            flex: 1 1 auto;
            min-height: 0;
            overflow: hidden;
            overflow-wrap: break-word;
            word-break: normal;
        }}

        .cover-subtitle {{
            font-weight: 350;
            font-size: {int(width * 0.067)}px;
            line-height: 1.4;
            color: #000000;
            margin-top: auto;
            flex-shrink: 0;
        }}
    </style>
</head>
<body>
    <div class="cover-container">
        <div class="cover-inner">
            <div class="cover-emoji">{emoji}</div>
            <div class="cover-title">{title}</div>
            <div class="cover-subtitle">{subtitle}</div>
        </div>
    </div>
</body>
</html>'''


def generate_card_html(content: str, theme: str, page_number: int,
                       total_pages: int, width: int, height: int) -> str:
    """生成正文卡片 HTML"""
    html_body = convert_markdown_to_html(content)
    theme_css = load_theme_css(theme)
    bg = CARD_BACKGROUNDS.get(theme, CARD_BACKGROUNDS['default'])
    page_text = f"{page_number}/{total_pages}" if total_pages > 1 else ""

    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width={width}">
    <title>小红书卡片</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700;900&display=swap');

        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: 'Noto Sans SC', 'Source Han Sans CN', 'PingFang SC', 'Microsoft YaHei', sans-serif;
            width: {width}px;
            background: transparent;
        }}

        .card-container {{
            width: {width}px;
            min-height: {height}px;
            background: {bg};
            position: relative;
            padding: 50px;
        }}

        .card-inner {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            padding: 60px;
            min-height: calc({height}px - 100px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(10px);
        }}

        .card-content {{
            line-height: 1.7;
        }}

        .card-content :not(pre) > code {{
            overflow-wrap: anywhere;
            word-break: break-word;
        }}

        {theme_css}

        /* 覆盖 Tailwind preflight：ol 需要恢复数字标记（主题只用 ::marker 着色） */
        .card-content ol {{ list-style: decimal; }}

        .page-number {{
            position: absolute;
            bottom: 80px;
            right: 80px;
            font-size: 36px;
            color: rgba(255, 255, 255, 0.8);
            font-weight: 500;
        }}
    </style>
</head>
<body>
    <div class="card-container">
        <div class="card-inner">
            <div class="card-content">{html_body}</div>
        </div>
        <div class="page-number">{page_text}</div>
    </div>
</body>
</html>'''


# ============================================================
# 渲染引擎
# ============================================================

async def _wait_for_tailwind(page):
    """等待 Tailwind CDN 脚本加载完毕并完成 DOM 扫描/样式注入"""
    await page.wait_for_load_state('networkidle')
    try:
        await page.wait_for_function(
            '() => window.tailwind !== undefined', timeout=5000,
        )
    except Exception:
        pass  # Tailwind CDN 可能因网络原因加载失败，不阻塞渲染
    await page.wait_for_timeout(300)  # 等 Tailwind 扫描完 DOM 注入样式


async def render_html_to_png(html: str, output_path: str,
                             width: int, height: int, dpr: int) -> int:
    """将 HTML 渲染为 PNG 图片，返回实际图片高度"""
    async with async_playwright() as p:
        browser = await p.chromium.launch()

        # 视口高度给足够余量（3 倍卡片高度），内容超出时 scrollHeight 仍然准确
        page = await browser.new_page(
            viewport={'width': width, 'height': height * 3},
            device_scale_factor=dpr,
        )

        # 写入临时文件后通过 file:// 加载，比 set_content 更稳定
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.html', delete=False, encoding='utf-8'
        ) as f:
            f.write(html)
            temp_path = f.name

        try:
            await page.goto(f'file://{temp_path}')
            await _wait_for_tailwind(page)
            await page.wait_for_timeout(500)  # 等 Google Fonts 加载完成

            # 测量 .card-container 的实际渲染高度
            content_height = await page.evaluate('''() => {
                const container = document.querySelector('.card-container');
                return container ? container.scrollHeight : document.body.scrollHeight;
            }''')

            # 实际输出高度不低于设定的最小高度
            actual_height = max(height, content_height)

            await page.screenshot(
                path=output_path,
                clip={'x': 0, 'y': 0, 'width': width, 'height': actual_height},
                type='png',
            )

            print(f"  ✅ 已生成: {output_path} ({width}x{actual_height})")
            return actual_height

        finally:
            os.unlink(temp_path)
            await browser.close()


# ============================================================
# 自动分页
# ============================================================

async def measure_card_height(page, md_content: str, theme: str,
                              width: int, height: int) -> float:
    """生成临时卡片 HTML 并测量 .card-content 的实际渲染高度"""
    html = generate_card_html(md_content, theme, 1, 1, width, height)

    with tempfile.NamedTemporaryFile(
        mode='w', suffix='.html', delete=False, encoding='utf-8'
    ) as f:
        f.write(html)
        temp_path = f.name

    await page.goto(f'file://{temp_path}')
    await _wait_for_tailwind(page)

    measured = await page.evaluate('''() => {
        const content = document.querySelector('.card-content');
        return content ? content.scrollHeight : 0;
    }''')

    os.unlink(temp_path)
    return measured


def _split_body_to_sentences(text: str) -> list:
    """将纯正文按中文标点切分为句子，过短的句子合并到前一句"""
    sentences = re.split(r'(?<=[。！？；\n])', text)
    result = []
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        # 短句（< 15 字符）合并到前一句，避免零碎卡片
        if result and len(result[-1]) < 15:
            result[-1] += s
        else:
            result.append(s)
    return result


def _split_para_to_sentences(para: str) -> list:
    """将段落按句子切分。如果以 markdown 标题开头，标题独立不拆分"""
    heading_match = re.match(r'^(#{1,6}\s[^\n]*)(\n|$)', para)
    if heading_match:
        heading = heading_match.group(1)
        rest = para[heading_match.end():].strip()
        if rest:
            return [heading] + _split_body_to_sentences(rest)
        return [heading]
    return _split_body_to_sentences(para)


def _is_heading(text: str) -> bool:
    """判断文本块是否为 markdown 标题行（以 # 开头）"""
    return bool(re.match(r'^#{1,6}\s', text.strip()))


def _join_sentences(sentences: list) -> str:
    """拼接句子列表，标题后自动补换行，避免标题吞掉正文"""
    parts = []
    for s in sentences:
        parts.append(s)
        if _is_heading(s):
            parts.append('\n')
    return ''.join(parts)


async def _fit_sentences(page, sentences: list, base_md: str,
                         available_height: int, theme: str,
                         width: int, height: int) -> tuple:
    """
    在 base_md 基础上，逐句追加 sentences，返回 (可塞入的句子, 剩余句子)。
    不会让标题单独留在卡片末尾（heading orphan 保护）。
    """
    fit_count = 0
    for _ in sentences:
        extra = _join_sentences(sentences[:fit_count + 1])
        test_md = base_md + '\n\n' + extra if base_md else extra
        test_h = await measure_card_height(page, test_md, theme, width, height)
        if test_h > available_height:
            break
        fit_count += 1

    # 末尾不留下孤立的标题 —— 把它推到下一张卡片
    while fit_count > 0 and _is_heading(sentences[fit_count - 1]):
        fit_count -= 1

    return sentences[:fit_count], sentences[fit_count:]


async def auto_split_body(body: str, theme: str, width: int, height: int,
                          dpr: int) -> list:
    """
    按段落累加分页。段落超出时先按句子切分尽量塞入，剩余句子作为新段落回填。
    保证标题不会孤零零地挂在卡片底部。

    可用空间 = 卡片高度 - 220px
    """
    paragraphs = re.split(r'\n\n+', body)
    available_height = height - 220
    cards = []
    current_paras = []

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(
            viewport={'width': width, 'height': height * 2},
            device_scale_factor=dpr,
        )

        try:
            idx = 0
            while idx < len(paragraphs):
                para = paragraphs[idx]

                # 尝试整段加入
                candidate_md = '\n\n'.join(current_paras + [para])
                h = await measure_card_height(page, candidate_md, theme, width, height)

                if h <= available_height:
                    current_paras.append(para)
                else:
                    # 超出 → 拆句
                    sentences = _split_para_to_sentences(para)
                    base = '\n\n'.join(current_paras)
                    fitted, remaining = await _fit_sentences(
                        page, sentences, base, available_height, theme, width, height,
                    )

                    if fitted:
                        current_paras.append(_join_sentences(fitted))

                    # 检查整张卡片末尾是否挂着标题
                    while current_paras and _is_heading(current_paras[-1]):
                        orphan = current_paras.pop()
                        remaining.insert(0, orphan)

                    if current_paras:
                        cards.append('\n\n'.join(current_paras))

                    # 剩余句子回填到段落队列
                    current_paras = []
                    if remaining:
                        paragraphs.insert(idx + 1, _join_sentences(remaining))

                idx += 1

            if current_paras:
                cards.append('\n\n'.join(current_paras))

        finally:
            await browser.close()

    return cards


# ============================================================
# 主编排函数
# ============================================================

async def render_markdown_to_cards(
    md_file: str,
    output_dir: str,
    theme: str = 'sketch',
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
    dpr: int = 2,
) -> int:
    """主入口：Markdown 文件 → 封面 + N 张正文卡片 PNG"""
    print(f"\n🎨 开始渲染: {md_file}")
    print(f"  📐 主题: {theme}")
    print(f"  📐 尺寸: {width}x{height}")

    os.makedirs(output_dir, exist_ok=True)

    # 1. 解析文件
    data = parse_markdown_file(md_file)
    metadata = data['metadata']
    body = data['body']

    # 2. 自动分页
    print("  ⏳ 分析内容并自动分页...")
    card_contents = await auto_split_body(body, theme, width, height, dpr)
    total_cards = len(card_contents)
    print(f"  📄 共 {total_cards} 张正文卡片")

    # 3. 渲染封面
    if metadata.get('emoji') or metadata.get('title'):
        print("  📷 生成封面...")
        cover_html = generate_cover_html(metadata, theme, width, height)
        cover_path = os.path.join(output_dir, 'cover.png')
        await render_html_to_png(cover_html, cover_path, width, height, dpr)

    # 4. 逐张渲染正文卡片
    for i, content in enumerate(card_contents, 1):
        print(f"  📷 生成卡片 {i}/{total_cards}...")
        card_html = generate_card_html(content, theme, i, total_cards,
                                       width, height)
        card_path = os.path.join(output_dir, f'card_{i}.png')
        await render_html_to_png(card_html, card_path, width, height, dpr)

    print(f"\n✨ 渲染完成！图片已保存到: {output_dir}")
    return total_cards


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description='将 Markdown 文件渲染为小红书风格的图片卡片（自动分页）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f'''
可用主题:
  default             - 默认风格
  playful-geometric   - 活泼几何风格（Memphis 设计）
  neo-brutalism       - 新粗野主义风格
  botanical           - 植物园自然风格
  professional        - 专业商务风格
  retro               - 复古怀旧风格
  terminal            - 终端/命令行风格
  sketch              - 手绘素描风格（默认）
''',
    )
    parser.add_argument('markdown_file', help='Markdown 文件路径')
    parser.add_argument('--output-dir', '-o', default=os.getcwd(),
                        help='输出目录（默认为当前工作目录）')
    parser.add_argument('--theme', '-t', choices=AVAILABLE_THEMES,
                        default='sketch', help='排版主题（默认: sketch）')
    parser.add_argument('--width', '-w', type=int, default=DEFAULT_WIDTH,
                        help=f'图片宽度（默认: {DEFAULT_WIDTH}）')
    parser.add_argument('--height', type=int, default=DEFAULT_HEIGHT,
                        help=f'图片高度（默认: {DEFAULT_HEIGHT}）')
    parser.add_argument('--dpr', type=int, default=2,
                        help='设备像素比（默认: 2）')

    args = parser.parse_args()

    if not os.path.exists(args.markdown_file):
        print(f"❌ 错误: 文件不存在 - {args.markdown_file}")
        sys.exit(1)

    asyncio.run(render_markdown_to_cards(
        md_file=args.markdown_file,
        output_dir=args.output_dir,
        theme=args.theme,
        width=args.width,
        height=args.height,
        dpr=args.dpr,
    ))


if __name__ == '__main__':
    main()
