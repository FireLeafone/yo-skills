# 架构图

> 本文件用于**系统/技术类主题**的架构图；概念/原理类主题请改用 `simple-diagram.md`。

创建专业的架构图，输出为自包含的 HTML 文件，内嵌 SVG 图形与 CSS 样式。

## 设计系统

### 调色板

按组件类型使用以下语义化颜色：

| 组件类型 | 填充色 (rgba) | 描边色 |
|---------------|-------------|--------|
| 1 | `rgba(8, 51, 68, 0.4)` | `#22d3ee`（青色-400） |
| 2 | `rgba(6, 78, 59, 0.4)` | `#34d399`（翡翠绿-400） |
| 3 | `rgba(76, 29, 149, 0.4)` | `#a78bfa`（紫罗兰-400） |
| 4 | `rgba(120, 53, 15, 0.3)` | `#fbbf24`（琥珀色-400） |
| 5 | `rgba(136, 19, 55, 0.4)` | `#fb7185`（玫瑰红-400） |
| 6 | `rgba(251, 146, 60, 0.3)` | `#fb923c`（橙色-400） |
| 7 | `rgba(30, 41, 59, 0.5)` | `#94a3b8`（石板灰-400） |

### 字体排版

所有文字统一使用 JetBrains Mono（等宽字体，更具技术感）：
```html
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
```

字号：组件名称 12px、副标签 9px、注释 8px、微小标签 7px。

### 视觉元素

**背景：** `#020617`（石板灰-950），带细微网格图案：
```svg
<pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
  <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#1e293b" stroke-width="0.5"/>
</pattern>
```

**组件方框：** 圆角矩形（`rx="6"`），1.5px 描边、半透明填充。

**安全组：** 虚线描边（`stroke-dasharray="4,4"`）、透明填充、玫红色。

**区域边界：** 更大间距的虚线描边（`stroke-dasharray="8,4"`）、琥珀色、`rx="12"`。

**箭头：** 使用 SVG marker 绘制箭头头部：
```svg
<marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
  <polygon points="0 0, 10 3.5, 0 7" fill="#64748b" />
</marker>
```

**箭头层级顺序：** 在 SVG 中较早绘制连接箭头（放在背景网格之后），使它们渲染在组件方框的后面。SVG 元素按文档顺序绘制，因此先绘制的箭头会显示在后来绘制的图形后面。

**在半透明填充后遮蔽箭头：** 由于组件方框使用半透明填充（`rgba(..., 0.4)`），其后的箭头会透显出来。要完全遮蔽箭头，可先在相同位置绘制一个不透明的背景矩形（如 `fill="#0f172a"`），再在其上绘制半透明的样式化矩形：
```svg
<!-- 不透明背景，用于遮蔽箭头 -->
<rect x="X" y="Y" width="W" height="H" rx="6" fill="#0f172a"/>
<!-- 上层样式化组件 -->
<rect x="X" y="Y" width="W" height="H" rx="6" fill="rgba(76, 29, 149, 0.4)" stroke="#a78bfa" stroke-width="1.5"/>
```

**认证/安全流程：** 玫红色（`#fb7185`）虚线。

**消息总线/事件总线：** 服务之间的小型连接元素。使用橙色（描边 `#fb923c`、填充 `rgba(251, 146, 60, 0.3)`）：
```svg
<rect x="X" y="Y" width="120" height="20" rx="4" fill="rgba(251, 146, 60, 0.3)" stroke="#fb923c" stroke-width="1"/>
<text x="CENTER_X" y="Y+14" fill="#fb923c" font-size="7" text-anchor="middle">Kafka / RabbitMQ</text>
```

### 间距规则

**关键：** 纵向堆叠组件时，务必留出充足间距，避免重叠：

- **标准组件高度：** 服务 60px，较大的组件 80-120px
- **组件之间的最小垂直间距：** 40px
- **内联连接器（消息总线）：** 放置在组件之间的间隙内，不要重叠

**纵向布局示例：**
```
组件 A：y=70，高 60 → 结束于 y=130
间隙：  y=130 至 y=170 → 40px 间隙，总线放在 y=140（高 20px）
组件 B：y=170，高 60 → 结束于 y=230
```

**错误做法：** 组件 B 从 y=170 开始，却把消息总线放在 y=160（导致重叠）
**正确做法：** 把消息总线放在 y=140，居中于 40px 间隙内（y=130 至 y=170）

### 图例摆放

**关键：** 图例要放在所有边界框（区域边界、集群边界、安全组）之外。

- 计算所有边界的结束位置（y 坐标 + 高度）
- 图例放在最低边界下方至少 20px 处
- 必要时扩展 SVG viewBox 高度以容纳图例

