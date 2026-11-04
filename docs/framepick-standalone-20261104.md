# 橘生梦厂独立成站记录

2026-11-04

## 两个站，两个仓库

| | 橘生梦厂 | 作品集 |
|---|---|---|
| 地址 | https://highstrith.github.io/jusheng/ | https://highstrith.github.io/highstrithstate/ |
| 仓库 | `highstrith/jusheng`（产物仓库） | `highstrith/highstrithstate`（主仓库） |
| 内容 | 只有发布产物：9 个 js/css + 3 个 html + img/ | index/projects/in-progress/resume + assets/data |
| 部署 | 自己仓库的 `main`，workflow 直接发布仓库根目录 | `main`，workflow 打包 `public/` 后发布 |

开发仍然只有一个源：主仓库的 `reel/` 目录。工具、测试、构建脚本、封面母版（`reel/img/raw`）全在主仓库，`highstrith/jusheng` 里不手改任何文件。

## 为什么拆

1. **数据分开算。** 30 天验证要算订阅转化率，分母必须只是来看片的人。原来作品集访客和片单访客混在一个域名下，H1 的数字是糊的。
2. **品牌分开。** 橘生梦厂是产品，作品集是履历，混在一起两边都不像。
3. **能退。** 验证不成立就把独立站归档，作品集删掉一个入口链接即可，不牵动作品页。

## 作品集这边改了什么

- 首页「推荐区」三张卡与入口按钮指向 `https://highstrith.github.io/jusheng/`，`target="_blank" rel="noopener"`
- 三张封面从 `reel/img/` 复制到 `assets/film-recommendation/`，作品集不再依赖 reel 目录
- 产品区文案与 i18n 从「帧选 / Framepick」改为「橘生梦厂 / Jusheng Mengchang」
- `pages.yml` 不再打包 `reel/`，避免两站双发布
- 顺手修掉一个老问题：三张卡的 `srcset` 挂着 `xianggu.webp 1280w` 等三个不存在的文件（线上一直 404），改为单 640w

## 发布流程

```
scripts/framepick-ship.sh "说明文字"
```

1. 取封面、转 640w webp
2. 上传 `reel/img/` 与 `assets/film-recommendation/` 到 OSS，逐张自检 200
3. 重建首页与片库页，跑校验与测试
4. 同步 `reel/` → `../jusheng/`（排除 `img/raw`、`._*`，保留 `.git`、`.github`、README）
5. 同步 `reel/` → `../framepick-live/reel/`（本地预览副本，3100 端口）
6. 提交并推送两个仓库，等两边的 Actions 跑完，复核线上

`--no-push` 只做到本地校验；`--fast` 跳过浏览器测试。

## 踩过的坑

**MEDIA_CDN 会把封面改写到 OSS。** 仓库变量 `MEDIA_CDN_BASE_URL` 已配置，所以 `assets/film-recommendation/` 下的图必须上传到 OSS 对应路径，否则上线后是三张破图。第一次拆完就踩了，已补进 ship 脚本和自检。

**exFAT 的 `._*` 伴生文件会污染新仓库。** `rsync -a`、`git init` 都会生成，`git fsck` 会读错。ship 脚本同步后统一 `find -name '._*' -delete`，`jusheng` 的 `.gitignore` 也加了这一条。

**旧 `/reel/` 已经 404。** 拆之前站外没有任何链接指向它（第一期还没发），所以没有断链风险。以后不要再引用 `/reel/`。

## 以后

- 绑自有域名（需要买域名 + 国内加速要备案）留到 30 天验证通过之后，现在不值得为它花钱。
- 如果要给独立站加访问统计，直接在新仓库的 `index.html` 里加，不经过作品集。
