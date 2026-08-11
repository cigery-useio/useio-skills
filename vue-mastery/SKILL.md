---
name: vue-mastery
description: Vue 3 expert skill for writing production-grade code. Covers Composition API, script setup, reactivity, component architecture, state management, testing, performance, Tailwind, and Nuxt. Compatible with Vue 3.3+. Load for any Vue, .vue, Pinia, Vue Router, or Nuxt work. ALWAYS use Composition API with `<script setup lang="ts">` unless the project explicitly requires otherwise.
license: MIT
version: "1.0.0"
---

# Vue Mastery

> 基于 Vue 3.3+。始终使用 Composition API + `<script setup lang="ts">`。3.4+ 和 3.5+ 的新 API 在 references 中标注版本要求，使用前确认项目版本。

## 核心原则

1. **单一数据源，其余皆派生。** 保持状态最小化（`ref`/`reactive`），用 `computed` 派生其余一切。watcher 仅用于副作用。
2. **Props 向下，Events 向上。** 通过 `defineProps`/`defineEmits` 建立显式、类型安全的契约。`v-model` 仅用于真正的双向绑定。
3. **组件小而专注。** 每个组件只做一件事。当组件有 3+ 个独立 UI 区域、重复的模板块、或混合了编排逻辑与展示层时，必须拆分。
4. **逻辑放 composables，不放组件。** 将复用、有状态、或副作用重的逻辑提取到 `useXxx()` composable 中。组件只负责渲染和交互。
5. **性能优化是功能完成后的步骤。** 核心行为验证通过之前不要优化。
6. **测试行为，不测实现。** 优先断言可观察的输入/输出。`wrapper.vm` 仅作为最后手段。
7. **全面使用 TypeScript。** 为 props、emits、composables、stores 强类型标注。优先显式类型而非推断。

## 工作流

按以下步骤顺序执行。仅当任务范围明确不需要某步骤时可跳过。

### Step 1: 确认架构

- 默认技术栈：Vue 3 + Composition API + `<script setup lang="ts">`。
- 如果项目明确使用 Options API 或 JSX，适配项目约定——不要未经询问就切换。
- **加载 `references/component-architecture.md`** — 任何非简单组件工作都必读，整个任务期间保持活跃上下文。

### Step 2: 设计组件边界

编码任何非简单功能前，先创建简要的组件地图：

- 用一句话定义每个组件的单一职责。
- 保持入口/根组件和路由级 view 作为**组合层**（应用外壳、provider 接线、功能组合）。不要在入口/根/view 组件中放置完整功能实现。
- 为每个子组件定义 props/emits 契约。
- 添加 2+ 个组件时，优先使用功能文件夹布局（`components/<feature>/...`、`composables/use<Feature>.ts`）。

**满足以下任一条件时必须拆分组件：**

- 同时拥有编排/状态管理 AND 多个区域的展示性模板。
- 有 3+ 个独立 UI 区域（如：表单、筛选器、列表、底部栏/状态）。
- 存在重复的或可复用的模板块（列表行、卡片、列表项）。

对于 CRUD/列表功能（todo、table、catalog、inbox），至少拆分为：容器组件、输入/表单组件、列表/项组件、底部/操作组件。仅允许在极小的临时 demo 中使用单文件实现——若选择此方案，需明确说明为何不需要拆分。

### Step 3: 实现核心

应用 `references/component-architecture.md`（Step 1 已加载）中的基础规范：

- SFC 区域顺序：`<script setup>` → `<template>` → `<style scoped>`。
- 保持状态最小化，用 `computed` 派生。避免在模板中重复计算昂贵逻辑。
- 保持模板声明式；将分支/派生逻辑移到 script 中。
- 应用 Vue 模板安全规则（`v-html`、列表渲染、条件渲染选择）。
- **加载 `references/reactivity-system.md`** — 涉及 ref、watcher、computed 或 Vue 3.5 API 时。

### Step 4: 添加可选特性（仅当需求明确需要时）

不要默认添加。仅当需求存在时加载对应 reference：

