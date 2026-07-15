---
name: optimize
description: 识别当前界面的真正性能瓶颈，修复它，然后测量。不要优化不慢的东西。性能是一项功能。
---

性能是一项功能。识别当前界面的真正性能瓶颈，修复它，然后测量。不要优化不慢的东西。

## 评估性能问题

理解当前性能并识别问题：

1. **测量当前状态**：
   - **Core Web Vitals**：LCP、FID/INP、CLS 分数
   - **加载时间**：可交互时间、首次内容绘制
   - **包大小**：JavaScript、CSS、图片大小
   - **运行时性能**：帧率、内存使用、CPU 使用
   - **网络**：请求数量、载荷大小、瀑布图

2. **识别瓶颈**：
   - 什么慢？（初始加载？交互？动画？）
   - 是什么造成的？（大图片？昂贵的 JavaScript？布局抖动？）
   - 有多严重？（可感知？烦人？阻塞？）
   - 谁受影响？（所有用户？仅移动端？慢速连接？）

**关键**：前后测量。过早优化浪费时间。优化真正重要的。

## 优化策略

创建系统化的改进计划：

### 加载性能

**优化图片**：
- 使用现代格式（WebP、AVIF）
- 正确尺寸（不要为 300px 显示加载 3000px 图片）
- 首屏以下图片延迟加载
- 响应式图片（`srcset`、`picture` 元素）
- 压缩图片（80-85% 质量通常不可感知）
- 使用 CDN 加速交付

```html
<img 
  src="hero.webp"
  srcset="hero-400.webp 400w, hero-800.webp 800w, hero-1200.webp 1200w"
  sizes="(max-width: 400px) 400px, (max-width: 800px) 800px, 1200px"
  loading="lazy"
  alt="Hero image"
/>
```

**减少 JavaScript 包**：
- 代码分割（基于路由、基于组件）
- Tree shaking（移除未使用代码）
- 移除未使用的依赖
- 延迟加载非关键代码
- 对大组件使用动态导入

```javascript
// 延迟加载重型组件
const HeavyChart = lazy(() => import('./HeavyChart'));
```

**优化 CSS**：
- 移除未使用的 CSS
- 关键 CSS 内联，其余异步加载
- 最小化 CSS 文件
- 对独立区域使用 CSS containment

**优化字体**：
- 使用 `font-display: swap` 或 `optional`
- 字体子集（只加载需要的字符）
- 预加载关键字体
- 适当使用系统字体
- 限制加载的字重数量

```css
@font-face {
  font-family: 'CustomFont';
  src: url('/fonts/custom.woff2') format('woff2');
  font-display: swap; /* 立即显示降级字体 */
  unicode-range: U+0020-007F; /* 仅基本拉丁字符 */
}
```

**优化加载策略**：
- 关键资源优先（async/defer 非关键资源）
- 预加载关键资源
- 预取可能的下一页
- 用于离线/缓存的 Service worker
- HTTP/2 或 HTTP/3 多路复用

### 渲染性能

**避免布局抖动**：
```javascript
// ❌ 不好：交替读取和写入（导致重排）
elements.forEach(el => {
  const height = el.offsetHeight; // 读取（强制布局）
  el.style.height = height * 2; // 写入
});

// ✅ 好：批量读取，然后批量写入
const heights = elements.map(el => el.offsetHeight); // 所有读取
elements.forEach((el, i) => {
  el.style.height = heights[i] * 2; // 所有写入
});
```

**优化渲染**：
- 对独立区域使用 CSS `contain` 属性
- 最小化 DOM 深度（更扁平更快）
- 减少 DOM 大小（更少的元素）
- 对长列表使用 `content-visibility: auto`
- 超长列表使用虚拟滚动（react-window、react-virtualized）

**减少绘制与合成**：
- 使用 `transform` 和 `opacity` 实现可靠的移动，但当它们创造有意义的润色时允许 blur、filters、masks、clip paths、shadows 和 color shifts
- 避免随意动画化布局驱动属性（`width`、`height`、`top`、`left`、margins）
- 对已知昂贵操作少量使用 `will-change`
- 将 blur/filter/shadow 效果的昂贵绘制区域限制在小范围或隔离区域

