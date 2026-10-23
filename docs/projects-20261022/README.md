# 项目与应用分页

2026-10-22，本地实现，尚未推送或发布。

执行计划：增加独立分页及首页入口，复用 V2 字体与颜色，接入用户确认的积分比价系统和 AA 计算器，补真实截图；先验证缺失入口的失败行为，再实现并检查双语、响应式、应用操作与实际 Pages 打包。主要风险是静态应用快照需要同步更新、AA 不同网址的本机账单彼此独立。

开源调研：[asad-albadi/Portfolio](https://github.com/asad-albadi/Portfolio) 声明 MIT，采用项目数据与卡片链接的思路。现有原生站点和两个用户应用均可直接复用，因此不下载或复制第三方模板代码，不引入新的运行依赖；应用原有 React / ECharts 等许可注释保持。

## 应用来源

| 站内文件 / 目标链接 | 原成品 / 源码 | 说明 |
| --- | --- | --- |
| `assets/apps/ai-infinite-canvas.html` | `/Users/linjunjie/画布/ai-infinite-canvas` | AI 无限画布自包含单文件前端应用（样式与脚本全内联，支持 file:// 与离线直接双击运行），封面截图为新海诚项目电影感节点视图 |
| `assets/apps/points-comparison.html` | `/Users/linjunjie/Downloads/积分比价/frontend/dist/index.html` | `08ef261ebc91c99edb5c597d8795399b1cb3f68d68e5eb67e7c45970009ef232` |
| `assets/apps/aa-calculator.html` | `/Volumes/E61--/AA计算器/site/index.html` | `df96b34523bd04c3736f34a02bc0b7202d0faffef899200a752a0ae8942cdb77` |

两份副本与原成品逐字节一致，不包含浏览器内保存的账单、图片凭证或账号数据。AA 原网址 `https://aa-split-bill-18393.app.workbuddy.host/` 在本次网络中返回连接关闭，故使用同站静态成品；没有改动原服务。

## 后续维护

更新项目名称、简介或目标链接：编辑 `projects.html` 对应卡片及其中的 `data-cn` / `data-en` 文案。封面和按钮链接一起更新。可使用现有卡片结构添加更多项目。

更新应用：先在源项目完成正常构建和验证，再将上表原成品复制到对应站内文件；更新快照日期与此处哈希，必要时重新截取界面。不要手改打包后的 React 代码。当前没有自动同步，不把本机路径或本地服务器地址用作公开链接。

页面与构建检查：`python3 tests/projects-smoke.py -v`（先运行本站本地服务）、`node tests/pages-artifact-integration.mjs`。截图为 `desktop.png` / `mobile.png`，应用封面来自运行中的真实应用，AA 截图使用空白表单。
