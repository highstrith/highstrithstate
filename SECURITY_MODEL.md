# 安全模型：作品集（highstrithstate）

> 2026-11-11 初稿，根据代码、`AGENTS.md` 与 `docs/部署说明.md` 整理。安全扫描会读取本文件；可接受风险尚待维护者确认（见末节）。

## 组件与信任边界

| 组件 | 代码 | 运行位置 |
|---|---|---|
| **Portfolio-Site** | 根目录页面、`assets/`、`data/`、`.github/workflows/pages.yml` | 纯静态 GitHub Pages，只有 `main` 部署；产物由 workflow 的 `cp` 白名单决定 |
| **Portfolio-Local-Admin** | `serve.js`、`server/static-site.cjs`、`admin.html`、`scripts/` | 维护者本机 `node serve.js`（端口 3000）；`listen(port)` 未指定 host，即监听所有网卡 |

- 本地接口 `GET/POST /api/works`、`PUT/DELETE /api/works/:id`、`POST /api/upload-file` 没有鉴权，依赖「只在本机使用」；线上 Pages 没有这些接口。
- 评论配置 `assets/comment-config.js`（Twikoo，`envId` 默认空）。

## 资产

- 中：线上作品集内容完整性。
- 低：本地作品库 `data/works.json` 与上传的媒体（可从 Git 恢复）。

## 现有控制

- 静态服务做目录穿越检查；上传限制扩展名与大小。
- Pages 产物白名单，原始素材不发布。

## 待确认

- 本地管理服务是否会在不可信局域网中运行；本机恶意网页是否在考虑范围。
