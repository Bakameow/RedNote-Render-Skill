---
name: rednote-render-skill
description: This skill renders Markdown documents into Xiaohongshu (RedNote) style image cards with 9 curated visual themes. Use this skill when the user asks to create RedNote/Xiaohongshu card images, generate social-media image cards from text, convert Markdown to styled card images, or produce content cards for posting on Xiaohongshu. Supports automatic content-aware pagination based on rendered height.
---

# RedNote Render Skill

将 Markdown 内容渲染为小红书风格的精美图片卡片，自动根据内容高度分页。

> 详细参数文档见 `references/params.md`

---

## 工作流程

### 第一步：撰写笔记内容

根据用户需求和资料，创作小红书风格的内容：

**标题**：不超过 20 字，吸引眼球，可用数字/疑问句/感叹号增强吸引力。

**正文**：段落清晰，点缀少量 Emoji（每段 1-2 个），短句短段，结尾附 5-10 个 SEO 标签。

---

### 第二步：生成渲染用 Markdown 文档

**注意：此 Markdown 专为图片渲染设计，禁止直接使用上一步的笔记正文。**

文档结构：

```markdown
---
emoji: "🚀"
title: "封面大标题（≤15字）"
subtitle: "封面副标题（≤15字）"
---

# 正文内容...
```

分页说明：脚本会根据内容高度自动分页，无需手动插入分隔符。

---

### 第三步：渲染图片卡片

```bash
python scripts/rednote_render.py <markdown_file> [options]
```

**默认主题**：`sketch`（手绘素描风格）

常用示例：

```bash
# 默认（sketch 主题，1080×1440，自动分页）
python scripts/rednote_render.py content.md

# 切换主题
python scripts/rednote_render.py content.md -t neo-brutalism

# 自定义尺寸
python scripts/rednote_render.py content.md -t retro -w 1080 --height 1440

# 自定义输出目录
python scripts/rednote_render.py content.md -o ./output -t botanical
```

生成结果：`cover.png`（封面）+ `card_1.png`、`card_2.png`...（正文卡片）

**可用主题**（`-t`）：`default`、`professional`、`botanical`、`retro`、`playful-geometric`、`neo-brutalism`、`terminal`、`sketch`、`minimalist`

> 完整参数说明见 `references/params.md`

---

## 技能资源

### 脚本
- `scripts/rednote_render.py` — 渲染脚本（9 主题 + 自动分页）

### 模板与样式
- `assets/cover.html` — 封面 HTML 模板
- `assets/card.html` — 正文卡片 HTML 模板
- `assets/styles.css` — 公共容器样式
- `assets/themes/` — 各主题 CSS 文件（9 个）

### 参考文档
- `references/params.md` — 完整参数参考
