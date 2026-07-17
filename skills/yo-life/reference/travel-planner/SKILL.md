---
name: travel-planner
description: >
  面向旅行顾问与定制游服务商的旅行策划与路书交付 Skill。把简版行程资料（文本/截图/文档/XLS）解析为结构化
  tripData.json，并默认自动执行交付级流水线（每日正文润色 → 亮点/费用/服务 LLM → 住宿飞猪简介 → 小红书
  strict 配图 → 校验 → HTML/PDF），产出可直接交付客户的 roadbook-v2 路书；亦支持目的地推荐、多维信息采集、
  行程编排与预算编制。当用户提到旅行计划、行程规划、路书、roadbook、行程单、报价单、定制游方案时使用。
---

# Travel Planner · 旅行策划与路书交付

把客户资料变成 **可直接给客户看的 roadbook-v2 HTML**，并保留可编辑的 `tripData.json`。输出为中文。

**两种工作模式**：

| 模式 | 触发 | 产出 |
|------|------|------|
| **路书交付**（默认） | 客户简版资料（文本/截图/文档/XLS）、「生成路书」「给客户看的行程单」 | `tripData.json` + 交付级 roadbook-v2 HTML/PDF |
| **旅行策划** | 「帮我规划去哪玩」「做个旅行计划」（无客户资料） | 目的地推荐 + 行程方案 + 旅行计划 HTML |

细则见 `references/roadbook-v2-delivery.md` 与 `references/trip-planning.md`。

## 硬性规则（违反即视为未完成）

1. **默认跑交付流水线**：`tripData.json` 就绪后，在仓库根执行 `scripts/deliver_roadbook_v2.py`。**禁止**问用户「要不要完整交付 / 补图 / 校验 / 跑小红书」。
2. **日期写死**：deliver 必须带 `--check-in` / `--check-out`（客户首晚入住/离店）。缺日期时最少字数追问日期，不问「要不要交付」。
3. **默认 strict 配图**：不加 `--allow-local-placeholders`；配图必须 https 远端 URL。小红书接口异常时流水线自动降级仍生成 HTML，但须在回复中注明降级、提醒人工核对配图与正文。
4. **文案每次重写**：住宿简介（`--hotel-force` 默认开）、每日正文、亮点/费用/服务均默认 `--force` 重跑；仅当需保留已达字数旧稿时才加 `--no-hotel-force` / `--no-daily-force` / `--no-copy-llm-force`。
5. **草稿/离线须用户明示**：仅当用户明文说「草稿 / 预览 / 离线」才加 `--allow-local-placeholders`，并在回复中标注 **非交付稿**。
6. **数据诚实**：报价按实查 / 参考（`~`）/ 估算（`≈`）分级标注；不得编造未包含项目、精确票价与班次。

## 一键命令

### 交付（默认）

```bash
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
python3 scripts/deliver_roadbook_v2.py \
  "路书目录/tripData.json" \
  "路书目录/路书名.html" \
  --check-in YYYY-MM-DD \
  --check-out YYYY-MM-DD
# 可选：--intake-brief "路书目录/sources/itinerary-brief.txt"  从简表刷新费用/服务正文
# 草稿（须用户明示）：末尾加 --allow-local-placeholders
```

退出码：`0` = strict 交付成功；`2` = 已降级（不可直接交付，须人工核对）；需要「一步失败即退出」时加 `--fail-fast`。

### 录入（简表 → tripData 首版）

```bash
python3 scripts/roadbook_intake.py --input <brief.txt|brief.docx> --output-dir <目的地-年月> \
  [--render --html-name 路书名.html]
```

Intake 的 `--render` 只产首版，**对客户交付仍须再跑上面的 deliver 流水线**。

## 交付流水线（deliver 内部顺序）

