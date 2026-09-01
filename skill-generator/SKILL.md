---
name: skill-generator
description: UseIO 元技能，用于指导 Agent 在识别到用户Skill 创建意图时，按照标准化规范生成 Skill 目录结构及全部资源文件（含 SKILL.md 元数据、执行脚本、模板文件等）。涵盖能力边界约束、文档结构模板、创建工作流、质量校验清单及文件存储规范，确保每个 Skill 格式统一、逻辑闭环、脚本可执行。
triggerKeywords: [做一个skill, 创建技能, 生成skill, 新建skill, skill生成器, create skill, make skill]
version: 1.5.0
---

# Skill Generator - UseIO 技能生成器

## 1. 技能概述

**技能名称**：Skill Generator  
**技能描述**：当用户提出"创建一个技能"等需求时，Agent 按照本技能定义的标准流程和模板，生成一份结构完整、逻辑闭环、脚本可执行的 SKILL.md 文档。
**角色定位**：你是 UseIO 的技能架构师。你的职责是将用户的模糊需求转化为精确、可执行、可复用的 Skill 文档，并确保其中涉及的所有脚本和工具调用都在 UseIO 的能力边界之内。  
**适用场景**：
- 用户明确提出"创建一个技能""生成一个新的 Skill"等表述
- 用户描述了一个可复用的工作流程，希望固化为 Skill
- 用户要求将某套操作规范文档化为 Agent 可执行的技能

---

## 2. UseIO 可执行能力边界

> ⚠️ **铁律：生成的 Skill 中涉及的所有脚本、命令、工具调用，必须严格限制在以下能力矩阵之内。**  
> **零外部依赖优先。** Node.js 沙箱中 require 第三方包会被直接拒绝，脚本必须零第三方依赖；Python 可使用已安装的 pip 第三方库，未安装的依赖必须在 SKILL.md 中声明 `pip install` 前置步骤，并限制在极简范围内。

### 2.1 能力矩阵

