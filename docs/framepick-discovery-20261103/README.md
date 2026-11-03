# 帧选搜片管道（2026-11-03）

解决"片源太少"：定时去公开平台搜新片，机器做初筛与复核，结果落到候选池并出报告；**上架始终由人决定**。

## 抓取后端：先用现成的，不自己写爬虫

| 方案 | 结论 |
| --- | --- |
| **bilibili-api-python 17.4.2**（默认） | ✅ 采用。B 站公开网页接口的封装，库自己处理 wbi 签名与 buvid，无需登录。一条搜索请求直接返回 `bvid／标题／UP 主／时长／播放量／发布时间／简介／标签`，不用解析 DOM |
| yt-dlp（`bilisearch`） | ❌ 试过。flat 模式只给 id；逐条取详情被 B 站 412 反爬拦下，需登录 cookie 才可能可用 |
| Playwright 渲染搜索页 | ⚠️ 保留为 `--backend browser` 兜底。能用，但依赖 B 站卡片 DOM，改版即失效，且 37 条要跑 3 分钟 |
| Scrapy / Crawlee | ➖ 不采用。它们是通用爬取框架，本场景只有一个有公开接口的站点，框架只增加活动部件 |
| Apify / Firecrawl 等托管服务 | ➖ 不采用。按量计费、数据出境，抖音 actor 同样要你的登录 cookie |

实测对比：同一批候选，API 后端 **约 2 秒／关键词**，浏览器后端 约 25 秒／关键词。

## 边界

| 环节 | 谁做 | 说明 |
| --- | --- | --- |
| 搜索 | 脚本（B 站公开接口） | 抖音／小红书站内搜索与作者页需登录，只登记线索，不核实、不臆造 |
| 初筛 | `framepick-discovery-cli.mjs` | 时长 3–40 分钟、来源与链接匹配、排除教程／解说／合集／预告等、必须带 AI 制作属性证据、去重 |
| 复核 | 同上 `verify` | 打开原页比对标题与作者，判定链接是否失效 |
| 入池 | 同上 `add` | 写入候选池（站点外 `~/.framepick/library`），状态 `new` |
| 看片与上架 | **人** | `candidate convert` → `draft → reviewing → approved → scheduled → published` |

自动任务**不会**改 `reel/index.html`、不会提交、不会发布。**收录时间不是重点**：不查证、不核对，需要填 `intakeDate` 时直接取当天。

## 依赖

```bash
python3 -m pip install bilibili-api-python curl_cffi   # 前者是 B 站接口封装，后者是它需要的 HTTP 客户端
```

浏览器兜底额外需要 `playwright`（项目测试已依赖，浏览器用系统 Chrome 即可）。

## 三块组成

- `docs/framepick-discovery-20261103/sources.json` —— 搜什么：关键词、平台状态、排除词、时长区间、AI 证据要求。
- `scripts/framepick-discovery-scan.py` —— 怎么搜：`scan`（API 后端批量搜索）、`channel`（按 UP 主 mid 拉最新投稿）、`enrich`（重算 AI 证据，无需开页面）。
- `scripts/framepick-discovery-cli.mjs` —— 怎么筛和存：`plan / screen / add / verify / report`。规则在 `scripts/framepick-discovery-rules.mjs`，与测试共用一份。

## 一次完整运行

```bash
cd /Volumes/E61--/网站/site-portfolio-upgrade
node scripts/framepick-discovery-cli.mjs plan                                   # 本轮搜什么
python3 scripts/framepick-discovery-scan.py scan --out /tmp/fp-found.json --limit 15
node scripts/framepick-discovery-cli.mjs add --file /tmp/fp-found.json           # 初筛并入池
node scripts/framepick-discovery-cli.mjs verify                                  # 复核链接与元数据
node scripts/framepick-discovery-cli.mjs report                                  # 写 runs/*.md
```

监控已入库作者的新稿（mid 取自搜索结果的 `mid` 字段）：

```bash
python3 scripts/framepick-discovery-scan.py channel --mid 123456 --out /tmp/fp-channel.json --limit 20
node scripts/framepick-discovery-cli.mjs add --file /tmp/fp-channel.json
```

## 人工收口

```bash
node scripts/framepick-library-cli.mjs candidate list              # 看候选池
node scripts/framepick-library-cli.mjs candidate convert <id> --file 作品.json
node scripts/framepick-library-cli.mjs status <作品id> reviewing --note "人工审片"
node scripts/framepick-library-cli.mjs build                       # 重新生成片库页面
```

`作品.json` 的 `intakeDate` 填当天即可，不用查证发布时间。

## 实测记录

- 2026-11-03 浏览器后端：3 关键词 → 37 条 → 22 条被拦 → 15 条入池。
- 2026-11-03 API 后端：2 关键词 × 15 条 → 30 条 → 17 条被拦、4 条重复、9 条入池（与首轮重叠部分被去重）。
- 入池 ≠ 收录：AI 音乐翻唱、同人二创、资讯解说、连续剧单集都会混进来，**初筛只能缩短清单，不能替代看片**。

## 已知限制

- 抖音／小红书需登录，自动化里无法核实；相关线索只记录不入库。
- AI 制作属性只认标题／简介／UP 主自填标签里的明确表述（`\bai\b` 词边界），页面推荐位与评论里的 AI 字样不算。
- B 站接口字段与风控会变；失败时脚本在 stderr 打印原因并跳过该关键词，不会中断整轮。
- 候选 ID 由标题生成 slug，可能退化为 `cand-N`；需要可读 ID 时入池时自行指定。

## 关联

- [帧选 PRD](framepick-prd-20261102.md) · [片库运营流程](framepick-library-operations-20261102.md) · [首轮 AI 搜片试跑](../ai-film-discovery-trial-20261102/试跑结果.md)
- 测试：`tests/framepick-discovery-integration.mjs`（规则／去重／报告）、`tests/framepick-discovery-scan-test.py`（时长与证据解析，无需联网）