| 需求 | Reference |
|------|-----------|
| Slots、fallthrough attrs、KeepAlive、Teleport、Suspense、Transition/TransitionGroup、指令、异步组件、render 函数、plugins | `references/built-in-components.md` |
| 全局/共享状态、Pinia stores、provide/inject、Vue Router | `references/state-management.md` |
| Tailwind CSS、scoped styles、响应式/暗色模式 | `references/styling-guide.md` |
| Nuxt SSR、auto-imports、useAsyncData、server routes | `references/nuxt-patterns.md` |

### Step 5: 编写测试

**加载 `references/testing-strategies.md`** — 创建或审查测试时。

- 每个测试只测一个行为。
- 优先断言可观察的输入/输出（渲染文本、emit 的事件、store 状态变化）。
- 组件测试用 `createTestingPinia`；纯 store 测试用 `createPinia()`。
- `wrapper.vm` 仅当 DOM/emit/prop/store 断言都无法表达行为时才使用。

### Step 6: 性能优化（行为正确之后）

**加载 `references/performance-optimization.md`** — 仅当识别到或可能出现性能问题时：

- 大列表渲染瓶颈 → 虚拟化。
- 静态子树不必要重渲染 → `v-once`/`v-memo`。
- 热列表路径中过度抽象 → 扁平化组件树。
- 昂贵的更新触发过于频繁 → 优化 `updated` hook。

### Step 7: 自检

- [ ] 核心行为正常且符合需求。
- [ ] 状态最小化且可预测；派生值使用 `computed`。
- [ ] SFC 结构遵循 `<script setup>` → `<template>` → `<style>` 顺序。
- [ ] 组件专注且拆分合理；拆分决策有据可依。
- [ ] 入口/根和路由 view 组件保持为组合层。
- [ ] 数据流契约显式且类型安全（`defineProps`、`defineEmits`）。
- [ ] 复用/复杂度合理时使用 composables；状态/副作用已移出组件。
- [ ] 可选特性仅在需求明确时使用。
- [ ] 测试断言行为而非实现细节。
- [ ] 性能优化仅在功能完成后进行。

## 版本适配与防幻觉策略

### 版本检测

编码前先检查项目的 Vue 版本（`package.json` 中的 `vue` 依赖），根据版本确定可用 API。本技能以 Vue 3.3+ 为基准，references 中标注了 3.4+ 和 3.5+ 新 API 的最低版本要求，使用前确认项目版本满足要求。

### 版本差异速查表

| API | 最低版本 | 不满足时的降级方案 |
|-----|---------|-------------------|
| `defineModel()` | 3.4+ | `modelValue` prop + `update:modelValue` emit |
| 响应式 props 解构 | 3.5+ | `props.xxx` 访问或 `toRefs()` |
| `useTemplateRef()` | 3.5+ | `ref()` + `ref="xxx"` 模板属性 |
| `onWatcherCleanup()` | 3.5+ | watcher 回调的 `onCleanup` 参数 |
| `useId()` | 3.5+ | 自定义 ID 生成（`crypto.randomUUID()` 或计数器） |
| `watch` `deep: N` | 3.5+ | `deep: true`（无深度限制） |
| `watch` `once: true` | 3.4+ | 手动调用返回的 `stop()` |
| `watch/watchEffect` `pause/resume` | 3.5+ | 手动控制（条件变量 + `stop()`） |
| `defineOptions()` | 3.3+ | 额外的 `<script>` 块声明选项 |
| `defineSlots()` | 3.3+ | 无类型提示，直接使用 `$slots` |
| 泛型组件 `generic` | 3.3+ | 用 `any` 或函数式类型推断 |
| `toValue()` | 3.3+ | `unref()` + 手动判断 getter |
| `Teleport defer` | 3.5+ | `nextTick()` 后手动操作 DOM |
| `hydrateOnVisible()` | 3.5+ | 不使用懒水合，正常水合 |

### 查证策略

当不确定某个 API 在特定版本的行为、或不确定某个 API 是否存在时，**不要凭记忆猜测**，按以下优先级查证：

1. **优先使用 Context7 MCP**（如果环境可用）：
   - 用 `mcp__context7__resolve-library-id` 搜索 "Vue" 或 "Vue.js"
   - 用 `mcp__context7__query-docs` 查询具体 API 的文档和示例
   - 这是最权威的实时文档查询方式