| 能力 | 可用范围 | 限制说明 |
|------|----------|----------|
| **Node.js** | v22+，沙箱内白名单模块：`fs`, `path`, `os`, `crypto`, `http`, `https`, `url`, `querystring`, `util`, `stream`, `zlib`, `events`, `string_decoder`, `timers`, `buffer`, `assert` | 沙箱通过 `vm.createContext` 在独立子进程隔离，`fs` 经路径安全包装（双根判定）；代码大小上限 50KB，内存上限 256MB，超时 180 秒；禁止 `child_process`/`net`/`dgram`/`cluster` 等可逃逸沙箱的模块；require 白名单外模块（含全部 npm 第三方包）会被直接拒绝，Node.js 脚本必须零第三方依赖 |
| **Python** | v3.x，默认可使用全部标准库；**仅禁止** 4 个危险模块：`subprocess`、`ctypes`、`pickle`、`multiprocessing` | 代码大小上限 100KB，超时 180 秒；安全检测采用三层机制：① 4 个 BANNED_MODULES 拦截 `import subprocess/ctypes/pickle/multiprocessing`；② 4 个 BANNED_BUILTINS 拦截 `__import__`（任何引用）、`exec`/`eval`/`compile`（仅 bare 调用，不误伤 `re.compile`/`obj.exec`/`def exec`）；③ 5 个 DANGEROUS_PATTERNS 正则检测 `__import__()`、`__builtins__`、`subprocess`、`os.popen`、`os.system`（作为①②的兜底，在剥离注释/字符串后的代码骨架上检测，避免误伤）；**已安装的第三方库（pip 包）可直接 import 使用**，未安装的依赖需在前置准备章节标注 `pip install` 步骤，或改用标准库实现 |
| **Shell** | Windows CMD / PowerShell / Git Bash；采用**灾难性操作硬拦 + 常规操作确认制**（v3 安全模型） | 默认超时 30s，最大超时 5 分钟；**硬拦**（执行即拒绝）灾难性/不可逆/攻击向量级操作：电源操作（`shutdown`/`reboot`/`halt`/`poweroff`）、磁盘与启动（`format`、`mkfs`、`fdisk`、`parted`、`diskpart`、`bcdedit`、`bootrec`、`dd if=`、写裸设备 `/dev/sdX`）、`rm -rf /`（根/家目录）、`del /s /q` 盘符根、`rd/rmdir /s /q` 系统关键目录（普通目录放行）、系统级持久化（`net user /add`、`net localgroup administrators`、`netsh advfirewall`、`wevtutil cl`、`cipher /w`）、LOLBins（`mshta`、`rundll32`、`regsvr32`、`certutil -urlcache`、`bitsadmin /transfer`）、远程执行（`curl/wget | sh`）、fork bomb、PowerShell 隐藏执行（独立参数 `-e`/`-encodedcommand`、`-nop`、`-w hidden`）；**不硬拦但属 DANGEROUS 级需用户确认**：`sudo`、`systemctl`、`reg`（全部子命令）、`taskkill /f`、`sc stop`、`icacls /grant` 等常规运维命令；不可假设 Linux 专属工具（`grep`, `sed`, `awk`）存在，除非通过 Git Bash 执行 |
| **命令执行** | `run_command`（同步，默认 30s）/ `run_command` + `persistent=true`（常驻 PTY 终端会话） | 常驻模式通过 PTY 管理器创建后台会话（`sess_xxx`），适用于 `npm run dev`、`vite`、`docker compose up` 等；可通过 `kill_process` 终止 |
| **常驻终端读取** | `read_terminal_output` | 读取常驻 PTY 终端会话的输出；支持增量读取（仅返回自上次读取后的新增输出）和全量读取；支持条件等待（`waitMs` + `waitPattern`），适用于查看开发服务器启动日志、编译错误等常驻进程输出 |
| **浏览器自动化** | `browser_action`（基于 `puppeteer-core` 通过 CDP 控制真实浏览器） | 优先检测系统 Chrome，Edge 作为 fallback；支持导航、页面状态获取、等待选择器/文本、元素点击/坐标点击/选择器点击、输入、滚动、按键、截图、页面内容提取、页面内 JS 执行、批量脚本（run_script）、控制台日志与网络请求监控查询等 22 个 action；浏览器需已启动，若未启动会自动尝试启动系统 Chrome；脚本中不硬编码浏览器路径，由系统 ChromeDetector 动态检测 |
| **文件 I/O** | `read_file`（完整/范围/尾部读取）、`write_file`、`edit_file`（增量操作 + diff 补丁）、`list_dir`（递归遍历）、`search_files`（文件名 + 内容搜索，ripgrep 加速）、`file_ops`（创建/删除/复制/移动）、`file_info`（存在检查 + 详细信息）、`undo_file`（撤销最近一次敏感操作）、`redo_file`（重做撤销的操作） | 所有文件操作通过 UseIO 内置工具完成；支持路径 scope 四态判定（workspace / sandbox / outside / blocked）；`undo_file`/`redo_file` 用于回滚/重做工作区修改（依赖检查点机制） |
| **文档提取** | `extract_document` | 提取 Office 文档（docx/pptx/xlsx/odt/odp/ods）和 PDF/RTF 的结构化内容；返回纯文本、元数据和可选附件信息；支持 OCR 图片文字识别（本地 tessdata，内网可用）；仅支持上述二进制格式，纯文本/Markdown/CSV 等请使用 `read_file` |
| **网页搜索** | `web_search` | 使用搜索引擎查询实时网页信息，支持关键词搜索；返回结构化搜索结果（条件可用：需配置搜索引擎） |
| **任务规划** | `plan`（生成规划文档）、`plan_file`（读取/列出/更新 Plan 文件） | `plan` 适用于复杂任务/开发任务，生成详细实施规划并保存 Markdown 到 plans 目录；`plan_file` 支持步骤状态管理、内容追加/更新、单步详情生成；严禁用 `read_file`/`list_dir` 操作 Plan 文件路径 |
| **记忆检索** | `recall_memory` | 从用户记忆库中检索与当前话题相关的历史记忆（偏好、习惯、过往经历）；仅在实际需要回忆特定信息时调用，不要每次对话都调用 |
| **知识库** | `query_knowledge_base`（查询）、`save_knowledge`（保存） | 查询个人知识库获取相关知识条目；批量保存知识条目（分类：tech/ideas/reading/work/life） |
| **Skill 加载** | `load_skill`（加载 Skill 正文与子文件清单）、`read_skill_file`（读取 Skill 子文件） | 专用工具，仅可加载已启用的 Skill（摘要列表可能截断，用户 ⌈@技能：xxx⌋ 提及的也可加载，见 2.8）；`read_skill_file` 只能读取已通过 `load_skill` 加载的 Skill 子文件 |
| **图片分析** | `read_image` | 读取本地图片文件（png/jpg/jpeg/webp），调用视觉模型分析图像内容（条件可用：需配置 vision 模型） |
| **屏幕捕获** | `capture_screen` | 捕获用户屏幕并调用视觉模型分析（条件可用：需配置 vision 模型） |
| **路径解析** | `resolve_path` | 相对路径->绝对路径转换、符号链接解析、存在性检查 |
| **文件打开** | `open_target` | 打开本地文件（系统默认应用）或网址（浏览器） |
| **用户交互** | `ask_followup_question` | 向用户提问以获取额外信息或确认；提供 2-4 个建议选项，用户选择结果作为工具返回值反馈给 Agent |
| **进程管理** | `kill_process`（终止进程）/ `kill_process` + `action=list`（列出进程） | 支持终止 child_process 进程（`cmd_xxx`）和 PTY 会话（`sess_xxx`） |
| **Git** | `git diff`, `git log`, `git show`, `git status`, `git branch` 等只读命令（通过 `run_command` 执行） | 写操作（commit/push/merge）需用户明确授权；Git 命令非独立工具，均通过 `run_command` 执行并受其安全策略约束 |
| **MCP 工具** | `mcp__{serverName}__{toolName}`（动态注册的外部工具） | 由用户配置的 MCP 服务器运行时注入；命名空间格式避免与内置工具重名；默认安全级别 CAUTION；详见 2.7 MCP 工具机制 |

### 2.2 Node.js 沙箱运行环境

Node.js 代码在 `child_process.fork` 子进程中通过 `vm.createContext` 执行，除白名单 `require` 模块外，沙箱全局对象还注入以下安全子集，生成的脚本可直接使用：

| 类别 | 可用对象 |
|------|----------|
| 全局对象 | `process`（仅 env/platform/arch/versions.node/cwd/pid 安全子集，敏感环境变量已过滤）、`__dirname`（=workspaceRoot）、`__filename`（固定为空字符串 `''`）、`console`（log/error/warn/info，输出回传主进程） |
| 内置工具 | `JSON`、`Buffer`、`URL`、`URLSearchParams`、`TextEncoder`、`TextDecoder`、`atob`、`btoa`、`performance`、`structuredClone`、`AbortController` |
| 路径工具 | 全局 `path`（透传 join/resolve/normalize/dirname/basename/extname/relative/isAbsolute/parse/format/sep/delimiter/win32/posix，无危险操作） |
| 文件系统 | 全局 `fs` 与 `require('fs')` 行为完全一致，均经路径安全包装（双根判定 + 软链接检查）；注意 `fs.promises` 不暴露，异步操作请使用回调式方法 |
| 定时器 | `setTimeout`/`clearTimeout`（上限 5s）、`setInterval`/`clearInterval`（上限 5s）、`setImmediate`/`clearImmediate`（任务结束时统一清理，防止进程无法退出） |

