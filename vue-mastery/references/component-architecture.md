# 组件架构

> 任何 Vue 组件工作都必读。整个任务期间保持活跃上下文。

## 项目结构

### 推荐布局（Feature-First）

```
src/
├── api/              # API 客户端和端点定义
├── assets/           # 静态资源（图片、字体、图标）
├── components/       # 共享/复用组件
│   ├── base/         # 基础 UI 原语（Button、Input、Modal）
│   └── features/     # 功能特定共享组件
├── composables/      # 复用 Composition API 逻辑
├── layouts/          # 页面布局（可选）
├── pages/            # 路由级页面组件
├── router/           # Vue Router 配置
├── stores/           # Pinia stores
├── types/            # TypeScript 类型定义
├── utils/            # 纯工具函数
└── App.vue           # 根组件
```

### 文件命名约定

| 约定 | 适用场景 |
|------|----------|
| `PascalCase.vue` | 所有组件（`vue/multi-word-component-names` 强制） |
| `useCamelCase.ts` | Composables |
| `camelCase.ts` | 工具函数、API 客户端、类型 |
| `kebab-case` 目录 | 路由段、功能文件夹 |

### 功能文件夹布局

添加 2+ 个组件时，优先按功能组织：

```
components/
├── features/
│   ├── todo/
│   │   ├── TodoContainer.vue    # 容器组件
│   │   ├── TodoInput.vue        # 输入组件
│   │   ├── TodoList.vue         # 列表组件
│   │   └── TodoItem.vue         # 项组件
│   └── user/
│       ├── UserProfile.vue
│       └── UserAvatar.vue
composables/
├── useTodo.ts
└── useUser.ts
```

## SFC 结构

### 区域顺序

```vue
<script setup lang="ts">
// 1. Imports（vue → 生态 → 绝对路径 → 相对路径）
// 2. Props & Emits & Slots（defineProps, defineEmits, defineModel）
// 3. Composables（useXxx）
// 4. 本地状态（ref/reactive）
// 5. Computed 属性
// 6. 方法
// 7. Watchers
// 8. 生命周期钩子
</script>

<template>
  <!-- 声明式模板 -->
</template>

<style scoped>
  /* Scoped 样式 */
</style>
```

### 规则

- 保持模板声明式。将分支、过滤、派生逻辑移到 script 中用 `computed` 或方法处理。
- 禁止 `v-if` 和 `v-for` 同元素使用。用 computed 过滤数组替代。
- `v-for` 始终用稳定的数据库 ID 作为 key，绝不用数组索引。
- 禁止 `v-html` 渲染用户内容——先用 DOMPurify 消毒。
- 频繁切换可见性时用 `v-show` 替代 `v-if`（避免卸载/重挂）。

## Script Setup 宏

### defineProps

```ts
// 类型声明（推荐）
const props = defineProps<{
  title: string
  count?: number
  items: string[]
}>()

// 带默认值（Vue 3.5+ — 响应式 props 解构）
const { title, count = 0 } = defineProps<{
  title: string
  count?: number
}>()

// 带默认值（Vue 3.4 及以下）
const props = withDefaults(defineProps<{
  title: string
  items?: string[]
}>(), {
  items: () => []  // 数组/对象用工厂函数
})
```

**规则：**
- 始终提供 `type`，以及适当的 `required`/`default`。
- 布尔 props 命名：`isXxx`、`hasXxx`、`canXxx`。
- 禁止直接修改 props——应 emit 事件。
- Vue 3.5 响应式 props 解构：不能直接 `watch()` 解构的 prop——用 getter：`watch(() => count, ...)`。
- 共享/库组件中不建议使用响应式 props 解构，以保持更广泛兼容性。

### defineEmits

```ts
const emit = defineEmits<{
  update: [value: string]
  change: [id: number, name: string]
  close: []
}>()

emit('update', 'new value')
```

- 模板中用 kebab-case（`@update:model-value`）。
- script 中用 camelCase（`emit('update:modelValue', val)`）。

### defineModel

通过 `v-model` 实现双向绑定。Vue 3.4+ 可用。

```ts
// 基础用法 — 创建 "modelValue" prop
const model = defineModel<string>()
model.value = 'hello'  // 触发 "update:modelValue"

// 命名 model — 通过 v-model:name 消费
const count = defineModel<number>('count', { default: 0 })

// 带修饰符和转换器
const [value, modifiers] = defineModel<string>({
  get(val) { return val?.toLowerCase() },
  set(val) { return modifiers.trim ? val?.trim() : val }
})

// TypeScript 泛型修饰符（Vue 3.4+）
const [modelValue, modifiers] = defineModel<string, 'trim' | 'uppercase'>()
// modifiers 类型为 Record<'trim' | 'uppercase', true | undefined>
```

