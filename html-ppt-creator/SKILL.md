---
name: html-ppt-creator
description: HTML 幻灯片制作技能，生成专业级静态 HTML 演示文稿。内置 36 套主题、15 套完整 deck 模板、31 种页面布局、47 个动效，以及演讲者模式（逐字稿提词器+计时器）。最终通过 bundle.js 打包为单 HTML 文件，可拷贝发送给他人。当用户要求做 PPT、幻灯片、演讲稿、分享 slides、pitch deck、小红书图文等时触发。
triggerKeywords: [PPT, 幻灯片, 演示文稿, 演讲稿, slides, 做PPT, 制作幻灯片, 分享稿, pitch deck, 小红书图文, presentation, deck, keynote, 技术分享, 产品发布]
version: 1.0.0
---

# HTML PPT Creator - HTML 幻灯片制作技能

## 1. 技能概述

**技能名称**：HTML PPT Creator
**技能描述**：生成专业级静态 HTML 演示文稿，内置丰富的主题、布局、动效和演讲者模式，最终打包为可移植的单 HTML 文件。
**角色定位**：你是 HTML 幻灯片制作专家。你的职责是根据用户需求，利用本技能的设计系统和模板库，生成结构清晰、内容丰富、视觉美观的 HTML 演示文稿，并打包为单文件交付。
**适用场景**：
- 工作汇报、项目提案、技术分享
- 产品介绍、投资人路演（pitch deck）
- 培训材料、会议演示
- 小红书图文（9 页 3:4 竖版）
- 带逐字稿的演讲/分享（演讲者模式）

**技术特点**：
- 纯静态 HTML/CSS/JS，零构建、零外部框架依赖
- 单 HTML 文件交付（bundle.js 内联所有 CSS/JS），可拷贝发送
- 36 套主题一键切换，31 种布局覆盖常见场景
- 演讲者模式：S 键弹出独立窗口，含当前页/下页预览 + 逐字稿 + 计时器
- 支持 PNG 截图和 PDF 导出（通过 Chrome/Edge 无头浏览器，优先 Chrome）

## 2. 能力边界

本技能使用以下 UseIO 工具：

| 工具 | 用途 |
|------|------|
| `load_skill` | 加载本技能，获取技能目录路径 `{skillDir}` |
| `read_skill_file` | 按需读取 docs/ 下的参考文档（主题/布局/动画目录等） |
| `read_file` | 读取 starter.html 模板和 page-layouts/ 布局文件 |
| `write_file` | 将生成的 deck HTML 写入用户工作空间 |
| `run_command` | 执行 bundle.js 打包单文件；执行 render.js 生成 PNG/PDF |
| `open_target` | 在浏览器中打开 deck 预览（系统默认浏览器） |
| `capture_screen` | 截屏验证页面渲染效果（检查白屏/报错） |

**禁止事项**：
- ❌ 不使用 puppeteer、playwright 等重依赖库
- ❌ 不假设系统安装了 ffmpeg、imagemagick 等工具
- ❌ 不使用 reveal.js 等外部演示框架
- ❌ 不在用户工作空间残留中间文件

## 3. 资源清单

```
{skillDir}/
├── SKILL.md                          # 本文件
├── design-system/                    # 设计系统
│   ├── tokens.css                    # 设计 token（颜色/圆角/阴影/字体变量）
│   ├── typography.css                # Web 字体导入（Noto Sans/Serif SC）
│   ├── deck-runtime.js               # 键盘运行时（翻页/主题/演讲者/概览）
│   ├── themes/                       # 36 套主题（每个 .css 覆盖 token 变量）
│   └── motion/                       # 动效系统
│       ├── animations.css            # 27 个 CSS 入场动画
│       ├── fx-runtime.js             # Canvas FX 自动初始化
│       └── fx/                       # 20 个 Canvas FX 模块（粒子/烟花/知识图谱等）
├── deck-templates/                   # 模板库
│   ├── starter.html                  # 最小起始模板（6 页 demo）
│   ├── showcases/                    # 4 个 showcase（主题/布局/动画/全 deck 浏览）
│   ├── full-decks/                   # 15 套完整 deck 模板（scoped CSS，互不污染）
│   └── page-layouts/                 # 31 种单页布局（带 demo 数据）
├── scripts/                          # 脚本
│   ├── bundle.js                     # 单文件打包脚本（将 CSS/JS 内联到单 HTML）
│   └── render.js                     # 跨平台 PNG/PDF 渲染命令生成
└── docs/                             # 中文参考文档（按需加载）
    ├── themes.md                     # 36 套主题目录 + 使用场景
    ├── layouts.md                    # 31 种布局目录 + 选择指南
    ├── animations.md                 # 47 个动画目录 + 使用建议
    ├── full-decks.md                 # 15 套完整 deck 模板说明
    ├── presenter-mode.md             # 演讲者模式 + 逐字稿编写指南
    └── authoring-guide.md            # 完整编写工作流
```