### 2.3 脚本生成规则

1. **零依赖优先**：Node.js 脚本只用白名单内置模块（见 2.1），require 第三方包会被白名单直接拒绝，Node.js 脚本必须零第三方依赖；Python 脚本优先使用标准库并避开禁止模块（`subprocess`/`ctypes`/`pickle`/`multiprocessing`），已安装的 pip 第三方库可直接 import 使用
2. **跨平台兼容**：路径分隔符使用 `path.join()` 或 `path.sep`，不硬编码 `\\` 或 `/`
3. **浏览器路径动态检测**：浏览器路径不硬编码，由系统 ChromeDetector 动态检测（Chrome 优先，Edge fallback）
4. **错误兜底**：所有脚本必须有 `try-catch` / `try-except`，失败时输出可读的错误信息
5. **前置安装声明**（仅 Python 适用）：若依赖未安装的 pip 第三方包，必须在 SKILL.md 的「前置准备」章节中写明 `pip install` 安装命令；Node.js 无此机制（require 第三方包一律被拒），改用内置模块或 `run_command`/`browser_action` 等工具实现
6. **脚本存放位置**：辅助脚本存放在 Skill 目录下，文件名使用 kebab-case
7. **路径 scope 意识**：文件操作路径受双根目录安全模型约束--用户工作空间（`workspace`）为首选，应用沙箱（`sandbox`）为次选；系统敏感目录（`blocked`）禁止访问；跨工作空间路径会被标记为 `outside`。生成的脚本应优先使用相对路径
8. **常驻进程规范**：若 Skill 需要启动常驻服务（如开发服务器），必须使用 `persistent: true` 模式，并通过 `read_terminal_output` 读取输出、用 `kill_process` 终止

### 2.4 禁止事项

- ❌ 生成需要 `puppeteer`、`playwright`、`canvas` 等重依赖的 Node.js 脚本（require 第三方包会被沙箱直接拒绝，声明安装步骤也无法在 run_javascript 中使用）；此类需求应改用 `browser_action`、`run_command` 等内置能力实现
- ❌ 假设系统安装了 `ffmpeg`、`imagemagick`、`wkhtmltopdf` 等工具
- ❌ 生成 Linux-only 命令却不提供 Windows 兼容方案
- ❌ 脚本中硬编码用户特定路径（如 `C:\Users\xxx`）
- ❌ Python 脚本中使用 `subprocess`、`ctypes`、`pickle`、`multiprocessing` 模块
- ❌ Python 脚本中使用 `__import__`（任何引用均拦截）及 `exec()`、`eval()`、`compile()` bare 调用（属性方法调用如 `re.compile` 不受影响）
- ❌ Python 脚本中使用 `os.popen()`、`os.system()`、`__builtins__` 等危险模式
- ❌ Shell 命令中使用 `shutdown`、`reboot`、`halt`、`poweroff`、`diskpart`、`bcdedit`、`bootrec`、`format`、`mkfs`、`fdisk`、`parted`、`dd if=` 等系统级不可逆操作（硬拦）
- ❌ Shell 命令中使用 `powershell -e`/`-encodedcommand`（Base64 编码执行）、`-nop`、`-w hidden`（隐藏窗口）等攻击向量（硬拦）
- ❌ Shell 命令中使用 `rm -rf /`、`del /s /q` 盘符根、`rd /s /q` 系统关键目录、`curl|sh`、fork bomb、`net user /add`、`netsh advfirewall`、`wevtutil cl`、`cipher /w`、LOLBins（`mshta`/`rundll32`/`regsvr32`/`certutil -urlcache`/`bitsadmin /transfer`）等危险模式（硬拦）
- ❌ Shell 命令中不加说明地使用 `sudo`、`systemctl`、`reg`、`taskkill /f`、`icacls` 等常规运维命令（不硬拦，但属 DANGEROUS 级需用户逐次确认，生成的 Skill 应在工作流中提示用户会弹出确认）
- ❌ 在生成的 Skill 中硬编码假定 MCP 工具一定存在（MCP 工具为运行时动态注入，详见 2.7）

### 2.5 工具级超时配置

不同工具有差异化的超时阈值，生成 Skill 时应据此预估执行耗时，避免因超时导致工具调用失败：

| 工具 | 超时阈值 | 说明 |
|------|----------|------|
| `plan` | 660s（11min） | 骨架先行 + 分步串行生成详情，耗时较长 |
| `plan_file` | 240s（4min） | `generate_step_detail` 调用 LLM，含续写余量 |
| `search_files` | 120s | ripgrep 主路径快速；120s 兼顾 rg 不可用时降级为 fs 串行遍历（10 万文件级项目/网络挂载盘）的场景 |
| `browser_action` | 120s | 浏览器导航、等待加载可能较慢 |
| `read_terminal_output` | 120s | 支持 `waitMs` 条件等待（上限 60s）+ 处理开销 |
| `read_image` | 120s | IPC 取图 + vision 调用 |
| 其他工具（默认） | 180s | 通用兜底超时 |

> 超时后工具返回错误信息，引导 LLM 拆分任务。生成的 Skill 若涉及长耗时操作，应考虑超时约束。

### 2.6 自动批准与信任模式

UseIO 的工具执行采用三级安全分级（SAFE / CAUTION / DANGEROUS），并支持自动批准以减少用户确认打断：

