---
name: ppt-creator
description: PPT 制作技能，支持创建和修改 PowerPoint 演示文稿。包含嵌入式 Python（Windows x64，约 25MB），支持企业内网环境零依赖运行。支持标题页、内容页、双栏页、表格页、图片页、章节页、图表页等多种布局。默认 16:9 宽高比，支持模板创建和修改前自动备份。
triggerKeywords: [PPT, 演示文稿, 幻灯片, PowerPoint, 做个PPT, 制作幻灯片, 汇报, 报告, 演讲稿, presentation, slides]
version: 2.0.0
---

# PPT Creator — PPT 制作技能

## 0. 硬约束（必须遵守）

> ⚠️ 本技能自带嵌入式 Python 和 python-pptx，在任何情况下都应优先使用技能自带资源。

**禁止执行以下操作**，除非已通过 `detect_env.py` 确认 `recommended_route: "NONE"`：
- `pip install` 任何包
- `npm install` 任何包
- 安装任何第三方运行时或库

**所有命令为 Windows cmd 语法**（`if exist`、`del`、`&&` 等），不要使用 PowerShell 语法。

**`run_python` 工具不适用于本技能**：它硬编码使用系统 `python`/`python3`，无法使用嵌入式 Python，且禁止 `subprocess` 模块。所有脚本必须通过 `run_command` 用绝对路径执行。

**禁止复制脚本到工作空间**：技能自带 `scripts/` 目录已有完整脚本，应通过绝对路径直接调用。

**前置检查**：若当前无用户工作空间（system prompt 中未出现「当前用户工作空间」章节），先提示用户设置工作空间后再继续。

**技能安装说明**：本技能通过 ZIP 导入安装。若 `load_skill` 失败提示技能不存在，请引导用户通过技能管理页面导入 ppt-creator 技能包。

## 1. 技能概述

**技能名称**：PPT Creator  
**技能描述**：创建和修改 PowerPoint 演示文稿（.pptx 格式），支持多种布局类型和主题自定义。  
**角色定位**：你是 PPT 制作专家。你的职责是根据用户需求，生成结构清晰、内容丰富、视觉美观的演示文稿。  
**适用场景**：
- 工作汇报、项目提案
- 产品介绍、技术分享
- 培训材料、会议演示
- 修改已有 PPT（追加/插入/替换/删除幻灯片）

**技术特点**：
- 包含嵌入式 Python（Windows x64），内网环境零依赖运行
- 支持 python-pptx（高质量）和纯标准库（兜底）两种生成路线
- 支持创建新 PPT 和修改已有 PPT
- 默认 16:9 宽高比，可选 4:3
- 支持基于模板创建 PPT
- 修改 PPT 前自动备份源文件

## 2. 环境检测（必须首先执行）

**重要**：在生成 PPT 前，必须先执行环境检测，获取环境信息和可用模板。

### 2.1 获取技能目录路径

`load_skill` 工具返回的内容中包含「技能目录」字段，即为技能目录的绝对路径（如 `C:\Users\xxx\.useio\skills\ppt-creator`）。将其记为 `{skillDir}`，后续所有命令中替换为实际值。

### 2.2 执行环境检测脚本

用单条命令执行 `detect_env.py`，优先使用嵌入式 Python 的绝对路径：

```cmd
"{skillDir}\vendor\python\python.exe" "{skillDir}\scripts\detect_env.py" --skill-dir "{skillDir}"
```

若该命令失败（嵌入式 Python 不存在或无法启动），降级为系统 Python：

```cmd
python "{skillDir}\scripts\detect_env.py" --skill-dir "{skillDir}"
```

**重要**：`run_command` 执行时设置 `timeout: 30000`（30秒）。所有命令为单条命令，不依赖跨 shell 变量传递。

### 2.3 解析检测结果

`detect_env.py` 输出 JSON，包含：
- `skill_dir`：技能目录绝对路径
- `system_python`：系统 Python 信息（含 `available`、`version`、`executable`、`is_store_stub`）
- `system_pptx_available`：系统 Python 是否有 python-pptx
- `embed_python_available`：嵌入式 Python 是否存在
- `embed_python_path`：嵌入式 Python 路径
- `embed_python_test`：嵌入式 Python 可启动性验证结果
- `embed_pptx_available`：嵌入式 Python 是否有 python-pptx
- `recommended_route`：推荐路线（A / A_NEED_PIP / B / C / NONE）
- `ppt_templates`：PPT 模板信息（含 `available`、`dir`、`templates` 数组）

