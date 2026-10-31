# 全部作品翻页定位

用户报告分页点击后有奇怪的上下偏移。目标是保持回到新一页开头的既有行为，消除大幅瞬跳与反弹；涉及studio.js分页处理器、首页资源版本、真实浏览器分页回归和项目文档。先逐帧复现，再最小修复，最后检查末页往返、目录／手机、减少动态及章节锚点。风险是误改翻页焦点或与章节顶部偏移冲突。

## 调查与复用评估

修改前检索并评估[scroll-into-view-if-needed](https://github.com/scroll-into-view/scroll-into-view-if-needed)，核对[MDN scrollIntoView](https://developer.mozilla.org/en-US/docs/Web/API/Element/scrollIntoView)与[CSS Scroll Anchoring规范](https://www.w3.org/TR/css-scroll-anchoring-1/)。本站目标是正常回到开头，原生API足够，不引入polyfill、滚动库或复制第三方代码。

记录分页点击前及随后1100ms各帧的scrollY和作品区top。旧处理器在applyFilters后强制instant回顶，桌面画廊单帧移动662px、390px手机2074px、目录900px；减少动态下同样直接定位。末页只有两张卡片时自然缩短，放大了切换时的视觉变化。最终位置稳定，没有证据需要全局禁用滚动锚定或锁定页面高度。

## 实现与验证

只将普通偏好的分页定位改为smooth，减少动态继续instant，明确block:start。原有标题preventScroll聚焦、页码、历史、筛选、搜索、双语与末页内容不改，沿用上一轮章节的scroll-margin。资源版本为20261101-paging-scroll。

- `python3 tests/catalogue-pages-smoke.py -v`：7项通过；新增逐帧回归先在旧版三种普通动态场景失败，再验证桌面／手机／目录3→4→3，检查单帧不突跳、没有向下反弹、无顶部越界、最终top在1px内、焦点及作品准确；减少动态仍直接定位。
- `python3 tests/home-modules-smoke.py -v`：3项通过。
- `node --test tests/pages-artifact-integration.mjs`：1项通过。
- `node --check assets/studio.js`、`git diff --check`通过。
- 独立IAB标签实际点击末页后，作品区top=-0.22px，页码4，标题获得焦点；[结果截图](pagination-scroll-20261101/after.png)。截图只能展示最终落点，运动连续性由逐帧回归验证。测试标签关闭，不更改用户其他标签。

验证环境为本机Chrome及手机视口／动态偏好模拟，未验证真实移动硬件或Safari。仅本地提交，未推送或发布。
