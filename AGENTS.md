# 项目协作规则

本文件适用于 `/Volumes/E61--/网站/site-portfolio-upgrade`（仓库 `highstrith/highstrithstate`）及其子目录。

**橘生梦厂不在这里。** 它是独立项目，源码在 `/Volumes/E61--/网站/jusheng`（仓库 `highstrith/jusheng`），有自己的 `AGENTS.md`、测试与发布脚本。两边只靠一个公开链接相连，互不引用文件。

## 开始前读什么

1. `AGENTS.md`（本文件）
2. `docs/部署说明.md`——发布链路、白名单、上线后排查顺序

没有单独的 `产品需求.md` / `当前进度.md`：这个仓库的模式已经稳定，改动都记在 `docs/<主题>-<日期>.md` 里，按日期倒着看最近的几份就够。

## 执行流程

1. 明确的功能、修改或修复指令视为授权执行；会影响方向的方案先征求确认。
2. 行为变化先补真实行为测试，再改实现。
3. 完成后跑 `./scripts/run-portfolio-tests.sh`，未解决事项写进 `docs/`。
4. 每个完成的改动集提交一次，提交信息说清「改了什么、为什么」。仓库已有 git 历史，不要重写。

## 发布纪律

- 只有 `main` 会触发 Pages；推 `release/white-pages` 不等于上线，必须再 `git push origin HEAD:main`。
- **部署失败时不要点「Re-run failed jobs」**：重跑会再上传一份同名 `github-pages` 产物，`deploy-pages` 直接报 `Multiple artifacts named "github-pages" ... Artifact count is 2`。改用 Actions 页面的 **Run workflow** 开一次新运行，详见 `docs/部署说明.md`。
- 本地预览是 `node serve.js` → `http://127.0.0.1:3000`；橘生梦厂用 3200，两个服务可以同时开。

## 工程纪律

- 本地服务只提供静态托管与作品上传接口，线上是纯静态 Pages，不要把本地管理能力当成线上能力。
- 媒体只在用户提供或明确授权的范围内复制到 `assets/`。
- 新增页面要加进 `.github/workflows/pages.yml` 的 `cp` 白名单，否则线上 404；新增作品要跑 `node scripts/optimize-media.mjs` 生成派生视频。
- 改 CSS/JS 时同步改 HTML 里的 `?v=` 后缀，否则浏览器缓存会挡住改动。
- 遇到测试失败先定位根因再改实现；`tests/` 里任何一条红都不能带着上线。
