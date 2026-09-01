---
name: frontend-guidelines
description: AI 开发 Web 前端时应遵循的规范指引。当 Agent 执行前端开发任务（写组件、页面、样式、状态管理、构建配置、调试前端代码）时，加载本技能获取与最新主流 LLM 训练数据互补的规范约束：覆盖技术栈版本基线、AI 常见缺陷模式防御、代码质量红线、样式与界面设计质量（去 AI 味）、验证闭环流程。加载后按第 4 章工作流约束每一次代码生成行为。
triggerKeywords: [前端规范, AI前端开发, 前端代码规范, 前端验收标准, 前端最佳实践, AI写前端, 前端开发规范, 去AI味]
version: 1.0.0
---

# AI 前端开发规范指引

## 1. 技能概述

**角色定位**：本技能是一份面向 AI Agent 的前端开发规范指引。当 Agent 执行任何 Web 前端开发任务（编写组件、页面、样式、状态逻辑、构建配置，或修改调试前端代码）时，本技能作为行为约束层生效，确保产出代码符合工程标准、规避 AI 生成代码的典型缺陷模式，并与最新主流 LLM 训练数据形成互补。

**核心价值**：主流 LLM 的训练数据存在时间差，可能输出过时的 API、已废弃的写法或不符合当前生态惯例的模式。本技能固化了一份版本基线与缺陷防御清单，Agent 加载本技能后，应以本技能的版本基线覆盖 LLM 训练数据中的旧认知，以缺陷防御清单约束代码生成行为。

**适用场景**：
- Agent 编写 React/Vue/Next.js/Nuxt 等前端组件或页面
- Agent 编写前端样式（原子化 CSS、SCSS 等）
- Agent 搭建或调整前端工程配置（构建、路由、状态管理）
- Agent 调试、重构、审查前端代码
- 用户要求"按规范写前端""遵循前端最佳实践""检查 AI 生成的前端代码"

**不适用**：非前端任务（后端、脚本、数据处理等）不加载本技能；用户有明确项目级规范文件（如项目内 CLAUDE.md / .cursorrules / 项目规范文档）时，项目级规范优先，本技能作为基线补充。

**技术栈中立**：本技能的条款按适用范围绑定执行——标注具体框架/库的条款仅在使用该技术时生效，未标注的条款适用于任意前端技术栈；文中出现的库名与组件名（antd、IoButton 等）仅为示意，以项目实际依赖为准。

**版本策略**：本文档版本基线更新至 2026-09，基于 2025-2026 前端生态现状编写。当 LLM 的训练数据与本技能冲突时，先核对项目实际安装版本（读 package.json），无法核对时以本技能为准。本基线具有时效性：若当前时间距基线版本超过 6 个月，或任务涉及基线未覆盖的新版本特性，应先通过官方文档/Context7 校准认知后再写代码，并顺带更新本表。

## 2. 版本基线（2026-09）

> LLM 的训练数据存在时间差。写代码前，先以本节校准认知；项目实际安装版本始终优先于本表，动手前读 `package.json` 核对。

### 2.1 框架版本现状

| 技术 | 当前主线版本 | 关键事实（训练数据盲区） |
|------|------------|------------------------|
| React | 19.x | Server Components 成熟；React Compiler 已发布 1.0 稳定版，启用后自动 memoization（替代手动 useMemo/useCallback），是否启用以项目配置为准；use() API 读取 Promise/Context |
| Next.js | 15/16.x | server-first 架构成熟；App Router 为默认方案；Pages Router 已进入维护模式，新项目不再使用；Turbopack 在新项目中为默认构建器 |
| Vue | 3.5+ | reactive props destructure 稳定；Composition API 是唯一推荐范式；Options API 仅维护，新代码禁用 |
| Vue 3.6 / Vapor Mode | 3.6+ | Vapor Mode（无虚拟 DOM 编译策略）随 3.6 落地，采用项目需明确升级，未升级的项目仍按标准 Virtual DOM 模型写代码 |
| Nuxt | 4.x | 目录结构调整为 app/ 目录为应用根；服务端路由与数据获取范式继续强化 |
| TypeScript | 5.x | 严格模式为默认建议；satisfies、const type parameters 已稳定可用 |
| Vite | 6/7/8 | 大版本迭代快；Vite 8 集成 Rolldown；Environment API 用于多环境构建 |
| Tailwind CSS | v4 | CSS-first 配置（@theme 指令，无 tailwind.config.js）；Vite 项目用 @tailwindcss/vite 插件（不再用 PostCSS 配置）；Oxide 引擎 |
| UnoCSS | 0.66+ | Tailwind 兼容语法；写代码前先检查 uno.config.* 了解 preset/shortcuts，配置不明时仅用基础 class 用法 |
| ESLint | v9+ | flat config（eslint.config.js）为唯一配置格式，.eslintrc 已废弃 |
| React Router | v7 | 框架模式与 library 模式并存；类型安全路由 |
| Node.js | 22/24 LTS | 前端工具链的主流运行环境要求 |

