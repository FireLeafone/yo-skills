# roadbook-v2 交付细则

> 路径约定：本文所有 `scripts/`、`assets/` 相对路径均以本 skill 目录（travel-planner/）为基准。脚本经 `Path(__file__)` 自定位，任意 cwd 下用正确路径调用即可执行。

## 1. 交付流水线全景

`scripts/deliver_roadbook_v2.py` 按固定顺序串联（`--dry-run` 可只打印不执行）：

| # | 脚本 | 关键默认 | 说明 |
|---|------|---------|------|
| 0 | `merge_intake_fee_service.py` | 仅 `--intake-brief` 传入时 | 把简表中费用类/服务类段落写入 `text-cost-001` / `text-service-001` |
| 1 | `enrich_daily_descriptions_from_xhs.py` | `--force`、`--daily-min-chars 200` | 每日 `description` 润色；识别并重写 `[话题]`/emoji/机位清单等劣质拼接 |
| 2 | `enrich_roadbook_copy_from_llm.py` | `--force` | 行程亮点 `content`+`items`、费用/服务 HTML；无 LLM 密钥自动跳过 |
| 3 | `enrich_hotel_intro_from_flyai.py` | `--hotel-force`（默认开）、`--min-chars 200` | 住宿长简介写入 `feature`/`subtype: 住宿` 的 `items[].description` |
| 4 | `sync_brand_logo.py` | — | 封面固定「玩点旅行」Logo，落 `roadbook-images/logo-brand-wdtrip.png` |
| 5 | `fill_xhs_images.py` | `--require-remote-urls`、每槽 4 张 | 含 search_feeds 预检；封面 Logo、费用/服务 text-block 不配图 |
| 6 | `validate_roadbook_image_alternates.py` | `--require-remote-urls`、`--min` 与 deliver 一致 | 校验每槽备选 URL 数量与 https |
| 7 | `assets/generate.py` | `--template roadbook-v2 --no-serve --no-open --no-localize-images` | 渲染 HTML；配图保持 https 远程 URL |

## 2. 严格模式、降级链与退出码

- **默认 strict**：不加 `--allow-local-placeholders`，小红书预检 + strict https 配图 + strict 校验。
- **自动降级**（默认不中断流水线）：`fill_xhs_images` 失败 → 原参数重试一次 → `--skip-xhs`（飞猪 FlyAI → Wikimedia → placehold.co 占位）→ `relink_local_roadbook_images.py` 本地回链 → 放宽校验（先去 https 门禁，仍不满再 `--min 1`）→ **仍执行 `generate.py`**。降级后日志出现 WARN，回复中必须注明「非 strict 产出，配图与正文需人工核对」。
- **`--fail-fast`**：任一步骤非零退出即中止。
- **退出码**：`0` = strict 成功；`2` = 已降级（不可直接交付客户）。
- **草稿**：`--allow-local-placeholders` 会同步跳过每日正文 enrich、亮点/费用/服务 LLM、住宿 enrich 与 strict 配图，校验仅数 URL 数量；仅限用户明示草稿/预览/离线时使用，并标注 **非交付稿**。

## 3. 每日正文 enrich

- 目标 **120–280 字**，顾问文风，紧扣当日真实节点；不新增素材外景点或承诺。
- 配置 `OPENAI_API_KEY` 或 `DEEPSEEK_API_KEY`（本 skill 目录 `.env`，与 `scripts/` 同级，`scripts/repo_dotenv.py` 自动加载）时经 OpenAI 兼容 Chat Completions 统一文风；否则以 `overview` + 飞猪/维基洁净句合成。
- deliver 参数：`--no-daily-force`（保留旧稿）、`--daily-no-llm`（禁用 LLM）、`--skip-daily-enrich`（整步跳过）、`--daily-min-chars`（默认 200）。
- DeepSeek 专用变量与示例见 `docs/deepseek-llm-setup.md`。

## 4. 亮点/费用/服务 LLM

- 默认 `--force` 重写：行程亮点 `content` + `items`、费用说明与服务说明 HTML，与 `skill.md` 格式约定对齐。
- 无 LLM 密钥时整步跳过（不视为失败）；`--skip-copy-llm` 手动跳过；`--no-copy-llm-force` 保留已达字数成稿；`--copy-llm-no-llm` 禁用 LLM。

## 5. 住宿简介标准化

- **前置**：住宿卡片 `description` 保留 `备选酒店：…` 或 `【拟定酒店】…` 清单；`items[].title` 为飞猪检索地名（脚本内置别名，如「西江」→雷山，无需手改）。
- **固定参数**：`--check-in` / `--check-out` 与客户首晚入住/离店一致（与报价同一窗口），`--min-chars 200` 为交付下限；已达标且带清单的条目默认被 `--hotel-force` 重写，保留旧稿用 `--no-hotel-force`。
- **业务责任**：携程侧酒店全称/房型/设施核对不可被脚本替代；飞猪匹配错误时须在 JSON 标注「拟定酒店 + 参考检索」，避免误导客户。
- 手工单跑：

```bash
python3 scripts/enrich_hotel_intro_from_flyai.py "路书目录/tripData.json" \
  --check-in YYYY-MM-DD --check-out YYYY-MM-DD --min-chars 200
```

## 6. 配图细则