**安全级别**：
- **SAFE**：纯读取/查询/用户交互类工具，静默执行无需确认（如 `read_file`、`list_dir`、`ask_followup_question`、`recall_memory`、`plan` 等）
- **CAUTION**：有一定影响但风险可控（如 `write_file`、`edit_file`、`file_ops`、`capture_screen`、`browser_action`）
- **DANGEROUS**：状态变更/代码执行，必须用户确认（如 `run_command`、`kill_process`、`run_javascript`、`run_python`）

**路径动态分级**：部分工具的安全级别会根据操作路径动态升降。例如 `write_file` 在 workspace/sandbox 内为 CAUTION，路径在 workspace 外（`outside`）则升级为 DANGEROUS；`read_file` 在 workspace/sandbox 内为 SAFE，在 workspace 外（`outside`）升级为 CAUTION（需用户确认），在 `blocked` 系统目录则为 DANGEROUS。涉及文件路径的工具均受此机制约束（多路径工具如 `file_ops` 取最危险 scope）。另有 **action 级动态分级**：`browser_action` 的只读 action（`get_state`/`screenshot`/`extract_content`/`wait`/`wait_for_selector`/`wait_for_text`/`get_console_logs`/`get_network_logs`/`get_network_request`）降级为 SAFE 免确认，其余 action 保持 CAUTION。

**自动批准**：用户可在设置中为以下 CAUTION 级工具开启自动批准，免去每次确认：`write_file`、`edit_file`、`file_ops`、`open_target`、`capture_screen`、`browser_action`、`read_image`。路径升级为 DANGEROUS 时自动批准自动失效。**全信任模式**（`trust_mode_enabled`）开启后，所有工具调用自动批准（包括 DANGEROUS 级别），生成的 Skill 应知晓此模式下工具执行不会被用户确认拦截。

> 生成的 Skill 工作流不应假定工具一定会被用户确认拦截（可能因自动批准或信任模式直接执行），也不应假定 CAUTION 工具一定静默执行（用户未开启自动批准时仍需确认）。

### 2.7 MCP 工具机制

UseIO 支持通过 MCP（Model Context Protocol）协议接入外部工具服务器。MCP 工具在运行时由用户配置的服务器动态注入，**非内置工具**，生成 Skill 时需注意：

- **命名空间格式**：MCP 工具名采用 `mcp__{serverName}__{toolName}` 格式，避免与内置工具重名
- **动态注册**：MCP 服务器连接时，系统自动注册其工具定义（ToolDefinition）、执行器（executor）和安全级别（safetyLevel）三件套；断开时自动注销
- **安全级别**：MCP 工具默认为 CAUTION 级别，可由用户配置调整
- **可用性不确定**：MCP 工具是否存在取决于用户是否配置了对应的 MCP 服务器，**不可硬编码假定其存在**
- **生成 Skill 的约束**：若 Skill 工作流依赖某个 MCP 工具，必须在「前置准备」章节声明该 MCP 服务器需已配置并连接；工作流中应包含检测 MCP 工具是否可用的降级逻辑

### 2.8 Skill 动态加载机制

UseIO 的 Skill 系统采用 Tier 1 摘要 + 按需加载的两级机制，生成的 Skill 会被系统自动消费：

**Tier 1 摘要注入**：
- 系统启动时，将所有已启用 Skill 的摘要（id、name、description、triggerKeywords）自动注入 system prompt 的 Skills 章节
- 摘要总字符上限 4000（约 1k token），超出部分尾部提示"已省略 N 项"
- 摘要由系统自动构建，Skill 作者无需关心注入逻辑，只需确保 frontmatter 的 name/description/triggerKeywords 准确

**按需加载（Tier 2）**：
- LLM 根据 Tier 1 摘要判断需要某个 Skill 时，调用 `load_skill` 工具加载完整 SKILL.md 正文与子文件清单
- `load_skill` 仅可加载已启用的 Skill，`skillId` 与摘要中的 id 一致；摘要列表可能因长度限制截断，用户通过 ⌈@技能：xxx⌋ 明确提及的技能即使未在列表中也可直接加载
- 加载后若需读取 Skill 的子文件（脚本、模板等），使用 `read_skill_file` 工具，不可使用通用 `read_file`
- SKILL.md 正文超过 20000 字符（约 5k token）时自动截断，尾部提示使用 `read_skill_file` 按需读取具体小节；`read_skill_file` 单次读取上限 64000 字符（约 16k token）；单个 Skill 目录文件数超过 200 个时清单截断。**生成的 SKILL.md 应控制在 20000 字符内**，超长内容拆分到子文件按需读取

**内置 Skill 与用户 Skill**：
- **内置 Skill**：随应用分发的预置技能（如本 skill-generator），位于应用 resources 目录，不可修改
- **用户 Skill**：用户创建的技能，位于应用数据根目录下的 `skills/` 子目录
- 两类 Skill 在 frontmatter 结构上完全一致，区别仅在于存储位置和 `builtin` 标志

**分类与启用控制**：
- `skills-config.json` 维护全局分类池和技能-分类关联映射，以及禁用列表
- 默认全部启用，被加入禁用列表的 Skill 不会出现在 Tier 1 摘要中，也无法被 `load_skill` 加载

> 生成 Skill 时，应确保 frontmatter 的 `description` 简明准确地描述核心能力，因为它是 Tier 1 摘要中 LLM 判断是否加载该 Skill 的主要依据。triggerKeywords 应覆盖用户可能的表述方式。

---

## 3. SKILL.md 标准文档结构模板

所有新生成的 SKILL.md 必须包含以下两部分：**YAML Front Matter** + **正文章节**。

### 3.1 YAML Front Matter

