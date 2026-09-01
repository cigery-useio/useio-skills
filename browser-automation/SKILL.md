---
name: browser-automation
description: 浏览器自动化技能，通过 browser_action 工具控制 Chrome 浏览器执行多步骤网页操作任务。支持页面导航、元素点击与输入、页面状态提取、截图分析、控制台错误与网络请求监控查询等。适用于网页数据采集、表单自动填写、网页信息查询、多步骤网页交互等场景。
triggerKeywords: [浏览器操作, 打开网页, 网页自动化, browser automation, web scraping, 填表单, 网页点击, 自动填表, 爬取网页, web interaction]
version: 1.4.0
---

# Browser Automation — 浏览器自动化技能

## 1. 技能概述

**技能名称**：Browser Automation
**技能描述**：通过 `browser_action` 工具控制本地 Chrome/Edge 浏览器执行多步骤网页操作任务，支持页面导航、DOM 状态读取、元素点击/输入、滚动、按键、CSS 内容提取、截图获取，以及控制台日志/网络请求监控查询（get_console_logs/get_network_logs/get_network_request）。截图仅提供图像数据，视觉理解由后续对话逻辑处理。
**角色定位**：你是浏览器自动化专家。你的职责不是"猜页面"，而是持续观察真实页面状态、基于最新元素 ID 谨慎操作、验证每一步结果，并在页面结构复杂或工具能力不足时及时切换策略或明确告知用户限制。
**适用场景**：

- 网页数据采集与信息提取
- 表单自动填写（敏感提交前必须请示用户）
- 网页信息查询
- 多步骤网页交互（搜索、登录、导航、筛选、分页等）
- 结合本地知识库中的操作手册执行自动化流程或测试

**不擅长/需谨慎的场景**：

- Canvas/WebGL/图片内文字、复杂图表：DOM 无法提取，改用 `screenshot`（已支持视觉模型分析）或如实说明限制
- 跨域 iframe、closed Shadow DOM 内元素：当前工具集无法穿透（open Shadow DOM 和同域 iframe 可通过 `eval_in_page` 访问）
- 拖拽、文件上传、鼠标悬停、右键菜单：当前工具集不支持
- 验证码、二次验证、强反爬风控页：不模拟绕过，请示用户人工处理

## 2. 前置准备

- 系统已安装 Chrome 或 Edge 浏览器
- 首次使用时会自动尝试启动系统 Chrome
- 如未检测到浏览器，需在设置 > 系统通用 > 浏览器自动化 中手动指定路径
- 浏览器使用隔离的独立用户数据目录，不复用用户 Chrome Profile，因此已登录的站点状态不会自动保留（每次需重新登录）

### 2.1 能力边界（重要）

以下限制由当前实现决定，操作时必须心中有数，避免在不可能成功的路径上反复尝试：