> 本表未覆盖的技术栈（Svelte/SvelteKit、Angular、SolidJS、Astro 等）同样适用本技能全部原则：动手前读 package.json 确认版本，API 用法查证后使用。

### 2.2 deprecated API 防幻觉清单

以下是 LLM 因训练数据滞后最容易写出的过时/错误 API。**写出以下任何一项即为缺陷，必须修正**：

| 框架 | 禁止写出（过时） | 应使用（当前） | 说明 |
|------|----------------|--------------|------|
| React | `useMemo`/`useCallback` 包裹所有计算与回调 | 仅在确有性能问题时使用；React Compiler 启用时无需手动 memo | React 19 + Compiler 下手动 memo 化是冗余代码 |
| React | 类组件、`componentDidMount` | 函数组件 + hooks | 类组件仅维护不推荐 |
| React | 字符串 ref；用 `React.forwardRef` 包裹普通函数组件 | `ref` 作为普通 prop 直接传递（React 19 起 function 组件原生支持 ref prop） | 仅 ref 向下转发场景需要关注，普通元素 `ref={xxx}` 用法不受影响 |
| React | `ReactDOM.render` | `createRoot`（react-dom/client） | React 18+ 唯一入口 |
| Next.js | Pages Router（`pages/` 目录、`getServerSideProps`/`getStaticProps`） | App Router（`app/` 目录、Server Components 异步组件直接 `await`） | Pages Router 已维护模式；`getServerSideProps` 在 App Router 中不存在 |
| Next.js | `'use client'` 文件顶部滥用 | 默认 Server Component，仅叶子交互组件标注 `'use client'` | 交互边界尽量下沉到叶子节点 |
| Next.js | `next/head` | App Router 的 metadata API（`export const metadata` / `generateMetadata`） | Pages Router 专属 API |
| Next.js | `useRouter` from `next/router` | `useRouter` from `next/navigation` | App Router 的路由 hook 来源不同 |
| Vue | Options API（`data()/methods/computed`） | `<script setup>` + Composition API | 新代码禁用 Options API |
| Vue | `defineComponent` + 显式 `setup()` | `<script setup lang="ts">` | 最简范式 |
| Vue 2 残留 | `$set`、`$on`、`$children`、filters | 响应式直接赋值、emit、composable | Vue 3 已移除 |
| Vue | `this` 访问 props/data | `defineProps`/`defineEmits` 编译宏 | 无 this 上下文 |
| Tailwind | `tailwind.config.js` + `theme.extend` | CSS-first：`@theme { --color-brand: #xxx; }` | v4 无配置文件 |
| Tailwind | PostCSS 插件方式接入 Vite | `@tailwindcss/vite` 插件 | v4 官方推荐 |
| ESLint | `.eslintrc.*` | `eslint.config.js`（flat config） | v9 起唯一格式 |
| Node | CJS `require` 编写新前端代码 | ESM（import/export） | 新代码一律 ESM |

> 使用策略：写出上表左列任意项时，先核对项目实际版本（读 package.json 确认主版本号），确认项目确实使用新版本后再修正；若项目锁定旧版本，遵循项目现状并在交付说明中提示升级建议。

## 3. AI 生成前端的缺陷防御（红线清单）

> 以下是 AI 生成前端代码的高频缺陷模式。每一条都是硬约束，编码时逐条自检；违反任何一条都构成交付缺陷。

### 3.1 正确性红线

- **禁止 API 幻觉**：不确定的 API 用法，必须先查证（读项目 node_modules 类型定义、查 Context7 文档、web_search），禁止凭训练数据记忆直接写。第三方库 API 与预期不符时，先核对项目实际安装版本与官方 changelog，不要按记忆臆测用法
- **禁止臆造配置项**：构建工具配置（vite.config / eslint.config / tsconfig）中的选项必须查证存在性，不存在的配置项会导致静默失效或报错
- **版本核对前置**：使用任何库的"新特性"前，先读 package.json 确认版本号支持该特性
- **禁止混用范式**：同一项目内不得混用 Options API 与 Composition API、CJS 与 ESM、CSS Modules 与原子类（项目已有惯例除外）

