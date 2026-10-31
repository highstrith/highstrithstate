# 首页独立章节与导演工作台整屏

用户希望导演台像精选放映一样成为完整一屏，并把主页分成比例合适的模块。本轮明确沿用连续主页、已有内容与锚点，涉及首页结构、专用章节CSS、共享导航的首页锚点计算及真实浏览器回归。先测量旧布局并建立失败回归，再调整独立舞台与响应式，最后核对轮播、标题、媒体画框和入口。风险是单纯固定高度裁切英文／短屏内容，以及跳转时仍露出前一节。

## 参考与设计

开始制作前检索并评估[DevPortfolio](https://github.com/ryanfitzgerald/devportfolio)（MIT）的单页分区与响应式组织；其完整Astro／Tailwind模板不适合替换本站的静态作品与动效系统，因此只借鉴内容分区思路，没有复制代码或资源。[MDN viewport lengths](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Values/length)用于核对svh与视口尺寸关系。

沿用既有纸白#f4f4f0、墨黑#171918、橘色#e46740、明亮表面#fcfdfb、柔和表面#e8ebe4与双主题变量；系统黑体、现有字号层级和标题反馈保留。布局以真实影片、制作界面和作者肖像为主体，不增加序号装饰或新媒体。

主页顺序：首屏 → 精选放映 → 全部作品 → 正在制作 → 作品截图 → 导演工作台 → 关于 → 联系，片单推荐作为页尾入口。导演台的通栏舞台内为「约1/3文案｜约2/3界面」，对齐统一内容边距。初次实测1440×900时导演台约643px、制作记录537px、关于747px，缺少独立章节空间。

## 实现与比例

- 首页独立home-modules.css覆盖布局，独立项目、制作记录和片单的排版不受影响。导演台增加内部page-width容器，外层负责整屏背景和纵向居中；轮播、暂停、现有弹性文字与跳转选择器继续使用。
- 801px以上核心章节至少100svh；使用min-height，目录、截图、英文和短屏内容均可增长。首屏大画框在足够高的桌面按剩余屏高控制，保持480–640px。精选仍为原340vh滚动轨道／100svh舞台和四边渐隐。
- 1440×900／减少动态下：首屏821px（另有100px导航流内空间）、目录1324px、制作记录900px、截图1517px、导演台900px、关于900px、联系944px、底部片单218px。减少动态精选保留507px静态图带；正常动态仍为整屏舞台。
- 1000px以下导演台改为上下排；800px以下章节自然高度，顶部96px安全留白、底部56px，肖像随宽度控制。界面图不因固定舞台高度而被强制拉伸。
- CSS scroll-margin抵消导航外部偏移，章节自身保留安全内边距；shell只对首页直接章节读取此值。独立页面和内层标题偏移延续。无脚本使用相同原生锚点，无需新增滚动库。

## 验证

- `python3 tests/home-modules-smoke.py -v`：3项。先红后绿，覆盖1024／1440／1920双语章节高度与图文比例，320／390／820与600px短窗、菜单落点、主题切换不变形、原生无脚本入口。无脚本测试需等load完成再点击，因为DOMContentLoaded不保证样式已加载。
- `python3 tests/hero-frame-smoke.py -v`：2项，真实五片切换／返回、延迟／失败全过程画框稳定。
- `python3 tests/typography-smoke.py -v`：2项；`tests/director-word-smoke.py`：4项。
- `tests/exhibition-upgrade-smoke.py`共享导航布局／同标签导航：2项；`tests/fly-vortex-smoke.py`：5项；`tests/production-strip-smoke.py`紧凑15图／响应式双语：2项；`tests/contact-rows-smoke.py`：4项。
- `node --test tests/pages-artifact-integration.mjs`：1项；`node --check assets/site-shell.js`、`git diff --check`通过。共25项定向检查。
- 实际IAB导演台截图见[桌面](home-modules-20261101/director.png)，独立Chrome手机截图见[手机](home-modules-20261101/mobile.png)。临时IAB尺寸已恢复；未验证真实Safari或移动硬件。

仅本地提交，未推送或发布。