### 主题推荐表

| 场景 | 推荐主题 |
|------|----------|
| 商务/投资人路演 | `pitch-deck-vc`、`corporate-clean`、`swiss-grid` |
| 技术分享/工程 | `tokyo-night`、`dracula`、`catppuccin-mocha`、`terminal-green`、`blueprint` |
| 小红书图文 | `xiaohongshu-white`、`soft-pastel`、`rainbow-gradient`、`magazine-bold` |
| 学术/报告 | `academic-paper`、`editorial-serif`、`minimal-white` |
| 潮流/赛博/发布 | `cyberpunk-neon`、`vaporwave`、`y2k-chrome`、`neo-brutalism` |
| 生活方式/慢生活 | `japanese-minimal`、`sunset-warm`、`midcentury` |

### 布局选择指南

| 内容类型 | 推荐布局 |
|----------|----------|
| 开场 | `cover` -> `toc` |
| 章节过渡 | `section-divider` |
| 要点列表 | `bullets`、`two-column`、`three-column` |
| 展示数字 | `stat-highlight`（单个）、`kpi-grid`（4 个） |
| 展示图表 | `chart-bar`、`chart-line`、`chart-pie`、`chart-radar` |
| 对比/差异 | `comparison`、`diff`、`pros-cons` |
| 计划/规划 | `timeline`、`roadmap`、`gantt`、`process-steps` |
| 架构图 | `arch-diagram`、`flow-diagram`、`mindmap` |
| 代码/终端 | `code`、`terminal` |
| 结尾 | `cta` -> `thanks` |

## 4. 输入规范

用户需提供（或由 Agent 引导确认）：

1. **内容与观众**：主题是什么？多少页？观众是谁（工程师/高管/小红书读者/学生/VC）？
2. **风格偏好**：推荐 2-3 个主题候选（见主题推荐表）。若不确定，根据观众类型推荐。
3. **起始模板**：是否使用完整 deck 模板？还是从 starter.html 起步？
4. **演讲者模式**：是否需要逐字稿？（提到"演讲/分享/讲稿/逐字稿"时默认需要）

## 5. 执行工作流

### Step 1：需求确认

在开始编写前，必须向用户确认三件事（若用户已提供充足信息则直接推荐并确认）：

1. **内容与观众**：主题、页数、观众类型
2. **风格偏好**：推荐 2-3 个主题候选
3. **起始模板**：选择完整 deck 模板还是从零搭建

**示例开场**：
> 我可以给你做这份 HTML 幻灯片！先确认三件事：
> 1. 大致内容 / 页数 / 观众是谁？
> 2. 风格偏好？我建议从这 3 个主题里选一个：`tokyo-night`（技术分享默认好看）、`xiaohongshu-white`（小红书风）、`corporate-clean`（正式汇报）。
> 3. 要不要用我现成的 `tech-sharing` 全 deck 模板打底？

### Step 2：脚手架生成

使用 `read_file` 读取 `{skillDir}/deck-templates/starter.html`，然后用 `write_file` 写入用户工作空间：

- 文件路径：`{workspace}/{deck-name}/index.html`
- **重要**：starter.html 中的资源引用路径是相对路径（如 `../design-system/tokens.css`）。写入用户工作空间后，需要将相对路径改为技能目录的绝对路径。

**路径替换规则**（write_file 前执行）：
- `../design-system/tokens.css` -> `{skillDir}/design-system/tokens.css`
- `../design-system/typography.css` -> `{skillDir}/design-system/typography.css`
- `../design-system/deck-runtime.js` -> `{skillDir}/design-system/deck-runtime.js`
- `../design-system/motion/animations.css` -> `{skillDir}/design-system/motion/animations.css`
- `../design-system/themes/` -> `{skillDir}/design-system/themes/`
- `data-theme-base="../design-system/themes/"` -> `data-theme-base="{skillDir}/design-system/themes/"`

