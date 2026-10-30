# 导演工作台左侧标题的鼠标反馈

2026-10-30。用户明确只要导演工作台左侧文字的类似交互；本轮最终仅修改首页标题，临时试作的全站像素光标、其他页面引用与其测试／截图均已撤回。

参考实际访问的 [Hello World](https://helloworlddsgn.com/) 底部 Hello_world 字标：附近字母随鼠标拉伸、倾斜、变色，移动时产生局部波动，离开后恢复。开工前评估了 [swe-labs/custom-cursor](https://github.com/swe-labs/custom-cursor) 和 [MS-Cursor](https://github.com/guillaume-rygn/MS-Cursor)；它们主要处理光标替换，与用户最终指定的文字交互不匹配。未复制外部代码或素材，使用原生DOM、CSS和SVG滤镜自行实现。

执行方案：新增独立director-word CSS／JS和首页资源引用，保留原字号、双语、左侧正文及右侧轮播；先验证原标题缺少逐字响应，再实现附近字形的轻微拉伸／波动，最后检查恢复、翻译、移动端与跳转。风险是拆字影响换行和辅助阅读，以及动效导致周围排版抖动；通过词组包裹、完整aria-label和仅改变内部字形transform处理。

- 仅`#toolsTitle`被拆字。以68px距离场给附近字符分配影响值，纵向最大增加18%，轻微横向收缩／倾斜并向原有橘色混合。SVG局部位移最多2.2px，运动停止后消散。
- 字符transform不参与排版，标题原30px及手机28px规则保留，不移动正文或入口。英文按词保持换行，标题可访问名称为完整文字，装饰字组aria-hidden。
- 监听标题文本变化，语言切换后重建原位字符及独立滤镜，不保留旧语言文案。不会修改页面鼠标、其他标题、链接行为或轮播节点。
- 触屏／减少动态静态展示，滚动／失焦／后台清理。仅在鼠标移动或字形收敛时调度rAF；无脚本为原始可读标题。

验证：`python3 tests/director-word-smoke.py -v` 3项通过，覆盖近字强于远字、实际矩阵拉伸、标题／正文占位不变、移开恢复、语言／可访问名称、减少动态、触摸、脚本失败和真实项目入口。原版缺少字符响应时失败，实施后通过。

`StudioRedesign.test_layout_and_contacts_at_supported_widths` 的5档中英文布局通过，`node --test tests/pages-artifact-integration.mjs`、JS语法及Git空白检查通过。截图见`director-word-20261030/hover.png`。浏览器为本机Chrome；未验证Safari和真实触屏设备。仅本地提交，未发布。
