# 交互式网页简历（双模式）实施计划 (Dual-Mode Interactive Resume Implementation Plan)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个以简历为主导、可与个人作品集放映厅无缝双向动态切换的高质感可交互简历单页（`resume.html`），并支持一键打印高质量 A4 PDF 简历及手机扫码看片。

**Architecture:** 
采用纯静态前端技术栈（无重依赖、极致加载速度），构建双视图单页应用（Dual-Mode SPA）。通过 `active-view="resume"` 与 `active-view="cinema"` 状态机实现履历与放映厅的无缝平滑切换；通过 `@media print` 样式实现高对比度标准纸质简历；结合已有 `site-qr.svg` 与 `assets/base.css` 实现统一视觉与体验。

**Tech Stack:** 
- HTML5 / Vanilla Modern JavaScript (ES2022)
- CSS3 (CSS Custom Properties, Flexbox, CSS Grid, Transitions, Media Queries, Print Styles)
- Python Playwright (Automated Smoke & Integration Testing)

**Spec:** `/Volumes/E61--/网站/site-portfolio-upgrade/docs/superpowers/specs/2026-10-23-interactive-resume-design.md`

## Global Constraints

- 根设计变量严格沿用 `assets/base.css` 中的 `--paper: #f4f4f0; --ink: #171918; --muted: #686d69; --line: #d6d9d2; --orange: #e46740;`。
- 全页支持 `data-cn` / `data-en` 多语言双语切换，状态通过 URL query `?lang=en` 维持。
- 保证移动端及桌面端均具备优秀的自适应与触控交互体验。
- 不引入外部 CDN 或重型前端框架，确保 GitHub Pages 极速离线与静态托管兼容。

---

### Task 1: 编写自动化测试套件 (Test Scaffolding)

**Files:**
- Create: `tests/resume-smoke.py`

**Interfaces:**
- Consumes: Static server at `http://127.0.0.1:3000` (or `STUDIO_BASE_URL`)
- Produces: Playwright test cases verifying:
  1. `resume.html` loads successfully with 200 OK and no JS errors.
  2. Default view is `resume` view showing creator info, impact stats, skills, timeline, and QR code.
  3. Clicking segmented control switches to `cinema` view with works grid.
  4. Clicking `返回个人简历` switches back to `resume` view.
  5. Clicking `现场放映` on featured work triggers switch to cinema view and opens video player.
  6. Copy contact button puts WeChat ID into clipboard and shows toast.

- [ ] **Step 1: 编写失败的 Playwright 测试脚本**

```python
"""Tests for the interactive dual-mode resume page."""
import os
import unittest
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

BASE = os.environ.get('STUDIO_BASE_URL', 'http://127.0.0.1:3000')
ROOT = Path(__file__).resolve().parents[1]


class ResumePageSmoke(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime = sync_playwright().start()
        cls.browser = cls.runtime.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.runtime.stop()

    def setUp(self):
        self.context = self.browser.new_context(reduced_motion='reduce')
        self.page = self.context.new_page()
        self.errors = []
        self.page.on('pageerror', lambda error: self.errors.append(str(error)))

    def tearDown(self):
        self.context.close()

    def test_resume_default_view_loads(self):
        self.page.goto(BASE + '/resume.html')
        expect(self.page).to_have_title('林俊杰 · 个人简历与作品展厅 — Highstrith')
        expect(self.page.locator('#view-resume')).to_be_visible()
        expect(self.page.locator('.profile-name')).to_contain_text('林俊杰')
        expect(self.page.locator('.badge-dual-engine')).to_be_visible()
        self.assertEqual(self.errors, [])

    def test_switch_to_cinema_and_back(self):
        self.page.goto(BASE + '/resume.html')
        # Switch to cinema
        self.page.locator('[data-switch-view="cinema"]').click()
        expect(self.page.locator('#view-cinema')).to_be_visible()
        expect(self.page.locator('#view-resume')).to_have_attribute('hidden', '')
        
        # Switch back to resume
        self.page.locator('[data-switch-view="resume"]').first.click()
        expect(self.page.locator('#view-resume')).to_be_visible()
        expect(self.page.locator('#view-cinema')).to_have_attribute('hidden', '')
        self.assertEqual(self.errors, [])

    def test_spotlight_play_switches_and_opens_player(self):
        self.page.goto(BASE + '/resume.html')
        self.page.locator('[data-play-work="work-ai-patient"]').click()
        expect(self.page.locator('#view-cinema')).to_be_visible()
        expect(self.page.locator('#resumePlayer')).to_have_attribute('open', '')
        self.assertEqual(self.errors, [])
```