## 3. 三路线选择策略

根据环境检测结果选择路线：

| 条件 | 路线 | Python 解释器 | 脚本 |
| --- | --- | --- | --- |
| 系统有真实 Python（非桩）+ python-pptx 可用 | A | `system_python.executable` | `generate_pptx.py` |
| 系统有真实 Python（非桩）+ 无 python-pptx + 有外网 | A_NEED_PIP | `system_python.executable`（先 pip install） | `generate_pptx.py` |
| 嵌入式 Python 可用 + python-pptx 可用 | B | `embed_python_path` | `generate_pptx.py` |
| 嵌入式 Python 可用 + python-pptx 不可用 | C | `embed_python_path` | `generate_stdlib.py` |

**重要说明**：
- 路线 A 优先级最高，其次是 B，最后是 C
- 路线 A_NEED_PIP 需 LLM 判断网络环境，内网无外网应直接降级 B/C
- 路线 C 不支持图表（chart）布局，修改已有 PPT 时依赖 XML 解析可能因格式差异失败
- 若完全无 Python（NONE），提示用户安装 Python 或重新导入技能包

## 3.5 模板检查与引导

环境检测后，检查 `ppt_templates.available`：

**若 `available: false`**：告知用户「检测到尚未放置 PPT 模板。如需使用模板，请在应用数据目录的 `data/ppt-templates/` 子目录下放置 .pptx 模板文件，然后重新执行环境检测。**也可以不放置模板直接继续，将使用默认空白模板制作。**」然后**立即继续正常创建流程**。

**若 `available: true`**：通过 `ask_followup_question` 列出模板询问用户选择。用户选择模板后，在 slides JSON 中设置 `template` 字段为模板绝对路径；用户选择跳过则不设置 `template` 字段。

## 4. 创建新 PPT 流程

### 4.1 构造 slides JSON

```json
{
  "title": "演示文稿标题",
  "author": "作者名",
  "theme": {
    "primaryColor": "2B579A",
    "fontFamily": "微软雅黑",
    "aspectRatio": "16:9"
  },
  "mode": "create",
  "template": "C:\\Users\\xxx\\.useio\\data\\ppt-templates\\report.pptx",
  "slides": [
    {
      "layout": "title",
      "elements": [
        {"type": "title", "text": "主标题"},
        {"type": "subtitle", "text": "副标题"}
      ]
    }
  ]
}
```

注意：`theme.aspectRatio` 可选（`16:9` 默认或 `4:3`）；`template` 可选，与 `source` 互斥。

### 4.2 写入 JSON 文件

使用 `write_file` 将 JSON 写入工作空间：`{"filePath": "slides.json", "content": "..."}`

**重要**：`write_file` 写入的目录必须与 `run_command` 的 `cwd` 一致。

### 4.3 执行生成命令

- **路线 A**：`PYTHON_EXE` = `system_python.executable`
- **路线 B/C**：`PYTHON_EXE` = `embed_python_path`

**路线 A/B（python-pptx）**：

```cmd
"{PYTHON_EXE}" "{skillDir}\scripts\generate_pptx.py" --input slides.json --output output.pptx --skill-dir "{skillDir}" --aspect-ratio 16:9
```

若使用模板，追加 `--template "模板路径"`（此时 `--aspect-ratio` 被忽略）。

**路线 C（纯标准库）**：

```cmd
"{PYTHON_EXE}" "{skillDir}\scripts\generate_stdlib.py" --input slides.json --output output.pptx --skill-dir "{skillDir}" --aspect-ratio 16:9
```

**重要**：`run_command` 设置 `timeout: 300000`（5分钟）。

### 4.4 清理中间文件

生成成功后必须清理：`del slides.json`

## 5. 修改已有 PPT 流程

### 5.1 读取已有 PPT 内容

使用 `extract_document`：`{"filePath": "existing.pptx"}`