```yaml
---
name: <skill-name>          # kebab-case，与目录名一致
description: <一句话描述>    # 概括技能核心能力、输入输出、适用场景
triggerKeywords: [关键词1, 关键词2, ...]  # 3-8个触发词，中英文均可（可选）
version: 1.0.0              # 语义化版本号（可选）
---
```

**字段规范**：
- `name`：全小写 kebab-case，如 `git-code-review`、`api-doc-generator`；必须以小写字母开头，只含小写字母、数字、短横线，长度不超过 50 字符
- `description`：必须包含"做什么 + 怎么做 + 输出什么"三要素，建议简明扼要
- `triggerKeywords`：覆盖用户可能的表述方式，中英文混合；为可选字段，未提供时 parser 补全为空数组
- `version`：语义化版本号，建议初始版本使用 `1.0.0`，后续迭代递增；为可选字段

> **字段必填性说明**：`name` 和 `description` 为必填字段；`triggerKeywords` 和 `version` 为可选字段（parser 会将缺失的数组字段补全为空数组，version 缺失时保留为空）。

> **防误导**：frontmatter **仅支持**上述 4 个字段，不要添加 `category`/`categories`/`tags`/`permissions` 等额外字段（分类归属由用户在应用 UI 中管理，存储于 `skills-config.json`，与 SKILL.md 无关）。

> **自举一致性约束**：`name` 字段必须与 Skill 目录名完全一致，否则系统加载时会抛出 `FRONTMATTER_MISMATCH` 错误（[`loadCore.ts`](src/main/services/skill/loadCore.ts:152) 会校验 frontmatter.name 与目录名一致性）。

### 3.2 正文标准章节

```markdown
# <Skill 名称>

## 1. 技能概述
- 技能名称、技能描述、角色定位、适用场景

## 2. 前置准备 / 环境要求
- 依赖工具版本、环境变量、前置安装步骤（如有）
- MCP 服务器配置声明（如依赖 MCP 工具）

## 3. 输入规范
- 用户需提供什么输入（文件路径、参数、选项等）
- 输入格式示例

## 4. 执行工作流
- Step 1 -> Step 2 -> Step 3 -> ...（每步明确做什么、用什么工具、产出什么）
- 工作流必须形成闭环，无悬空节点

## 5. 输出规范
- 产出物格式（Markdown / JSON / PNG / 文件等）
- 存储路径规则
- 自动打开 / 自动通知等后续动作

## 6. 脚本与工具约束
- 列出本 Skill 用到的所有脚本和命令
- 标注每个脚本的能力边界合规性

## 7. 异常处理
- 核心失败场景的兜底策略
- 用户引导（缺少输入时如何提示）

## 8. 质量校验（可选）
- 自检清单，确保执行结果达标

## 9. 报告存储与自动打开（如适用）
- 路径规则、命名规则、自动打开目录
```

### 3.3 章节裁剪规则

| 场景 | 必选章节 | 可选章节 |
|------|----------|----------|
| 纯流程型 Skill（无脚本） | 1, 3, 4, 5, 7 | 2, 6, 8, 9 |
| 脚本型 Skill | 1, 2, 3, 4, 5, 6, 7 | 8, 9 |
| 报告输出型 Skill | 1, 2, 3, 4, 5, 7, 9 | 6, 8 |

---

## 4. Skill 创建标准化工作流

当用户提出创建技能的需求时，Agent 必须按以下 6 步闭环执行：

### Step 1：需求分析与重名检测

**目标**：精确理解用户要做什么 Skill，并检测是否存在同名或雷同的已有 Skill。

**执行要点**：
1. 提取核心目标：这个 Skill 解决什么问题？
2. 识别输入输出：用户会提供什么？Skill 产出什么？
3. 确认能力边界：是否需要脚本？脚本是否在 UseIO 能力矩阵内？
4. 如有关键信息缺失（如输入格式不明确、输出目标未指定），使用 `ask_followup_question` 向用户确认
5. **重名检测**（必须执行）：
   - 使用 `list_dir` 扫描应用 Skills 存储目录（位于应用数据根目录下的 `skills/` 子目录）下所有子目录
   - 检查是否已存在与目标 `name` 同名的目录（内置 Skill 启动时会镜像安装到同一目录，扫描天然覆盖）
   - 若存在同名目录，使用 `read_file` 读取其 `SKILL.md` 的 YAML front matter（前 10 行即可）
   - 对比已有 Skill 的 `description` 和 `triggerKeywords` 与用户当前需求，判断是否**雷同**
   - **判定雷同的标准**（语义判断为主）：已有 Skill 与目标解决同类问题、面向同类输入输出、或 description 表述的核心能力一致，即视为雷同；仅名称碰巧相同但功能完全不同的不算雷同
   - 若判定为雷同，使用 `ask_followup_question` 向用户提示：
     - 展示已有 Skill 的 name、description、triggerKeywords
     - 询问用户是「复用已有 Skill（在其基础上迭代升级）」还是「创建新 Skill（使用不同名称）」
   - 若用户选择创建新 Skill，要求用户提供一个新的不重名的 `name`
   - 若用户选择复用，进入已有 Skill 目录进行版本迭代（递增 version），不创建新目录

> **路径获取说明**：Skills 存储目录为应用数据根目录下的 `skills/` 子目录，不随用户当前工作空间变化。系统提示词的 Skill 摘要**不含路径**，Agent 按以下顺序定位：① 调用 `resolve_path('~/.useio/skills')` 探测（`resolve_path` 支持 `~` 展开）→ 存在即为安装版数据根目录；② 探测失败时（portable 版数据目录跟随 exe，路径不固定），使用 `ask_followup_question` 请用户提供数据根目录，或引导用户在「技能管理」页面查看。注意：该目录在用户工作空间之外，对它的 `write_file`/`file_ops` 属 DANGEROUS 级路径，执行时会触发用户确认，属预期行为。

