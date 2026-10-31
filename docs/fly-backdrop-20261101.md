# 精选放映径向背景

用户反馈：放映段没有参考中的背景与径向渐变。目标为补齐整屏空间层次，涉及fly-forward.css、首页资源版本、真实浏览器回归及项目文档。先复现舞台没有渐变，再最小CSS修改，最后验证主题、滚动与静态回退。主要风险为把渐变铺在340vh轨道造成中心偏移，以及边缘文字对比不足。

## 参考与复用

开工前检索并评估[Codrops depth gallery](https://github.com/houmahani/codrops-depth-gallery/)的纵深画廊思路；本次只需背景，未引入其Three.js或GLSL代码，未复制素材。读取[Hello World](https://helloworlddsgn.com/#work)公开CSS及works.js确认其中心亮、边缘暗的径向背景另有WebGL速度模糊。参考页浏览器读取超时，使用公开源码核对机制；未复制其源码、纹理或蓝色配色。

旧版本只有.fly-head::before的局部纸色遮罩，#flyStage的background-image为none。新增真实浏览器测试先确认此失败，再在舞台上添加CSS径向渐变，避免全滚动轨道产生不同的光源中心。

## 结果与验证

- 浅色：暖纸中心到灰绿边缘；深色：暖光到炭黑。仅区域内颜色变量与辅助文字改变，主题跟随原切换按钮。
- 标题遮罩改用当前光晕颜色，避免突兀的纯纸白色块；静态图带也使用舞台背景，不增加运行时调度或图片请求。
- `python3 tests/fly-vortex-smoke.py -v`：4项通过，覆盖全舞台背景、深浅切换、粘性位置、手机与减少动态，以及原螺旋正反向、双语和作品入口。
- `python3 tests/studio-redesign-smoke.py StudioRedesign.test_cold_mobile_initial_images_stay_within_network_budget -v`：通过，104,621B，主封面960px。
- `node --test tests/pages-artifact-integration.mjs`：通过。`git diff --check`通过。
- 实际IAB预览刷新并核对两种主题；截图：[浅色](fly-backdrop-20261101/light.png)、[深色](fly-backdrop-20261101/dark.png)。测试使用本机Chrome，未验证真实移动设备。

本次完成CSS径向背景，没有实现WebGL径向速度模糊。仅本地提交，未推送或发布。