| 限制项                      | 说明                                                                                                                              | 应对策略                                                                                                   |
| --------------------------- | --------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| 启发式元素识别              | `get_state` 已支持 `cursor:pointer`、`tabindex>=0`、`onclick`、`data-*` 事件属性的启发式识别（已排除 Vue `data-v-` 和 Naive UI `data-n-` 框架 scoped 属性），覆盖大部分伪交互元素；命中元素标注 `reason=cursor:pointer` 等，可直接用 `click` 操作 | 未被识别的元素可用 `click_selector`（CSS 选择器点击）或 `eval_in_page`（页面内执行 JS）                     |
| 元素列表默认上限 100 个     | `get_state` 默认最多返回 100 个可交互元素，可通过 `max_elements` 调整，硬性上限 200；超出会截断（返回 `elementsTruncated: true`） | 元素多时优先用 `max_elements` 适度提高上限，或用 `scroll` 分段获取 / `extract_content` 精确提取            |
| 元素去重与视口优先排序      | `get_state` 已自动去重（以"文本+坐标"为 key，避免同一元素被多个选择器重复命中）并按"视口内优先"排序（视口内元素排前列，同组保持 DOM 顺序） | 无需手动处理；视口内元素优先返回有助于快速定位当前可见可操作元素                                            |
| 区域化过滤 `container_selector` | `get_state` 支持传入 `container_selector`（CSS 选择器）限定遍历范围，仅返回容器内部元素；容器不存在时返回空列表（不报错） | 页面元素过多或只需关注特定业务区域时使用，避免全局无关 DOM 挤占元素上限                                      |
| 压缩模式 `compact`          | `get_state` 支持传入 `compact=true` 启用压缩输出：元素行仅保留核心字段，页面文本摘要阈值降至 500 | 元素密集页/长任务自动化场景使用，降低 Token 消耗；默认关闭                                                  |
| 坐标点击 `click_at` 对动态布局脆弱 | `click_at` 直接按坐标点击，对窗口缩放/响应式断点/懒加载位置漂移敏感 | 坐标稳定可预测时（循环答题、分页采集）使用 `click_at`；动态布局页面优先用 `click`/`click_selector` 定位    |
| 批量脚本 `run_script` 步骤与超时 | `run_script` 支持 4 种原子步骤（click_at/wait_for_selector/wait_for_text/wait），任一步骤失败即终止；整体超时 60s，单步 wait_for_* 超时默认 5000ms 最大 30000ms | 确定性流程的批量执行；步骤数不宜过多，单次总耗时不超过 60s                                                |
| 元素文本截断 100 字符       | 单个元素的 text 字段最多 100 字符                                                                                                 | 长文本内容用 `extract_content` 获取完整文本                                                                |
| 页面文本上限 2000 字符      | `get_state` 的 textContent 最多 2000 字符                                                                                         | 需要完整页面文本时用 `extract_content` 指定选择器                                                          |
| 无悬停/右键/拖拽            | 当前不支持 hover、contextmenu、drag 操作                                                                                          | 用 `click` 触发或 `press_key` 模拟，无法实现时向用户说明                                                   |
| 支持选择器/文本等待         | `wait_for_selector` 可等待 CSS 选择器对应元素出现；`wait_for_text` 可等待页面指定文本出现（轮询检测，默认 5000ms，最高 30000ms）；均为只读免确认，优于固定 `wait(ms)` | SPA/异步渲染优先用 `wait_for_selector`/`wait_for_text`，无法确定选择器/文本时再用 `wait` + `get_state`     |
| 单活动标签页                | 虽可 `new_tab`，但仅跟踪单一活动页，无法并发操作多个标签                                                                          | 串行操作，用完一个标签页再开下一个                                                                         |
| 截图为整页视口              | `screenshot` 截取当前视口（1280×800），不支持指定元素区域                                                                         | 需要局部时先 `scroll` 定位再截图                                                                           |
| `type` 为追加输入           | 输入文本会追加到现有值之后，不会自动清空                                                                                          | 输入前用 `press_key("Control+A")` + `press_key("Backspace")` 清空，或 `press_key("Control+A")` 后直接 type |
| 无 Cookie/LocalStorage 注入 | 不支持预设登录态，隔离 Profile 每次为空                                                                                           | 需登录的任务每次走完整登录流程                                                                             |
| `click` 为 CDP 真实鼠标事件 | 元素点击通过 CDP `Input.dispatchMouseEvent`（`page.mouse.click`）实现，生成 `isTrusted=true` 真实鼠标事件，对 Vue/React 框架组件有效 | 坐标获取失败时降级为 `el.click()`；少数极端情况仍不响应时用 `press_key`（如 Enter/Space）替代                |
| 不支持嵌套 `:has()`         | `:has()` 本身可用（Chrome 105+），但嵌套 `:has()` 内部不能再嵌套 `:has()`，浏览器原生限制                                          | 避免使用嵌套 `:has()` 选择器，改用其他定位方式                                                                |
| 不支持 `:contains()`        | `:contains()` 是 jQuery 扩展伪类，非标准 CSS，`querySelector` 不支持                                                               | 用 `extract_content` 或 `eval_in_page` 替代文本匹配                                                            |
| headless 默认关闭           | 浏览器默认有头（可见窗口），非无头模式                                                                                            | 正常情况无需调整，任务完成后可 `close` 释放                                                                |
| 观测缓冲上限                | console 与 network 各 500 条环形缓冲，超出淘汰最旧                                                                                | 需要完整历史时尽早分页查询                                                                                  |
| 响应体仅预缓存错误响应      | 仅预缓存错误响应（xhr/fetch 且状态码 >= 400，最近 20 条）                                                                        | 成功响应体不可查，属刻意设计                                                                                |
| 跨导航保留最近 3 代记录     | 观测查询默认仅当前导航代，`include_preserved=true` 时保留最近 3 代                                                                | 排查登录跳转链路时传 include_preserved=true                                                                 |

## 3. 核心操作流程

### 3.1 元素 ID 规范（核心）

**铁律：每次操作前必须通过 `get_state` 获取最新元素列表和 ID。**