**示例：**
```
Kubernetes 集群：y=30，高 460 → 结束于 y=490
图例应起始于：y=510 或更下
SVG viewBox 高度：至少 560 以容纳图例
```

**错误做法：** 图例放在 y=470，位于结束于 y=490 的集群边界内部
**正确做法：** 图例放在 y=510，位于集群边界下方，并扩展 viewBox 高度

### 布局结构

1. **页头** - 带脉动圆点指示器的标题、副标题和导出工具栏
2. **主 SVG 图** - 置于圆角边框卡片内
3. **概要卡片** - 图下方 3 张卡片组成的网格，展示关键信息
4. **页脚** - 极简的元数据行

### 导出工具栏（内置）

每张图都会在页头内置一个不起眼的 `⋯` 切换按钮。点击后展开三个按钮——📋 复制（高分辨率 PNG 复制到剪贴板，缩放比例 2）、🖼️ PNG（下载高分辨率 PNG）、📄 PDF（通过 jsPDF 将 PNG 嵌入单页 PDF）。工具栏默认收起为图标，以免遮挡图面。三种格式都使用相同的 html2canvas 截图（排除工具栏，内容四周留 32px 内边距），因此 PDF 能保留深色主题，无需走浏览器打印对话框。

生成新图时，请保持模板中的以下内容不变：

- `<head>` 中的两个 CDN 脚本（固定版本，带 Subresource Integrity 哈希与 `crossorigin="anonymous"`）：
  - `https://cdn.jsdelivr.net/npm/html2canvas@1.4.1/dist/html2canvas.min.js` — `integrity="sha384-ZZ1pncU3bQe8y31yfZdMFdSpttDoPmOZg2wguVK9almUodir1PghgT0eY7Mrty8H"`
  - `https://cdn.jsdelivr.net/npm/jspdf@2.5.2/dist/jspdf.umd.min.js` — `integrity="sha384-en/ztfPSRkGfME4KIm05joYXynqzUgbsG5nMrj/xEFAHXkeZfO3yMK8QQ+mP7p1/"`
  - SRI 可确保生成的图在 CDN 遭篡改时具备防篡改校验能力。不要修改这些哈希；若升级版本号，必须重新计算新哈希。
- 最外层 `.container` div 上的 `id="report-container"`（这是被截图的对象）
- `.toolbar` 标记，包含 `.toolbar-actions`（默认收起）与 `.toolbar-toggle`（即 `⋯` 按钮）
- `.toolbar` 的 CSS 及 `@media print { .toolbar { display: none !important; } }`
- `</body>` 之前的 `copyAsImage()`、`downloadPNG()` 与 `downloadPDF()` 脚本，均使用 `getBoundingClientRect()` + `html2canvas(document.body, { x, y, width, height, ignoreElements })` 精确截取带有留白且不含工具栏的矩形区域

注意事项：剪贴板 API 需要用户手势且处于安全上下文（https/file/localhost）。SVG `<foreignObject>` 在 html2canvas 中渲染不一致——尽量使用纯 `<svg>` 形状与 `<text>`。如需更高分辨率输出，可将 `scale: 2` 提升到 `3` 或 `4`。

### 组件方框模板

```svg
<rect x="X" y="Y" width="W" height="H" rx="6" fill="FILL_COLOR" stroke="STROKE_COLOR" stroke-width="1.5"/>
<text x="CENTER_X" y="Y+20" fill="white" font-size="11" font-weight="600" text-anchor="middle">LABEL</text>
<text x="CENTER_X" y="Y+36" fill="#94a3b8" font-size="9" text-anchor="middle">sublabel</text>
```

### 信息卡片模板

```html
<div class="card">
  <div class="card-header">
    <div class="card-dot COLOR"></div>
    <h3>Title</h3>
  </div>
  <ul>
    <li>• 条目一</li>
    <li>• 条目二</li>
  </ul>
</div>
```

## 模板

复制 `resources/template.html` 中的模板并按需定制。关键定制点：

1. 更新 `<title>` 和页头文字
2. 按需修改 SVG viewBox 尺寸（默认：`1000 x 680`）
3. 添加/删除/调整组件方框位置
4. 在组件之间绘制连接箭头
5. 更新三张概要卡片
6. 更新页脚元数据

## 输出

始终产出一个自包含的 `.html` 文件，要求：

- 内嵌 CSS（除 Google Fonts 外不引用外部样式表）
- 内联 SVG（不引用外部图片）
- 无需 JavaScript（纯 CSS 动画）

该文件在任意现代浏览器中直接打开即可正常渲染。导出工具栏使用两个 CDN 脚本（html2canvas 和 jsPDF），除此之外无其他 JavaScript 依赖。
