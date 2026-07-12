# 资源提示 (Resource Hints)

> 对应 web.dev 模块：Optimize Resource Loading / Resource Hints

## 核心概念

Resource Hints 是浏览器提供的声明式 API，让开发者提前告诉浏览器"接下来会用到哪些资源/连接"。它们是性能预算中最便宜、回报率最高的优化之一。

### 四种 Hint 的层级关系

```
dns-prefetch     ← 仅 DNS 解析
  └─ preconnect  ← DNS + TCP + TLS（包含 dns-prefetch）
       └─ preload    ← 强制提前下载指定资源（当前页面需要）
       └─ prefetch   ← 低优先级下载，给下一页/未来导航用
```

## 常见问题现象

| 滥用方式 | 后果 |
|----------|------|
| 预连接过多（> 5 个源） | 每个连接占用内存和 CPU，反而拖慢 | 
| 预加载未使用的资源 | 浪费带宽，触发浏览器 Console 警告 |
| 预加载缺失 `as` 属性 | 浏览器不知道资源类型，可能以错误的优先级下载 |
| 预加载缺少 `crossorigin`（字体） | 字体请求会发两次（一次不带 CORS，一次带） |
| 对同源资源使用 `preconnect`（没用） | 浪费字符，同源不需要额外连接 |
| 对 `<body>` 中已出现的图片 preload | 浏览器扫描器已经发现了，多余的 hint |
| 对动态 URL 使用 prefetch（命中率低） | 浪费带宽 |

## 检测方式

### 1. 手动检查清单
- 页面中用到的第三方域名，是否都加了 `preconnect`？
- `<head>` 中最关键的 2-3 个资源（LCP 图片、关键字体）是否加了 `preload`？
- Chrome DevTools Console 是否有 "The resource ... was preloaded using link preload but not used within a few seconds" 警告？
- Network 面板中，preload 资源是否确实以 High 优先级被下载？

### 2. 本技能脚本（`check_resource_hints.py`）
- 扫描所有 `<link rel="preload|prefetch|preconnect|dns-prefetch">`
- 检查 preload 的 `as` 属性是否缺失或不当
- 检查字体 preload 是否有 `crossorigin`
- 检查 preconnect 的超时（浏览器会保留连接约 3-5 分钟）

## 优化手段

### 1. Preconnect 正确用法

```html
<!-- ✅ 对关键第三方源做预连接 -->
<link rel="preconnect" href="https://fonts.gstatic.com">
<link rel="preconnect" href="https://api.example.com">

<!-- ❌ 不要预连接本域资源 -->
<link rel="preconnect" href="https://mysite.com">  <!-- 浪费 -->

<!-- ❌ 不要预连接不确定用不用的源 -->
<link rel="preconnect" href="https://maybe-used.com">  <!-- 过度优化 -->
```

### 2. Preload 正确用法

```html
<!-- ✅ 预加载 LCP 图片 -->
<link rel="preload" as="image" href="/hero.webp">

<!-- ✅ 预加载关键字体（必须指定 crossorigin） -->
<link rel="preload" as="font" href="/fonts/main.woff2" crossorigin>

<!-- ✅ 预加载动态加载的 JS 模块 -->
<link rel="preload" as="script" href="/chunk-vendors.js">

<!-- ❌ 预加载但没有设置正确的 as，浏览器当普通 fetch -->
<link rel="preload" href="/styles.css">  <!-- 缺少 as="style" -->

<!-- ❌ 预加载了所有图片（preload 只给 2-3 个最关键资源） -->
<link rel="preload" as="image" href="/img1.webp">
<link rel="preload" as="image" href="/img2.webp">
<link rel="preload" as="image" href="/img3.webp">
<!-- ...太多了！非关键资源用 prefetch 或不加 -->
```

### 3. Prefetch 用法

```html
<!-- ✅ 预取下一页可能需要的资源（低优先级、不影响当前页面） -->
<link rel="prefetch" as="document" href="/next-page.html">
<link rel="prefetch" as="script" href="/next-chunk.js">

<!-- ❌ 对当前页面确定需要的资源用 prefetch（应该用 preload） -->
<link rel="prefetch" as="style" href="/critical.css">  <!-- 优先级太低 -->
```

### 4. DNS Prefetch

```html
<!-- ✅ 对不确定是否会连接但概率较高的源，低成本预热 DNS -->
<link rel="dns-prefetch" href="https://analytics.example.com">
```

## 优先级决策表

| 场景 | 推荐 Hint | 数量限制 |
|------|----------|---------|
| 需要连接的关键第三方API | `preconnect` | ≤ 5 |
| 当前页面的 LCP 元素（图片/字体） | `preload` | ≤ 3 |
| 用户大概率会导航到的下一个页面 | `prefetch` | 不限（但低优先级） |
| 可能用到的第三方域名 | `dns-prefetch` | ≤ 10 |

## 预期收益

| 优化项 | 影响指标 | 典型提升 |
|--------|---------|----------|
| preconnect 关键第三方源 | FCP, LCP | -0.3s ~ -1s |
| preload LCP 图片 | LCP | -0.5s ~ -2s |
| preload 关键字体 | LCP, CLS | -0.3s ~ -0.8s |
| 清理无效 preload | TBT | -0.1s ~ -0.3s |
