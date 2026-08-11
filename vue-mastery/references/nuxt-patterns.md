# Nuxt 模式

> Nuxt SSR 项目时加载。覆盖 auto-imports、数据获取、server routes 和 runtime config。

## Auto-Imports

Nuxt 自动导入 `ref`、`computed`、`watch`、`useFetch`、`useAsyncData` 等。直接使用，无需 import。

非 Nuxt 项目中，始终从 `'vue'` 显式导入。

**不要**在 Nuxt 项目中为自动导入的 API 添加显式 import——这会造成冗余并可能影响 Nuxt 的 auto-import 解析。

## useAsyncData / useFetch

### useAsyncData

```ts
const { data: user, pending, error, refresh } = await useAsyncData(
  'user',  // 唯一 key，用于缓存
  () => $fetch(`/api/users/${id}`),
)
```

### useFetch

```ts
const { data: posts } = await useFetch('/api/posts', {
  query: { page: 1 },
  key: 'posts-page-1',  // 请求去重
})
```

### 规则

- 始终提供唯一的 `key` 用于缓存和去重。
- 自定义数据获取逻辑用 `useAsyncData`。
- 简单的 `$fetch` 包装场景用 `useFetch`。
- 在模板中处理 `pending` 和 `error` 状态。

## Server Routes

```ts
// server/api/users/[id].ts
import { z } from 'zod'

export default defineEventHandler(async (event) => {
  const { id } = await getValidatedRouterParams(event, z.object({
    id: z.string().uuid(),
  }).parse)

  const user = await db.user.findUnique({ where: { id } })
  if (!user) {
    throw createError({ statusCode: 404, statusMessage: 'User not found' })
  }
  return user
})
```

### 规则

- 用 `zod` 或类似 schema 验证输入。
- 用 `createError()` 返回结构化错误响应。
- server routes 保持精简——业务逻辑委托给 service 层。

## Runtime Config

```ts
// nuxt.config.ts
export default defineNuxtConfig({
  runtimeConfig: {
    // 仅服务端——绝不暴露给客户端
    apiSecret: '',
    // public——暴露给客户端
    public: {
      apiBase: 'https://api.example.com',
    },
  },
})
```

### 在组件中访问

```ts
// 客户端（仅 public config）
const config = useRuntimeConfig()
const apiBase = config.public.apiBase

// 服务端（完整 config）
const config = useRuntimeConfig()
const secret = config.apiSecret  // 仅在 server routes/middleware 中
```

**绝不要**将密钥放在 `public` config 中——它会被暴露到客户端 bundle。

## Vue 3.5+ SSR 特性

懒水合（`hydrateOnVisible`）和 `defer Teleport` 在 Nuxt SSR 中特别有用，详见 `built-in-components.md` 中的异步组件和 Teleport 章节。
