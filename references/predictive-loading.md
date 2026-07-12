# 预测式加载

> 对应 web.dev 模块：Prefetching / Prerendering / Service Worker Precaching

## 核心概念

预测式加载（Predictive Loading）是在用户实际需要某资源之前就提前获取它。与 Resource Hints 不同，预测式加载侧重于"猜测用户的下一个意图"——基于当前页面的导航可能性、用户行为模式或历史数据。

### 四种预测加载方式

```
prefetch   → 提前下载下一页的资源（浏览器在空闲时低优先级下载）
prerender  → 提前渲染整个下一页（包括 JS 执行，用户感觉瞬间打开）
preload    → 当前页面确定需要的资源（不是预测，是确定性提示）
Service Worker precaching → 在 SW 安装阶段缓存关键资源（离线可用）
```

## 常见问题现象

| 现象 | 根因 |
|------|------|
| 站内导航有明显白屏（SPA 除外） | 未使用 prefetch/prerender |
| PWA 离线时白屏 | Service Worker 未做预缓存 |
| 移动端导航到下一页流量消耗大 | prefetch 了过多资源，或用 prerender（会实际渲染） |
| 用户点击链接后 2s 才响应 | 下一页的关键资源未被预测式加载 |

## 检测方式

### 1. Network 面板
- 查看是否有 Lowest 优先级的请求（Browser 自动发起的 prefetch）
- 检查 Service Worker Cache 中的资源

### 2. 本技能脚本检测
- 扫描 HTML 中的 `<link rel="prefetch">` 和 `<link rel="prerender">`
- 检查 Service Worker 注册状态（`navigator.serviceWorker.controller`）
- 对有 SW 的页面，检查 precache 列表是否覆盖关键资源

## 优化手段

### 1. 链接预取（Link Prefetch）

```html
<!-- ✅ 对用户大概率点击的链接做 prefetch -->
<a href="/product/123" onmouseenter="prefetchLink('/product/123')">
  View Product
</a>

<script>
function prefetchLink(url) {
  const link = document.createElement('link')
  link.rel = 'prefetch'
  link.href = url
  document.head.appendChild(link)
}
</script>

<!-- ✅ 或静态声明 -->
<link rel="prefetch" href="/next-page.html" as="document">
```

### 2. 整页预渲染（Prerender）

```html
<!-- ⚠️ 慎重使用：prerender 会实际渲染整页，消耗 CPU 和内存 -->
<link rel="prerender" href="/checkout.html">
<!-- 适用于：用户必然要去的下一步（如结账流程的下一步） -->
```

**使用建议：**
- 只对 1-2 个"几乎确定用户会去"的页面使用
- 移动端慎用（耗电、耗流量）
- 及时取消不再需要的 prerender

### 3. Service Worker 预缓存

```js
// service-worker.js
const CACHE_NAME = 'v2'
const PRECACHE_ASSETS = [
  '/',
  '/styles.css',
  '/app.js',
  '/offline.html'
]

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(PRECACHE_ASSETS)
    })
  )
})

// ✅ 使用 Workbox 更简单
// import { precacheAndRoute } from 'workbox-precaching'
// precacheAndRoute(self.__WB_MANIFEST)
```

### 4. 基于视口的预取（Intersection Observer）

```js
// ✅ 当链接滚动到视口附近时预取
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const link = entry.target
      const prefetchLink = document.createElement('link')
      prefetchLink.rel = 'prefetch'
      prefetchLink.href = link.href
      document.head.appendChild(prefetchLink)
      observer.unobserve(link)  // 只 prefetch 一次
    }
  })
}, { rootMargin: '200px' })  // 距离视口 200px 时触发

document.querySelectorAll('a[href^="/"]').forEach(link => {
  observer.observe(link)
})
```

### 5. 数据预取

```js
// ✅ 在列表页 hover 时预取详情页 API 数据
let prefetchedData = {}

function onProductHover(productId) {
  if (!prefetchedData[productId]) {
    prefetchedData[productId] = fetch(`/api/product/${productId}`)
      .then(res => res.json())
  }
}

function onProductClick(productId) {
  // 数据可能已经回来了，页面秒开
  prefetchedData[productId].then(data => renderProductPage(data))
}
```

### 6. Quicklink / Guess.js

```html
<!-- ✅ 使用成熟的预测加载库 -->
<script src="https://unpkg.com/quicklink@2/dist/quicklink.umd.js"></script>
<script>
  quicklink.listen()  // 自动检测视口中的链接并 prefetch
</script>
```

## 预期收益

| 优化项 | 影响指标 | 典型提升 |
|--------|---------|----------|
| prefetch 下一页关键资源 | 导航感知延迟 | -50% ~ -80% |
| SW pre-cache 关键资源 | 重复访问 LCP | -1s ~ -3s |
| Intersection Observer prefetch | 导航感知延迟 | -0.5s ~ -1.5s |
| API 数据预取 | INP（导航后首次交互） | -0.3s ~ -1s |