- **每槽 4 张备选 URL**（deliver `--min-images/--max-images`，或环境变量 `ROADBOOK_V2_IMAGE_ALTERNATES` / `_MIN` / `_MAX`）。
- 备选结构：URL 数组或 `{ "alternates": [...], "slotLabel": "地点/槽位名" }`；首张默认展示，其余进入模板「备选图片」面板。封面 `cover.backgroundImage` 与每个组件 `data.backgroundImage` 同规则。
- **不配图槽位**：封面 `cover.logo`、费用/服务 text-block。
- **交通配图**（`subtype: 交通` 用车图 + 章节背景）：仅 `flyai keyword-search` 的网络 `picUrl`；手工刷新用 `scripts/refill_transport_images_from_flyai.py`。
- **检索词规则**：`scripts/xhs_search_keyword_rules.py` —— 封面/大标题偏「目的地 + 风景/建筑 + 大气」分桶；daily 槽以当日 theme 为主干轮换后缀；住宿偏「酒店名 + 实拍/房型/大堂」。
- **节流与并发**：`ROADBOOK_FILL_XHS_COOLDOWN_MS`、`ROADBOOK_FILL_XHS_SLOT_GAP_MS`、`ROADBOOK_FILL_XHS_MAX_DETAIL_FEEDS`；并发默认 4 线程（`ROADBOOK_FILL_XHS_CONCURRENCY`）。
- **可选 pHash 去重**：`fill_xhs_images.py --visual-dedupe`（或 `ROADBOOK_FILL_VISUAL_DEDUPE=1`），需先 `pip install -r requirements-roadbook-images.txt`；与并发互斥（自动回退单线程）。deliver 默认未开。
- **禁止**：交付路径用 `fill_xhs_images.py --skip-existing`（仅本地提速可用）。
- 分拆手工执行（仅在一键脚本不可用时）：

```bash
python3 scripts/fill_xhs_images.py "路书目录/tripData.json" --min-images 4 --max-images 4 --require-remote-urls
python3 scripts/validate_roadbook_image_alternates.py "路书目录/tripData.json" --require-remote-urls   # 须退出码 0
```

## 7. 费用/服务 text-block 规范

- 版式：仅 `data.title` + `data.content`（单块 HTML）；**不写 `sections`**（`须知`/`规则`/`其他` 才可用 sections）。
- 推荐骨架：一两段导语 `<p>…</p>` + `<ul class="textblock-lines textblock-rich-bullets"><li>…</li></ul>`，一条资料条目对应一个 `<li>`。
- 筛项：**费用块** ← 报价、包含/不含、用车/门票/保险等计价与打包范围句；**服务块** ← 服务范围、预订/签约、出行须知、注意事项、退改政策、服务承诺句。不得互相塞错。
- `subtype: 须知`：无正文则导出前从 tripData 移除；有正文则并入「服务说明」同一富文本页。
- 旧数据 `lines`/旧 `sections` 仅作迁移合并进 `content`，保存后以 `content` 为准。

## 8. Intake 与 XLS 解析

**最低必需字段**（缺失则追问）：`D1..Dn` 日程骨架、每日路线/核心节点、费用说明（至少包含项 + 成人价）。

**输入识别优先级**：纯文本直接解析 → 截图/图片先 OCR 再人工补齐 → 文档（docx/pdf）先抽文本主干、图片仅作搜图关键词。

**脚本首版**：

```bash
python3 scripts/roadbook_intake.py --input <brief.txt|brief.docx> --output-dir <目的地-年月> [--render --html-name 路书名.html]
```

**XLS 表格客户**：
1. 读取表格（可用 `python -c "import openpyxl; …"`）。
2. 找表头行（含「时间|天数|行程区间|行程内容|用餐|住宿」）。
3. 逐行提取：行程内容按 `-`/`—` 拆节点；识别早/午/晚餐与「酒店含早」；提取酒店名与航班/车次。
4. 提取报价区：成人价/儿童价/总价、「报价包含」「报价不包含」明细。
5. 按路书 schema 组装 tripData。

**合并到已有 JSON**：`scripts/merge_intake_fee_service.py` 或 deliver `--intake-brief`（规则同 intake 的 `extract_sections_from_text`）。

## 9. 输出与浏览器编辑

1. 生成/更新 `[路书目录]/tripData.json`（住宿卡片须保留备选/拟定清单）。
2. 跑 deliver 流水线（见 `../SKILL.md` 一键命令）。
3. 浏览器打开 HTML → 顶部「编辑模式」：点文字直接改；点图片替换 URL；封面/章节背景右下角「替换背景」「备选 N 张」切换；「保存 JSON」导出。
4. 导出后再次交付：重跑 deliver（可加 `--no-hotel-force` 等保留已成稿文案）。
5. 本地裂图修复：`scripts/relink_local_roadbook_images.py`（只修回链，不补足远端备选；对客户交付仍需 strict deliver）。

## 10. 酒店数据源顺序（交付口径）

信息与图片的来源顺序口径同 `../SKILL.md`「数据源优先级」表，此处仅补充交付侧报价口径：

| 用途 | 顺序 |
|------|------|
| 指定日期报价 | FlyAI 传日期返回 `price` 可标「实查」；未传日期或仅搜索结果的标「参考价」 |

常用命令：

```bash
flyai search-hotels --dest-name "目的地" --check-in-date YYYY-MM-DD --check-out-date YYYY-MM-DD \
  [--poi-name "景点名"] [--hotel-stars "4,5"] [--max-price 800] [--sort price_asc]
```
