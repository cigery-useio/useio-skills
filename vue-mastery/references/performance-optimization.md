# 性能优化

> 仅当识别到或可能出现性能问题时加载。性能优化是功能完成后的步骤——核心行为实现并验证之前不要优化。

## 决策表

| 技术 | 适用场景 |
|------|---------|
| `v-memo` | 列表项很少变化 — 依赖未变时跳过重渲染 |
| `v-once` | 只渲染一次且永远静态的内容 |
| `shallowRef()` | 整体替换的大型数据结构（无需深层响应式） |
| `shallowReactive()` | 仅顶层属性需要响应式 |
| `v-show` 替代 `v-if` | 频繁切换可见性（避免卸载/重挂） |
| `<KeepAlive :max="N">` | 缓存切换的视图，用 `max` 限制内存 |
| 懒加载路由 | `() => import(...)` 用于非关键路由 |
| `Suspense` | 异步组件加载带 fallback |
| 虚拟列表 | 大列表渲染瓶颈（>1000 项） |
| 扁平化组件树 | 热列表路径中过度抽象 |

## 虚拟化大列表

渲染 1000+ 项的列表时，虚拟化只渲染可见项。

**何时用：** 大列表渲染瓶颈——可见项是总项数的一小部分。

**方案：** 使用虚拟化库（如 `vue-virtual-scroller`、`@tanstack/vue-virtual`）。

```vue
<script setup lang="ts">
import { RecycleScroller } from 'vue-virtual-scroller'
import 'vue-virtual-scroller/dist/vue-virtual-scroller.css'
</script>

<template>
  <RecycleScroller :items="items" :item-size="50" key-field="id">
    <template #default="{ item }">
      <ItemRow :item="item" />
    </template>
  </RecycleScroller>
</template>
```

**不要**虚拟化少于 ~100 项的列表——开销大于收益。

## v-memo 和 v-once

### v-memo

依赖未变时跳过重渲染。用于列表项性能优化。

```vue
<template>
  <div v-for="item in list" :key="item.id" v-memo="[item.selected]">
    <!-- 仅当 item.selected 变化时才重渲染 -->
    <ExpensiveComponent :item="item" />
  </div>
</template>
```

**何时用：** 列表项渲染昂贵且只依赖少数字段。

**不要**对简单项使用 `v-memo`——memoization 开销可能超过渲染成本。

### v-once

只渲染一次，跳过所有后续更新。

```vue
<span v-once>静态：{{ neverChanges }}</span>
```

**何时用：** 首次渲染后内容确实静态不变（标题、标签、装饰性文本）。

## 避免列表中的组件抽象

**问题：** 在热路径中为每个列表项包装组件会增加开销。1000+ 项的列表中，每个组件实例都有 setup、render 和 patch 成本。

**何时用：** 热列表路径中有很多项且每项都包装在子组件中。

**修复：**
- 简单项直接在 `v-for` 块中内联模板，而非使用子组件。
- 项模板复杂时，用 `v-memo` 跳过不必要的重渲染，而非增加组件抽象。
- 仅当项有自己的状态、生命周期或在列表外复用时才抽象为组件。

```vue
<!-- ❌ 避免：简单列表项的组件抽象 -->
<template v-for="item in items" :key="item.id">
  <SimpleItemRow :item="item" />
</template>

<!-- ✅ 更好：简单项内联模板 -->
<div v-for="item in items" :key="item.id" v-memo="[item.selected]">
  <span>{{ item.name }}</span>
  <span>{{ item.value }}</span>
</div>
```

## Updated Hook 性能

**问题：** `onUpdated` 中的昂贵操作在每次触发重渲染的响应式变化时都会运行。

**何时用：** 组件有昂贵逻辑在更新期间运行过于频繁。

**修复：**
- 将昂贵逻辑移到 `computed`（缓存，仅依赖变化时重新计算）。
- 用特定源的 `watch` 替代 `onUpdated`（后者在任何更新时都触发）。
- 用 `watchPostEffect` 处理特定依赖的 DOM 更新后副作用。
- 如果不需要每次更新都运行，对昂贵操作进行防抖或节流。

```ts
// ❌ 避免：onUpdated 中的昂贵逻辑
onUpdated(() => {
  recalculateLayout()  // 每次更新都运行
})

// ✅ 更好：限定到特定依赖
watch(() => items.value.length, () => {
  recalculateLayout()  // 仅当 items.length 变化时运行
}, { flush: 'post' })
```

## 通用性能规则

- 大型数据结构不需要深层响应式时，优先用 `shallowRef` 而非 `ref`。
- 路由和重型/少用组件使用懒加载。
- `KeepAlive` 的 `:max` 要有上限，防止内存增长。
- 避免不必要的 watcher——用 `computed` 派生状态。
- 先分析再优化——不要猜测瓶颈在哪。
