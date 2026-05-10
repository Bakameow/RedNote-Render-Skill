# RedNote-Render-Skill

将 Markdown 渲染为小红书风格图片卡片，支持 9 种视觉主题和自动分页。

## 安装

### Claude Code Plugin（推荐）

```bash
# 添加 marketplace
/plugin marketplace add Bakameow/RedNote-Render-Skill

# 安装插件
/plugin install rednote-render-skill@Bakameow-RedNote-Render-Skill
```

安装后运行 `/reload-plugins` 即可使用。

### 手动安装

```bash
git clone https://github.com/Bakameow/RedNote-Render-Skill.git
cd RedNote-Render-Skill
pip install -r requirements.txt
playwright install chromium
```

---

## 特性

- **9 套视觉主题**：default、playful-geometric、neo-brutalism、botanical、professional、retro、terminal、sketch、minimalist
- **自动分页**：根据内容渲染高度自动拆分，无需手动分隔
- **Playwright 渲染**：高质量 HTML → PNG 输出

---

## 使用方法

```bash
python scripts/rednote_render.py <markdown_file> [options]
```

```bash
# 默认（sketch 主题）
python scripts/rednote_render.py content.md

# 切换主题
python scripts/rednote_render.py content.md -t neo-brutalism

# 自定义尺寸和输出目录
python scripts/rednote_render.py content.md -t retro -o ./output
```

生成结果：`cover.png`（封面）+ `card_1.png`、`card_2.png`...（正文卡片）

**参数说明**：

| 参数 | 简写 | 说明 | 默认值 |
|---|---|---|---|
| `--output-dir` | `-o` | 输出目录 | 当前目录 |
| `--theme` | `-t` | 排版主题 | `sketch` |
| `--width` | `-w` | 图片宽度（px） | `1080` |
| `--height` | | 图片高度（px） | `1440` |
| `--dpr` | | 设备像素比 | `2` |

---

## 项目结构

```
RedNote-Render-Skill/
├── SKILL.md                    # 技能定义
├── README.md
├── requirements.txt            # Python 依赖
├── references/
│   └── params.md               # 完整参数参考
├── assets/
│   ├── cover.html              # 封面 HTML 模板
│   ├── card.html               # 卡片 HTML 模板
│   ├── styles.css              # 公共容器样式
│   ├── example.md              # 示例 Markdown
│   └── themes/                 # 各主题 CSS 文件
│       ├── default.css
│       ├── playful-geometric.css
│       ├── neo-brutalism.css
│       ├── botanical.css
│       ├── professional.css
│       ├── retro.css
│       ├── terminal.css
│       ├── sketch.css
│       └── minimalist.css
├── skills/
│   └── rednote-render-skill/
│       └── SKILL.md → ../../SKILL.md
└── scripts/
    └── rednote_render.py       # 渲染脚本
```

---

## 注意事项

- 默认输出 1080×1440px（小红书推荐 3:4 比例）
- 图片可反复渲染覆盖

---

## License

MIT License © 2026 Bakameow

Original work by ZhangJia (comeonzhj).
