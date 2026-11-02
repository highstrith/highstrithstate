# 帧选片库运营流程

- 日期：2026-11-02
- 范围：阶段 A「独立维护与免费发现」里的**片库运营流程与共享服务**。不含片库后台、创作者投稿、账号与交易（属阶段 B／C）。
- 依据：`docs/framepick-prd-20261102.md` 第 5、6 节与第 14 节阶段 A；[影院路线与片库更新](framepick-cinema-roadmap-20261102.md)。

现在补片仍然是改 `reel/index.html` 里的作品卡（阶段 B 才有后台）。这份文档把「怎么改」从口述变成**字段规范 + 机器校验 + 固定清单**，避免每次靠记忆。

## 1. 片源字段规范

一部作品是一张 `<article class="card" data-film="…">`。**`data-film` 是稳定标识，一旦发布就不再改、不复用。**

| 字段 | 位置 | 必填 | 取值 | 含义与常见错误 |
| --- | --- | --- | --- | --- |
| `data-film` | article | 是 | 小写字母／数字／连字符 | 稳定 ID。评价、跳转统计、收藏都以它为主键；改名会让历史数据失联 |
| `data-score` | article | 否 | 空或 0–10 | **编辑评分**。空值页面显示「待评」，**不得按 0 分参与排序** |
| `data-category` | article | 是 | `film` / `series` / `short` | 完整电影／系列单集／短片。连载的一集不能填 `film` |
| `data-genres` | article | 是 | 空格分隔的题材键 | 现用 `fantasy` `wuxia` `scifi` `xianxia`；可扩充，但要在筛选器同步中文名 |
| `data-source` | article | 是 | `douyin` / `xiaohongshu` / `bilibili` | 首批三个来源。X、YouTube、快手**尚未接通**，不得冒充已采集 |
| `data-access` | article | 是 | `free` / `paid` | 免费外链／站内授权放映。**只有 `film` 可以是 `paid`** |
| `data-date` | article | 是 | `YYYY-MM-DD` | **本站收录日期**（北京时间），不是原片首发日期。不得填未来日期 |
| 片名 | `<h3>` | 是 | — | 详情页标题与榜单条目都取这里 |
| 作者 | `.author-name` | 是 | — | 与来源名 `.source-name` 分开显示 |
| 简介 | `.desc` | 是 | — | 帧选整理的介绍，不是原平台文案照抄 |
| 编辑推荐语 | `.recommendation` | 否 | `hidden` | 详情页展示，说明「为什么值得看」 |
| 集号 | `.episode` | `series` 必填 | `hidden` | 例「第 01 集 · 原片发布于 2026.08.18」。缺它就无法说明这是一集而非完整片 |
| 时长 | `.card-runtime` | 是 | `mm:ss` 或 `h:mm:ss` | 真实完整时长 |
| 封面 | `.card-media img` | 是 | 相对 `img/` | 概念重绘图要在图旁保留「概念封面」标注，**不得冒充官方海报**（LIB-10） |
| 原作链接 | `.watch` 的 `href` | 是 | HTTPS | 域名必须与 `data-source` 对应（抖音↔douyin.com 等） |
| 跳转统计 | `data-outbound-film` | 是 | 同 `data-film` | 只有带它的链接计入近 10 天原作跳转榜 |
| 详情／收藏 | `data-open-film`、`data-save-film` | 是 | 同 `data-film` | 缺一个就少一项能力 |

**免费外链不等于可收费放映。** 公开片源链接只证明能跳转观看，不构成本站转载或收费的权利（LIB-10、PRD 12.7）。

## 2. 补片清单

按顺序做，每步都能独立检查：