- [ ] **Step 2: 运行测试以确认失败（因为 `resume.html` 尚不存在）**

Run: `python3 -m unittest tests/resume-smoke.py`
Expected: FAIL with 404 or connection error / navigation failure.

- [ ] **Step 3: 提交测试文件**

Run: `git add tests/resume-smoke.py && git commit -m "test: add smoke test suite for dual-mode resume page"`

---

### Task 2: 构建 `resume.html` 页面结构 (Page Markup)

**Files:**
- Create: `resume.html`

**Interfaces:**
- Consumes:
  - `assets/base.css`
  - `assets/studio-mark.svg`
  - `assets/site-qr.svg`
  - `assets/social/wechat-qr.png`
  - Data from `求职与简历/林俊杰_AIGC视频_简历.md`
  - Works catalog from `index.html` (14 selected works)
- Produces: Complete semantic HTML5 structure with:
  - Segmented control nav bar
  - `#view-resume` (Profile, Metrics, Skills, Timeline, Featured works, QR print box)
  - `#view-cinema` (Cinema header, Return button, Filter toolbar, Works grid)
  - Modals (`#resumePlayer` dialog, `#qrDialog` dialog, `#toast` notification)

- [ ] **Step 1: 编写 `resume.html` 核心语义结构**
- [ ] **Step 2: 校验 HTML 语法与无障碍标记 (ARIA attributes)**
- [ ] **Step 3: 运行本地静态服务器验证 HTML 解析无异常**

---

### Task 3: 编写 `assets/resume.css` 核心样式与打印规范 (Styling & Print)

**Files:**
- Create: `assets/resume.css`

**Interfaces:**
- Consumes: CSS custom variables from `assets/base.css` (`--paper`, `--ink`, `--muted`, `--orange`, `--line`)
- Produces:
  - Modern typography and magazine-inspired resume layout
  - Dual-mode tab toggle animations
  - Responsive cards, badges, and timeline nodes
  - Cinema grid layout with hover previews
  - Video player modal overlay
  - `@media print` rules:
    - Pure white page background, crisp black text
    - Strict hiding of navigation, buttons, and cinema view
    - Clean 2-column header with QR code + URL in top right
    - Page break control (`break-inside: avoid`)

- [ ] **Step 1: 编写组件级 CSS 规则与平滑动效**
- [ ] **Step 2: 编写 `@media print` 打印专用样式**
- [ ] **Step 3: 响应式适配验证（375px 移动端 / 768px 平板 / 1200px 桌面）**

---

### Task 4: 编写 `assets/resume.js` 交互状态机 (Interactive Logic)

**Files:**
- Create: `assets/resume.js`

**Interfaces:**
- Consumes: DOM elements in `resume.html`
- Produces:
  - View switcher state machine (`switchView('resume' | 'cinema')`)
  - Direct video player loader (`playWork(workId)`)
  - Bi-directional i18n switcher (`data-cn` / `data-en`)
  - Clipboard copy handler with floating toast notification
  - Print dialog trigger (`window.print()`)
  - QR dialog modal opener/closer

- [ ] **Step 1: 实现视图切换与 Hash 同步**
- [ ] **Step 2: 实现作品直达播放器控制器**
- [ ] **Step 3: 实现剪贴板复制、二维码弹窗与多语言切换**

---

### Task 5: 全面自动化测试与验收 (Verification & Acceptance)

**Files:**
- Test: `tests/resume-smoke.py`
- Modify: `docs/superpowers/plans/2026-10-23-interactive-resume.md` (Update checklist)

**Interfaces:**
- Consumes: Completed `resume.html`, `assets/resume.css`, `assets/resume.js`, `assets/site-qr.svg`
- Produces: All automated smoke tests passing cleanly with zero console errors.

- [ ] **Step 1: 启动静态服务并运行全量 Playwright 测试**
- [ ] **Step 2: 验证打印模式的 CSS 规则与版面完整性**
- [ ] **Step 3: 最终 Git 提交与总结**