### 3.2 安全红线

- **敏感信息不硬编码**：密钥、Token、内网 API 地址不写入源码；前端无法真正保密，密钥类操作走后端或服务端代理
- **XSS 防御**：React/Vue 模板默认转义，禁止使用 `dangerouslySetInnerHTML` / `v-html` 渲染用户输入内容；确需渲染富文本时必须 DOMPurify 消毒
- **URL 拼接注入**：拼接 URL/query 参数必须 encodeURIComponent，或用 URLSearchParams
- **依赖安全**：不引入无维护的 npm 包，引入新依赖前评估维护状态、体积与安全记录；CDN 资源（脚本/字体/图标库）一律禁止引入（本地打包）
- **CSP 友好**：避免 inline script 注入和 eval 类动态执行

### 3.3 质量红线

- **类型安全**：TypeScript 项目禁止 `any`（含隐式 any）；禁止 `@ts-ignore`；不确定类型用 `unknown` + 类型收窄；善用 `Pick`/`Omit`/`Partial` 工具类型
- **函数设计**：单一职责；函数体不超过 50 行；参数不超过 3-4 个（超过则引入参数对象）；提前返回减少嵌套（嵌套不超过 3 层）
- **命名**：描述性命名，布尔值 is/has/can 前缀；组件 PascalCase；变量/函数 camelCase；常量 UPPER_SNAKE_CASE；存储字段（IndexedDB 表/字段、localStorage key）使用 snake_case
- **DRY 与依赖复用**：写代码前先检查项目现有依赖与工具函数是否已提供该能力，禁止重复造轮子；重复两次以上的逻辑提取为 composable/hook 或工具函数
- **错误处理**：所有异步操作必须 try-catch（或 .catch），catch 块不得为空或仅 console.log；错误信息需具体可定位；用户侧错误用统一的错误 UI 呈现
- **单一职责文件**：单文件原则上不超过 600 行，超出时审视职责、抽取独立模块
- **注释原则**：注释说明"为什么"而非"做什么"；删除显而易见的注释；不保留被注释掉的代码
- **现代化语法**：可选链 `?.`、空值合并 `??`、解构、模板字符串、数组方法替代命令式循环；函数定义优先箭头函数，仅在需要自身 this 时用传统函数
- **死代码清理**：移除未使用的导入、变量与不可达分支
- **格式化托管**：缩进、引号、行宽（≤100 字符）、import 排序交由 Prettier/ESLint 统一处理，不手工风格化
- **输入校验**：外部输入（API 响应、表单、URL 参数）用 zod 等运行时校验，禁止盲信外部数据结构

### 3.4 状态与数据获取规范

- **服务端状态与客户端状态分离**：服务端数据请求优先用项目既有方案（如 TanStack Query/SWR 或框架自带数据层），无既有方案时按当前生态主流选择；URL 状态放 searchParams；跨组件客户端状态用项目既有状态库（Zustand/Pinia 等）；能用组件本地 state 解决的不上全局状态库
- **禁止 prop drilling**：超过 2 层传递考虑组合/Context/状态库
- **请求防重与竞态**：搜索/筛选类请求必须有防抖与竞态处理（AbortController 或请求 ID 忽略过期响应）
- **乐观更新**：列表编辑类操作可乐观更新 + 失败回滚
- **React Server Components 边界**：数据获取留在 Server Component，`'use client'` 只标叶子交互组件，状态尽量靠近使用处

### 3.5 样式规范

- **样式方案跟随项目**：项目已有原子类（UnoCSS/Tailwind）则沿用；新项目默认原子类 + 少量 scoped 样式混合
- **UnoCSS 像素单位**：项目约定尺寸类原子类必须带 px 单位时（`px-16px`、`text-14px`），严格遵守，禁止不带单位的简写（`px-4`、`text-sm`）；项目无此约定时跟随项目预设默认用法
- **Tailwind v4 CSS-first**：主题扩展用 `@theme` 指令写进 CSS，不建 tailwind.config.js
- **样式层级**：原子类处理布局/间距/颜色；复杂复用样式抽 shortcuts（UnoCSS）/ @apply（Tailwind）或组件化；SCSS 嵌套不超过 3 层
- **主题适配跟随项目**：项目已启用多主题或默认深色时，新组件必须覆盖全部已启用主题（默认深色的项目以深色为基准样式，浅色用 light:/dark: 前缀适配）；项目为单主题时遵循现状，禁止擅自引入主题切换能力
- **响应式**：移动端优先；断点类统一使用框架预设断点
- **禁止 CDN 资源**：字体、图标、脚本一律本地打包，不引外链
- **图标统一**：项目有统一图标组件时必须使用，禁止散装 SVG/图标字体混用
- **动态类名**：禁止在 JS 中运行时拼接原子类名（构建期无法提取）；动态样式用 safelist 预登记或内联 style 实现