**产出**：一份需求摘要（内含目标、输入、输出、是否需要脚本）+ 重名检测结论（无冲突 / 已复用 / 已使用新名称）

### Step 2：结构设计

**目标**：套用标准模板，规划章节。

**执行要点**：
1. 根据 3.3 章节裁剪规则，确定必选和可选章节
2. 规划工作流步骤数量和每步职责
3. 确定文件存储路径和命名规则（如适用）
4. 列出需要的辅助脚本清单（如适用）

**产出**：章节大纲 + 工作流步骤草案

### Step 3：内容编写

**目标**：填充每个章节的具体内容。

**执行要点**：
1. 先写 YAML Front Matter（name / description / triggerKeywords / version）
2. 再写正文，从概述到工作流到异常处理
3. 工作流步骤必须具体到"用什么工具、做什么操作、产出什么结果"
4. 如有脚本，同步编写脚本代码：Node.js 确保零第三方依赖（仅白名单内置模块），Python 确保仅用标准库和已安装的 pip 包（未安装的依赖需声明前置步骤）
5. 脚本必须跨平台兼容、有错误兜底

**产出**：完整的 SKILL.md 草稿 + 辅助脚本文件（如有）

### Step 4：脚本约束检查

**目标**：确保所有脚本和命令在 UseIO 能力边界内。

**执行要点**：
1. **Node.js**：逐行检查 `require()` 是否只用了白名单模块（`fs`, `path`, `os`, `crypto`, `http`, `https`, `url`, `querystring`, `util`, `stream`, `zlib`, `events`, `string_decoder`, `timers`, `buffer`, `assert`），禁止 `child_process`/`net`/`dgram`/`cluster`
2. **Python**：检查 `import` 是否命中禁止模块（`subprocess`, `ctypes`, `pickle`, `multiprocessing`），检查是否使用 `__import__`（任何引用均拦截）及 bare 调用形式的 `exec`/`eval`/`compile`（属性方法调用如 `re.compile` 不受影响），检查是否使用 `__builtins__`/`os.popen`/`os.system` 等危险模式
3. **Shell**：检查命令是否命中硬拦清单（`BANNED_PATTERNS`：电源/磁盘格式化、`rm -rf /`、`del /s /q` 盘符根、`rd /s /q` 系统关键目录、`net user /add`、`netsh advfirewall`、`wevtutil cl`、`cipher /w`、LOLBins、远程执行 `curl/wget | sh`、fork bomb、PowerShell `-e`/`-nop`/`-w hidden` 隐藏执行；`BANNED_PREFIXES`：`shutdown`/`reboot`/`halt`/`poweroff`/`mkfs`/`fdisk`/`parted`/`diskpart`/`bcdedit`/`bootrec`/`mshta`/`rundll32`/`regsvr32`）。注意 `sudo`/`systemctl`/`reg`/`taskkill`/`icacls` 等常规运维命令不在硬拦清单，但属 DANGEROUS 级需用户确认
4. 检查路径是否跨平台兼容，是否使用相对路径（受 workspace/sandbox 双根目录约束）
5. 检查是否有 `try-catch` / `try-except` 错误兜底
6. 如有 Python 第三方依赖（且未安装），确认已在前置准备章节声明 `pip install` 安装步骤
7. 如有常驻进程需求，确认已使用 `persistent: true`，并通过 `read_terminal_output` 读取输出、用 `kill_process` 终止
8. 如依赖 MCP 工具，确认已在前置准备章节声明 MCP 服务器配置要求，并包含降级逻辑

**产出**：合规确认（或修复后的脚本）

### Step 5：质量校验

**目标**：运行质量校验清单（见第 5 章），确保文档达标。

**执行要点**：
1. 逐项对照质量校验清单
2. 不合格项立即修复
3. 全部通过后方可进入交付

**产出**：校验通过的最终文档

### Step 6：交付

**目标**：输出最终文件并告知用户。

**执行要点**：
1. 将 SKILL.md 写入应用数据根目录下的 `skills/<skill-name>/SKILL.md`（路径定位方式见 Step 1 的「路径获取说明」：`resolve_path('~/.useio/skills')` 探测，portable 版询问用户；该路径在工作空间外，写入会触发 DANGEROUS 级用户确认，属预期行为）
2. 将辅助脚本写入 `skills/<skill-name>/` 或其 `scripts/` 子目录
3. **禁止覆盖**：写入前再次确认目标目录不存在（Step 1 已检测，此处为二次保险）。若目录已存在且用户未选择复用，在目录名后追加 `-v2`、`-v3` 等后缀
4. 向用户展示技能概要（名称、触发词、工作流步骤数、核心能力）
5. 提供使用示例（如何触发、预期输出）

**产出**：已写入的文件路径 + 使用说明

---

## 5. 质量校验清单

生成的 SKILL.md 必须逐项通过以下校验：

### 5.1 Front Matter 校验

| # | 检查项 | 通过标准 |
|---|--------|----------|
| 1 | YAML 格式 | `---` 包裹，无语法错误 |
| 2 | name 字段 | 存在，kebab-case（小写字母开头，只含小写字母/数字/短横线），长度 ≤ 50 字符，与目录名一致 |
| 3 | description 字段 | 存在，包含"做什么+怎么做+输出什么"三要素 |
| 4 | triggerKeywords 字段 | 存在或省略均可（省略时 parser 补全为空数组）；建议 3-8 个关键词，覆盖中英文表述 |
| 5 | version 字段 | 存在或省略均可（省略时 parser 保留为空）；建议使用语义化版本号 |

