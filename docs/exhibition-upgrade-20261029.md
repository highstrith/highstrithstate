# 实验画廊 UI 与交互升级

日期：2026-10-29。用户选择「更有实验感：不规则画廊布局、更强的视觉节奏」。

## 目标与设计

沿用白色 V2、N 标志、真实作品和克制字号。主标题不超过 44px、章节标题不超过 36px。以作品的尺寸变化和留白制造节奏，不使用巨型字、虚构履历或新增运行依赖。

- 色彩沿用纸白 #f4f4f0、墨黑 #171918、灰绿 #686d69、线条 #d6d9d2、橘色 #e46740，增加冷白 #fcfdfb 作为片单与工具区表面。中文沿用本机苹方等系统字体，英文沿用现有无衬线字体，不新增远程字体请求。
- 首页精选拆成大画面与片单侧栏。标题、简介、五部缩略图形成独立的信息层；真实媒体时间驱动选中项进度，访客可暂停自动预览，并继续手动选片。
- 作品集使用 7:5 / 5:7 的交错双列，筛选后根据可见顺序重排。新增目录视图，切换不重建作品节点，不丢搜索、分类或评论状态。
- 截图画廊保留竖幅角色与横幅器物的不同构图；原生 dialog 大图浏览支持键盘、触摸切换、放大、Esc 和焦点返回。
- 顶部为粘性导航，手机使用可收起菜单，当前区块有清晰状态。联系区增加邮箱复制及真实成功／失败反馈。
- 项目分页以 AI 无限画布为横向主项目，其余双列，延续同一导航和视觉系统。

## 执行计划

1. 调研开源图片画廊与作品集交互，阅读现有文档、代码、真实页面。
2. 新增真实浏览器交互契约并确认基线失败。
3. 修改 index.html、studio.js、studio.css，增加独立 exhibition.css 与 site-shell.js，整合现有截图和滚动展开；同步项目分页。
4. 运行新增行为测试、现有作品/评论/项目回归、媒体目录与 Pages 打包检查；检查 320/390/820/1440/1920、中英、减少动态、无脚本和子路径。
5. 更新三份固定文档并创建 Git commit；本轮本地交付，不自动推送发布。

## 开源评估与复用

评估 https://github.com/dimsemenov/PhotoSwipe （MIT）及其 options 文档：https://github.com/dimsemenov/PhotoSwipe/blob/master/docs/options.md 。借鉴键盘左右切图、Esc 关闭、焦点恢复、触摸与放大的成熟交互。本站仅 8 张静态图片且已有原生 dialog 与单预览调度，采用现有基础实现所需交互，比引入完整画廊库更合适。本轮不复制其源码，不引入第三方媒体。

## 约束与风险

当前已在 release/white-pages 隔离工作树，有未提交的截图区、4 张截图与滚动动画；保留并整合，禁止回退这些工作。既有 Git AppleDouble 对象索引告警不属于页面改版范围。桌面新的非对称画框保留 contain 避免裁切视频；触屏关闭卡片自动预览；原生媒体缓冲、重试、评论与音乐意图沿用现有逻辑。新增弹窗必须纳入滚动锁、自动预览和音乐暂停判断。

## 验证与维护

- 真实浏览器：`python3 tests/exhibition-upgrade-smoke.py -v`（10 项）、`python3 tests/studio-redesign-smoke.py -v`（30 项）、`python3 tests/projects-smoke.py -v`（8 项）、`python3 tests/comments-smoke.py -v`（8 项）。使用系统 Chrome。
- Node：`node --test tests/pages-artifact-integration.mjs tests/media-integration.mjs tests/catalogue-sync-integration.mjs tests/image-optimization-integration.mjs`（9 项）。图片构建测试依赖本地 FFmpeg，可用 `FFMPEG_PATH` 指定；本轮测试工具临时安装在 `/tmp/highstrith-media-tools/`，不进入站点。
- 语法：`node --check assets/studio.js`、`node --check assets/site-shell.js`、`node --check assets/scroll-reveal.js`，以及 Git 空白检查。
- 新交互先增加测试并确认基线失败；菜单焦点与长章节导航补测同样确认过修复前失败。独立审查发现菜单 Tab 导航问题，修复后复审通过。
- 手机冷启动图片 327,823 B，主封面 960px；画廊使用小图，截图原图只在打开时请求。双语、5 个宽度、file、无脚本与模拟静态子路径保持可用。
- 预览截图保存在同名目录 `docs/exhibition-upgrade-20261029/`。本地地址 http://127.0.0.1:3000/ ，本轮不自动发布。