1. （可选）`--intake-brief` → `merge_intake_fee_service.py` 合并费用/服务正文
2. `enrich_daily_descriptions_from_xhs.py` — 每日正文（小红书素材 + 可选 LLM，默认 `--force`）
3. `enrich_roadbook_copy_from_llm.py` — 行程亮点 + 费用/服务（默认 `--force`；无 LLM 密钥自动跳过）
4. `enrich_hotel_intro_from_flyai.py` — 住宿长简介（飞猪，`--min-chars 200`）
5. `sync_brand_logo.py` — 品牌 Logo 落本地 `roadbook-images/`
6. `fill_xhs_images.py` — 预检 + 按槽搜图（默认 `--require-remote-urls`，每槽 4 张备选；封面 Logo、费用/服务 text-block 不配图）
7. `validate_roadbook_image_alternates.py --require-remote-urls` → `assets/generate.py --template roadbook-v2 --no-serve --no-open --no-localize-images`

## 数据源优先级（硬约束，前序命中即停）

| 数据 | 顺序 |
|------|------|
| 酒店**信息**（名称/房型/设施/介绍） | 携程 → 飞猪（FlyAI）→ 通用搜索（须标「参考/待核验」）→ 人工 |
| 酒店**图片** | 携程 → 飞猪 → 小红书 → 人工 → 通用图库 → 兜底 |
| 非酒店图片（景点/美食/玩法） | 小红书（TikHub）→ 通用图库 → 兜底 → 人工 |
| 交通配图（`subtype: 交通`） | **仅** 飞猪 `flyai keyword-search`，不调小红书 |
| 报价可靠度 | 实查（无标注）→ 参考（`~`）→ 估算（`≈`） |

小红书与未标注来源的泛网页**不得**作为酒店主信息来源；四步均无效时标注「酒店数据缺失」，不得凑数。

## tripData 关键约定

- 每个图片槽默认 **4 张备选 URL**（可用 deliver `--min-images/--max-images` 或环境变量 `ROADBOOK_V2_IMAGE_ALTERNATES*` 调整）；封面与各组件大标题背景写 `{ "alternates": [...], "slotLabel": "地点·槽位" }`，首张为默认展示图。
- 住宿卡片 `description` 须保留 **`备选酒店：…` 或 `【拟定酒店】…`** 清单，供飞猪脚本解析首选店名。
- 每日 `daily.data.description` 目标 **120–280 字**，顾问文风；禁止小红书话题标签 / 机位清单式拼接。
- 费用（`subtype: 费用`）与服务（`subtype: 服务`）均为 `data.title` + 单块 `data.content`（`<p>` 导语 + `<ul class="textblock-lines textblock-rich-bullets"><li>…</li></ul>`），**不写 `sections`**；计价/打包范围入费用块，履约/服务条款入服务块。

## 输出目录

```
[目的地]-[出发年月]/            ← 如 弥勒建水-2026-04
├── tripData.json              ← 数据层（可复用，修改后重跑 deliver）
├── [目的地]-[天数]天旅行计划.html
└── sources/                   ← 搜索原始数据存档（可选，便于溯源）
```

## 环境与依赖

- 仓库根 `.env`（deliver 启动时自动加载）：`TIKHUB_API_KEY`（小红书搜索/配图，strict 交付必需）；`OPENAI_API_KEY` 或 `DEEPSEEK_API_KEY`（可选 LLM 润色，配置见 `docs/deepseek-llm-setup.md`）。
- 可选 CLI：`flyai`（`npm i -g @fly-ai/flyai-cli`，飞猪机票/酒店/门票/交通配图实时数据）。
- TikHub 异常：先查 `.env` 密钥与账户余额再重跑；策划阶段全程可用网络搜索兜底。

## 参考文件

- `references/roadbook-v2-delivery.md` — 交付细则：降级链与退出码、配图/校验参数、住宿简介标准化、费用/服务 text-block、Intake 与 XLS 解析、浏览器编辑
- `references/trip-planning.md` — 策划全流程：要素收集、目的地推荐 Phase A/B/B2/C、信息采集六维度、行程编排、预算、HTML 生成与部署、文案提示词
