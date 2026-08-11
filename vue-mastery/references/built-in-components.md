# 内置组件与指令

> 使用 Transition、Teleport、Suspense、KeepAlive、v-memo、指令、异步组件或 plugins 时加载。

## Transition

为单个元素或组件的进入/离开添加动画。

```vue
<template>
  <Transition name="fade">
    <div v-if="show">内容</div>
  </Transition>
</template>

<style>
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
```

### CSS 类名

| 类名 | 时机 |
|------|------|
| `{name}-enter-from` | 进入起始状态 |
| `{name}-enter-active` | 进入活动状态（在此添加过渡） |
| `{name}-enter-to` | 进入结束状态 |
| `{name}-leave-from` | 离开起始状态 |
| `{name}-leave-active` | 离开活动状态 |
| `{name}-leave-to` | 离开结束状态 |

### 过渡模式

```vue
<!-- 等离开完成后再进入 -->
<Transition name="fade" mode="out-in">
  <component :is="currentView" />
</Transition>
```

### JavaScript 钩子

```vue
<Transition
  @before-enter="onBeforeEnter"
  @enter="onEnter"
  @after-enter="onAfterEnter"
  @enter-cancelled="onEnterCancelled"
  @before-leave="onBeforeLeave"
  @leave="onLeave"
  @after-leave="onAfterLeave"
  @leave-cancelled="onLeaveCancelled"
  :css="false"
>
  <div v-if="show">内容</div>
</Transition>

<script setup lang="ts">
function onEnter(el: Element, done: () => void) {
  gsap.to(el, { opacity: 1, onComplete: done })
}
function onLeaveCancelled(el: Element) {
  // 离开动画被中断时的清理
}
</script>
```

### 其他 Props

| Prop | 说明 |
|------|------|
| `duration` | 显式指定过渡时长（毫秒），或 `{ enter: number, leave: number }` |
| `type` | 指定监听的事件类型：`'transition'` 或 `'animation'` |
| `appear` | 首次渲染时是否应用过渡（默认 `false`） |
| `css` | 是否应用 CSS 过渡类（设为 `false` 时仅用 JS 钩子） |

### 首次渲染动画

```vue
<Transition appear name="fade">
  <div>挂载时带动画显示</div>
</Transition>
```

## TransitionGroup

为列表项添加动画。每个子元素必须有唯一的 `key`。

### Props

| Prop | 说明 |
|------|------|
| `tag` | 渲染为的包装元素标签名。未定义时渲染为 fragment |
| `moveClass` | 移动过渡期间应用的自定义 CSS 类（默认 `{name}-move`） |

```vue
<template>
  <TransitionGroup name="list" tag="ul">
    <li v-for="item in items" :key="item.id">{{ item.text }}</li>
  </TransitionGroup>
</template>

<style>
.list-enter-active, .list-leave-active { transition: all 0.3s ease; }
.list-enter-from, .list-leave-to { opacity: 0; transform: translateX(30px); }
.list-move { transition: transform 0.3s ease; }  /* 重排序移动动画 */
</style>
```

## Teleport

将内容渲染到不同的 DOM 位置。

```vue
<Teleport to="body">
  <div v-if="open" class="modal">模态框内容</div>
</Teleport>
```

### Props

```vue
<Teleport to="#modal-container">           <!-- CSS 选择器 -->
<Teleport :to="targetElement">              <!-- DOM 元素 -->
<Teleport to="body" :disabled="isMobile">   <!-- 条件禁用 -->
<Teleport defer to="#late-rendered-target">  <!-- 延迟到目标存在（Vue 3.5+） -->
```

## Suspense

处理异步依赖的加载状态。**实验性功能。**

### Props

| Prop | 说明 |
|------|------|
| `timeout` | 超时时间（毫秒或字符串），超时后显示 fallback |
| `suspensible` | 是否暂停父级 Suspense 的解析（默认 `true`） |

### 事件

| 事件 | 说明 |
|------|------|
| `@resolve` | 所有异步依赖解析完成 |
| `@pending` | 新的异步依赖开始解析 |
| `@fallback` | 显示 fallback 内容 |

```vue
<Suspense>
  <template #default><AsyncComponent /></template>
  <template #fallback><div>加载中...</div></template>
</Suspense>
```

Suspense 等待：`async setup()` 组件、`<script setup>` 中的顶层 `await`、或 `defineAsyncComponent`。

```vue
<Suspense @pending="onPending" @resolve="onResolve" @fallback="onFallback">
  ...
</Suspense>
```

## KeepAlive

切换时缓存组件实例。

```vue
<KeepAlive>
  <component :is="currentTab" />
</KeepAlive>
```

### Include/Exclude/Max

```vue
<KeepAlive include="ComponentA,ComponentB">
<KeepAlive :include="/^Tab/">
<KeepAlive :include="['TabA', 'TabB']">
<KeepAlive exclude="ModalComponent">
<KeepAlive :max="10">
```