### 5.2 获取 PPT 绝对路径

使用 `resolve_path`：`{"targetPath": "existing.pptx"}`

### 5.3 构造修改 JSON

```json
{
  "title": "演示文稿标题",
  "mode": "modify",
  "source": "C:\\Users\\xxx\\existing.pptx",
  "modify_action": "append",
  "slides": [...]
}
```

`modify_action`：`append`/`insert`/`replace`/`delete`（后三者需 `target_slide` 字段，从 1 开始）。

**注意**：修改模式不应用 `--aspect-ratio`，保留源文件宽高比。

### 5.4 执行修改命令

**修改前自动备份**：脚本自动备份源文件到 `data/ppt-backups/`，保留最近 5 个版本。

**路线 A/B**：

```cmd
"{PYTHON_EXE}" "{skillDir}\scripts\generate_pptx.py" --input slides.json --source "C:\path\to\existing.pptx" --output modified.pptx --skill-dir "{skillDir}"
```

**路线 C**：

```cmd
"{PYTHON_EXE}" "{skillDir}\scripts\generate_stdlib.py" --input slides.json --source "C:\path\to\existing.pptx" --output modified.pptx --skill-dir "{skillDir}"
```

### 5.5 清理中间文件

修改成功后必须清理：`del slides.json`

## 6. 支持的布局类型

| 布局 | 说明 | 元素 | 路线 C |
| --- | --- | --- | --- |
| `title` | 封面页 | `title`, `subtitle`, `date` | ✅ |
| `content` | 内容页 | `title`, `bullets` | ✅ |
| `two_content` | 双栏页 | `title`, `left_bullets`, `right_bullets` | ✅ |
| `table` | 表格页 | `title`, `table` | ✅ |
| `image` | 图片页 | `title`, `image`（base64 或 filePath） | ✅ |
| `section` | 章节分隔 | `title`, `subtitle` | ✅ |
| `blank` | 空白页 | 自由排版 | ✅ |
| `chart` | 图表页 | `title`, `chart` | ❌ 仅 A/B |

## 7. slides JSON 详细格式

### 7.1 顶层字段

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `title` | string | 是 | 演示文稿标题 |
| `author` | string | 否 | 作者名 |
| `theme` | object | 否 | 主题配置 |
| `mode` | string | 否 | `create`（默认）或 `modify` |
| `source` | string | 否 | 修改模式，源 PPT 绝对路径 |
| `template` | string | 否 | 创建模式，模板 PPT 绝对路径（与 source 互斥） |
| `modify_action` | string | 否 | `append`/`insert`/`replace`/`delete` |
| `target_slide` | number | 否 | 目标页码（从 1 开始） |
| `slides` | array | 是 | 幻灯片数组 |

### 7.2 theme 字段

```json
{
  "primaryColor": "2B579A",
  "fontFamily": "微软雅黑",
  "aspectRatio": "16:9"
}
```

### 7.3 幻灯片元素类型

**title**：`{"type": "title", "text": "标题文本"}`

**subtitle**：`{"type": "subtitle", "text": "副标题文本"}`

**date**：`{"type": "date", "text": "2026-07-07"}`

**bullets**：`{"type": "bullets", "items": ["要点一", "要点二"]}`

**table**：
```json
{"type": "table", "headers": ["列1", "列2"], "rows": [["数据1", "数据2"]]}
```

**image**（base64 或 filePath 二选一）：
```json
{"type": "image", "data": "base64...", "width": 800, "height": 600}
```
或
```json
{"type": "image", "filePath": "C:\\path\\to\\image.png", "width": 800, "height": 600}
```

**chart**（仅路线 A/B）：
```json
{"type": "chart", "chart_type": "bar", "title": "标题", "categories": ["类1"], "series": [{"name": "系列1", "values": [10]}]}
```

## 8. 输出规范

- PPTX 文件保存到用户工作空间根目录
- 文件名由用户指定或使用默认名 `output.pptx`
- 修改模式输出新文件，不覆盖源文件（除非用户明确要求）
- 修改模式会自动备份源文件到 `data/ppt-backups/`，保留最近 5 个版本

### 8.1 中间文件清理（必须执行）