- `get_state` 返回页面中**当前可见且可交互**的元素，每个元素分配唯一 ID（如 `e1`、`e2`...）
- `click` 和 `type` 操作必须使用 `element_id` 参数，而非 CSS 选择器
- 每次 DOM 变化（点击、输入、页面跳转）后，元素 ID 会失效，需重新 `get_state`
- **元素 ID 仅在同一页面状态快照内有效**：一旦执行了任何改变 DOM 的操作，之前的 ID 全部作废

### 3.2 get_state 返回结构详解

`get_state` 返回的页面状态（PageState）包含以下字段，操作决策应综合使用：

| 字段                | 说明                                                                  | 用途                                                                                         |
| ------------------- | --------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| `url`               | 当前页面 URL                                                          | 判断是否已跳转/登录成功、是否仍在目标页                                                      |
| `title`             | 页面标题                                                              | 辅助判断页面状态                                                                             |
| `elements[]`        | 可交互元素列表（默认最多 100 个，可用 `max_elements` 调整，硬顶 200） | 定位要操作的元素，每项含 id/tag/text/type/role/ariaLabel/placeholder/value/href              |
| `elementsTruncated` | 元素是否被截断                                                        | 为 `true` 时说明页面元素超过当前上限，需提高 `max_elements`、scroll 分段或用 extract_content |
| `textContent`       | 页面可见文本（最多 2000 字符）                                        | 理解页面整体内容、查找线索                                                                   |
| `screenshot`        | 截图（仅 `include_screenshot=true` 时返回）                           | 视觉辅助判断，复杂布局时尤其有用                                                             |

**元素定位策略（按优先级）**：

1. **精确文本匹配**：优先用元素的 `text` 字段匹配目标（如登录按钮 text="登录"）
2. **placeholder 匹配**：输入框常无 text，用 `placeholder` 定位（如 placeholder="请输入用户名"）
3. **aria-label 匹配**：图标按钮常无可见文本，用 `ariaLabel` 定位
4. **type + 顺序**：表单中可用 `type`（如 type="email"/"password"）配合出现顺序定位
5. **截图兜底**：元素信息不足时，用 `get_state` 携带 `include_screenshot=true` 获取截图辅助判断

**元素返回顺序**：元素列表按"视口内优先"排序--视口内（元素中心点在当前可视区域内）的元素排在列表前排，视口外元素靠后。同组内保持 DOM 遍历顺序（稳定排序），便于优先识别当前可见的可操作元素。此外，元素已自动去重（以"文本+坐标"为 key），避免同一按钮被多个选择器重复命中。

**区域化过滤（container_selector）**：当页面元素过多或只需关注特定业务区域时，传入 `container_selector`（CSS 选择器）限定遍历范围，仅返回容器内部的可交互元素。容器不存在时返回空元素列表（不报错），可据此判断选择器是否正确。容器存在时 `textContent` 也只返回容器内可见文本，避免全局静态文本污染。

**压缩模式（compact）**：元素密集页或长任务自动化场景下，传入 `compact=true` 启用压缩输出：元素行仅保留 `[id] <tag> "text"` 核心字段（仅 input/a 标签保留 placeholder/type/href），页面文本摘要截断阈值从 1500 降至 500，大幅降低 Token 消耗。默认关闭，不传时格式与完整模式一致。

**关键提示**：`get_state` 的 `include_screenshot` 参数默认为 `false`。需要截图辅助判断时必须显式传 `include_screenshot: true`。但截图会显著增加返回数据量，仅在元素信息不足以决策时使用。

### 3.3 标准操作循环（ReAct 模式）

```
1. get_state → 获取页面状态和元素列表
2. 判断 → 综合元素列表、textContent、url 决定下一步操作
3. 操作 → click/type/navigate/press_key/scroll 等
4. get_state → 验证操作结果，获取最新页面状态（DOM 变化后 ID 已失效）
5. 重复 2-4 直到任务完成
```

**重要：每次操作后必须 get_state 复查。** 不要假设操作一定成功——点击可能触发弹窗、输入可能被校验拦截、导航可能跳转到了错误页。只有通过 get_state 确认页面状态符合预期，才能继续下一步。

### 3.4 各 action 使用规则