### 生命周期钩子

```ts
import { onActivated, onDeactivated } from 'vue'

onActivated(() => { /* 从缓存插入 */ })
onDeactivated(() => { /* 移入缓存 */ })
```

## v-memo

依赖未变时跳过重渲染。用于列表性能优化。

```vue
<div v-for="item in list" :key="item.id" v-memo="[item.selected]">
  <ExpensiveComponent :item="item" />
</div>
```

空数组等价于 `v-once`：`<div v-memo="[]">永不更新</div>`

## v-once

只渲染一次，跳过所有后续更新。

```vue
<span v-once>静态：{{ neverChanges }}</span>
```

## 自定义指令

当行为是 DOM 特定的且不适合用 composable/组件时使用。

```ts
const vFocus: Directive<HTMLElement> = {
  mounted: (el) => el.focus()
}

// 完整钩子
const vColor: Directive<HTMLElement, string> = {
  created(el, binding, vnode, prevVnode) {},
  beforeMount(el, binding) {},
  mounted(el, binding) { el.style.color = binding.value },
  beforeUpdate(el, binding) {},
  updated(el, binding) { el.style.color = binding.value },
  beforeUnmount(el, binding) {},
  unmounted(el, binding) {}
}
```

### 参数与修饰符

```vue
<div v-color:background.bold="'red'">
<!-- binding.arg = 'background', binding.modifiers = { bold: true }, binding.value = 'red' -->
```

### 全局注册

```ts
// main.ts
app.directive('focus', { mounted: (el) => el.focus() })
```

### `<script setup>` 中的本地指令

使用 `vNameOfDirective` 命名约定：

```ts
const vFocus = { mounted: (el: HTMLElement) => el.focus() }
// 或导入并重命名
import { myDirective as vMyDirective } from './directives'
```

## 异步组件

重型/少用的 UI 应懒加载。

```ts
import { defineAsyncComponent } from 'vue'

const AsyncComp = defineAsyncComponent(() => import('./HeavyComponent.vue'))

// 带选项
const AsyncComp = defineAsyncComponent({
  loader: () => import('./HeavyComponent.vue'),
  loadingComponent: LoadingSpinner,
  errorComponent: ErrorDisplay,
  delay: 200,
  timeout: 3000,
})

// 懒水合（Vue 3.5+）
const AsyncComp = defineAsyncComponent({
  loader: () => import('./Comp.vue'),
  hydrate: hydrateOnVisible(),
})
```

## Slots

当父组件需要控制子组件内容/布局时使用。

### 默认 Slot

```vue
<!-- 子组件 -->
<template>
  <div class="card">
    <slot />
  </div>
</template>

<!-- 父组件 -->
<Card>
  <p>卡片内容</p>
</Card>
```

### 具名 Slot

```vue
<!-- 子组件 -->
<template>
  <div class="layout">
    <slot name="header" />
    <slot />  <!-- 默认 slot -->
    <slot name="footer" />
  </div>
</template>

<!-- 父组件 -->
<Layout>
  <template #header><h1>标题</h1></template>
  <p>主体内容</p>
  <template #footer><span>页脚</span></template>
</Layout>
```

### 作用域 Slot（Slot Props）

子组件向 slot 内容传递数据：

```vue
<!-- 子组件 -->
<template>
  <ul>
    <li v-for="item in items" :key="item.id">
      <slot :item="item" :index="item.id" />
    </li>
  </ul>
</template>

<!-- 父组件 -->
<ItemList :items="items">
  <template #default="{ item, index }">
    <span>{{ index }}: {{ item.name }}</span>
  </template>
</ItemList>
```

### 规则

- 用 `defineSlots` 为 slot props 提供类型提示（见 `component-architecture.md`）。
- 作用域 slot 优先用解构接收 props：`#default="{ item }"`。
- slot 内容为空时提供 fallback：`<slot>默认内容</slot>`。

## Fallthrough Attributes

包装/基础组件必须安全地转发 attrs/events。

- 默认情况下，属性会透传到根元素。
- 用 `defineOptions({ inheritAttrs: false })` 禁用自动透传。
- 需要时显式绑定：`<input v-bind="$attrs" />`。

## Render 函数

仅当模板无法表达需求时使用。

```ts
import { h } from 'vue'

export default defineComponent({
  setup() {
    return () => h('div', { class: 'container' }, '内容')
  }
})
```

尽可能优先使用模板而非 render 函数。

## Plugins

当行为需要全应用安装时使用。

```ts
// plugins/myPlugin.ts
import type { App } from 'vue'

export function install(app: App) {
  app.directive('focus', { mounted: (el) => el.focus() })
  app.provide('myService', new MyService())
}

// main.ts
app.use(install)
```
