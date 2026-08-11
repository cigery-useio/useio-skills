# 测试策略

> 为 Vue 组件、composables 或 Pinia stores 创建或审查测试时加载。

## 工作流

1. 确定行为边界：组件 UI 行为、composable 行为、或 store 行为。
2. 选择能证明该行为的最窄测试方式。
3. 用覆盖场景所需的最小 Pinia 配置。
4. 通过公共输入驱动测试：props、表单更新、按钮点击、子组件 emit 的事件、store API。
5. 在考虑实例级断言之前，先断言可观察的输出和副作用。
6. 将测试名重构为描述行为而非实现。标注剩余的覆盖缺口。

## 核心规则

- 每个测试只测一个行为。
- 优先断言可观察的输入/输出行为：渲染文本、emit 的事件、回调调用、store 状态变化。
- 避免实现耦合的断言。
- `wrapper.vm` 仅在例外情况下使用——当没有合理的 DOM、prop、emit 或 store 级断言时。
- 优先在 `beforeEach()` 中显式设置，每个测试重置 mock。
- 保持测试数据确定性，避免随机值。

## Pinia 测试

### 默认：createTestingPinia

挂载时用 `createTestingPinia` 作为全局插件。优先用 `createSpy: vi.fn` 保持一致性和便于 action spy 断言。

```ts
const wrapper = mount(ComponentUnderTest, {
  global: {
    plugins: [createTestingPinia({ createSpy: vi.fn })],
  },
})
```

默认情况下，actions 被 stub 和 spy。当测试只需验证 action 是否被调用时，使用 `stubActions: true`（默认）。

### 可接受的最小配置

以下配置同样有效——不应标记为错误：

- `createTestingPinia({})` — 测试不涉及 Pinia action spy 断言时。
- `createTestingPinia({ initialState: ... })` 或 `createTestingPinia({ stubActions: ... })` 不带 `createSpy` — 仅需状态种子或 action stub 时。
- `setActivePinia(createPinia(...))` 用于 store/composable 专注测试（不挂载组件）— 需要 mock/种子依赖 store 时。

仅当 action spy 断言是测试意图的一部分时才使用 `createSpy: vi.fn`。

### 执行真实 Actions

仅当测试必须验证 action 的真实行为和副作用时才用 `stubActions: false`。简单的"是否调用"断言不要默认开启。

```ts
createTestingPinia({ createSpy: vi.fn, stubActions: false })
```

### 种子 Store 状态

```ts
createTestingPinia({
  createSpy: vi.fn,
  initialState: {
    counter: { n: 20 },
    user: { name: 'Leia Organa' },
  },
})
```

### 添加 Pinia 插件

```ts
createTestingPinia({ createSpy: vi.fn, plugins: [myPiniaPlugin] })
```

### Getter 覆盖（边界情况）

```ts
const pinia = createTestingPinia({ createSpy: vi.fn })
const store = useCounterStore(pinia)
store.double = 999
// @ts-expect-error test-only reset of overridden getter
store.double = undefined
```

### 纯 Store 单元测试

验证 store 状态转换和 action 行为（无需组件渲染）时，优先用 `createPinia()`。仅在需要 stub 依赖 store、种子测试替身或 action spy 时才用 `createTestingPinia()`。

```ts
beforeEach(() => { setActivePinia(createPinia()) })

it('increments', () => {
  const counter = useCounterStore()
  counter.increment()
  expect(counter.n).toBe(1)
})
```

## Composable 测试

测试 composable 时，需在组件 setup 上下文中运行（因为可能用到生命周期钩子）。

### 基本模式

```ts
import { withSetup } from './test-utils'
import { useCounter } from './useCounter'

it('increments', () => {
  const { count, increment } = withSetup(() => useCounter())
  expect(count.value).toBe(0)
  increment()
  expect(count.value).toBe(1)
})
```

### withSetup 辅助函数

```ts
// test-utils.ts
import { defineComponent, h } from 'vue'

export function withSetup<T>(composable: () => T): T & { unmount: () => void } {
  let result!: T
  const app = defineComponent({
    setup() {
      result = composable()
      return () => h('div')
    },
  })
  const mount = app.mount(document.createElement('div'))
  return { ...result, unmount: () => mount.unmount() }
}
```

### 规则

- 测试 composable 返回的 ref/computed 值，而非内部实现。
- 如果 composable 有副作用（定时器、事件监听），卸载后断言副作用已清理。
- 如果 composable 依赖 Pinia store，用 `setActivePinia(createPinia())` 设置。
- 如果 composable 依赖路由参数，用 mock 的 `useRoute()` 或 `createRouter`。

## Vue Test Utils

遵循 [Vue Test Utils 指南](https://test-utils.vuejs.org/guide/)。

- 聚焦单元测试默认**浅挂载**。
- 仅当集成行为是测试对象时才挂载完整组件树。
- 通过 props、类用户交互和 emit 的事件驱动行为。
- 子组件 stub 事件优先用 `findComponent(...).vm.$emit(...)`，而非触碰父组件内部。
- 仅当更新是异步时才用 `nextTick`。
- 用 `wrapper.emitted(...)` 断言 emit 的事件和载荷。
- `wrapper.vm` 仅当 DOM/emit/prop/store 断言都无法表达行为时才使用。视为例外，保持断言范围最小。

## 关键代码片段

### Emit 并断言载荷

```ts
await wrapper.find('button').trigger('click')
expect(wrapper.emitted('submit')?.[0]?.[0]).toBe('Mango Mission')
```

### 更新输入并断言输出

```ts
await wrapper.find('input').setValue('Agent Violet')
await wrapper.find('form').trigger('submit')
expect(wrapper.emitted('save')?.[0]?.[0]).toBe('Agent Violet')
```

## 组件测试模式

```ts
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import UserCard from './UserCard.vue'

beforeEach(() => { setActivePinia(createPinia()) })

it('renders and emits', async () => {
  const wrapper = mount(UserCard, {
    props: { user: { id: '1', name: 'Alice' } },
  })
  expect(wrapper.text()).toContain('Alice')
  await wrapper.find('button').trigger('click')
  expect(wrapper.emitted('select')![0]).toEqual(['1'])
})
```

## 约束

- 禁止测试私有/内部实现细节。
- 禁止过度使用快照测试动态 UI 行为。
- 如果只有一个行为相关，不要断言大对象的每个字段。
- 除非行为测试需要额外的表面积，否则不要将工作中的测试重写为更深挂载或真实 actions。
- 审查时显式标注缺失的测试覆盖、脆弱的选择器和实现耦合的断言。

## 输出契约

- `create` 或 `update`：返回完成的测试代码，附简短说明描述所选 Pinia 策略。
- `review`：先返回具体发现，再返回缺失覆盖或脆弱性风险。
- 当最安全的选择不明确时：说明驱动所选测试设置的假设。

## 外部参考

- [Pinia 测试 cookbook](https://pinia.vuejs.org/cookbook/testing.html)
- [Vue Test Utils 指南](https://test-utils.vuejs.org/guide/)
