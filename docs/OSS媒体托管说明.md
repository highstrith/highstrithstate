# OSS 媒体托管说明

更新：2026-11-01。本文是媒体托管（阿里云 OSS）的唯一操作手册：现状、云端配置、费用、验收数据、换素材与回滚步骤、已知限制。
需求与架构见 `产品需求.md`、`软件架构.md`；按轮次的交付记录见 `当前进度.md`；本轮迁移过程与决策见 `docs/oss-cdn-20261101.md`。

## 一句话现状

页面（HTML／JS／CSS）仍在 GitHub Pages，全部图片与视频共 286 个对象已迁到阿里云 OSS，线上已切换并验收通过。没有 CDN 加速（大陆加速域名需备案，本项目无独立域名），媒体直接走 OSS 默认域名。

## 云端资源

| 项目 | 值 |
| --- | --- |
| Bucket | `highstrith-assets` |
| 地域 | 华东1（杭州）`oss-cn-hangzhou` |
| 读写权限 | 公共读（匿名可 GetObject，不可列举目录） |
| 媒体基址 | `https://highstrith-assets.oss-cn-hangzhou.aliyuncs.com/` |
| 对象位置 | 桶根即对象根，保持 `assets/…`、`reel/img/…` 层级 |
| 对象数／体积 | 286 个文件／313,816,273 B（另有 36 个 0 字节目录对象，见「已知限制」） |
| 切换开关 | GitHub 仓库变量 `MEDIA_CDN_BASE_URL`（Variables，不是 Secrets） |

桶根直接对应站点目录，是为了让发布期重写只替换域名、不改层级；`.gitignore` 与打包白名单仍然排除母版（`assets/originals/`、`assets/works/`、`reel/img/raw/`），这些不进 OSS。

## 桶级配置

### CORS

首页 Hero 用 `crossOrigin="anonymous"` 抓帧做转场，缺 CORS 会导致视频直接加载失败，这一项是硬依赖。

| 项 | 值 |
| --- | --- |
| 来源 | `https://highstrith.github.io`、`http://localhost:5230`、`http://127.0.0.1:5230` |
| 方法 | GET、HEAD |
| 暴露头 | `Content-Length`、`Content-Range`、`Accept-Ranges`、`ETag`、`Content-Type` |
| 缓存时间 | 600 秒 |

本地两个来源是给「按 CI 白名单打包后本地预览」用的，验证 CDN 产物时需要真实浏览器跨域。

```sh
ossutil cors --method put oss://highstrith-assets cors.xml
ossutil cors --method get oss://highstrith-assets
```

### 缓存

全部 322 个对象（含目录对象）统一 `Cache-Control: public,max-age=600`，与 HTML 的缓存时间对齐。素材不是哈希命名，缓存过长会导致替换后访客看到旧图。

```sh
ossutil set-meta oss://highstrith-assets/ "Cache-Control:public,max-age=600" --update -r -f
```

`--update` 只改指定头，`Content-Type`、大小、ETag 均保持不变。注意 `set-meta` 内部走 CopyObject，策略里必须有 `oss:GetObjectAcl`、`oss:PutObjectAcl`，否则报 `You do not have read acl permission on this object`。

### Referer 防盗链

| 项 | 值 |
| --- | --- |
| 白名单 | `https://highstrith.github.io/`、`https://highstrith.github.io/*` |
| 允许空 Referer | 是 |

**OSS 的 Referer 是前缀匹配，条目必须带斜杠。**只写裸域名 `https://highstrith.github.io` 会让 `https://highstrith.github.io.evil.com/` 通过。代价是 Referer 恰为裸域名（无路径）时返回 403，浏览器不会产生这种值。

**换域名或加自定义域名时必须同步加白名单，否则全站媒体 403。**

```sh
ossutil referer --method put oss://highstrith-assets "https://highstrith.github.io/" "https://highstrith.github.io/*"
ossutil referer --method get oss://highstrith-assets
```

## 发布链路

`.github/workflows/pages.yml` 只在 `main` 上触发。打包白名单：`index.html`、`projects.html`、`in-progress.html`、`resume.html`、`assets/`（排除 `originals/`、`works/`、`uploads/*.mp4`）、`data/`、`reel/`（排除 `img/raw/`）。

打包后执行 `node scripts/prepare-media-cdn.mjs --site public`，读取 `vars.MEDIA_CDN_BASE_URL`：

- 有值：把已打包文件里命中的媒体引用重写到该前缀，并在每个 HTML 的 `<head>` 注入 `window.STUDIO_MEDIA_BASE_URL`；脚本、CSS、PDF、页面导航留在 Pages
- 为空：字节不变，媒体维持同源

