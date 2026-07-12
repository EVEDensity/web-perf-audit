# 视频性能

> 对应 web.dev 模块：Video Performance

## 核心概念

视频通常是单个体积最大的资源。一个未经优化的 10 秒 Hero 背景视频可能达到 20MB+，对大屏尤其致命——不仅拖累 LCP，大量解码还会导致主线程长任务，恶化 INP。

## 常见问题现象

| 现象 | 根因 |
|------|------|
| 页面打开后 5 秒视频才开始播放 | 视频文件过大，下载耗时太长 |
| 自动播放的背景视频卡顿 | 编码参数不当（码率过高、分辨率大于实际展示尺寸） |
| 滚动/点击不流畅 | 视频解码占用主线程 |
| 移动端消耗大量流量 | 未做移动端降级（显示静态 poster 替代） |
| 首屏 LCP 被视频拖慢 | 视频在 Hero 区域且未设置 poster |

## 检测方式

### 1. Network 面板
- 筛选 Media，按 Size 降序，找出体积 > 1MB 的视频
- 检查是否使用了 Range 请求（字节范围请求）来支持分片加载

### 2. 本技能脚本检测
- 扫描 `<video>` 标签是否缺少 `poster`、`preload="none"`
- 检测视频文件格式（MP4/H.264 vs WebM/VP9 vs HEVC）
- 对比视频原始分辨率 vs 实际显示尺寸

## 优化手段

### 1. 添加 poster + 控制预加载

```html
<!-- ❌ 无 poster，自动下载视频 -->
<video src="hero-bg.mp4" autoplay muted loop></video>

<!-- ✅ 有 poster（首帧占位），preload="none" 或 "metadata" -->
<video
  src="hero-bg.mp4"
  poster="hero-poster.webp"
  preload="none"
  autoplay
  muted
  loop
  playsinline
  width="1920"
  height="1080"
></video>
```

### 2. 移动端降级

```html
<!-- ✅ 移动端不加载视频，只显示静态图 -->
<picture>
  <source srcset="hero-bg.mp4" media="(min-width: 768px)" type="video/mp4">
  <img src="hero-bg-mobile.webp" alt="" width="375" height="667">
</picture>
```

或通过 JS 判断：
```js
if (window.innerWidth >= 768) {
  const video = document.createElement('video')
  video.src = 'hero-bg.mp4'
  // ...
} else {
  // 移动端直接用图片
}
```

### 3. 视频压缩参数建议

| 用途 | 推荐格式 | 码率建议 | 分辨率建议 |
|------|---------|---------|-----------|
| Hero 背景视频 | MP4 (H.264) | 1-2 Mbps | ≤ 1920px 宽 |
| 内容讲解视频 | MP4 (H.264) | 0.5-1 Mbps | ≤ 1280px 宽 |
| 短视频预览 | WebM (VP9) | 0.3-0.5 Mbps | ≤ 640px 宽 |

```bash
# FFmpeg 压缩示例：适合背景视频
ffmpeg -i input.mp4 \
  -c:v libx264 -crf 28 -preset slow \
  -an \                    # 如果 mute，直接去掉音频轨道
  -movflags +faststart \   # 流式加载
  -vf "scale=1920:-2" \    # 控制最大宽度
  output.mp4
```

### 4. 流式传输

```html
<!-- ✅ 使用 HLS/DASH 做自适应码率 -->
<video>
  <source src="video-720p.mp4" type="video/mp4" media="(min-width: 1280px)">
  <source src="video-480p.mp4" type="video/mp4" media="(min-width: 640px)">
  <source src="video-360p.mp4" type="video/mp4">
</video>
```

### 5. 用 GIF 替代方案

```html
<!-- ❌ GIF 10MB+ -->
<img src="demo.gif" alt="">

<!-- ✅ 用 <video> 替换动画 GIF -->
<video src="demo.mp4" autoplay loop muted playsinline width="800" height="600"></video>
<!-- 同样的视觉效果，体积可缩小 90% -->
```

## 预期收益

| 优化项 | 影响指标 | 典型提升 |
|--------|---------|----------|
| 添加 poster + preload="none" | LCP | -1s ~ -3s |
| GIF → MP4 | LCP, FCP | 体积 -80~95% |
| 移动端降级为静态图 | LCP (mobile) | -2s ~ -5s |
| 视频压缩 (crf 28) | LCP | -0.5s ~ -2s |