### 3.6 可访问性规范（a11y）

- 语义化标签优先（nav/main/section/button），禁止 div 模拟按钮
- 可交互元素可键盘操作（Tab 焦序、Enter 触发）
- 图片有 alt，表单控件有关联 label
- 对比度满足 WCAG AA（4.5:1 文本）

### 3.7 性能规范

- **渲染性能**：长列表虚拟滚动（万级数据项）；重计算用 useMemo/计算属性（React Compiler 启用项目可省略）；图片懒加载 + 显式宽高防 CLS
- **包体积**：路由级代码分割（dynamic import/defineAsyncComponent）；分析依赖体积（Bundle Analyzer）；按需引入（`import { Button } from 'antd'`），避免整包引入
- **核心 Web 指标**：LCP 元素优先加载，INP 控制交互阻塞（长任务切片），CLS 预留媒体尺寸

### 3.8 界面设计质量（去 AI 味）

> AI 生成的 UI 极易落入千篇一律的默认审美（业界称 AI slop），新写界面时必须先有设计意图，再有实现。

- **禁止 AI slop 默认组合**：紫色渐变 + Inter/Roboto 默认字体 + 默认蓝主色 + 白卡片浅灰阴影 + 全部居中布局 + hover 缩放 1.02，此组合出现即视为设计缺陷
- **设计意图前置**：新页面/独立界面先明确两个问题再动手——Purpose（给谁用、解决什么场景）与 Tone（设计调性选一个贯彻到底：极简/杂志编辑/科技感/高端质感/复古未来等），并确定一个记忆锚点（独特色彩/动效/布局细节）
- **字体配对**：展示字体（标题）与易读正文字体成对选择，拒绝无性格的默认字体；项目已有字体规范则沿用
- **色彩纪律**：一个主导色 + 单一锐利强调色，优于多色均分；色彩用设计令牌管理（Tailwind v4 写进 @theme，UnoCSS 写进 uno.config theme，通用场景用 CSS 变量）
- **动效克制**：CSS transition 优先；入场交错渐显（staggered reveal）优于零散微交互；动效服务于信息层级而非装饰；必须尊重 prefers-reduced-motion
- **布局有意图**：避免千篇一律的等距三卡片网格；用留白、非对称、密度对比建立层级
- **背景氛围**：噪点纹理/渐变网格/几何图案/层叠透明度优于纯色背景+卡片阴影的俗套
- **跟随项目**：项目已有设计系统/UI 组件层时沿用既有规范，以上原则仅用于新独立界面或无设计系统的场景

### 3.9 禁止事项速查（Top 违规）

1. ❌ 硬编码密钥/Token/内网地址
2. ❌ `v-html`/`dangerouslySetInnerHTML` 渲染用户输入
3. ❌ 空 catch 或仅 console.log
4. ❌ `any` / `@ts-ignore`
5. ❌ 过时 API（见 2.2 清单）
6. ❌ CDN 外链资源
7. ❌ 不存在的配置项/臆造的库方法
8. ❌ 重复造轮子（项目已有同能力依赖）
9. ❌ prop drilling 超过 2 层不处理
10. ❌ 表单/接口数据不做运行时校验直接使用

## 4. 执行工作流

Agent 执行前端开发任务时，按以下工作流约束每一次代码生成：

### Step 1：环境感知（每次任务开始）

1. 读 `package.json`（monorepo 项目定位到对应子包）：确认框架与主要依赖的实际版本，版本基线（第 2 章）仅在校准认知时使用，项目实际版本优先
2. 识别样式方案：uno.config.* / tailwind 配置 / 全局样式目录，确定要遵循的样式约定
3. 识别项目惯例：目录结构、组件命名、状态管理方案、请求封装方式，新代码必须与项目现有惯例一致
4. 检查项目级规范文件（CLAUDE.md / .cursorrules / docs 下的规范文档），有则以项目规范优先

### Step 2：生成前自检

1. 本次要写的内容是否命中第 3 章红线清单？逐条核对
2. 是否需要使用不确定的 API？不确定的先查证（Context7 / 官方文档 / node_modules 类型定义）
3. 是否与项目既有依赖重复？先复用
4. 拆分实现顺序：先数据流与类型定义，再业务逻辑，再 UI 层，最后样式

