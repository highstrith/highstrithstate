# 精选放映边缘渐隐

目标：图片接近屏幕四边时平滑消失，解决出画硬切。改动限于fly-forward.css、首页资源版本、真实浏览器测试和项目文档；先复现边缘像素不透明，再加入图片层遮罩，验证四边、主题、原旋转与静态回退。主要风险为遮罩误伤标题／背景以及手机横向图带的可读性。

## 参考与实现

修改前检索了GitHub上的[MDN CSS masking示例](https://github.com/mdn/content/blob/main/files/en-us/web/css/guides/masking/mask_properties/index.md)，并核对[Tailwind CSS多方向渐变遮罩](https://tailwindcss.com/docs/mask-image)和[MDN mask-composite](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/mask-composite)。适合复用的是浏览器原生渐变与intersect机制；无需安装Tailwind或引入库，未复制第三方代码或素材。

根因：已有JS只按卡片深度改变整张透明度，图片到达屏幕边缘时仍由overflow直接裁切。现在桌面动态图片层的上下／左右遮罩取交集，四边各20%渐隐；中间保持完整对比，四角同时受两轴影响。遮罩直接露出原有径向背景，适配两种主题，不用模拟背景的覆盖层。

只遮罩.fly-field；标题、按钮、进度和舞台背景仍独立。手机、减少动态与无脚本模式不启用。保留原深度渐隐，不增加每帧DOM测量、定时器或请求。资源版本更新为20261101-edge-fade。

## 验证

- 新像素回归先在旧版失败：四边图片不透明度均为1。新版将首张卡片临时变成全舞台黑色测试平面，分别截图纯背景／带图层，在深浅主题的上下左右各采样四个距离；边界不透明度低于4%，向内逐步增加，内区高于98%。测试平面仅在测试中使用，结束移除。
- `python3 tests/fly-vortex-smoke.py -v`：5项通过，含四边实际像素、主题、标题不受遮罩、手机／reduce无残留遮罩，原螺旋与反向还原、背景、双语和全部作品入口。
- `node --test tests/pages-artifact-integration.mjs`：通过。`git diff --check`通过。
- 实际预览刷新后查看滚动和深浅主题，截图见[浅色](fly-edge-fade-20261101/light.png)、[深色](fly-edge-fade-20261101/dark.png)。本机Chrome通过；未验证真实Safari／移动设备。

仅本地提交，未推送或发布。
