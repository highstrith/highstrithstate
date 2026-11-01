# 零成本求职作品集调整

日期：2026-11-01。

## 方向与改动

用户确认网站只在偶尔投简历时展示，不熟悉托管且希望先不付费；随后说明作品已发国内平台，但网站有其独立价值。因此保留网站的排版、动效、目录和站内视频，本轮暂不添加国内平台跳转入口。

最小改动是用现有预览按钮控制视频下载：初始不启用，点击「播放预览」才启用原轮播／桌面悬停预览；再暂停时所有预览停止。完整播放仍可直接点击作品进入。代码采用共享调度入口检查，避免只停首屏却让作品悬停继续耗流量。

开源参考先查阅了[GoogleChrome/web.dev视频懒加载实现说明](https://github.com/GoogleChrome/web.dev/blob/main/src/site/content/en/fast/lazy-loading-video/index.md)和[当前Chrome指导](https://developer.chrome.com/docs/modern-web-guidance/guides/performance/lazy-load-video-and-audio)，采用封面优先、媒体延后加载的原生思路。沿用现有代码，没有复制外部实现或引入依赖。

## 免费托管筛选

| 方案 | 本站适配结论 |
| --- | --- |
| 现有GitHub Pages | 保留现有入口，已复现视频慢和偶发TLS失败；点击加载只能减轻传输，无法解决域名或线路完全不可达 |
| Netlify Free | 作为下一步实际部署测试候选；官方说明可免绑卡，免费计划有硬额度，耗尽会暂停，不能承诺无上限或国内一定快 |
| Cloudflare Pages Free | 官方单文件25MiB限制，小于本站最大31.61MiB视频；不能原样整站上传，且本轮未验证默认域名国内访问效果 |
| EdgeOne Makers免费版 | 默认域名在大陆访问有预览链接时效限制，单文件25MB也不覆盖现有视频；用户没有自有域名，本轮不优先采用 |

来源：[Netlify免绑卡说明](https://www.netlify.com/blog/introducing-netlify-free-plan/)、[现行价格与免费额度](https://www.netlify.com/pricing/)、[大文件部署建议](https://docs.netlify.com/resources/troubleshooting/error-reference/)、[Cloudflare限制](https://developers.cloudflare.com/pages/platform/limits/)、[EdgeOne域名](https://pages.edgeone.ai/document/domain-overview)、[EdgeOne配额](https://pages.edgeone.ai/document/limits-and-quotas)。平台规则可能变化，正式部署时需再确认。

### 当前网络单点测试

从开源模板仓库[one-click-hugo-cms](https://github.com/decaporg/one-click-hugo-cms)核对公开示例域名，使用curl `--noproxy '*'`进行请求：

- `https://master-template-one-click-hugo-cms.netlify.app/`：200，11,020字节，约1.37秒。
- `https://highstrith.github.io/highstrithstate/`：约5秒TLS超时。

两站内容、文件大小与缓存不同，这个结果只说明当时该示例入口可达，不能比较完整加载性能或代表三家运营商。浏览器访问Netlify控制台显示登录页，尚未创建项目、授权GitHub、部署本站或开通任何付费资源。下一步实际测试需要用户自己的免费账号登录。

## 可供后续部署的产物

准备独立ZIP，包含四个公开HTML、公开assets、data及reel；排除源视频、片单母版、管理页、服务端和AppleDouble文件。保留目录结构，核对21条作品的封面与三档视频引用存在。

产物位于本次聊天的可视化目录，未提交到源码仓库。Netlify官方提示手动网页上传对大文件／大产物不够可靠，本站实际迁移宜通过Git集成或CLI部署相同白名单，不能把ZIP生成成功当成部署成功。

文件：`/Users/linjunjie/.codex/visualizations/2026/11/01/01a195ab-eaf4-7102-8c04-d8fd996e1f34/portfolio-free-preview.zip`，330个文件、329,782,040字节；ZIP完整性及5个本轮公开文件与最终工作区字节一致性检查通过。

## 验证

- 新增点击加载4项先红后绿：桌面／手机真实请求为零，手动预览和暂停、完整视频播放／关闭、双主题按钮文字可读。实看发现按钮遗留白色文字，增加回归后改用主题正文色，未修改整体排版。
- 画廊／导航／主题等14项、固定视频框2项、Pages真实打包与发布分支2项通过。既有预览用例显式启用后继续验证播放、轮播、单预览、离屏、短片结束和减少动态。
- 原测试用鼠标点击尚未显现的跟随播放圆标会被视频层拦截；将两处媒体测试改为真实键盘聚焦／Enter，保留完整播放与回焦点断言，没有改产品的跟随效果或使用强制点击。
- 冷启动手机DPR 2实测图片177,925字节（低于400KiB预算），主封面960物理像素，无视频请求。此为本地网络预算，不代表国内线上加载速度。
- Ego实际检查原版面与「播放预览」，Hero无src、按钮为主题正文色；截图在聊天可视化目录`click-to-load-desktop.png`。JS语法与Git空白检查通过。本轮只本地修改／提交，没有推送或迁移。
