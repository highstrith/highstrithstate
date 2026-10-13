# 手机视频、软件标签与首页放映

本轮在本地实现并验证，2026-10-13 经用户授权推送至 main / release/white-pages，代码提交为 `28025a5`。GitHub Pages [38361637338](https://github.com/highstrith/highstrithstate/actions/runs/38361637338) 发布成功，正式站为 https://highstrith.github.io/highstrithstate/。

线上 HTML/CSS/JS/目录与本地发布文件逐字节一致；15 部新手机版均正常返回 Range 响应并匹配文件长度。已通过手机静音自动轮播、新手机版完整播放和桌面缩略图悬停切换验收；5 种软件页尾标记、14 部公开作品、无装饰箭头、无手机横向溢出均确认。管理页继续由本地服务提供。

## 手机完整视频

15 部完整手机版共 57,599,537 B → 42,167,862 B（54.93 → 40.21 MiB），减少 26.79%。原片、桌面文件和首页预览路径保持不变，原片哈希均一致；部分已较小的视频因增加关键帧略有增长。手机上限为 960×540（按比例约束两个边长），视频 750kbps、关键帧约 2 秒以内，声音 80kbps。相较原 720p 手机版，画面细节有所取舍，桌面完整观看保留原有质量。

使用 Ego Lite Chromium、390×844 / DPR 2、下载 1.5Mbps、延迟 150ms、禁用缓存，实际请求保留的旧文件和新文件；每个版本各测 3 次。点击到 `playing` 的中位数：

| 作品 | 修改前 | 修改后 |
| --- | ---: | ---: |
| 重置日 | 3.251 秒 | 3.257 秒 |
| 街头篮球 | 2.667 秒 | 2.482 秒 |
| Two Seconds | 3.342 秒 | 2.506 秒 |

《重置日》开播没有明显改善；结果属于本地限速模拟，不能代表真实手机或线上服务器。逐片体积、源哈希、完整 18 次开播样本见 `performance.json`。`basketball-before-after.jpg` 左侧为旧手机版，右侧为新手机版同一时刻；已检查画面主体、轮廓和色彩，没有发现明显异常。

## 软件标记

页尾标记：达芬奇、Blender、剪映、AE、ChatGPT。未替任何作品填写未经确认的软件。

本地服务运行后，打开管理页，选择作品的“编辑”，在“制作软件”中勾选对应软件并保存。作品卡片与完整播放器展示已保存的标签；取消全部勾选再保存会清除标签。内置作品可编辑标签，媒体锁定规则保持。`software-admin-mobile.png` 为 390px 管理页界面截图。

## 首页预览与装饰

每部精选实际静音播放约 10 秒后推进下一部；最后一部回到首部。缩略图鼠标经过、键盘聚焦或手机点击可直接切换。每次重新选择同一作品会轮换已有 20 秒预览中的两个 10 秒片段；短于 10 秒的预览在结束时推进。加载、缓冲和暂停不消耗播放时长；离屏、后台、弹窗和减少动态效果继续停用预览。仅当前作品加载预览。箭头装饰已从公开站中英文入口和作品卡片移除，功能按钮仍可正常操作。最终首页画面见 `home-desktop.png`、`home-mobile.png` 与 `home-mobile-prove-it.png`。

## 开源参考

实施前评估了 [Splide Video Extension](https://github.com/Splidejs/splide-extension-video)（MIT，Naotoshi Fujita）。其切换时停止旧视频的思想适合本需求，但引入轮播依赖没有必要，因此继续复用站点原生唯一预览会话，未复制第三方代码。

视频事件参考 [MDN timeupdate](https://developer.mozilla.org/en-US/docs/Web/API/HTMLMediaElement/timeupdate_event) 和 [currentTime](https://developer.mozilla.org/en-US/docs/Web/API/HTMLMediaElement/currentTime)，编码参考 [FFmpeg 文档](https://ffmpeg.org/ffmpeg.html) 与 [格式文档](https://ffmpeg.org/ffmpeg-formats.html)。未把转码工具或新增运行依赖打包到公开站。
