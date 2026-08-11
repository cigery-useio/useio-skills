# 响应式系统

> 涉及 ref、watcher、computed 或 Vue 3.4+/3.5+ 新 API 时加载。

## ref vs shallowRef

```ts
import { ref, shallowRef } from 'vue'

// ref — 深层响应式（追踪嵌套变化）
const user = ref({ name: 'John', profile: { age: 30 } })
user.value.profile.age = 31  // 触发响应式

// shallowRef — 仅 .value 赋值触发响应式（性能更好）
const data = shallowRef({ items: [] })
data.value.items.push('new')  // 不触发响应式
data.value = { items: ['new'] }  // 触发响应式
```

**优先用 `shallowRef`** 处理大型数据结构或不需要深层响应式的场景。

## shallowReactive

```ts
import { shallowReactive } from 'vue'

// 仅顶层属性是响应式的，嵌套属性不追踪
const state = shallowReactive({
  user: { name: 'John' },  // user 对象不是响应式的
  count: 0                  // count 是响应式的
})
state.count++              // 触发响应式
state.user.name = 'Jane'   // 不触发响应式
```

**何时用：** 仅需顶层属性响应式、嵌套对象较大且不需要深层追踪的场景。

## computed

```ts
import { ref, computed } from 'vue'

const count = ref(0)

// 只读
const doubled = computed(() => count.value * 2)

// 可写
const plusOne = computed({
  get: () => count.value + 1,
  set: (val) => { count.value = val - 1 }
})
```

**规则：**
- 保持源状态最小化，尽可能用 `computed` 派生。
- 避免在模板中重复计算昂贵逻辑——用 `computed`。
- watcher 用于副作用，不用于派生状态。

## reactive & readonly

```ts
import { reactive, readonly } from 'vue'

const state = reactive({ count: 0, nested: { value: 1 } })
state.count++  // 响应式

const readonlyState = readonly(state)
readonlyState.count++  // 警告，修改被阻止
```

**陷阱：**
- `reactive()` 解构后失去响应性。用 `ref()` 或 `toRefs()` 替代。
- `reactive()` 适用于不会被整体替换的对象状态。需要整体替换时用 `ref()`。
- `reactive()` 用于可替换状态时，替换会破坏响应性——用 `ref()` 替代。

## Watchers

### watch

```ts
import { ref, watch } from 'vue'

const count = ref(0)

// 监听单个 ref
watch(count, (newVal, oldVal) => {
  console.log(`从 ${oldVal} 变为 ${newVal}`)
})

// 监听 getter
watch(
  () => props.id,
  (id) => fetchData(id),
  { immediate: true }
)

// 监听多个源
watch([firstName, lastName], ([first, last]) => {
  fullName.value = `${first} ${last}`
})

// 深度监听带深度限制（Vue 3.5+）
watch(state, callback, { deep: 2 })

// 仅一次（Vue 3.4+）
watch(source, callback, { once: true })
```

### watchEffect

立即执行并自动追踪依赖。

```ts
import { ref, watchEffect, onWatcherCleanup } from 'vue'

const id = ref(1)

// 方式一：onWatcherCleanup（Vue 3.5+，全局可导入）
watchEffect(async () => {
  const controller = new AbortController()
  onWatcherCleanup(() => controller.abort())

  const res = await fetch(`/api/${id.value}`, { signal: controller.signal })
  data.value = await res.json()
})

// 方式二：effect 函数接收 onCleanup 参数（所有版本）
watchEffect((onCleanup) => {
  const timer = setTimeout(() => { /* ... */ }, 1000)
  onCleanup(() => clearTimeout(timer))
})
```

### watch 和 watchEffect 的暂停/恢复/停止

`watch` 和 `watchEffect` 都返回 `WatchHandle`，支持 `pause`、`resume`、`stop`：

```ts
const { stop, pause, resume } = watch(source, callback)
// 或
const { stop, pause, resume } = watchEffect(() => {})

pause()   // 暂停（Vue 3.5+）
resume()  // 恢复
stop()    // 停止，不可恢复
```

### Flush 时机