2. **使用 web_search**：
   - 搜索 "Vue 3.x [API名称] documentation" 或 "Vue [API名称] version support"

3. **查看项目源码**：
   - 检查 `node_modules/vue/package.json` 确认实际安装版本
   - 检查 `node_modules/vue/dist/*.d.ts` 类型定义确认 API 是否存在

### 防幻觉原则

- **不确定就查证**：宁可多查一步，不要凭记忆生成可能错误的 API 用法。
- **版本标注优先**：references 中所有版本敏感的 API 都标注了最低版本，使用前必须确认。
- **降级方案明确**：上表提供了每个 API 的降级方案，当项目版本不满足时使用替代方案。
- **代码示例验证**：生成的代码如果使用了版本敏感的 API，在输出时标注所需最低版本。

## 反模式速查表

| 反模式 | 为什么错 | 正确做法 | 详见 |
|--------|---------|---------|------|
| `v-if` + `v-for` 同元素 | 执行顺序歧义 | 用 computed 过滤数组 | component-architecture.md |
| `v-for` key = 数组索引 | 重排序时状态错乱 | 用稳定的数据库 ID | component-architecture.md |
| 直接修改 props | 违反单向数据流 | emit 事件或用 `v-model` | component-architecture.md |
| `reactive()` 用于可替换状态 | 替换时响应性丢失 | 用 `ref()` | reactivity-system.md |
| 解构 `reactive()` 对象 | 解构字段失去响应性 | 用 `toRefs()` 或 `ref()` | reactivity-system.md |
| `watch()` 解构后的 prop（Vue 3.5+） | 编译时错误 | 用 getter：`watch(() => prop, ...)` | reactivity-system.md |
| watcher 无清理 | 内存泄漏、竞态条件 | `onWatcherCleanup()` 或 watcher `onCleanup` | reactivity-system.md |
| `v-html` 渲染用户内容 | XSS 漏洞 | 用 DOMPurify 消毒 | component-architecture.md |
| Vue 3 中使用 Mixins | 不透明、易冲突 | 用 composables 替代 | component-architecture.md |
| composable 中模块级副作用 | 跨实例共享 | 在 `onMounted` + `onUnmounted` 中作用域化 | component-architecture.md |
| 新 Vue 3 代码用 Options API | 生态已迁移 | 用 `<script setup>` | — |
| 功能未完成就优化 | 过早增加复杂度 | 行为正确后再优化 | performance-optimization.md |
| 模板引用用普通 ref（Vue 3.5+） | 无动态 ref 支持、脆弱 | 用 `useTemplateRef()` | reactivity-system.md |

## References 索引

| 文件 | 何时加载 | 主题 |
|------|---------|------|
| `references/component-architecture.md` | **始终**（任何组件工作） | SFC 结构、script setup 宏、props/emits/v-model、组件拆分触发条件、composables 设计 |
| `references/reactivity-system.md` | 涉及 ref、watcher、computed 或 3.5 API | ref/shallowRef、computed、watch/watchEffect、effectScope、Vue 3.5 新 API |
| `references/built-in-components.md` | 使用 Transition、Teleport、Suspense、KeepAlive、v-memo、指令、异步组件、Slots、fallthrough attrs、render 函数、plugins | 所有内置组件和指令、Slots |
| `references/state-management.md` | 全局/共享状态、Pinia stores、provide/inject、Vue Router | 状态管理决策表、Pinia setup store、provide/inject、Vue Router |
| `references/testing-strategies.md` | 创建或审查测试 | Vitest、Vue Test Utils、Pinia 测试、行为优先断言 |
| `references/performance-optimization.md` | 性能优化 | 虚拟列表、v-memo/v-once、组件抽象、updated hook |
| `references/styling-guide.md` | Tailwind 样式、scoped CSS | Tailwind 工具类、响应式、暗色模式、class 可读性 |
| `references/nuxt-patterns.md` | Nuxt SSR 项目 | auto-imports、useAsyncData、server routes、runtime config |

## 相关技能

- `typescript` — TypeScript 最佳实践在 Vue 项目中的应用
- `accessibility` — ARIA、语义化 HTML、焦点管理