### 5.2 正文校验

| # | 检查项 | 通过标准 |
|---|--------|----------|
| 6 | 章节完整性 | 必选章节全部存在，无遗漏 |
| 7 | 工作流闭环 | 每个步骤有明确的输入和产出，无悬空节点 |
| 8 | 工具引用 | 工作流中引用的工具/命令在能力矩阵内 |
| 9 | 输入规范 | 明确列出用户需提供什么，有格式示例 |
| 10 | 输出规范 | 明确产出物格式和存储路径 |
| 11 | 异常处理 | 覆盖至少 3 个核心失败场景 |

### 5.3 脚本校验（如适用）

| # | 检查项 | 通过标准 |
|---|--------|----------|
| 12 | Node.js 依赖合规 | `require()` 仅使用 16 个白名单模块，未使用 `child_process`/`net`/`dgram`/`cluster`；代码大小 ≤ 50KB |
| 13 | Python 依赖合规 | 未导入 `subprocess`/`ctypes`/`pickle`/`multiprocessing`；未使用 `__import__`（任何引用均拦截）及 bare 调用形式的 `exec`/`eval`/`compile`（属性方法调用如 `re.compile` 不受影响）；未使用 `__builtins__`/`os.popen`/`os.system` 等危险模式；代码大小 ≤ 100KB |
| 14 | Shell 命令合规 | 命令不命中硬拦清单：`BANNED_PATTERNS`（电源/磁盘格式化、`rm -rf /`、`del /s /q` 盘符根、系统关键目录递归删除、`net user /add`、`netsh advfirewall`、`wevtutil cl`、`cipher /w`、LOLBins、远程执行 `curl/wget | sh`、fork bomb、PowerShell `-e`/`-nop`/`-w hidden`）和 `BANNED_PREFIXES`（`shutdown`/`reboot`/`halt`/`poweroff`/`mkfs`/`fdisk`/`parted`/`diskpart`/`bcdedit`/`bootrec`/`mshta`/`rundll32`/`regsvr32`） |
| 15 | 跨平台 | 路径使用 `path.join()`，不硬编码分隔符 |
| 16 | 路径 scope | 文件操作使用相对路径，不硬编码绝对路径；工作空间外路径需用户确认 |
| 17 | 错误兜底 | 有 try-catch / try-except，失败输出可读信息 |
| 18 | 浏览器路径 | 不硬编码浏览器路径，由系统 ChromeDetector 动态检测 |
| 19 | 脚本存放 | 存放在 Skill 目录下，kebab-case 命名 |
| 20 | 常驻进程 | 使用 `persistent: true` 的命令需通过 `read_terminal_output` 读取输出、用 `kill_process` 终止 |
| 21 | MCP 依赖声明 | 若工作流依赖 MCP 工具，已在前置准备章节声明，且包含降级逻辑 |

### 5.4 格式校验

| # | 检查项 | 通过标准 |
|---|--------|----------|
| 22 | Markdown 格式 | 层级清晰，表格/代码块格式正确 |
| 23 | 目录规范 | 文件位于 `skills/<skill-name>/SKILL.md` |
| 24 | 无矛盾 | 术语一致，定义与使用无冲突；不引用禁止模块/命令 |
| 25 | 可读性 | 步骤描述具体可操作，无泛泛之词 |
| 26 | 超时预估 | 涉及长耗时工具（plan/browser_action 等）的工作流，已考虑超时约束（见 2.5） |

---

## 6. 文件存储与目录规范

### 6.1 存储根目录

所有 Skill 必须存储在 **应用数据根目录**下的 `skills/` 子目录中：

```
<应用数据根目录>/skills/
```

> 该路径不随用户当前工作空间变化。安装版默认 `~/.useio`，portable 版跟随 exe 所在目录（`<exeDir>/data`）。系统提示词的 Skill 摘要不含路径，Agent 通过 `resolve_path('~/.useio/skills')` 探测定位，探测失败时询问用户（详见第 4 章 Step 1）。该目录在用户工作空间之外，写入操作会触发 DANGEROUS 级用户确认。

### 6.2 目录结构

```
<应用数据根目录>/skills/
├── <skill-name>/
│   ├── SKILL.md              # 主文档（必须）
│   ├── scripts/              # 辅助脚本（可选）
│   │   ├── helper.js
│   │   └── utils.py
│   ├── assets/               # 静态资源（可选）
│   │   ├── template.md
│   │   └── config.json
│   └── README.md             # 补充说明（可选）
```

### 6.3 命名规则

| 对象 | 规则 | 示例 |
|------|------|------|
| Skill 目录名 | kebab-case，与 `name` 字段一致 | `git-code-review/` |
| SKILL.md | 固定文件名，大写 | `SKILL.md` |
| 脚本文件 | kebab-case，带 `.js` / `.py` / `.sh` 后缀 | `generate-report.js` |
| 资源文件 | kebab-case，保留原始扩展名 | `report-template.md` |

### 6.4 重名检测与冲突处理

创建新 Skill **前**，必须执行以下检测流程：

1. **扫描已有 Skill**：使用 `list_dir` 扫描应用数据根目录下 `skills/` 子目录的所有子目录
2. **同名检测**：检查是否已存在与目标 `name` 同名的目录
3. **雷同检测**：若存在同名目录，读取其 `SKILL.md` 的 front matter，对比 `description` 和 `triggerKeywords`：
   - **雷同判定**（语义判断为主）：解决同类问题、面向同类输入输出、或 description 核心能力一致
   - **非雷同**：名称碰巧相同但功能完全不同