1. **看完全片**，确认不是预告、混剪、制作教程或赛事合集；确认是完整故事还是某一集。
2. **核实来源**：原作者、准确原片链接、标题、集号、时长、原片发布时间、可访问状态。留证据（截图／链接），存进 `docs/ai-film-discovery-trial-20261102/` 或候选记录。
3. **去重**：同一部作品在多个平台有链接时，以原作／作者／版本关联，不把转发重复算成新片。有疑问交人工确认。
4. **确认封面来源**：自己画的概念图要标注；不要用官方海报或他人素材冒充。
5. **改卡片**：复制现有卡片结构，填第 1 节全部字段。`data-score` 没有正式编辑评分就留空。
6. **跑校验**：`node scripts/check-framepick-library.mjs`，错误必须为 0。
7. **重启本地服务**（`node serve.js` 或 `node serve-framepick.js`），让评价服务读到新作品 ID。
8. **跑测试**：`scripts/run-framepick-tests.sh`，确认筛选、详情、每日更新榜、无脚本原片入口都正常。
9. **看一遍页面**：桌面与 390px 手机，确认无横向溢出、封面加载正常。
10. **提交**，发布另按 [部署说明](部署说明.md) 执行。

「每日更新」按收录日期排序，**不要求每天凑数量**；没有合格作品就留空状态。介绍更新不重置 `data-date`，避免旧片反复霸占新片榜。

## 3. 校验脚本

```
node scripts/check-framepick-library.mjs                 检查 reel/
node scripts/check-framepick-library.mjs --site .        检查独立仓库根（拆仓后）
node scripts/check-framepick-library.mjs --json          机器可读输出
```

退出码：0 通过、1 有错误、2 找不到页面。提醒（warning）不阻断，但要人工判断。

**会拦下来的错误**：ID 重复；缺必填字段；`data-category`／`data-access`／`data-source` 取值非法；`data-date` 不是日期或是未来日期；评分超出 0–10；无评分却不显示「待评」；**单集被标成付费**；原作链接不是 HTTPS 或域名与来源不符；时长格式错；封面文件不存在；缺片名／作者／简介／原作链接。

**只提醒不拦**：`series` 缺集号说明；付费作品的授权留档（脚本查不到，必须运营自己留）；卡片缺少打开／跳转／收藏钩子；卡片没显示时长。

## 4. 共享服务：评价与原作跳转

两者都在 `server/framepick-reviews.cjs`，不是前端 localStorage。

| 项 | 位置／接口 |
| --- | --- |
| 数据文件 | `~/.framepick/reviews/reviews.json`（**站点根目录之外**，不进 Git、不进发布产物） |
| 访客身份 | 签名 cookie，`Path=/api/framepick`、`HttpOnly`、`SameSite=Lax`、一年有效 |
| 评价 | `GET/POST/DELETE /api/framepick/films/:id/reviews` |
| 跳转统计 | `GET /api/framepick/outbound/summary`、`POST /api/framepick/films/:id/outbound` |
| 作品白名单 | 启动时从 `reel/index.html` 读取 `data-film` 列表 |

**运维要点**

- 新增作品后必须重启本地服务，否则评价接口不认新 ID。
- 统计失败、服务未启动时，**原作跳转必须照常可用**，页面显示明确状态而不是假数据（PRD 12.4）。
- 正式 GitHub Pages **尚未部署这个 API**，线上目前是「未配置」状态。这是已知边界，不是故障；阶段 C 之前要单独安排部署（PRD 12.10）。
- 数据只有一份、单进程文件存储。备份＝复制 `~/.framepick/reviews/` 整个目录；恢复＝停服务、放回文件、重启。
- 清 cookie 或换设备会变成另一个访客，评价的修改权可能找不回。这不是 bug，页面已说明边界。
- 跨站部署受 `SameSite=Lax` 限制：API 与页面必须同源，否则带不上 cookie。

## 5. 本轮不做

- 不做片库后台、候选池与自助投稿（阶段 B，见路线文档「下一步建设顺序」第 1 项）。
- 不做账号、订单、支付、收益（阶段 C）。
- 不做常驻搜片 AI 与定时采集（阶段 D）。
- 不自动抓取原平台评论；原平台评价只给真实入口，页面上不声称已同步（LIB-05）。

## 6. 关联

- [帧选 PRD](framepick-prd-20261102.md)
- [帧选独立维护](framepick-standalone-20261102/README.md)
- [拆仓方案](framepick-repo-split-20261102.md)
- [访客评价](framepick-guest-reviews-20261102/README.md) · [跳转榜](framepick-outbound-20261102/README.md)
