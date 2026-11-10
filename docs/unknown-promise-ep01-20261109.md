# 《未知之诺》第一集上架（2026-11-09）

## 来源与授权
- 成片与三比例封面来自 `~/Downloads/《未知之诺》_上传包_2026-11-09/`，由导演 2026-11-09 明确要求「上传到我的作品平台」，并选定「完整上架＋线上可播」「全站统一《未知之诺》」两项口径后执行。
- 片名按成片导出件定为《未知之诺》；站内旧写法《未识之诺》属历史稿，本次一并收口。
- **目录名 `assets/progress/weishizhinuo/` 保留不改**：它是 15 张制作记录的相对路径标识，改名会断掉 30 余处引用；对外展示文字已全部改为《未知之诺》。历史 `docs/` 记录保持原样，不回改。

## 改动
1. `data/works.json` 新增 `work-unknown-promise-ep01-20261109`（共 22 条），中文简介取发布描述稿「短简介」，英文为对应意译；中英副标题标「第一集」。
2. 源片 `assets/uploads/unknown-promise-ep01-20261109.mp4`（76,319,535 B）与封面 `assets/uploads/posters/unknown-promise-ep01-20261109-16x9.png`（6,815,210 B）落地仓库；源 mp4 按仓库约定只留本地、不上线。
3. 跑 `node scripts/optimize-media.mjs` 生成 preview／mobile／web 三档派生视频，并同步 `index.html` 的 `baseWorkData` 静态快照与无 JS 回退卡片。
4. 首页与制作记录页：状态徽章「制作中」→「第一集已发布」，导航／页标题「正在制作」→「制作记录」，阶段说明改成成片已发布口径；`assets/studio.js` 中英字典同步，避免 i18n 覆盖回旧文案；`studio.js?v=` 版本号随之更新。
5. 派生视频与封面上传到杭州桶 `highstrith-assets` 对应路径，页面由 `pack-orange.sh` → `prepare-media-cdn.mjs` 注入的 `STUDIO_MEDIA_BASE_URL` 取媒体；香港桶只放页面。

## 工具链说明
- 本机原本只有 VideoToolbox 版 ffmpeg（无 `libx264`），且 `~/.cache/portfolio-media-tools` 的标准二进制缺失。本次把 `ffmpeg-static` 的 ffmpeg 6.0 装回隔离缓存，二进制 sha256 与 `assets/optimized/media-report.json` 记录的 `toolHash` 完全一致，因此既有 21 条缓存直接复用、没有重编码。
- 部署**不走** `deploy-orange.sh` 整包：该脚本会把 `film-old` 覆盖到 `/film/` 片单真身。本次只组装并把 `portfolio/` 上传到 `oss://orangeaistudio-hk/highstrith/`，`/orangedream/` 与 `/film/` 一律不碰。

## 测试口径维护（公开作品 20 → 21）
新增本片后，公开作品数从 20 变 21（另有 1 条隐藏条目），首轮整套测试出现 49 处失败、2 处错误。原因与处理：
- **测试里写死的数量**：`to_have_count(20)`、`1–6 / 20 部作品`、第 4 页 `2` 张、`MANAGED_WORKS = 21`、`media-integration.mjs` 的 `works.length === 21` 等。改为从 `data/works.json` 动态读取 `PUBLIC_WORKS / MANAGED_WORKS / FIRST_WORK_ID`，或在 Node 测试里改为「至少 21 条且包含本片」。共改 11 个测试文件。
- **首页精选里唯一的竖屏片被挤出**：`studio.js` 的 `featuredWorks` 取排序后前 5 条，新片排到首位后 `featured-timeline-1`（540×960）掉出，导致 hero 画幅与竖屏播放用例失去竖屏样本。把 `added-visual-study` 的映射改为 `featured-timeline-1`，保留精选里的竖屏覆盖；`tests/studio-redesign-smoke.py` 的映射镜像同步。
- **飞轮只取前 20 张海报**：`assets/fly-forward.js` 原为 `.slice(0, 20)`，第 21 张作品不会出现在飞轮里。改为取全部作品卡片，飞轮与作品网格数量一致。
- **文案变更**：「正在制作」→「制作记录」、`In progress` → `Production notes`、`《未识之诺》` → `《未知之诺》`，`tests/progress-smoke.py` 的对应断言同步。
- **封面体积预算**：新 poster 缺 WebP 派生图会触发 `media-budget-integration` 失败，也让移动端首屏直接拉 6.8 MB PNG。补跑 `node scripts/optimize-images.mjs`，生成 160/480/960/1600w 四档 WebP（3.7 / 23 / 68.8 / 140.6 KB，均低于 200 KB），并把这 4 个文件上传到杭州桶 `assets/optimized-images/`。

## 验收
- `scripts/run-portfolio-tests.sh`、`node scripts/sync-work-catalogue.mjs --check`
- 线上 GET 抽查：`/highstrith/`、`index.html`、`data/works.json`、新封面与三档视频
- 只发布 `portfolio/` 到 `oss://orangeaistudio-hk/highstrith/`；`/orangedream/`、`/film/` 不覆盖
