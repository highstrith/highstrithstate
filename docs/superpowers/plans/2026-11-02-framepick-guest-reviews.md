# 帧选访客评论与评分实施计划

**Goal:** 访客无需注册即可在本地共享服务中评论、1–10分评分，其他浏览器可查看；作品介绍、原平台评价入口、本站编辑与访客评价清楚分开。

**Architecture:** 保留GitHub Pages静态片库，新增独立原生Node HTTP评价模块与前端评价面板。模块接入现有本地serve.js供预览，另支持API单独运行；数据存到站点根目录以外，不进入Git或Pages。GitHub Pages未配置共享服务时明确不可提交，不用localStorage冒充共享评论。

**Tech Stack:** 原生Node http/fs/crypto，原生浏览器fetch/dialog/form，Node真实HTTP测试、Python Playwright多浏览器会话测试。当前已隔离worktree，保留本地、不发布。

**Scope:** 用户本轮明确要求访客模式、评论、评分、原作介绍／评价与站内评价。本次把可运行本地服务与前端做实；线上部署共享服务另行配置，原平台评论不伪造或混入本站评分。

## 复用评估

制作前查阅[Twikoo](https://github.com/twikoojs/twikoo)（MIT）、[Waline](https://github.com/walinejs/waline)（GPL-2.0）及现有assets/comment-config.js。现有Twikoo环境为空，无法直接运行；两者都需要独立部署。为保持本地零依赖及10分制评分／本人评价更新契约，采用本项目原生服务实现，不复制上游代码，不创建收费云资源。

## Task 1: 独立访客评价服务

- [ ] 先写`tests/framepick-reviews-api-integration.mjs`，运行确认缺少模块失败，再实现`server/framepick-reviews.cjs`。
- [ ] 模块导出`createReviewHandler({dataDir,filmIds,cooldownMs})`，返回async(req,res,url)=>boolean；支持GET `/api/framepick/session`建立HttpOnly访客cookie、GET `/api/framepick/summary`、GET/POST/DELETE `/api/framepick/films/:id/reviews`。
- [ ] POST输入`{nickname,text,rating}`，昵称最多24字、正文最多1000字，评分null或1–10整数；至少正文或评分有一项。同一cookie访客每作品一份评价，可更新和删除，评分平均值只计有效评分，返回数量与均分。
- [ ] GET评论返回`{reviews,total,averageRating,ratingCount,yourReview}`，支持offset分页（每页20）；条目`{id,nickname,text,rating,createdAt,updatedAt,isMine}`不泄漏访客令牌或内部身份。summary返回`{films:[{filmId,averageRating,ratingCount,commentCount}]}`。
- [ ] 签名随机访客身份、服务端校验、写入串行且原子持久化、同访客短时频控、请求体上限、同源写入保护；独立API允许通过环境变量显式配置一个前端来源，禁止任意跨源凭证。
- [ ] Node测试覆盖双访客共享、独立影片、不重复计分、更新／撤回、重启持久化、伪造cookie、非法输入、跨源、并发写入和私密数据不出现在响应。

## Task 2: 页面和服务集成

- [ ] 本地serve.js以可选模块接入API，原有单文件server测试fixture仍可运行；正式评价API不要暴露本地管理功能。运行数据默认站点根目录之外。
- [ ] 新增`reel/review-config.js`（API地址默认空）与`reel/framepick-reviews.js`，loopback自动使用同源API；线上未配置不请求本地地址，展示服务不可用并保留介绍／外链。
- [ ] header访客模式入口；作品详情增加「作品介绍」「原平台评价」「站内评价」三个标签。原作入口跳转真实来源，当前简介标明本站整理，不伪造源平台评论／评分。
- [ ] 本站面板：访客昵称、可选1–10分、正文、发布／更新／撤回，站内均分／人数、分页评论、本人标记和编辑评分分离；异步切片／关闭不会把A作品结果显示到B作品，写入失败保留草稿并可重试。
- [ ] 卡片显示独立本站评分摘要；评分依据可在编辑／站内用户间切换，筛选与排序使用选定依据。避免少量访客评分冒充编辑评分。

## Task 3: 验证与交付

- [ ] 新增真实多会话浏览器测试：昵称与评论／评分提交、刷新、另一浏览器查看、更新不重复、切片隔离、失败／未配置状态、来源区隔、手机布局和键盘。
- [ ] 跑API、新旧片库／入口、Pages与相关本地works API回归；私密数据库／服务端模块不进入Pages产物，新增公开资源完整打包。
- [ ] ego-browser实际使用本地页面并检查桌面／手机截图。测试使用隔离数据库，实际预览库不留示例评价。
- [ ] 独立审查、同步三份固定文档和部署边界，Git检查后提交，不推送发布。
