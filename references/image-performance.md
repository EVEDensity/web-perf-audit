# 图片性能

> 对应 web.dev 模块：Image Performance

## 核心概念

图片通常是网页中体积最大的资源类别，平均占页面总大小的 ~50%。在 LCP 指标中，绝大多数页面的 LCP 元素就是一张图片。图片优化是回报率最高的单项优化。

## 常见问题现象

| 现象 | 根因 |
|------|------|
| LCP 指标 > 2.5s | LCP 图片懒加载了、用了低优先级请求 |
| 移动端下载了桌面端大图 | 缺少 srcset/sizes 做响应式图片 |
| 图片模糊然后变清晰 (LQIP) | 未使用 progressive JPEG 或合适的占位方案 |
| 页面跳动（CLS > 0.1） | `<img>` 没有 width/height 显式占位 |
| 图片体积 > 200KB | 未使用现代格式 (WebP/AVIF)，未做压缩 |
| 下方未出现的图片也全部加载 | 缺少 loading="lazy" |

## 检测方式

### 1. Lighthouse 审计
```
modern-image-formats       → 检测是否使用 WebP/AVIF
uses-responsive-images     → 检测 srcset/sizes 使用
offscreen-images           → 检测未懒加载的屏外图片
uses-optimized-images      → 检测可被压缩的图片
image-aspect-ratio         → 检测 width/height 设置
```

### 2. DevTools Network 面板
- 按 Img 过滤，按 Size 降序排序
- 检查每张图片的原始尺寸 vs 显示尺寸

### 3. 本技能脚本（`audit_images.py`）
- 扫描所有 `<img>` 和 CSS background-image
- 计算"实际像素浪费率"（natural size / rendered size）
- 检测格式是否可优化（PNG → WebP, JPEG → AVIF）
- 检查 LCP 候选元素是否被懒加载

## 优化手段

### 1. 响应式图片

```html
<!-- ❌ 所有设备都用同一张大图 -->
<img src="hero-2000px.jpg" alt="Hero">

<!-- ✅ srcset + sizes：让浏览器按需选择 -->
<img
  src="hero-800px.jpg"
  srcset="
    hero-400px.jpg   400w,
    hero-800px.jpg   800w,
    hero-1200px.jpg 1200w,
    hero-2000px.jpg 2000w
  "
  sizes="(max-width: 600px) 100vw, (max-width: 1200px) 50vw, 33vw"
  alt="Hero"
  width="1200"
  height="600"
>

<!-- ✅ <picture> 做艺术方向控制 + 格式降级 -->
<picture>
  <source srcset="hero.avif" type="image/avif">
  <source srcset="hero.webp" type="image/webp">
  <img src="hero.jpg" alt="Hero" width="1200" height="600">
</picture>
```

### 2. 现代图片格式

| 格式 | 压缩率 (vs JPEG) | 浏览器支持 |
|------|:---:|---|
| WebP | -25-35% | 97%+ |
| AVIF | -50% | 93%+ |

```bash
# 批量转换（推荐 sharp CLI 或 ImageMagick）
# WebP
sharp -i input.jpg -o output.webp

# AVIF
sharp -i input.jpg -o output.avif --format avif
```

### 3. 显式宽高（防 CLS）

```html
<!-- ❌ 无尺寸，图片加载后撑开布局 -->
<img src="photo.jpg" alt="">

<!-- ✅ 显式 width/height，浏览器提前预留空间 -->
<img src="photo.jpg" alt="" width="800" height="600">

<!-- ✅ 或在父级容器用 aspect-ratio -->
<div style="aspect-ratio: 4/3; overflow: hidden;">
  <img src="photo.jpg" alt="" style="width:100%; height:100%; object-fit:cover;">
</div>
```

### 4. 懒加载

```html
<!-- ✅ 原生懒加载（除 LCP 候选图片外都加） -->
<img src="below-fold.jpg" alt="" loading="lazy" width="800" height="600">

<!-- ⚠️ LCP 候选图片不要加 loading="lazy"！ -->
<img src="hero.jpg" alt="" width="1200" height="600">
<!-- 不加 loading attr，或用 fetchpriority="high" -->
```

### 5. LCP 图片特殊处理

```html
<!-- ✅ 预加载 LCP 图片 -->
<link rel="preload" as="image" href="/hero.webp" fetchpriority="high">

<!-- ✅ 或直接在 <img> 上加 fetchpriority -->
<img src="hero.webp" alt="" fetchpriority="high" width="1200" height="600">

<!-- ❌ LCP 图片不要从 JS 动态创建 → 浏览器 preload scanner 发现不了 -->
```

### 6. CDN 图片处理

```html
<!-- ✅ 通过 CDN URL 参数动态裁剪/压缩 -->
<!-- Cloudflare: -->
<img src="https://cdn.example.com/photo.jpg?w=800&q=80&f=webp">

<!-- Cloudinary: -->
<img src="https://res.cloudinary.com/demo/image/upload/w_800,q_auto,f_auto/photo.jpg">

<!-- imgix: -->
<img src="https://demo.imgix.net/photo.jpg?w=800&auto=format,compress">
```

## 预期收益

| 优化项 | 影响指标 | 典型提升 |
|--------|---------|----------|
| JPEG/PNG → WebP/AVIF | LCP | -0.5s ~ -2s（取决于图片总体积） |
| 添加 srcset/sizes | LCP (mobile) | -0.3s ~ -1.5s |
| 添加 width/height | CLS | 消除 0.05~0.3 CLS |
| 屏外图片懒加载 | LCP, TBT | -0.2s ~ -0.5s LCP |
| LCP 图片 fetchpriority="high" | LCP | -0.3s ~ -1s |
