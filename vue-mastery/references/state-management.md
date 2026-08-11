# 状态管理

> 涉及全局/共享状态、Pinia stores 或 provide/inject 时加载。

## 决策表

| 模式 | 适用场景 |
|------|---------|
| `ref()` / `reactive()` | 组件本地状态 |
| Props + Emits | 父子组件通信 |
| Provide / Inject | 主题、配置、插件 API — 深层树共享上下文 |
| Pinia store | 全局、共享、跨功能边界的复杂状态 |
| Server state composable | 带缓存的 API 数据（包装 `fetch` / TanStack Query） |

**规则：**
- 从本地状态开始。仅当状态跨功能边界时才升级到 Pinia。
- `provide/inject` 仅用于深层树依赖或共享上下文（主题、配置、i18n）。
- 契约保持显式且类型安全，按需使用 `InjectionKey`。

## Pinia

### Setup Store（推荐）

```ts
// stores/useCartStore.ts
import { defineStore } from 'pinia'

export const useCartStore = defineStore('cart', () => {
  const items = ref<CartItem[]>([])
  const isLoading = ref(false)

  const totalPrice = computed(() =>
    items.value.reduce((sum, i) => sum + i.price * i.quantity, 0)
  )
  const itemCount = computed(() =>
    items.value.reduce((sum, i) => sum + i.quantity, 0)
  )

  async function addItem(productId: string) {
    isLoading.value = true
    try {
      const item = await fetchProduct(productId)
      const existing = items.value.find(i => i.id === item.id)
      if (existing) existing.quantity++
      else items.value.push({ ...item, quantity: 1 })
    } finally {
      isLoading.value = false
    }
  }

  return { items, isLoading, totalPrice, itemCount, addItem }
})
```

### 规则

- 使用 Setup Store 语法（不用 Options Store）。
- 业务级变更优先用 actions，批量更新用 `$patch()`。
- 每个异步 action：处理 loading + success + error。
- 保持 store API 小巧且类型安全。
- 用 `computed` getter 派生值——不要复制状态。

## Provide / Inject

### 类型安全模式

```ts
import type { InjectionKey } from 'vue'
import type { Theme } from './types'

export const ThemeKey: InjectionKey<Theme> = Symbol('theme')

// 提供方
provide(ThemeKey, reactive({ mode: 'dark' }))

// 消费方
const theme = inject(ThemeKey)
if (!theme) throw new Error('Theme not provided')
```

### 默认值与工厂函数

```ts
// 带默认值（未提供时使用）
const path = inject('path', '/default-path')

// 带工厂函数默认值（非原始类型必须用工厂函数，避免跨实例共享）
const config = inject('config', () => ({ timeout: 3000 }), true)
// 第三个参数 true 表示第二个参数是工厂函数
```

### 规则

- 始终使用类型化的 `InjectionKey` 保证类型安全。
- 提供响应式值（`ref`、`reactive`、`computed`）。
- 非原始类型的默认值必须用工厂函数，防止跨实例共享。
- `provide/inject` 仅用于深层树依赖或共享上下文——不作为 prop 穿透的快捷方式（应通过合理的组件组合解决）。

## Vue Router

### 路由定义

```ts
const routes = [
  {
    path: '/users/:id',
    name: 'user-detail',
    component: () => import('@/pages/UserDetail.vue'),  // 懒加载
    props: true,  // 将 params 作为 props 传递
    meta: { requiresAuth: true },
  },
]
```

### 导航守卫

```ts
router.beforeEach((to, from) => {
  const { isLoggedIn } = useAuthStore()
  if (to.meta.requiresAuth && !isLoggedIn) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
})
```

### 响应式路由参数

当组件保持挂载但路由参数变化时：

```ts
const route = useRoute()
const id = computed(() => route.params.id as string)
watch(id, (newId) => fetchItem(newId))
```
