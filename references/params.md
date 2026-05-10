# 参数参考文档

## 渲染脚本（rednote_render.py）

```bash
python scripts/rednote_render.py <markdown_file> [options]
```

### 参数列表

| 参数 | 简写 | 说明 | 默认值 |
|---|---|---|---|
| `--output-dir` | `-o` | 输出目录 | 当前工作目录 |
| `--theme` | `-t` | 排版主题 | `sketch` |
| `--width` | `-w` | 图片宽度（px） | `1080` |
| `--height` | | 图片高度（px） | `1440` |
| `--dpr` | | 设备像素比（清晰度） | `2` |

> 分页逻辑：脚本根据内容渲染高度自动分页，无需手动插入分隔符。

### 排版主题（`--theme`）

| 值 | 名称 | 说明 |
|---|---|---|
| `sketch` | 手绘素描 | 手绘风格，默认 |
| `default` | 默认简约 | 暖灰背景（`#f5f4f0`）+ 靛蓝强调 |
| `playful-geometric` | 活泼几何 | Memphis 设计风格 |
| `neo-brutalism` | 新粗野主义 | 粗框线条、强对比 |
| `botanical` | 植物园自然 | 自然绿植风格 |
| `professional` | 专业商务 | 简洁商务蓝 |
| `retro` | 复古怀旧 | 暖色复古感 |
| `terminal` | 终端命令行 | 深色代码终端风格 |
| `minimalist` | 极简现代风 | 近乎单色，极致克制排版 |

### 常用命令示例

```bash
# 默认：sketch 主题 + 自动分页
python scripts/rednote_render.py content.md

# 切换主题
python scripts/rednote_render.py content.md -t neo-brutalism

# 自定义尺寸
python scripts/rednote_render.py content.md -t retro -w 1080 --height 1440 --dpr 2

# 自定义输出目录
python scripts/rednote_render.py content.md -o ./output -t botanical
```

---

## Markdown 文档格式

### YAML 头部元数据

```yaml
---
emoji: "🚀"           # 封面装饰 Emoji
title: "大标题"        # 封面大标题（不超过 15 字）
subtitle: "副标题文案"  # 封面副标题（不超过 15 字）
---
```

### 分页说明

脚本会根据内容高度自动分页，无需手动插入 `---` 分隔符。