`assets/studio.js` 的 `mediaURL()` 只接受相对 `assets/` 路径或该前缀下的 `assets/` URL，作品目录无法指定任意外部媒体源。

## 费用模型

花钱的只有 OSS 外网流出流量；HTML／CSS／JS 在 Pages 免费。

| 项目 | 单价（按量，华东1） | 实际 |
| --- | --- | --- |
| 存储 | 约 ¥0.12/GB/月 | 313MB ≈ ¥0.04/月 |
| 外网流出流量 | 约 ¥0.5/GB | 主要开销 |
| 请求 | GET 约 ¥0.01/万次 | 可忽略 |

单次访问实际下载约 1.5–2.5MB（懒加载、按视口播放，不是一开页就拉 300MB），约 ¥0.001；即 ¥1 ≈ 400–600 次访问。回访受 600 秒缓存保护，同一访客短期重复浏览不重复计费。

费用预警：预算 `媒体OSS月度预算`，滚动周期月、固定值 ¥5、范围全部产品，两档预警（本期实际值 80%、100%），邮件＋短信＋站内信。**添加预警时接收人那行复选框默认不勾，不勾则通知发不出去；每档预警有独立的消息设置，第二档要再勾一次。** 预算的「总额」只是百分比基数（¥5 × 月数），不是会被扣掉的钱。

## 验收记录（2026-11-01）

- 上传：`ossutil cp -r --update --jobs 8 --parallel 3`，286 对象／313,816,273B，46 秒，未使用 `--delete`
- 逐对象匿名 HEAD 286 项：大小、`Content-Type`、`Cache-Control` 全部正确，0 异常
- `Range: bytes=0-2047` 返回 206 且 MP4 头部含 `ftyp`；预检 `OPTIONS` 返回 200
- 本机实测下载 39.5 MB/s
- 线上真实 Chrome 五页（首页／项目／进行中／简历／片单）：0 个 4xx、0 个控制台错误、媒体请求 100% 指向 OSS、横向溢出 0、Hero `readyState=4`、canvas 写入后可 `getImageData`（跨域未污染）
- 首屏加载：首页 1.25s，其余 0.39–0.81s

## 换素材

1. 本地改动后跑 `node scripts/prepare-media-cdn.mjs --site public --media-dir <临时目录>`，得到与公开文件一一对应的上传目录（或按 CI 白名单手工打包）
2. 在 RAM 控制台临时启用上传用 AccessKey（见「凭据」），`ossutil cp -r <上传目录>/ oss://highstrith-assets/ --update` 覆盖同名对象
3. 缓存 600 秒，访客最多 10 分钟后看到新版本；急用可改文件名并在页面引用新名
4. 推 `main` 重新部署页面，用完禁用 AccessKey

## 回滚

- **媒体回同源**：把仓库变量 `MEDIA_CDN_BASE_URL` 清空后重新部署，转换器自动跳过重写，页面回到 `assets/…` 同源引用
- **恢复单个对象**：从 Git 历史取旧字节重新上传覆盖同名对象
- **关闭防盗链**：`ossutil referer --method delete oss://highstrith-assets`（排查「图打不开」时先做这个）

## 凭据

- RAM 子账号 `oss-uploader`，自定义策略 `highstrith-assets-rw`：仅限本桶的 ListObjects／GetObject／PutObject／分片上传／CORS 与 Referer 读写／对象 ACL 读写，**不含 DeleteObject**
- **AccessKey 平时保持禁用**，需要上传时临时启用，用完立即禁用；本机 `~/.ossutilconfig` 用完即删
- `ossutil` 位置：`~/bin/ossutil`（v1.7.18，macOS arm64）

## 已知限制

- **未开 CDN 加速**：大陆加速域名需备案，无独立域名。GitHub Pages 仍承载 HTML，入口本身不可达时媒体再快也没用
- **公共读 + 默认域名**：防盗链只能挡住「嵌到别人网页」，直接粘贴链接到地址栏仍可访问（空 Referer 放行）
- 桶内有 **36 个 0 字节目录对象**（`ossutil cp -r` 的副作用），无害；当前策略无删除权限，清不掉
- 目录数据里仍有 `assets/works/*.mp4`、`assets/uploads/*.mp4` 等母版兜底字段，这些文件不发布，线上必然 404；属既有行为，页面只在实际预览缺失时才回落到它们
- 首页会探测 `/api/works`（本地服务接口），静态站返回 404，属既有行为
- 页面引用 `assets/site.webm`，该文件在仓库中不存在，浏览器跳过，属既有问题
- SVG 走 OSS 默认域名会带 `x-oss-force-download`，`<img>` 渲染不受影响
