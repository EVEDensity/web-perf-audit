# HTML 加载性能

> 对应 web.dev 模块：General HTML Performance / Parse Blocking / Render Blocking

## 核心概念

HTML 是页面的骨架。浏览器的 HTML 解析器遇到外部资源（`<script>`、`<link>`、`<img>`）时会触发不同策略。理解解析器行为是性能优化的起点。

### 解析器阻塞矩阵

| 资源类型 | 默认行为 | 阻塞 DOM 解析？ | 阻塞渲染？ |
|----------|---------|:---:|:---:|
| `<script src>` | 同步下载+执行 | ✅ | ✅ |
| `<script src defer>` | 异步下载，DOMContentLoaded 前执行 | ❌ | ❌ |
| `<script src async>` | 异步下载，下载完立即执行 | 执行时阻塞 | ❌ |
| `<link rel="stylesheet">` | 异步下载，但 CSSOM 构建完毕前阻塞渲染 | ❌ | ✅ |
| `<img>` | 异步下载，解码时占用主线程 | ❌ | ❌ |
| `<link rel="preload">` | 提前下载 | ❌ | ❌ |

## 常见问题现象

| 现象 | 根因 |
|------|------|
| `<body>` 中的内容长时间白屏 | `<head>` 中同步 `<script>` 阻塞解析，`<body>` 还未被解析到 |
| 点击事件无反应 | `defer` 脚本还未执行完，或脚本执行时间 > 50ms（成为长任务） |
| DOMContentLoaded 很晚（>3s） | 多个 `defer` 脚本链式等待，或 CSS 在 `defer` 脚本前 |
| 页面先显示无样式内容再闪变 | CSS `<link>` 放在 `<body>` 尾部 |

## 检测方式

### 1. `<head>` 顺序审计
```bash
# 手动检查 head 中的资源声明顺序
# 理想顺序：charset → viewport meta → preload/preconnect → 内联 CSS → 外部 CSS → defer JS
```

### 2. 脚本属性扫描
```bash
# 统计页面中有多少 <script> 缺少 async/defer
# 目标：0 个同步阻塞脚本（除非有充分理由）
```

### 3. Performance API
```js
// 在浏览器控制台中运行
performance.getEntriesByType('navigation').forEach(n => {
  console.log('DOM 解析耗时:', n.domContentLoadedEventEnd - n.responseEnd, 'ms')
  console.log('DOM 交互就绪耗时:', n.domInteractive - n.responseEnd, 'ms')
})
```

### 4. 本技能脚本检测 (`check_resource_hints.py`)
- 扫描所有 `<script>` 缺少 async/defer 的标签
- 检查 `<head>` 中是否出现了不应在此的 `<img>` 或大型内联脚本
- 检查 viewport meta 是否存在（移动端体验相关）

## 优化手段

### 1. 修复 `<head>` 资源顺序

**推荐顺序：**
```html
<head>
  <!-- 1. 字符编码，必须最先 -->
  <meta charset="utf-8">

  <!-- 2. Viewport（移动端必备） -->
  <meta name="viewport" content="width=device-width, initial-scale=1">

  <!-- 3. 预连接到关键第三方源（尽早开始 DNS+TCP+TLS） -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://cdn.example.com">

  <!-- 4. 内联首屏 CSS -->
  <style>/* ATF only */</style>

  <!-- 5. 预加载关键资源 -->
  <link rel="preload" href="/fonts/main.woff2" as="font" crossorigin>

  <!-- 6. 外部 CSS -->
  <link rel="stylesheet" href="/styles.css">

  <!-- 7. 阻塞脚本（仅当绝对必要） -->
  <!-- <script src="/must-be-sync.js"></script> -->
</head>
<body>
  <!-- 内容 -->

  <!-- 8. defer 脚本尽量放 <body> 末尾或按需 -->
  <script src="/app.js" defer></script>
</body>
```

### 2. 消除同步脚本

```html
<!-- ❌ 阻塞解析 -->
<script src="third-party-widget.js"></script>

<!-- ✅ 方案A：defer（保留执行顺序） -->
<script src="third-party-widget.js" defer></script>

<!-- ✅ 方案B：动态加载（完全可控时机） -->
<script>
  const s = document.createElement('script')
  s.src = 'third-party-widget.js'
  s.async = true
  document.body.appendChild(s)
</script>
```

### 3. 减少 HTML 内联资源体积

- 内联 CSS 控制在 14KB 以内（一个 TCP 拥塞窗口的大小）
- 避免内联 Base64 大图（增大 HTML 体积，延迟解析完成）
- 内联关键 SVG icon，其余用 `<img>` 懒加载

### 4. 使用恰当的 HTML 属性

```html
<!-- 给首屏不需要的 iframe 加 loading="lazy" -->
<iframe src="map.html" loading="lazy" title="Store Map"></iframe>

<!-- 给 <details> 提供良好的默认折叠状态 -->
<details>
  <summary>展开查看更多（内部内容不会被立即解析到渲染树）</summary>
  <!-- heavy content -->
</details>
```

## 预期收益

| 优化项 | 影响指标 | 典型提升 |
|--------|---------|----------|
| 所有 `<script>` 加 defer | TBT, FCP | -300ms ~ -800ms TBT |
| `<head>` 资源重排 | FCP, LCP | -0.3s ~ -0.6s |
| 内联 CSS < 14KB | FCP | -0.2s ~ -0.4s |
| 消除 HTML 内 Base64 大图 | TTFB, FCP | -0.1s ~ -0.3s |
