# 样式指南

> 使用 Tailwind CSS、scoped styles 或处理响应式/暗色模式时加载。

## Tailwind CSS

### 核心规则

- 所有样式使用 Tailwind CSS 工具类。除非必要，避免编写自定义 CSS。
- 工具类保持样式一致且与模板同置。
- 多个组件共享相同样式时，提取为可复用的 Vue 组件，或在最小化的 scoped styles 中使用 Tailwind 的 `@apply`。

### Class 列表可读性

过长的 class 列表换行书写以提高可读性：

```vue
<!-- ✅ 好：多行提高可读性 -->
<ItemCard
  :item="item"
  class="rounded-xl shadow p-4 bg-white dark:bg-gray-800"
/>

<!-- ✅ 好：多行 class 字符串 -->
<div
  class="flex items-center justify-between"
  :class="[
    isActive ? 'bg-blue-500 text-white' : 'bg-gray-100',
    isDisabled && 'opacity-50 cursor-not-allowed',
  ]"
>
  {{ content }}
</div>
```

适当使用组件级抽象——将重复的 class 组合提取到 composable 或包装组件中。

### 响应式设计

一致使用 Tailwind 的响应式断点：

```vue
<div class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
  <!-- 移动端 1 列，平板 2 列，桌面 3 列 -->
</div>
```

### 暗色模式

确保组件在明暗主题下都表现良好：

```vue
<div class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">
  <p class="text-gray-500 dark:text-gray-400">描述文字</p>
</div>
```

### @apply 使用

在 scoped styles 中谨慎使用 `@apply` 处理重复的工具类组合：

```vue
<style scoped>
.btn-primary {
  @apply px-4 py-2 rounded-lg bg-blue-500 text-white hover:bg-blue-600;
}
</style>
```

**不要**过度使用 `@apply`——单次使用的样式优先直接在模板中用工具类。`@apply` 仅保留给跨多个元素真正重复的模式。

## Scoped Styles

### 何时使用

- 组件特定样式使用 `<style scoped>`。
- 全局样式仅用于基础重置、CSS 变量和 Tailwind 指令。

```vue
<style scoped>
.container {
  @apply max-w-4xl mx-auto;
}
</style>
```

### CSS 组织

- 样式区域顺序：`<script setup>` → `<template>` → `<style scoped>`。
- 跨组件共享的主题 token 使用 CSS 变量。
- 避免 `:deep()` 深层选择器，除非需要样式化子组件内部——优先通过 props 或 class props 传递。

## 无障碍

Tailwind 不会自动处理无障碍。确保：

- 使用语义化 HTML（`<button>`、`<nav>`、`<main>`、`<article>` 等）而非通用 `<div>`。
- 按需添加 ARIA 属性：`aria-label`、`aria-describedby`、`role`。
- 交互组件处理焦点：`focus:ring`、`focus:outline-none` 配合可见的焦点指示器。
- 确保明暗主题下的颜色对比度符合 WCAG 标准。

```vue
<button
  class="px-4 py-2 rounded-lg bg-blue-500 text-white hover:bg-blue-600
         focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
  :aria-label="isExpanded ? '折叠' : '展开'"
  @click="toggle"
>
  <ChevronIcon :class="{ 'rotate-180': isExpanded }" />
</button>
```
