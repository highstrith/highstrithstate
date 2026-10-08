# 当代影像工作室改版交付

完成日期：2026-10-08。用户已授权推送白色版，正在验证 Pages 打包与部署。此前黑色 V1 已保存在远程 [v1-black 标签](https://github.com/highstrith/highstrithstate/tree/v1-black)。

## 设计和研究

参考研究：[GitHub 项目研究](../2026-10-07-github-research.md)，包含 7 个项目的一手来源、2026-10-07 约星数、许可证和适用性判断。借鉴精选/归档分层、作者专业表达、按需媒体、可理解的操作反馈与原生可访问交互；本轮自主实现，没有复制第三方代码或新增前端依赖。

用户选定当代影像工作室，并在实看后明确：保留原 N 标志；不要巨型标题或页脚字标。最终首页标题不超过 44px，章节不超过 36px，手机标题 28–30px，以真实作品、留白和常规字重组织页面。

当前 Hero：《重置日》、Prove It、《AI患者》、Two Seconds、《AI 之后》。按照用户要求替换原来的趴着办公、打斗、第 04 项和第 05 项；以后新增仍按日期倒序进入首位。目录中这些被替换的作品仍完整保留。

## 页面

- [桌面首页](public-desktop.png)
- [手机首页](public-mobile.png)
- [作品目录](works-desktop.png)
- [联系与页脚](contact-desktop.png)

截图为整体改版完成时的实际浏览器页面（第 05 项随后改为《AI 之后》）；公开页截图使用减少动态效果，展示稳定海报。通常桌面访问会自动播放当前轻量预览，作品悬停/聚焦时切换到唯一预览；手机不主动加载预览。

## 验证

新版完整浏览器回归 17 项通过；最后调整字号后，五种宽度中英文布局和五部精选播放 2 项定向回归通过。API/特殊文字目录同步 17 项通过；全部 15 部媒体解码、时长、faststart 与源完整性检查通过。公开隐藏巨轮空降，因此 14 部可见；管理页维护全部 15 个条目。

```sh
node serve.js
python3 -u tests/studio-redesign-smoke.py -v
node --test tests/works-api-integration.mjs tests/catalogue-sync-integration.mjs
node tests/media-integration.mjs
node tests/optimized-media-integration.mjs
node --test tests/pages-artifact-integration.mjs
node --check assets/studio.js
node --check serve.js
git diff --check
```

本地预览：http://127.0.0.1:3000/；管理：http://127.0.0.1:3000/admin.html。

上传测试在临时目录验证真实视频/封面上传、新增、持久化、编辑、播放与删除，不改变正式目录。浏览器为 Chromium 与触屏模拟，尚无真实安卓/iOS/Safari 实机验收。

维护或发布目录后运行 `node scripts/sync-work-catalogue.mjs`，以同步无脚本和离线目录。此前桌面横向展厅/舞台测试描述旧设计，新版使用上述回归。