| action              | 用途         | 必需参数             | 可选参数                             | 说明                                                               |
| ------------------- | ------------ | -------------------- | ------------------------------------ | ------------------------------------------------------------------ |
| `navigate`          | 导航到 URL   | `url`                | `max_elements`                       | 首次调用自动启动浏览器；等待 domcontentloaded                      |
| `get_state`         | 获取页面状态 | 无                   | `include_screenshot`, `max_elements`, `container_selector`, `compact` | 返回元素列表 + 页面文本 + 截图（可选）；支持区域化过滤与压缩模式；视口内元素优先 |
| `click`             | 点击元素     | `element_id`         | `max_elements`                       | 通过 CDP 真实鼠标事件实现；操作后自动返回新状态                    |
| `click_selector`    | 选择器点击   | `selector`           | `max_elements`                       | 逃生舱：当目标元素未被 get_state 识别时，直接用 CSS 选择器点击     |
| `type`              | 输入文本     | `element_id`, `text` | `max_elements`                       | 先 focus 再输入；**追加输入不清空**，见 3.6                        |
| `scroll`            | 滚动页面     | 无                   | `direction`, `amount`, `max_elements`| direction: up/down，amount 默认 300px；操作后自动返回新状态        |
| `press_key`         | 按键         | `key`                | `max_elements`                       | 支持组合键如 `Control+A`、`Enter`、`Escape`、`Tab`                 |
| `go_back`           | 返回上一页   | 无                   | `max_elements`                       | 浏览器后退                                                         |
| `new_tab`           | 新建标签页   | 无                   | `url`, `max_elements`                | 切换到新标签页；自动启动浏览器（如未启动）                         |
| `extract_content`   | 提取内容     | `query`              | -                                    | query 为 CSS 选择器，返回匹配元素的 tag/text/href；未匹配时返回软错误（retryable），提示检查选择器 |
| `wait`              | 固定等待     | 无                   | `ms`                                 | 固定等待，最多 10000ms，默认 1000ms                                |
| `wait_for_selector` | 等待元素出现 | `query`              | `ms`, `max_elements`                 | query 为 CSS 选择器；最多 30000ms，默认 5000ms；成功后自动等待网络空闲再返回页面状态 |
| `wait_for_text`     | 等待文本出现 | `text`               | `ms`, `max_elements`                 | 等待页面指定文本出现（轮询检测，300ms 间隔）；最多 30000ms，默认 5000ms；仅轮询读取不修改 DOM，只读免确认；成功后自动等待网络空闲再返回页面状态 |
| `click_at`          | 坐标点击     | `x`, `y`             | `max_elements`                       | 直接传入页面坐标进行 CDP 真实鼠标点击（isTrusted=true），无需前置 get_state；适用于坐标可预测的重复性操作（循环答题、分页采集）；对窗口缩放/响应式断点/懒加载位置漂移敏感，动态布局页面优先用 click/click_selector |
| `run_script`        | 批量脚本     | `steps`              | `max_elements`                       | 一次性传入多步操作序列，浏览器端串行执行；steps 每步 action 可选 click_at/wait_for_selector/wait_for_text/wait；任一步骤失败即终止并返回已执行结果；单次总耗时不超过 60s；Node 侧执行保证 isTrusted=true 真实事件 |
| `screenshot`        | 截图         | 无                   | `instruction`                        | 截取当前视口并送视觉模型分析（依赖 vision 模型配置，未配置时返回提示）；instruction 用于指定分析重点 |
| `eval_in_page`      | 页面内执行JS | `script`             | -                                    | 逃生舱：在浏览器上下文执行任意 JS 并返回结果；脚本在 async 函数体内执行，以 `return` 获取返回值（无 return 时返回提示）；语法错误预校验（# 不是注释符用 //）；script 上限 50KB，返回值上限 20KB，超时 10s |
| `launch`            | 启动浏览器   | 无                   | -                                    | 通常自动启动，无需手动调用                                         |
| `close`             | 关闭浏览器   | 无                   | -                                    | 任务完成后可关闭释放资源                                           |
| `get_console_logs`  | 查询控制台日志 | 无                 | `levels`, `include_preserved`, `page_idx`, `page_size` | 默认返回当前导航代的 error/pageerror；翻页用 page_idx；跨导航排查传 include_preserved=true |
| `get_network_logs`  | 查询网络请求 | 无                   | `resource_types`, `only_failed`, `include_preserved`, `page_idx`, `page_size` | 默认仅失败请求；API 排障优先 resource_types=["xhr","fetch"] |
| `get_network_request` | 查看单请求详情 | `request_id`       | -                                    | 返回请求基础信息与错误响应体；requestId 来自 get_network_logs 返回值 |

**安全分级提示**：`get_state`/`screenshot`/`extract_content`/`wait`/`wait_for_selector`/`wait_for_text`/`get_console_logs`/`get_network_logs`/`get_network_request` 为只读操作（SAFE，免确认）；`navigate`/`click`/`click_selector`/`type`/`scroll`/`press_key`/`go_back`/`new_tab`/`eval_in_page`/`click_at`/`run_script` 为操作类（CAUTION，需用户确认）。

