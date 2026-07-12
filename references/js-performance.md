# JavaScript 性能

> 对应 web.dev 模块：Code-split JavaScript / Lazy-load iframe / Web Worker

## 核心概念

JS 是 Web 性能的"双刃剑"：它赋予页面交互能力，也是 TBT（Total Blocking Time）和 INP（Interaction to Next Paint）的主要来源。核心目标：**减少主线程阻塞时间，确保每段 JS 执行 < 50ms**。

### 长任务（Long Task）机制

```
主线程上任何连续执行 > 50ms 的任务都称为 Long Task。
Long Task 的总和 = TBT。
当用户交互落在 Long Task 期间，交互延迟 = INP 变差。
```

## 常见问题现象

| 现象 | 根因 |
|------|------|
| FID/INP > 200ms | 事件处理器与 Long Task 竞争主线程 |
| TBT > 300ms | 首屏加载阶段执行了过多 JS（大 bundle、hydration） |
| 点击按钮 500ms 后才响应 | JS bundle 过大，主线程忙于解析/编译/执行 |
| Lighthouse 报 `unused-javascript` | 代码分割不当，用户下载了不用的代码 |
| 首次交互延迟 | SPA hydration 阻塞了事件绑定 |

## 检测方式

### 1. Lighthouse 审计
```
unused-javascript          → Coverage 数据，多少 JS 未被执行
unminified-javascript      → 是否缺少压缩
duplicated-javascript      → 是否重复打包了相同模块
legacy-javascript          → 是否包含不必要的 polyfill
third-party-summary        → 第三方脚本的主线程占用
```

### 2. Chrome DevTools Performance 面板
- 录制 → 查看 Main 线程 → 标记 > 50ms 的黄色块（Long Task）
- 查看 Bottom-Up / Call Tree，定位耗时函数

### 3. Coverage 面板
- 加载页面 → 简单交互 → 查看 JS 使用率 (Usage %)
- 目标：首屏 JS 使用率 > 60%

### 4. 本技能脚本（`audit_js_bundles.py`）
- Puppeteer 采集 Coverage 数据
- 统计每个 bundle 的未使用字节数
- 识别超过 50ms 的长任务
- 检测是否有重复模块

## 优化手段

### 1. 代码分割 (Code Splitting)

```js
// ❌ 静态导入：所有代码在首屏加载
import HeavyChart from './heavy-chart.js'

// ✅ 动态导入：按需加载
button.addEventListener('click', async () => {
  const { default: HeavyChart } = await import('./heavy-chart.js')
  HeavyChart.render()
})

// ✅ React: lazy + Suspense
const HeavyChart = React.lazy(() => import('./HeavyChart'))
```

### 2. Web Worker 卸载重计算

```js
// ❌ 主线程处理大量数据
const result = heavyProcess(largeDataArray)  // 阻塞 > 200ms

// ✅ 移到 Worker
const worker = new Worker('/workers/data-processor.js')
worker.postMessage(largeDataArray)
worker.onmessage = (e) => {
  const result = e.data
  updateUI(result)
}
```

### 3. 懒加载 iframe

```html
<!-- ❌ 加载页面时就加载所有 iframe -->
<iframe src="map.html"></iframe>

<!-- ✅ 懒加载 -->
<iframe src="map.html" loading="lazy" title="Store Location Map"></iframe>

<!-- ✅ 或完全按需创建（对性能影响最大的 iframe） -->
<script>
  document.querySelector('#show-map-btn').addEventListener('click', () => {
    const iframe = document.createElement('iframe')
    iframe.src = 'map.html'
    iframe.loading = 'lazy'
    document.querySelector('#map-container').appendChild(iframe)
  })
</script>
```

### 4. 减少第三方脚本影响

```html
<!-- ✅ 对非关键第三方脚本使用 async/defer -->
<script src="https://platform.twitter.com/widgets.js" async defer></script>

<!-- ✅ 或用 Facade 模式：先显示静态按钮，点击时才加载真实脚本 -->
<!-- 参考：lite-youtube, react-lite-twitter 等实现 -->
```

### 5. Bundle 体积控制

```js
// webpack.config.js 或 vite.config.js
// ✅ Tree Shaking 的前提：使用 ES Module
import { debounce } from 'lodash-es'  // ✅ 只导入需要的
// vs
import _ from 'lodash'               // ❌ 全量导入

// ✅ 检查 bundle 内容
// npx webpack-bundle-analyzer stats.json
// npx vite-bundle-visualizer
```

### 6. 脚本执行时机优化

```js
// ✅ 将非关键初始化推迟到空闲时间
if ('requestIdleCallback' in window) {
  requestIdleCallback(() => {
    // 初始化 analytics、加载评论组件等
    initAnalytics()
  })
} else {
  // 降级方案：延迟执行
  setTimeout(initAnalytics, 200)
}
```

### 7. 使用 `script-pre` 属性，script 分阶段执行

```html
<!-- 实验性：控制脚本执行的优先级 -->
<script type="module" src="critical.js"></script>
<script type="module" src="non-critical.js" blocking="none"></script>
<!-- 但兼容性有限，暂不推荐广泛使用 -->
```

## 预期收益

| 优化项 | 影响指标 | 典型提升 |
|--------|---------|----------|
| 代码分割 + 动态 import | TBT, LCP | -200ms ~ -800ms TBT |
| Web Worker 卸载计算 | INP, TBT | -100ms ~ -500ms INP |
| iframe 懒加载 | TBT | -100ms ~ -300ms TBT |
| 清理未使用 JS | TBT, LCP | -100ms ~ -400ms TBT |
| requestIdleCallback | INP | -50ms ~ -200ms INP |