生成完成后，**必须清理** slides.json，不得残留在用户工作空间：

```cmd
del slides.json
```

**禁止行为**：
- ❌ 禁止将 generate_pptx.py / generate_stdlib.py 的内容复制到工作空间再执行
- ❌ 禁止在用户工作空间残留任何非最终产物的文件

**正确做法**：
- ✅ slides.json 写入工作空间 → 执行生成 → 删除 slides.json
- ✅ 生成脚本始终用绝对路径调用：`"{skillDir}\scripts\generate_pptx.py"`
- ✅ 仅 output.pptx（最终产物）保留在工作空间

## 9. 异常处理

| 错误场景 | 处理策略 |
| --- | --- |
| 环境检测失败 | 用 `list_dir` 检查 `{skillDir}/vendor/python/` 是否存在 python.exe，用绝对路径直接执行 |
| 嵌入式 Python 不存在 | 降级为系统 Python 执行 `detect_env.py` |
| Python 执行失败 | 检查 stderr 错误信息，尝试路线降级（A→B→C） |
| 降级 A→B | 切换解释器为 `embed_python_path`，重新执行 generate_pptx.py |
| 降级 B→C | 切换脚本为 generate_stdlib.py，解释器不变 |
| slides JSON 格式错误 | 脚本会输出明确错误信息（退出码 1），检查 JSON 语法和必填字段 |
| vendor/libs 缺失 | 脚本输出退出码 2，提示使用路线 C（generate_stdlib.py） |
| PPTX 生成超时 | 建议减少幻灯片数量或简化内容 |
| 修改模式源文件不存在 | 提示用户检查文件路径 |
| 修改失败 | 源文件备份位于 `data/ppt-backups/`，可手动恢复 |
| python-pptx 导入失败 | 降级到路线 C（纯标准库） |

## 10. 注意事项

1. **命令语法**：所有命令为 Windows cmd 语法，不要使用 PowerShell 语法
2. **`run_python` 不适用**：禁 subprocess 且无法用嵌入式 Python，必须通过 `run_command` 执行脚本
3. **超时设置**：环境检测设 `timeout: 30000`（30秒），生成设 `timeout: 300000`（5分钟）
4. **图片处理**：支持 base64 编码或文件路径（`filePath`），大图片会增加生成时间
5. **中文支持**：默认使用"微软雅黑"字体，可在 theme 中自定义
6. **宽高比**：默认 16:9，创建模式可选 4:3；修改模式保留源文件宽高比
7. **模板功能**：使用模板时 `--aspect-ratio` 被忽略（模板自带宽高比）
8. **安全确认**：`run_command` 为 DANGEROUS 级别，每次执行需用户确认
9. **中间文件**：生成成功后必须 `del slides.json` 清理
10. **修改备份**：修改前自动备份到 `data/ppt-backups/`，双层清理（每文件 5 个 + 总量 500MB）

## 11. 常见场景示例

### 11.1 创建简单工作汇报

用户："帮我做一个Q3工作汇报PPT"

流程：
1. 执行环境检测（`detect_env.py`）
2. 检查模板（若有模板则询问用户，无模板直接继续）
3. 构造 slides JSON（封面 + 3-5 页内容 + 总结）
4. `write_file` 写入 slides.json
5. `run_command` 执行生成（`timeout: 300000`）
6. `del slides.json` 清理中间文件
7. 向用户报告 output.pptx 已生成

### 11.2 修改已有 PPT

用户："在这个PPT最后加一页总结"

流程：
1. 执行环境检测
2. `extract_document` 读取现有 PPT 内容
3. `resolve_path` 获取 PPT 绝对路径
4. 构造修改 JSON（mode: modify, modify_action: append）
5. `write_file` + `run_command` 执行修改（脚本自动备份源文件）
6. `del slides.json` 清理
7. 报告 modified.pptx 已生成

### 11.3 替换指定页面

用户："把第3页换成新的内容"

流程：
1. 执行环境检测
2. `extract_document` 读取现有 PPT
3. 构造修改 JSON（mode: modify, modify_action: replace, target_slide: 3）
4. `write_file` + `run_command`（脚本自动备份源文件）
5. `del slides.json` 清理
6. 报告结果