### 3.5 动态页面与 SPA 处理策略（关键）

现代网站大量使用单页应用（SPA）和异步加载，`navigate` 完成仅表示 DOM 就绪，不代表内容已渲染完成。以下策略可显著提升动态页面操作成功率：

**场景一：导航后内容未加载**

```
1. navigate(url)                      → domcontentloaded 返回，但元素列表可能为空
2. wait(2000)                         → 等待异步内容渲染
3. get_state                          → 获取实际渲染后的元素列表
```

- `navigate` 后若 `get_state` 返回元素过少或 textContent 为空，说明页面尚未渲染完成
- 此时先 `wait(1500~3000)` 再 `get_state`，不要在空页面上盲目操作

**场景二：点击后结果未出现**

```
1. click(e_login)                     → 触发登录请求
2. wait(2000)                         → 等待响应和页面更新
3. get_state                          → 确认是否登录成功/是否出现错误提示
```

- 点击触发异步操作（提交、搜索、展开）后，必须 `wait` + `get_state` 复查
- 不要连续点击多个元素而不复查——中间状态可能已变化导致后续元素 ID 失效

**场景三：元素在视口外**

```
1. get_state                          → 目标元素不在列表中（elementsTruncated 或在视口外）
2. scroll(down, 500)                  → 向下滚动
3. get_state                          → 新元素进入视口，重新获取 ID
```

- `get_state` 只返回**可见且可交互**的元素（getBoundingClientRect 宽高 > 0 且非 display:none/visibility:hidden）
- 懒加载列表、折叠菜单中的元素需先 `scroll` 或先 `click` 展开后才能获取到

**场景四：弹窗/对话框处理**

```
1. click(e_submit)                    → 触发操作
2. get_state                          → 出现确认弹窗 / 错误提示
3. 根据弹窗内容决策 → click(e_confirm) 或 click(e_close)
```

- 操作后出现的弹窗、toast、模态框会改变 DOM，必须 `get_state` 重新识别

**反模式（避免）**：

- ❌ `navigate` 后立即 `click`——页面可能还没渲染出元素
- ❌ 连续 `click`、`type` 多个元素中间不 `get_state`——ID 已失效
- ❌ 操作失败后用相同参数无限重试——应先 `get_state` 分析当前状态再调整
- ❌ 用 `wait(10000)` 一次等满——分段 `wait` + `get_state` 更高效且能及时响应

### 3.6 type 输入的正确姿势

`type` 操作是**追加输入**，不会自动清空元素现有内容。这是导致表单填写失败的常见原因。

**标准输入流程（清空后输入）**：

```
1. click(e_input)                     → 聚焦目标输入框
2. press_key("Control+A")             → 全选现有内容
3. type(e_input, "新内容")             → 输入会替换选中的内容
```

或使用 Backspace 清空：

```
1. click(e_input)
2. press_key("Control+A") → press_key("Backspace")  → 清空
3. type(e_input, "新内容")
```

**特殊输入场景**：

- **下拉选择框（select）**：`type` 可能无效，应 `click` 展开选项后 `click` 目标选项元素
- **富文本编辑器**：`contenteditable` 元素可用 `type`，但格式化需配合 `press_key`
- **搜索框 + 自动补全**：输入后等待补全列表出现，`get_state` 获取补全项再 `click`
- **密码字段**：`get_state` 返回的 `value` 为空（安全考虑），但仍可用 `type` 输入

### 3.7 元素不可识别时的处理优先级（关键）

当 `get_state` 返回的元素列表中找不到目标元素时，**严格按以下优先级处理，禁止跳级**：

1. **优先：复查 `get_state`** — 目标元素可能在视口外（先 `scroll`）、未渲染完成（先 `wait`）、或被折叠（先 `click` 展开父级）
2. **其次：`click_selector`** — 确认元素存在但未被识别时，用 CSS 选择器直接点击
3. **最后：`eval_in_page`** - 需要复杂 DOM 操作时（如读取 Shadow DOM、多步交互、自定义事件触发），在浏览器上下文执行 JS

**补充：`click_at` 坐标点击的适用场景**：当目标元素位置稳定可预测（如循环答题的固定选项区域、分页采集的"下一页"按钮固定坐标）时，可直接用 `click_at(x, y)` 省去前置 `get_state`。但坐标点击对窗口缩放/响应式断点/懒加载位置漂移敏感，动态布局页面仍优先用 `click`/`click_selector` 定位。

**严禁的回退路径**：