4. **内置技能同名禁令**：**禁止使用与内置技能相同的 name**（如 `skill-generator`、`browser-automation`、`knowledge-extractor`）。内置技能在应用每次启动时会以「先删后拷」的镜像替换方式重装到用户 skills 目录，与内置技能同名的用户 Skill 会在下次启动时**被内置版本覆盖丢失**，无法恢复
5. **冲突处理**：
   - 若**同名且雷同**：使用 `ask_followup_question` 提示用户，提供选项：
     - 「在已有 Skill 基础上迭代升级（递增 version，不创建新目录）」
     - 「创建为新 Skill（使用不同的 name，新目录）」
   - 若**同名但不雷同**：直接在目标 name 后追加领域后缀（如 `-v2`、`-alt`）避免冲突
   - 若**无同名**：正常创建
6. **禁止覆盖铁律**：任何情况下都不得覆盖已有 Skill 目录中的文件。若目录已存在且用户未明确选择复用，必须使用新目录名

### 6.5 存储规则

1. 每个 Skill 必须拥有独立的子目录，禁止多个 Skill 共用一个目录
2. SKILL.md 是唯一入口文件，文件名固定不可变
3. 辅助脚本和资源文件存放在同目录或子目录下
4. 禁止将 Skill 文件散落在项目根目录或工作空间临时目录
5. 如 Skill 有版本迭代，在 YAML front matter 中递增 version，不创建历史副本
6. 创建前必须执行重名检测（6.4），确保不覆盖已有 Skill

---

## 7. 异常处理

| 失败场景 | 处理策略 |
|----------|----------|
| 用户需求模糊，无法确定 Skill 目标 | 使用 `ask_followup_question` 提问，提供 2-4 个选项 |
| 需要的脚本依赖不在能力矩阵内 | 告知用户限制，提供替代方案（如用 `browser_action` 截图替代 puppeteer 脚本） |
| 用户要求的输出格式无法实现 | 说明限制，提供最接近的可行方案 |
| 脚本执行失败 | 检查错误信息，调整脚本或降级为纯文档指导 |
| 生成的 SKILL.md 未通过质量校验 | 逐项修复，全部通过后再交付 |
| 发现同名且雷同的已有 Skill | 使用 `ask_followup_question` 提示用户，展示已有 Skill 信息，询问是复用迭代还是创建新 Skill |
| 用户选择创建新 Skill 但未提供不重名名称 | 自动在原 name 后追加 `-v2` 后缀，并告知用户最终使用的名称 |
| 目标目录已存在但用户未选择复用 | 禁止覆盖，自动追加 `-v2`/`-v3` 后缀创建新目录 |
| `resolve_path('~/.useio/skills')` 探测失败（portable 版） | 使用 `ask_followup_question` 请用户提供数据根目录，或引导用户在「技能管理」页面查看；不要盲猜路径 |
| 目标 name 与内置技能同名 | 拒绝使用该 name（重启后会被内置版本镜像替换覆盖），要求用户更换名称或改名内置技能副本语义（如 `my-skill-generator`） |
| Skill 工作流依赖的 MCP 工具不可用 | 提示用户需配置对应 MCP 服务器，或提供不依赖 MCP 的降级方案 |
| 条件可用工具（web_search/capture_screen/read_image/browser_action）未满足前置条件 | 在前置准备章节声明所需配置（搜索引擎/vision 模型/浏览器），并提供降级方案 |

---

## 8. 强制规则

1. **能力边界不可逾越**：生成的所有脚本和命令必须在本技能第 2 章定义的能力矩阵之内；Node.js 仅用 16 个白名单模块（代码 ≤ 50KB、内存 ≤ 256MB、超时 180s，零第三方依赖），Python 采用三层安全检测（4 个 BANNED_MODULES + 4 个 BANNED_BUILTINS + 5 个 DANGEROUS_PATTERNS，代码 ≤ 100KB、超时 180s，已安装 pip 包可直接 import），Shell 命令不得命中硬拦清单（默认 30s、最大 300s；`sudo`/`reg` 等常规运维命令不硬拦但属 DANGEROUS 级需用户确认）。
2. **零依赖优先**：Node.js 仅用白名单内置模块（require 第三方包会被直接拒绝，必须零依赖）；Python 优先使用标准库并避开禁止项，已安装的 pip 第三方库可直接 import，未安装的需声明前置安装步骤。
3. **自举合规**：本元技能自身也必须符合其所定义的全部标准（YAML front matter 完整、章节齐全、工作流闭环）。
4. **质量校验必过**：交付前必须逐项通过第 5 章的质量校验清单，不合格项必须修复。
5. **目录规范必守**：所有 Skill 文件必须存放在应用数据根目录下的 `skills/<skill-name>/` 目录下，SKILL.md 为唯一入口；应用数据根目录由系统动态注入，不得硬编码绝对路径。
6. **工作流必闭环**：工作流的每个步骤必须有明确的输入和产出，最后一个步骤必须是交付/输出。
7. **禁止编造能力**：不得在生成的 Skill 中引用 UseIO 不具备的工具或能力。
8. **重名检测必做**：创建新 Skill 前必须扫描应用数据根目录下的 `skills/` 目录，检测同名和雷同 Skill（语义判断，见 6.4），雷同时必须提示用户；**禁止使用与内置技能相同的 name**（重启会被镜像替换覆盖）。
9. **禁止覆盖**：任何情况下不得覆盖已有 Skill 目录中的文件，冲突时使用新目录名或迭代 version。
10. **MCP 依赖必声明**：若 Skill 依赖 MCP 工具，必须在前置准备章节声明 MCP 服务器配置要求，并包含工具不可用时的降级逻辑。