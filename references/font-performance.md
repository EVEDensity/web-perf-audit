# Web 字体性能

> 对应 web.dev 模块：Optimize Web Fonts

## 核心概念

Web 字体是 FOIT（Flash of Invisible Text，文字闪隐）和 FOUT（Flash of Unstyled Text，文字闪变）的根源。如果在字体加载完成前文字不可见，用户感知到的白屏时间会显著延长；如果文字发生跳变（回退字体与自定义字体尺寸不同），CLS 也会受到影响。

### 字体加载时间线

```
请求页面 → 下载 HTML → 下载 CSS → 发现 @font-face → 下载字体文件 → 字体可用
                                                    ↑                    ↑
                                               FOIT 开始             FOIT/FOUT 结束
```

## 常见问题现象

| 现象 | 根因 |
|------|------|
| 页面打开 3 秒内文字完全不可见 | `font-display: block` 或未设置，浏览器默认 FOIT 行为 |
| 文字从 Arial 跳变成自定义字体 | FOUT，`font-display: swap` 的正常行为（可控制） |
| 布局因字体变化而抖动 (CLS) | 回退字体与自定义字体的度量（metrics）差异大 |
| 字体文件 > 100KB | 未做子集化（包含了不需要的字符） |
| 字体加载慢 | 未 preload，或通过 Google Fonts 等第三方下载 |
| 文档用了 6 个字重但只用到 2 个 | 无用字重被下载，浪费带宽 |

## 检测方式

### 1. DevTools Network 面板
- 筛选 Font，检查每个字体文件的 Size 和 Time
- 观察字体请求和首屏文字显示的时序关系

### 2. CSS 覆盖检查
```js
// 检查 @font-face 的 font-display 设置
[...document.styleSheets].forEach(sheet => {
  try {
    [...sheet.cssRules].forEach(rule => {
      if (rule.constructor.name === 'CSSFontFaceRule') {
        console.log(rule.style.fontFamily, rule.style.fontDisplay)
      }
    })
  } catch(e) {}
})
```

### 3. 本技能脚本（`audit_fonts.py`）
- 解析所有 @font-face 规则
- 统计实际使用的字重（和声明的对比）
- 检测 font-display 设置
- 检查是否有未 preload 的关键字体
- 检查字体文件是否来自第三方（需要 preconnect）

## 优化手段

### 1. font-display 策略

```css
/* ✅ swap: 立即显示回退字体，字体加载完后切换（推荐） */
@font-face {
  font-family: 'MyFont';
  src: url('/fonts/myfont.woff2') format('woff2');
  font-display: swap;
}

/* ✅ optional: 字体可有可无，100ms 内没加载完就用回退（极端性能优先） */
@font-face {
  font-family: 'DecorativeFont';
  src: url('/fonts/deco.woff2') format('woff2');
  font-display: optional;
}

/* ❌ block: FOIT 可达 3s（不推荐） */
@font-face {
  font-family: 'SlowFont';
  src: url('/fonts/slow.woff2') format('woff2');
  font-display: block;   /* 避免 */
}
```

**决策表：**
| 场景 | 推荐 font-display |
|------|------------------|
| 正文字体（必须加载） | `swap` |
| 图标字体 | `block` 或 `swap` |
| 品牌/装饰字体 | `optional` |

### 2. 字体文件子集化

```bash
# 使用 glyphhanger 或 fonttools 子集化
# 仅保留页面用到的字符
glyphhanger --subset=*.woff2 --US_ASCII

# 或指定字符范围
pyftsubset font.woff2 --unicodes="U+0020-007E,U+00A9,U+00AE" --output-file="font-subset.woff2"
```

### 3. 预加载关键字体

```html
<!-- ✅ 关键字体（正文字体、图标字体）预加载 -->
<link rel="preload" href="/fonts/body.woff2" as="font" type="font/woff2" crossorigin>

<!-- ⚠️ crossorigin 必须加！即使是同源 -->
```

### 4. 兼容现代字体格式

```css
/* ✅ 提供 woff2（压缩率最优）作为首选 */
@font-face {
  font-family: 'MyFont';
  src: url('/fonts/myfont.woff2') format('woff2'),
       url('/fonts/myfont.woff') format('woff');  /* 兜底 */
  font-display: swap;
}
```

### 5. 减少字重数量

```css
/* ❌ 加载所有字重 */
/* 导致 6 个字体文件下载 */

/* ✅ 只加载实际用到的字重 */
/* 仅保留 400 (Regular) 和 700 (Bold) */
```

### 6. 使用系统字体栈（零额外下载）

```css
/* ✅ 零成本高性能方案 */
body {
  font-family:
    system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial,
    'Noto Sans', sans-serif;
}
```

### 7. size-adjust 减少 CLS

```css
/* ✅ CSS 新特性：补偿回退字体与自定义字体的度量差异 */
@font-face {
  font-family: 'MyFont';
  src: url('/fonts/myfont.woff2') format('woff2');
  font-display: swap;
  size-adjust: 105%;  /* 让回退字体放大 5% 以匹配自定义字体宽度 */
}
```

## 预期收益

| 优化项 | 影响指标 | 典型提升 |
|--------|---------|----------|
| font-display: swap | LCP (含文字), FCP | -0.5s ~ -2s |
| 字体子集化 | LCP | -0.3s ~ -1s（体积 -60-80%） |
| 预加载关键字体 | LCP, CLS | -0.3s ~ -0.8s |
| 使用系统字体栈 | LCP | -0.5s ~ -2s（零下载） |
| size-adjust | CLS | 消除 0.02~0.1 CLS |