- ❌ 禁止 `write_file` 写 puppeteer/CDP 脚本到工作空间再 `run_command` 执行——这是被明确禁止的污染行为
- ❌ 禁止用 `run_javascript` 尝试操作页面 DOM——`run_javascript` 是 Node 沙箱，非浏览器上下文

`click_selector` 和 `eval_in_page` 已覆盖所有原本需要落盘脚本才能完成的操作，没有任何理由再落盘。

## 4. 与其他工具的协同

### 4.1 与 query_knowledge_base 协同（核心场景）

执行浏览器任务前，先查询本地知识库获取相关信息：

- **登录凭据**：用户可在知识库中存储目标网站的账号密码
- **操作手册**：用户可在知识库中存储目标网站的操作步骤指南
- **测试用例**：用户可在知识库中存储测试用例和预期结果

**示例流程**：

```
1. query_knowledge_base("目标网站登录信息") → 获取账号密码
2. navigate("https://目标网站.com/login")
3. get_state → 获取登录表单元素
4. type(e1, 账号) → type(e2, 密码) → click(e3, 登录按钮)
5. get_state → 验证登录成功
```

### 4.2 与其他工具协同

| 工具              | 协同场景                                                 |
| ----------------- | -------------------------------------------------------- |
| `write_file`      | 采集网页数据后保存到本地文件                             |
| `capture_screen`  | DOM 通道不足时（Canvas/图表）配合视觉分析                |
| `plan`            | 复杂多步骤任务先规划再执行                               |
| `extract_content` | `get_state` 获取元素列表，`extract_content` 提取特定内容 |
| `web_search`      | 先搜索目标网址，再用 `navigate` 打开                     |
| `recall_memory`   | 查询用户关于目标网站的偏好和历史操作记录                 |

## 5. 常见场景示例

### 5.1 结合知识库的自动登录（含清空输入与状态验证）

```
1. query_knowledge_base("XX网站 登录", category_id="work") → 获取凭据
2. navigate("https://example.com/login")
3. wait(1500) → 等待登录页 JS 渲染完成（SPA 常见）
4. get_state → 定位 [e1] placeholder="用户名"、[e2] placeholder="密码"、[e3] text="登录"
5. click(e1) → press_key("Control+A") → type(e1, "username")   ← 清空后输入
6. click(e2) → press_key("Control+A") → type(e2, "password")
7. click(e3)
8. wait(2000) → 等待登录请求完成、页面跳转
9. get_state → 检查 url 是否变化、textContent 是否含用户名/欢迎语等成功标志
   - 失败：识别错误提示元素，向用户报告，不要重复提交（可能触发风控）
```

### 5.2 按操作手册执行

```
1. query_knowledge_base("XX系统操作手册") → 获取步骤
2. 按手册步骤逐步执行，每步严格：
   - navigate/click/type/press_key → wait（如涉及异步）→ get_state → 与手册预期对比
3. 手册步骤中的选择器/文本若与实际不符，以 get_state 结果为准，不要生造 ID
4. write_file → 保存执行结果与截图（如需要）
```

### 5.3 按测试用例验证

```
1. query_knowledge_base("XX功能测试用例") → 获取用例
2. navigate → get_state → 操作 → wait → get_state
3. 对比预期结果（url/textContent/元素存在性）→ write_file 保存测试报告
4. 失败用例：include_screenshot=true 保留现场截图作为证据
```

### 5.4 数据采集（含分页/懒加载）

**单页表格采集**：

```
1. navigate("https://data-source.com/list")
2. wait(2000) → 等待表格数据加载
3. extract_content("table.data tbody tr") → 一次性提取当前页所有行
4. write_file → 保存
```

**分页采集**：

```
1. navigate → wait → extract_content 提取第 1 页数据 → 暂存
2. get_state → 定位"下一页"按钮（text="下一页" 或 ariaLabel）
3. click(e_next) → wait(1500) → extract_content 提取第 2 页 → 追加暂存
4. 循环 2-3，直到"下一页"按钮消失或变为禁用（get_state 中 disabled/无对应元素）
5. write_file → 汇总保存
```

**无限滚动/懒加载采集**：

```
1. navigate → wait → extract_content 提取当前可见项
2. scroll(down, 800) → wait(1500) → extract_content 再次提取
3. 对比两次结果去重；若连续 2-3 次滚动后无新内容，视为到底
4. 注意默认元素上限 100 个（可用 `max_elements` 调整到最多 200），超长列表应分段 scroll + extract，避免依赖单次 get_state
```

### 5.5 复杂网页遇到瓶颈时的回退策略