### Step 3：逐页编写

从 `{skillDir}/deck-templates/page-layouts/` 中选择布局，用 `read_file` 读取布局 HTML，复制 `<section class="slide">…</section>` 块到 deck 中，替换 demo 数据为真实内容。

**编写规则**：
- 每页设置 `data-title="..."` 属性（用于概览网格）
- 使用 CSS token 变量（`var(--text-1)`），不用硬编码色值
- 每页添加 `<div class="notes">…</div>` 或 `<aside class="notes">…</div>` 存放演讲者备注
- **禁止**将演讲者备注（如"这一页展示了…"）放在可见元素中，必须放在 `.notes` 内
- 动画克制使用：每页最多 1 个强调动画，其余保持平静

**按需加载参考文档**：
- 查看布局详情：`read_skill_file` 读取 `docs/layouts.md`
- 查看主题详情：`read_skill_file` 读取 `docs/themes.md`
- 查看动画详情：`read_skill_file` 读取 `docs/animations.md`
- 查看完整 deck 模板：`read_skill_file` 读取 `docs/full-decks.md`

### Step 4：浏览器预览

使用 `open_target` 在浏览器中打开 `{workspace}/{deck-name}/index.html` 预览。

**键盘操作**：`← ->` 翻页 · `T` 切换主题 · `O` 概览 · `S` 演讲者模式 · `F` 全屏
**鼠标操作**：底部居中翻页按钮（上一页/下一页/页码显示）

### Step 5：打包为单文件（核心交付步骤）

确认 deck 内容和主题满意后，使用 `bundle.js` 将所有 CSS/JS 内联打包为单 HTML 文件：

```cmd
node "{skillDir}/scripts/bundle.js" --input "{workspace}/{deck-name}/index.html" --output "{workspace}/{deck-name}/{output-name}.html" --skill-dir "{skillDir}"
```

**`run_command` 设置 `timeout: 30000`（30秒）。**

**输出文件名规则**：
- 根据用户需求自动命名，支持中文或英文
- 默认使用 deck 标题作为文件名（如 `Rust异步运行时.html`、`Q3工作汇报.html`）
- 若用户指定了文件名则使用用户指定的名称
- 文件名中的特殊字符（`/ \ : * ? " < > |`）需替换为 `-` 或移除

打包后产出的单 HTML 文件是自包含的（约 70-110KB），用户可拷贝发送给他人，双击即可在浏览器中打开播放。

**注意**：
- 单文件模式下 `T` 键主题切换功能降级（仅内联当前主题）
- Web 字体在离线时回退到系统字体，视觉影响很小
- 若 deck 使用了 Chart.js 或 highlight.js（CDN 引用），联网时正常工作，离线时不显示但不影响布局

### Step 5.5：截屏验证（建议执行）

打包完成后，**建议**截屏验证页面是否正常渲染，检查白屏或 JS 报错。

> **前提条件**：此步骤需要视觉模型支持（用于分析截图）。若用户未配置视觉模型，可跳过此步骤，改为在 Step 4 中让用户手动确认预览效果。

1. 使用 `run_command` 执行 render.js 生成首页截图：
```cmd
node "{skillDir}/scripts/render.js" --html "{workspace}/{deck-name}/{output-name}.html" --mode png --slide-count 1 --out-dir "{workspace}/{deck-name}/_verify"
```
render.js 会输出浏览器命令（优先 Chrome，其次 Edge），Agent 用 `run_command` 执行该命令生成截图。

2. 执行渲染命令后**等待 3-5 秒**（让浏览器完成页面加载和动画），然后使用 `capture_screen` 或读取截图文件进行视觉分析。

3. **验证要点**：
   - 页面是否白屏（白屏说明 JS 报错或资源加载失败）
   - 中文内容是否正常显示（无乱码）
   - 布局是否正确（标题、内容、翻页按钮可见）
   - 主题颜色是否应用

4. **如果发现白屏或异常**：
   - 检查打包后的 HTML 中是否有乱码字符
   - 检查 `bundle.js` 是否成功内联了所有资源
   - 修复后重新打包并再次截屏验证

5. 验证通过后，删除验证截图：`del "{workspace}/{deck-name}/_verify"` 或 `rm -rf "{workspace}/{deck-name}/_verify"`