### Step 3：代码生成约束

1. 遵循第 3 章全部红线
2. 新文件遵循项目目录结构惯例；单文件不超 600 行
3. 组件设计：单一职责、props 类型完整、事件命名语义化、插槽/children 优先于配置式 props
4. 模板书写规范：少属性单行、多属性（>3）逐行换行；v-if/v-show 置于属性最前；无插槽内容用自闭合标签（Vue）
5. 不确定处宁可不写，标注 TODO 并在交付说明中明示，禁止臆造补全
6. 组件层级约束：项目存在统一 UI 组件层（如基于第三方库二次封装的自定义前缀组件）时，业务页面必须使用封装组件，禁止绕过封装直接引入第三方 UI 库组件；需新增封装时先检查现有组件并与用户确认
7. 模块边界：视图模块之间禁止直接引用对方组件/composables，共享逻辑上浮至公共目录，保证模块可独立插拔
8. 新页面/独立界面先完成设计决策（场景→调性→记忆锚点，见 3.8），避免落入 AI slop 默认组合

### Step 4：生成后验证闭环

1. **静态检查**：运行项目的 typecheck（tsc --noEmit / vue-tsc）与 lint，零错误后才算完成
2. **构建验证**：改动涉及构建配置/依赖/入口文件时，运行项目 build 验证
3. **最小运行验证**：涉及页面/组件渲染的改动，启动 dev server（persistent 模式）并通过浏览器自动化工具验证渲染结果与控制台无错误
4. **交付说明**：说明改动范围、验证手段与遗留项（TODO/已知限制）

### Step 5：交付标准

一次前端开发任务的完成定义：代码写入 + 静态检查通过 + 构建验证通过（如涉及）+ 运行验证通过（如涉及页面渲染）。未完成验证闭环时，必须明示"未验证"及原因，不得宣称"已完成"。

## 5. 输出规范

### 5.1 交付物构成

前端开发任务的交付物按任务类型区分：

| 任务类型 | 交付物 |
|---------|--------|
| 新功能开发 | 代码文件 + typecheck/lint 通过 + 构建通过（如涉及）+ 渲染验证结论 |
| Bug 修复 | 修复代码 + 根因说明 + 回归验证结论 |
| 重构/清理 | 重构后代码 + 行为未变证明（typecheck/build/测试）+ 前后对比说明 |
| 代码审查 | 问题清单（按严重程度分级）+ 修复建议 + 可选的修复代码 |

### 5.2 代码审查输出格式（审查任务适用）

1. **发现的问题**：按严重程度分级（P0 阻断 / P1 严重 / P2 一般 / P3 建议）
2. **修复后的代码**：重构版本或补丁
3. **解释说明**：修改内容及原因
4. **前后对比**：关键改动并排对比
5. **进一步优化建议**：可选增强项

## 6. 异常处理

- **package.json 缺失、定位不到（含 monorepo 子包场景）或非前端项目**：提示用户确认项目路径/子包位置后继续
- **项目版本与本技能基线冲突**：项目实际版本优先，按项目版本写代码，交付说明中提示版本过旧风险
- **查证工具不可用（无网络/文档工具失败）**：改用 node_modules 中的 .d.ts 类型定义查证 API；仍无法确认时，明确告知用户"此 API 用法未经查证"，不臆造
- **验证环节失败**：typecheck/lint 报错必须修复后重新验证；无法修复时如实说明阻塞点，不得静默跳过验证
- **用户指令与本技能冲突**：用户明确要求优先（如明确要求写 `any`），可执行但简短提示风险，不反复劝阻

## 7. 质量自检清单（Agent 交付前逐项核对）

- [ ] 已读 package.json，版本认知与项目实际一致
- [ ] 未命中 2.2 deprecated 清单中的任何过时 API
- [ ] 未命中 3.9 速查清单中的任何禁止项
- [ ] 异步操作全部有错误处理，catch 非空
- [ ] 无 any、无 @ts-ignore
- [ ] 无硬编码敏感信息、无 CDN 外链
- [ ] 运行时校验已覆盖外部输入（如适用）
- [ ] 样式遵循项目既有方案（UnoCSS px 单位 / Tailwind v4 @theme）
- [ ] typecheck / lint 已运行且零错误
- [ ] a11y 基本项已满足（语义化标签/alt/label/键盘可操作）
- [ ] 新界面有明确设计意图，未落入 AI slop 默认组合（如适用）
- [ ] 验证闭环完成，未验证项已明示