当发现以下情况，说明超出 DOM 通道能力，应及时切换策略：

| 现象                    | 原因                                 | 应对                                                         |
| ----------------------- | ------------------------------------ | ------------------------------------------------------------ |
| 目标元素反复不在列表中  | 可能在 iframe/Shadow DOM/Canvas 中   | 按 3.7 优先级处理：先 `click_selector` 选择器点击，再 `eval_in_page` 穿透 Shadow DOM/同域 iframe；跨域 iframe/closed Shadow DOM 用 `screenshot` + 视觉判断 |
| textContent 空/仅骨架屏 | 页面依赖 JS 渲染但过慢               | 加大 `wait` 到 3000~5000ms；若仍无内容，用 `screenshot` 确认 |
| click 后无反应          | 组件依赖真实鼠标事件 / 需 hover 展开 | 改用 `press_key`（Enter/Space）触发，或 `scroll` 让菜单展开；若 health 显示失败请求，先 `get_network_logs` 定位是否接口报错 |
| 频繁跳转到验证/风控页   | 触发反爬机制                         | 停止自动化，告知用户手工完成关键步骤后再继续                 |
| 需要文件上传/拖拽       | 当前工具不支持                       | 直接告知用户此步骤需人工操作                                 |

### 5.6 调试排障模式（观测能力闭环）

排查"点击后无反应/白屏/数据未加载"类问题时，用观测 action 定位根因：

```
1. navigate("https://目标站") -> 观察 health 摘要（N 个错误 / M 个失败请求）
2. get_console_logs -> 定位 JS 报错与堆栈
3. get_network_logs(resource_types=["xhr","fetch"]) -> 定位失败 API
4. get_network_request(request_id) -> 读取错误响应体，定位后端报错信息
5. 结合 eval_in_page 验证修复假设或向用户报告根因
```

## 6. 安全约束

- 不自动提交涉及支付、转账、注销、删除数据等敏感操作的表单，先明确询问用户
- 从知识库获取的凭据仅用于当前任务，**不在回复中回显、不写入 write_file**
- 操作类 action（`navigate`/`click`/`click_selector`/`type`/`scroll`/`press_key`/`go_back`/`new_tab`/`eval_in_page`/`launch`/`close`/`click_at`/`run_script`）默认需要用户确认；只读 action（`get_state`/`screenshot`/`extract_content`/`wait`/`wait_for_selector`/`wait_for_text`/`get_console_logs`/`get_network_logs`/`get_network_request`）无需确认
- 凭据类知识库条目建议用户标注 tags 如 `credentials` 便于管理
- 不在公共页面（论坛评论、搜索框等）输入敏感信息
- 浏览器使用隔离的独立用户数据目录（`browser-profile`），不复用用户 Chrome Profile；已登录状态不会跨会话保留
- 登录失败连续 2 次时**停止自动重试**，向用户报告避免触发风控冻结账号
- 涉及验证码、短信验证、二次验证时，向用户说明并等待人工处理，不要模拟绕过
- 严禁为操作浏览器而 `write_file` 写 JS 脚本到工作空间
- 如需在页面执行 JavaScript，必须使用 `eval_in_page` action

## 7. 异常处理