### 动画性能

**GPU 加速**：
```css
/* ✅ GPU 加速（快） */
.animated {
  transform: translateX(100px);
  opacity: 0.5;
}

/* ❌ CPU 绑定（慢） */
.animated {
  left: 100px;
  width: 300px;
}
```

**流畅 60fps**：
- 每帧目标 16ms（60fps）
- JS 动画使用 `requestAnimationFrame`
- 滚动处理防抖/节流
- 尽可能使用 CSS 动画
- 动画期间避免长耗时 JavaScript

**Intersection Observer**：
```javascript
// 高效检测元素何时进入视口
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      // 元素可见，延迟加载或动画
    }
  });
});
```

### React/框架优化

**React 特定**：
- 对昂贵组件使用 `memo()`
- 对昂贵计算使用 `useMemo()` 和 `useCallback()`
- 长列表虚拟化
- 路由代码分割
- 避免 render 中内联函数创建
- 使用 React DevTools Profiler

**框架无关**：
- 最小化重新渲染
- 昂贵操作防抖
- 计算值记忆化
- 路由和组件延迟加载

### 网络优化

**减少请求**：
- 合并小文件
- 图标使用 SVG sprite
- 内联小型关键资源
- 移除未使用的第三方脚本

**优化 API**：
- 使用分页（不要加载所有内容）
- GraphQL 只请求需要的字段
- 响应压缩（gzip、brotli）
- HTTP 缓存头
- 静态资源 CDN

**慢速连接优化**：
- 基于连接的自适应加载（navigator.connection）
- 乐观 UI 更新
- 请求优先级
- 渐进增强

## Core Web Vitals 优化

### Largest Contentful Paint (LCP < 2.5s)
- 优化首屏图片
- 内联关键 CSS
- 预加载关键资源
- 使用 CDN
- 服务端渲染

### First Input Delay (FID < 100ms) / INP (< 200ms)
- 拆分长任务
- 延迟非关键 JavaScript
- 重型计算使用 Web workers
- 减少 JavaScript 执行时间

### Cumulative Layout Shift (CLS < 0.1)
- 为图片和视频设置尺寸
- 不要在现有内容上方注入内容
- 使用 `aspect-ratio` CSS 属性
- 为广告/嵌入预留空间
- 避免导致布局偏移的动画

```css
/* 为图片预留空间 */
.image-container {
  aspect-ratio: 16 / 9;
}
```

## 性能监控

**使用工具**：
- Chrome DevTools（Lighthouse、Performance 面板）
- WebPageTest
- Core Web Vitals（Chrome UX Report）
- 包分析器（webpack-bundle-analyzer）
- 性能监控（Sentry、DataDog、New Relic）

**关键指标**：
- LCP、FID/INP、CLS（Core Web Vitals）
- 可交互时间（TTI）
- 首次内容绘制（FCP）
- 总阻塞时间（TBT）
- 包大小
- 请求数量

**重要**：在真实设备和真实网络条件下测量。带快速连接的桌面 Chrome 不具代表性。

**绝不**：
- 没有测量就优化（过早优化）
- 为性能牺牲无障碍
- 优化时破坏功能
- 到处使用 `will-change`（创建新层，占用内存）
- 首屏内容延迟加载
- 忽略主要问题而优化微优化（首先优化最大瓶颈）
- 忘记移动端性能（通常设备更慢、连接更慢）

## 验证改进

测试优化是否有效：

- **前后指标**：比较 Lighthouse 分数
- **真实用户监控**：跟踪真实用户的改进
- **不同设备**：在低端 Android 上测试，不只是旗舰 iPhone
- **慢速连接**：限流到 3G，测试体验
- **无回归**：确保功能仍然工作
- **用户感知**：它*感觉*更快了吗？

当面向用户的数字改善时，交给 `/yo-ui polish` 做最终润色。