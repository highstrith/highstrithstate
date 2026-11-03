# 帧选搜片管道（2026-11-03）

解决"片源太少"：让一个 agent 定时去公开平台搜新片，机器先做初筛与复核，把结果落到候选池并出报告；**上架始终由人决定**。

## 边界

| 环节 | 谁做 | 说明 |
| --- | --- | --- |
| 搜索 | agent（真实浏览器，未登录） | B 站公开搜索可用；抖音／小红书站内搜索与作者页需登录，只登记线索不做核实 |
| 初筛 | 脚本 | 时长 3–40 分钟、来源与链接匹配、排除教程／解说／合集／预告等、必须带 AI 制作属性证据、去重 |
| 复核 | 脚本 | 打开原页比对标题与作者，判定链接是否失效 |
| 入池 | 脚本 | 写入候选池（站点外 `~/.framepick/library`），状态 `new` |
| 看片与上架 | **人** | `candidate convert` → `draft → reviewing → approved → scheduled → published`，不自动跳过 |

自动任务**不会**改 `reel/index.html`、不会提交、不会发布。

## 三块组成

- `docs/framepick-discovery-20261103/sources.json` —— 搜什么：关键词、平台状态、排除词、时长区间、AI 证据要求。
- `scripts/framepick-discovery-scan.py` —— 怎么搜：`scan` 抓 B 站搜索页（最新发布排序），`enrich` 打开每个原页核对标题／作者并在**标题与简介**里找 AI 制作属性表述。
- `scripts/framepick-discovery-cli.mjs` —— 怎么筛和存：`plan` 打印本轮清单、`screen` 只跑初筛、`add` 入池、`verify` 复核链接、`report` 出报告。规则实现在 `scripts/framepick-discovery-rules.mjs`（与测试共用一份）。

## 一次完整运行

```bash
cd /Volumes/E61--/网站/site-portfolio-upgrade
node scripts/framepick-discovery-cli.mjs plan                                   # 本轮搜什么
python3 scripts/framepick-discovery-scan.py scan --out /tmp/fp-found.json --limit 12
python3 scripts/framepick-discovery-scan.py enrich --file /tmp/fp-found.json     # 打开原页找 AI 证据
node scripts/framepick-discovery-cli.mjs add --file /tmp/fp-found.json           # 初筛并入池
node scripts/framepick-discovery-cli.mjs verify                                  # 复核链接与元数据
node scripts/framepick-discovery-cli.mjs report                                  # 写 docs/framepick-discovery-20261103/runs/*.md
```

## 人工收口

```bash
node scripts/framepick-library-cli.mjs candidate list              # 看候选池
node scripts/framepick-library-cli.mjs candidate status <id> watching
node scripts/framepick-library-cli.mjs candidate convert <id> --file 作品.json
node scripts/framepick-library-cli.mjs status <作品id> reviewing --note "人工审片"
node scripts/framepick-library-cli.mjs build                       # 重新生成片库页面
```

## 首轮实测（2026-11-03 09:00）

3 个关键词扫到 37 条（去重后），时长不足 3 分钟或命中排除词的 22 条被拦下，15 条入池，15 条原页标题与作者均一致。剩下的噪音仍需人看片判断：AI 音乐翻唱、同人二创、资讯解说、连续剧单集都不该进"电影片库"——**初筛只能缩短清单，不能替你判断作品**。

## 已知限制

- 抖音／小红书需登录，无法在自动化里核实；相关线索只记录不入库。
- B 站搜索页是前端渲染，抓取依赖卡片 DOM；页面改版需同步 `CARD_JS`。抓取失败会在 stderr 打印并跳过该关键词，不会中断整轮。
- AI 制作属性只认"标题或简介里的明确表述"，页面推荐位、标签、评论里的 AI 字样不算证据。
- 候选 ID 由标题生成 slug，可能重复到 `cand-N`；如需可读 ID，入池时用 `--json` 自行指定。

## 关联

- [帧选 PRD](framepick-prd-20261102.md) · [片库运营流程](framepick-library-operations-20261102.md) · [首轮 AI 搜片试跑](../ai-film-discovery-trial-20261102/试跑结果.md)
- 测试：`tests/framepick-discovery-integration.mjs`（初筛规则、入池去重、需登录平台不臆造、报告不出片、plan 不编造）