```ts
// 'pre'（默认）— 组件更新前
// 'post' — 组件更新后（可访问更新后的 DOM）
// 'sync' — 立即，谨慎使用

watch(source, callback, { flush: 'post' })
watchPostEffect(() => {})  // flush: 'post' 的别名
```

### Watcher 清理

**始终在 watcher 中清理副作用**，防止内存泄漏和竞态条件：

```ts
// Vue 3.5+ — 全局可导入
import { watch, onWatcherCleanup } from 'vue'

watch(userId, async (newId) => {
  const controller = new AbortController()
  onWatcherCleanup(() => controller.abort())
  // ... 用 signal 发起请求
})

// Vue 3.4 及以下 — watcher onCleanup
watch(source, (newVal, oldVal, onCleanup) => {
  const timer = setTimeout(() => { /* ... */ }, 1000)
  onCleanup(() => clearTimeout(timer))
})
```

## 生命周期钩子

```ts
import {
  onBeforeMount, onMounted,
  onBeforeUpdate, onUpdated,
  onBeforeUnmount, onUnmounted,
  onErrorCaptured,
  onActivated, onDeactivated,  // KeepAlive
  onServerPrefetch            // 仅 SSR
} from 'vue'

onMounted(() => { /* DOM 就绪 */ })
onUnmounted(() => { /* 清理定时器、监听器 */ })

// 错误边界
onErrorCaptured((err, instance, info) => {
  console.error(err)
  return false  // 阻止传播
})
```

## Effect Scope

将响应式副作用分组以便批量销毁。

```ts
import { effectScope, onScopeDispose } from 'vue'

const scope = effectScope()

scope.run(() => {
  const count = ref(0)
  const doubled = computed(() => count.value * 2)
  watch(count, () => console.log(count.value))
  onScopeDispose(() => { /* 清理 */ })
})

// 一次性销毁所有副作用
scope.stop()
```

## Vue 3.5+ 新 API

### 响应式 Props 解构

Vue 3.5 稳定了响应式 props 解构——从 `defineProps()` 解构的变量自动保持响应性：

```ts
// Vue 3.5+：解构的 props 是响应式的（无需 toRefs）
const { count = 0, msg = 'hello' } = defineProps<{
  count?: number
  msg?: string
}>()

// ⚠️ 限制：不能直接 watch 解构的 prop
watch(() => count, (newVal) => { ... })  // ✅ 需要 getter
// watch(count, ...)  // ❌ 编译时错误
```

**建议：** 共享/库组件中不建议使用响应式 props 解构，以保持更广泛兼容性。改用 `props.xxx` 访问模式。

### useTemplateRef()

用 `useTemplateRef()` 替代名称匹配的普通 ref：

```ts
import { useTemplateRef } from 'vue'
const inputEl = useTemplateRef<HTMLInputElement>('input')
// "input" 匹配模板中的 ref="input" 属性，而非变量名
```

支持动态 ref ID：`useTemplateRef(dynamicRefId)`。

### useId()

SSR 稳定的唯一 ID 生成，用于表单元素和无障碍：

```ts
import { useId } from 'vue'
const id = useId()
```

> `defer Teleport` 和懒水合等 Vue 3.5+ 特性详见 `built-in-components.md`。

## nextTick

在修改响应式状态后，等待 DOM 更新完成再执行操作：

```ts
import { ref, nextTick } from 'vue'

const count = ref(0)
async function increment() {
  count.value++
  // DOM 尚未更新
  await nextTick()
  // DOM 已更新，可安全操作
  console.log(document.getElementById('count')?.textContent)
}
```

**何时用：** 需要在状态变更后访问更新后的 DOM 时（如测量元素尺寸、聚焦输入框、触发第三方库初始化）。

## 关键 Import 参考

```ts
// 响应式
import { ref, shallowRef, computed, reactive, readonly, toRef, toRefs, toValue } from 'vue'  // toValue: Vue 3.3+

// Watchers
import { watch, watchEffect, watchPostEffect, onWatcherCleanup } from 'vue'

// 生命周期
import { onMounted, onUpdated, onUnmounted, onBeforeMount, onBeforeUpdate, onBeforeUnmount } from 'vue'

// 工具
import { nextTick, defineComponent, defineAsyncComponent, useTemplateRef, useId } from 'vue'
```