`v-model` 仅用于真正的双向组件契约，不作为 prop + emit 的快捷方式。

### defineExpose

组件默认封闭。显式暴露父组件需要的内容：

```ts
const count = ref(0)
const reset = () => { count.value = 0 }
defineExpose({ count, reset })
```

### defineOptions（Vue 3.3+）

```ts
defineOptions({ inheritAttrs: false, name: 'CustomName' })
```

### defineSlots（Vue 3.3+）

```ts
const slots = defineSlots<{
  default(props: { item: string; index: number }): any
  header(props: { title: string }): any
}>()
```

### 泛型组件（Vue 3.3+）

```vue
<script setup lang="ts" generic="T extends string | number">
defineProps<{ items: T[]; selected: T }>()
</script>
```

## useAttrs 和 useSlots

在 `<script setup>` 中以编程方式访问透传属性和插槽：

```ts
import { useAttrs, useSlots } from 'vue'

const attrs = useAttrs()  // 透传属性对象（class、style、id 等）
const slots = useSlots()  // 插槽对象

// 判断是否有传入插槽内容
if (slots.header) {
  // 父组件提供了 #header 内容
}
```

**何时用：**
- `useAttrs`：需要在 JS 中读取透传属性（如传递给内部元素、条件绑定）。
- `useSlots`：需要在 JS 中判断插槽是否有内容（如条件渲染包装元素）。
- 大多数场景直接在模板中使用 `$attrs` 和 `$slots` 即可，无需在 JS 中访问。

## 组件拆分

### 展示型 vs 容器型

- **容器组件**：拥有数据获取、状态和副作用。渲染展示型组件。
- **展示型组件**：接收 props，emit 事件。无 API 调用，无 store 访问。纯渲染。

### 拆分触发条件

满足以下**任一**条件时必须拆分：

1. 同时拥有编排/状态管理 AND 多个区域的展示性模板。
2. 有 3+ 个独立 UI 区域（如：表单、筛选器、列表、底部栏/状态）。
3. 存在重复的或可复用的模板块（列表行、卡片、列表项）。

### 入口/根和路由 View 规则

保持入口/根和路由 view 组件精简：应用外壳/布局、provider 接线、功能组合。不要在入口/根/view 组件中放置完整功能实现。

对于 CRUD/列表功能（todo、table、catalog、inbox），至少拆分为：
- 功能容器组件
- 输入/表单组件
- 列表/项组件
- 底部/操作或筛选/状态组件

仅允许在极小的临时 demo 中使用单文件实现——若选择此方案，需明确说明为何不需要拆分。

## Composables 设计

### 何时提取

当逻辑满足以下条件时提取为 composable：
- **复用**：跨多个组件使用。
- **有状态**：管理响应式状态。
- **副作用重**：API 调用、定时器、事件监听、DOM 操作。

### 结构

```ts
// composables/useMouse.ts
import { ref, onMounted, onUnmounted } from 'vue'

export function useMouse() {
  const x = ref(0)
  const y = ref(0)

  const update = (e: MouseEvent) => {
    x.value = e.pageX
    y.value = e.pageY
  }

  onMounted(() => window.addEventListener('mousemove', update))
  onUnmounted(() => window.removeEventListener('mousemove', update))

  return { x, y }
}
```

### 规则

- 必须以 `use` 前缀开头：`useMouse`、`useFetch`、`useCounter`。
- 返回响应式值（`ref`、`computed`），绝不返回原始值。返回包含 ref 的普通对象（不用 `reactive()`），保证解构兼容性。
- 通过 `MaybeRef` / `toRef()` / `toValue()` 接受响应式输入。
- 在 `onUnmounted` 或 watcher `onCleanup` 中清理副作用。
- 禁止模块级副作用——在 `onMounted` + `onUnmounted` 中作用域化。
- 保持 composable API 小巧、类型安全、可预测。

### 接受响应式输入

```ts
import { ref, watchEffect, toValue, type MaybeRefOrGetter } from 'vue'

export function useFetch(url: MaybeRefOrGetter<string>) {
  const data = ref(null)
  const error = ref(null)

  watchEffect(async () => {
    data.value = null
    error.value = null
    try {
      const res = await fetch(toValue(url))
      data.value = await res.json()
    } catch (e) {
      error.value = e
    }
  })

  return { data, error }
}

// 以下用法均可：
useFetch('/api/users')
useFetch(urlRef)
useFetch(() => `/api/users/${props.id}`)
```

### Composables vs Mixins

Composables 完全替代 Vue 2 的 mixins：
- **Mixins**：不透明的数据流、数据源冲突、命名冲突。
- **Composables**：显式导入、清晰的返回值、可组合且可 tree-shake。

Vue 3 代码中禁止使用 mixins。