| 失败场景                             | 处理策略                                                                                                                           |
| ------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------- |
| 未检测到 Chrome                      | 提示用户在设置 > 系统通用 > 浏览器自动化 中手动指定路径或安装 Chrome                                                               |
| 元素 ID 不存在                       | 重新调用 `get_state` 获取最新元素列表；不要用旧 ID 重试                                                                            |
| 页面加载超时（>30s）                 | 检查 URL 是否正确、网络是否通畅；用 `wait` + `get_state` 观察是否仅渲染慢                                                          |
| get_state 返回空/元素极少            | 页面可能未渲染完成或依赖懒加载：`wait(2000)` 后重试；仍空则 `include_screenshot=true` 观察                                         |
| 元素被截断（elementsTruncated=true） | 页面元素超当前上限（默认 100，可 `max_elements` 调整）：提高 `max_elements`、改用 `extract_content` 精确提取，或 `scroll` 分段获取 |
| click 无响应                         | 组件可能依赖真实鼠标事件：改用 `press_key`（Enter/Space）；或元素被遮挡，先滚动定位                                                |
| type 后内容错误                      | `type` 是追加输入：先 `press_key("Control+A")` 全选再 `type` 覆盖                                                                  |
| 登录失败                             | 检查凭据是否正确；连续失败 2 次立即停止，避免账号冻结                                                                              |
| 页面结构变化                         | 重新 `get_state` 分析当前页面状态，重新定位目标元素                                                                                |
| 浏览器断开                           | 状态自动清理，下次 `navigate` 会自动重新启动                                                                                       |
| 验证码/风控页                        | 停止自动化，明确告知用户，请求手工完成后再继续                                                                                     |
| click_selector 未命中元素            | 检查 CSS 选择器是否正确；先用 `get_state` 复查页面状态；若元素在 open Shadow DOM / 同域 iframe 内，改用 `eval_in_page` 穿透访问      |
| extract_content 未匹配元素           | 选择器未命中任何元素（软错误 retryable，容 6 次重试）：检查 CSS 选择器是否正确；先用 `get_state` 复查页面结构；注意元素可能在异步加载中，先 `wait` 再重试 |
| eval_in_page 脚本语法错误            | 工具会预校验脚本语法并返回友好错误提示：检查 `#` 不是注释符（用 `//` 或 `/* */`）、括号/引号配对、`await` 必须在 async 上下文         |
| eval_in_page 运行时错误              | 脚本执行异常（如访问不存在的属性）：工具会返回错误名称和消息，可换策略重试                                                           |
| eval_in_page 执行超时                | 脚本可能含死循环或等待过长：精简脚本，避免同步阻塞操作；拆分为多次调用；若脚本已阻塞页面 JS 线程，建议 `close` 浏览器释放后重新 `navigate` |
| eval_in_page 返回值过大              | 返回值已自动截断至 20KB：精简返回数据，只返回必要信息；避免返回整个 DOM 树                                                           |
| eval_in_page 返回值不可序列化        | 脚本返回了 DOM 节点/函数/Symbol 等不可序列化值：确保脚本返回 JSON 兼容类型（字符串/数字/布尔/数组/普通对象）                        |
| screenshot 视觉分析失败              | 视觉模型未配置或调用失败时会返回明确提示（而非静默降级）：检查 vision 模型是否已在设置中配置                                         |
| 需要 open Shadow DOM / 同域 iframe 内元素 | `eval_in_page` 可穿透：用 `element.shadowRoot.querySelector()` 或 `iframe.contentDocument.querySelector()` 访问               |
| 需要跨域 iframe / closed Shadow DOM 内元素 | `eval_in_page` 也无法穿透（同源策略 / closed shadowRoot 为 null）：告知用户此限制或改用截图 + 视觉判断                        |
| 需要文件上传/拖拽/hover              | 当前 action 集合不支持：直接告知用户此步骤需人工完成                                                                               |
| 连续多次同一操作失败                 | **不要无限重试**：系统对连续失败有保护机制--软错误（选择器未命中/等待超时）阈值 6 轮，硬错误（工具崩溃/IPC 异常）阈值 3 轮，触达后 Agent Loop 终止并弹出恢复卡片（可选"从失败处继续"保留上下文或"全部重试"重来）。应切换策略（等待更久、换定位方式、改截图路径）或向用户报告阻塞点 |
| `wait_for_text` 超时                 | 文本未在超时内出现：检查文本是否正确（注意空格/大小写/全半角）；适当增大 `ms`（最大 30000）；用 `get_state` 复查页面实际文案；为软错误（retryable），容 6 次重试 |
| `click_at` 点击无反应/误点           | 坐标漂移：窗口缩放/响应式断点/懒加载会导致坐标变化；改用 `click`/`click_selector` 通过元素定位；或先 `get_state` + `screenshot` 确认元素实际位置后再 `click_at` |
| `run_script` 步骤失败终止            | 查看返回的步骤执行结果，定位失败步骤索引与错误：修正该步骤参数后重新执行整个脚本，或改用单步 action 逐步执行排查；整体超时（60s）时减少步骤数或缩短单步等待 |
| `run_script` 整体超时                | 步骤过多或单步等待过长：精简步骤序列，单次总耗时不超过 60s；将长等待拆分为多次 `run_script` 调用；wait 步骤最多 10000ms，wait_for_* 步骤默认 5000ms 最大 30000ms |
| `get_network_request` requestId 不存在 | 硬错误（不可重试）：不要用同一 requestId 重试，先重新 `get_network_logs` 获取有效 requestId（旧条目可能已被环形缓冲淘汰） |
| 观测日志为空                          | 页面无错误或已被淘汰：传 `include_preserved=true` 查询最近 3 代记录排查跨导航问题 |
| 响应体为空                            | 未预缓存或成功响应：仅预缓存错误响应体（xhr/fetch 且状态码 >= 400，最近 20 条），成功响应体不可查 |