### Step 6（可选）：导出 PNG/PDF

**PNG 截图**（每页一张）：
```cmd
node "{skillDir}/scripts/render.js" --html "{workspace}/{deck-name}/{output-name}.html" --mode png --slide-count N --out-dir "{workspace}/{deck-name}/png"
```
render.js 会输出浏览器命令（优先 Chrome，其次 Edge），Agent 用 `run_command` 逐条执行。

**PDF 导出**（整个 deck 一份 PDF）：
```cmd
node "{skillDir}/scripts/render.js" --html "{workspace}/{deck-name}/{output-name}.html" --mode pdf --out-dir "{workspace}/{deck-name}"
```

## 6. 输出规范

- **最终产物**：单 HTML 文件（自包含，可拷贝发送），文件名根据用户需求自动命名（支持中英文）
- **存储路径**：用户工作空间 `{workspace}/{deck-name}/{output-name}.html`
- **中间文件**：`index.html`（多文件版，开发预览用）可保留或删除
- **可选产物**：PNG 截图目录、PDF 文件
- **自动打开**：打包完成后用 `open_target` 打开最终 HTML 文件确认效果

## 7. 脚本与工具约束

| 脚本 | 用途 | 依赖 | 能力边界合规 |
|------|------|------|-------------|
| `bundle.js` | 单文件打包（CSS/JS 内联） | Node.js 白名单模块（fs/path/os） | ✅ 零第三方依赖 |
| `render.js` | PNG/PDF 渲染命令生成 | Node.js 白名单模块（fs/path/os） | ✅ 零第三方依赖，不 spawn 子进程 |

**bundle.js 工作原理**：读取输入 HTML -> 正则匹配 `<link>`/`<script src>` 标签 -> 读取资源文件 -> 替换为内联 `<style>`/`<script>` 块 -> 写入输出文件

**render.js 工作原理**：检测浏览器路径（优先 Chrome，其次 Edge，跨平台）-> 根据模式拼接命令 -> 输出命令字符串到 stdout

## 8. 异常处理

| 失败场景 | 处理策略 |
|----------|----------|
| 用户需求模糊 | 使用 `ask_followup_question` 确认内容/页数/观众/风格 |
| 主题不存在 | 检查 `design-system/themes/` 目录，推荐已有主题替代 |
| 布局不适合内容 | 参考 `docs/layouts.md` 选择更合适的布局 |
| bundle.js 打包失败 | 检查资源路径是否为绝对路径，检查文件是否存在 |
| Chrome/Edge 未检测到 | render.js 输出安装指引，提示用户安装 Chrome 或 Edge 浏览器 |
| 打包后白屏 | 执行 Step 5.5 截屏验证，检查乱码字符和资源内联是否完整 |
| CDN 资源离线不可用 | Chart.js/highlight.js 离线时不显示但不影响布局，告知用户 |
| deck 页数过多 | 建议控制在 20 页以内，过多影响观众注意力 |

## 9. 演讲者模式指南

### 何时使用

当用户提到以下任何一项时，**启用演讲者模式**：
- "演讲"、"分享"、"讲稿"、"逐字稿"、"speaker notes"
- "presenter view"、"演讲者视图"、"演讲者模式"
- "30 分钟 / 45 分钟 / 1 小时的分享"
- "不想忘词"、"怕讲不流畅"、"需要提词器"

### 如何启用

1. 使用 `presenter-mode-reveal` 全 deck 模板作为起始点（每页自带示例逐字稿）
2. 或在任意 deck 中，每页添加 `<aside class="notes">逐字稿内容</aside>`
3. 确认 HTML 引入了 `deck-runtime.js`（所有模板已默认引入）
4. 按 `S` 键弹出演讲者窗口，包含 4 个磁吸卡片：
   - 🔵 **当前页**：iframe 像素级预览
   - 🟣 **下页**：iframe 像素级预览
   - 🟠 **逐字稿**：大字体滚动显示
   - 🟢 **计时器**：已用时间 + 页码 + 翻页/重置按钮

### 逐字稿三铁律

1. **不是讲稿，是提示信号** - 关键词加粗，过渡句独立成段
2. **每页 150-300 字** - 约 2-3 分钟/页的节奏
3. **用口语，不用书面语** - "所以"不是"因此"，"这个"不是"该"

详细指南参见 `docs/presenter-mode.md`（用 `read_skill_file` 按需加载）。
