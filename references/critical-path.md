# 关键渲染路径 (Critical Rendering Path)

> 对应 web.dev 模块：Why Speed Matters / Critical Rendering Path

## 核心概念

关键渲染路径（CRP）是浏览器将 HTML/CSS/JS 转换为屏幕上像素所经历的最小必要步骤序列。优化 CRP 就是缩短从"用户请求页面"到"首屏内容可交互"的时间。

### 五步流水线

```
HTML → DOM Tree
CSS  → CSSOM Tree
        ↓
   Render Tree (DOM + CSSOM 的交集，排除 display:none 节点)
        ↓
   Layout (计算每个节点的几何位置与尺寸)
        ↓
   Paint (将布局结果转化为像素)
```

## 常见问题现象

| 现象 | 根因 | 影响的 CWV 指标 |
|------|------|----------------|
| 白屏时间超过 2s | CSS/JS 阻塞 DOM 解析，Render Tree 迟迟无法构建 | LCP、FCP |
| 页面文字闪烁/样式跳变 (FOUC) | CSS 加载顺序不对，或 @import 嵌套过深 | LCP、CLS |
| 交互按钮点击无效 | 同步 JS 阻塞主线程，事件处理器尚未绑定 | INP、TBT |
| 首屏图片出现在 3s 以后 | 图片 URL 隐藏在 JS/CSS 中，浏览器预加载扫描器发现不了 | LCP |

## 检测方式

### 1. Lighthouse 审计项
```
render-blocking-resources    → 列出阻塞首次渲染的 CSS/JS
critical-request-chains      → 展示关键请求链的长度与耗时
dom-size                     → DOM 节点数 > 1500 会显著拖慢 Layout
```

### 2. Chrome DevTools Performance 面板
- 录制加载过程，观察 Main 线程上的 "Parse HTML"、"Evaluate Script"、"Layout" 块
- 在 Timings 轨道上对比 FCP / LCP 时间点

### 3. WebPageTest
- 导出 waterfall 图，确认 "Start Render" 时刻前加载了哪些资源
- 关注 "render-blocking" 标记的资源

### 4. 程序化检测（本技能脚本 `analyze_critical_path.py`）
- 解析 Lighthouse JSON 中的 `audits['render-blocking-resources']`
- 统计关键请求链深度和总字节数
- 计算关键路径的理论最短时间（链上资源下载+解析时间的累加）

## 优化手段

### 1. 消除渲染阻塞 CSS

**问题代码：**
```html
<!-- 阻塞渲染：浏览器必须等待这个 CSS 下载并解析完 -->
<link rel="stylesheet" href="styles.css">
```

**修复方案：**
```html
<!-- 方案A：内联首屏关键 CSS -->
<style>
  /* 只放 ATF (Above The Fold) 样式，一般 < 14KB */
  body { margin: 0; font-family: system-ui; }
  .hero { display: flex; min-height: 100vh; }
</style>

<!-- 方案B：剩余 CSS 用 media 属性延迟 -->
<link rel="stylesheet" href="full-styles.css" media="print" onload="this.media='all'">

<!-- 方案C：preload + 异步加载 -->
<link rel="preload" href="styles.css" as="style" onload="this.rel='stylesheet'">
```

### 2. 消除渲染阻塞 JS

**问题代码：**
```html
<!-- 阻塞 HTML 解析器，直到脚本下载+执行完毕 -->
<script src="app.js"></script>
```

**修复方案：**
```html
<!-- async: 下载不阻塞，下载完立即执行（适合独立脚本） -->
<script src="analytics.js" async></script>

<!-- defer: 下载不阻塞，等 DOM 解析完再按顺序执行（推荐） -->
<script src="app.js" defer></script>

<!-- 对真正关键的内联脚本可以考虑保留在 <head> 中但不操作 DOM -->
```

### 3. 减少关键请求链深度

**检查清单：**
- 主页 HTML 引用的 CSS 中，是否有 `@import`？（`@import` 会串行化请求）
- 关键资源是否来自多个不同域名？（每个新域名需要 DNS + TCP + TLS 握手）
- CSS 中的 `url()` 引用的字体/图片是否在首屏必要？

**修复代码示例：**
```css
/* ❌ 串行请求：HTML → CSS → @import 的 CSS → 字体 */
@import url('reset.css');

/* ✅ 用 link 标签并行加载，或将 reset 合并到主 CSS */
```

### 4. 控制 DOM 大小

- 首次渲染的 DOM 节点数控制在 ~800 以内
- 对长列表使用虚拟滚动（virtual scrolling）
- 避免深层嵌套（> 32 层）

## 预期收益

| 优化项 | 预计影响 | 典型提升 |
|--------|---------|----------|
| 内联首屏 CSS (<14KB) | LCP | -0.5s ~ -1.5s |
| JS 全部 defer | TBT, INP | -200ms ~ -500ms TBT |
| 消除 @import 链 | FCP | -0.3s ~ -0.8s |
| 减少 DOM 节点 | LCP, CLS | -0.2s ~ -0.5s LCP |
