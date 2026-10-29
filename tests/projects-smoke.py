"""Project navigation and actual app entry points on static hosting."""
import os
import unittest
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright, expect

BASE = os.environ.get('STUDIO_BASE_URL', 'http://127.0.0.1:3000')
ROOT = Path(__file__).resolve().parents[1]


class ProjectPages(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime = sync_playwright().start()
        cls.browser = cls.runtime.chromium.launch(channel=os.environ.get('STUDIO_BROWSER_CHANNEL', 'chrome'), headless=True)

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
        self.context.unroute_all(behavior='ignoreErrors')
        self.context.close()

    def test_home_navigation_opens_distinct_project_page(self):
        self.page.goto(BASE + '/')
        self.page.get_by_role('navigation').get_by_role('link', name='项目与应用', exact=True).click(timeout=3000)
        expect(self.page).to_have_url(BASE + '/projects.html')
        expect(self.page.get_by_role('heading', name='项目与应用', exact=True)).to_be_visible()
        expect(self.page.get_by_role('heading', name='AI 无限画布', exact=True)).to_be_visible()
        expect(self.page.get_by_role('heading', name='积分比价系统', exact=True)).to_be_visible()
        expect(self.page.get_by_role('heading', name='AA 计算器', exact=True)).to_be_visible()
        self.page.wait_for_function('Array.from(document.querySelectorAll(".project-preview img")).every(image => image.complete && image.naturalWidth > 0)')
        self.assertEqual(self.errors, [])

    def test_comparison_entry_opens_working_self_contained_app(self):
        self.page.goto(BASE + '/projects.html')
        with self.page.expect_popup() as popup:
            self.page.locator('.project-bottom').get_by_role('link', name='打开积分比价系统').click(timeout=3000)
        app = popup.value
        app.wait_for_load_state('load')
        expect(app.get_by_role('tab', name='年付', exact=True)).to_be_visible()
        app.get_by_role('tab', name='月付', exact=True).click()
        expect(app.get_by_role('tab', name='月付', exact=True)).to_have_attribute('aria-selected', 'true')
        self.assertIn('/assets/apps/points-comparison.html', app.url)
        self.assertEqual(self.errors, [])

    def test_aa_entry_opens_existing_calculator(self):
        self.page.goto(BASE + '/projects.html')
        link = self.page.locator('.project-bottom').get_by_role('link', name='打开 AA 计算器')
        expect(link).to_have_attribute('href', 'assets/apps/aa-calculator.html')
        expect(link).to_have_attribute('target', '_blank')
        self.assertIn('noopener', link.get_attribute('rel'))
        with self.page.expect_popup() as popup:
            link.click()
        app = popup.value
        app.wait_for_load_state('load')
        expect(app.get_by_role('heading', level=1)).to_contain_text('玩得尽兴，')
        for index, (name, paid) in enumerate((('小明', '90'), ('小红', '0'), ('小李', '0')), start=1):
            app.get_by_role('textbox', name=f'第 {index} 位姓名', exact=True).fill(name)
            app.get_by_role('textbox', name=f'第 {index} 位垫付金额', exact=True).fill(paid)
        app.get_by_role('button', name='算清这笔账', exact=True).click()
        expect(app.get_by_role('complementary', name='结算单')).to_contain_text('30.00')
        expect(app.get_by_role('complementary', name='结算单')).to_contain_text('小明')

    def test_language_survives_navigation_both_directions(self):
        self.page.goto(BASE + '/')
        self.page.locator('#langSwitch').click()
        self.page.get_by_role('navigation').get_by_role('link', name='Projects', exact=True).click(timeout=3000)
        expect(self.page.locator('html')).to_have_attribute('lang', 'en')
        expect(self.page.get_by_role('heading', name='Projects & apps', exact=True)).to_be_visible()
        self.page.get_by_role('navigation').get_by_role('link', name='Works', exact=True).click()
        expect(self.page.locator('html')).to_have_attribute('lang', 'en')
        expect(self.page.locator('#works')).to_be_in_viewport()
        self.assertEqual(self.errors, [])

    def test_responsive_layout_and_file_mode(self):
        for width in (320, 390, 820, 1440, 1920):
            for language in ('cn', 'en'):
                self.page.set_viewport_size({'width': width, 'height': 900})
                for route in ('/', '/projects.html'):
                    self.page.goto(BASE + route + '?lang=' + language)
                    self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth <= innerWidth'), (width, language, route))
                    boxes = self.page.locator('.main-nav a').evaluate_all('(links) => links.map(link => { const r = link.getBoundingClientRect(); return {left:r.left, right:r.right}; })')
                    self.assertTrue(all(a['right'] <= b['left'] for a, b in zip(boxes, boxes[1:])), (width, language, route))
        self.page.goto((ROOT / 'projects.html').as_uri())
        expect(self.page.locator('.project-bottom').get_by_role('link', name='打开 AI 无限画布')).to_be_visible()
        with self.page.expect_popup() as popup:
            self.page.locator('.project-bottom').get_by_role('link', name='打开 AI 无限画布').click()
        app = popup.value
        app.wait_for_load_state('load')
        expect(app.get_by_role('heading', name='你的创作工作台', exact=True)).to_be_visible()
        app.close()
        expect(self.page.locator('.project-bottom').get_by_role('link', name='打开积分比价系统')).to_be_visible()
        self.page.locator('#langSwitch').click()
        expect(self.page.get_by_role('heading', name='AI infinite canvas', exact=True)).to_be_visible()
        expect(self.page.get_by_role('heading', name='Points comparison', exact=True)).to_be_visible()
        self.assertEqual(self.errors, [])

    def test_canvas_entry_opens_working_app(self):
        self.page.goto(BASE + '/projects.html')
        link = self.page.locator('.project-bottom').get_by_role('link', name='打开 AI 无限画布')
        expect(link).to_have_attribute('href', 'assets/apps/ai-infinite-canvas.html')
        expect(link).to_have_attribute('target', '_blank')
        self.assertIn('noopener', link.get_attribute('rel'))
        with self.page.expect_popup() as popup:
            link.click()
        app = popup.value
        app.wait_for_load_state('load')
        expect(app.get_by_role('heading', name='你的创作工作台', exact=True)).to_be_visible()
        self.assertIn('/assets/apps/ai-infinite-canvas.html', app.url)
        self.assertEqual(self.errors, [])

    def test_project_entries_work_without_javascript(self):
        context = self.browser.new_context(java_script_enabled=False)
        try:
            page = context.new_page()
            page.goto(BASE + '/projects.html')
            expect(page.locator('.project-bottom').get_by_role('link', name='打开 AI 无限画布')).to_have_attribute('href', 'assets/apps/ai-infinite-canvas.html')
            expect(page.locator('.project-bottom').get_by_role('link', name='打开积分比价系统')).to_have_attribute('href', 'assets/apps/points-comparison.html')
            expect(page.locator('.project-bottom').get_by_role('link', name='打开 AA 计算器')).to_have_attribute('href', 'assets/apps/aa-calculator.html')
        finally:
            context.close()

    def test_static_subpath_keeps_app_and_return_links_working(self):
        public = 'https://portfolio.test/highstrithstate/'
        def static_route(route):
            relative = urlsplit(route.request.url).path.removeprefix('/highstrithstate/')
            route.fulfill(response=route.fetch(url=BASE + '/' + relative))
        self.context.route('https://portfolio.test/**', static_route)
        self.page.goto(public + 'projects.html?lang=en')
        with self.page.expect_popup() as popup:
            self.page.locator('.project-bottom').get_by_role('link', name='Open points comparison').click()
        app = popup.value
        app.wait_for_load_state('load')
        expect(app).to_have_url(public + 'assets/apps/points-comparison.html')
        expect(app.get_by_role('tab', name='年付', exact=True)).to_be_visible()
        self.page.get_by_role('navigation').get_by_role('link', name='Works', exact=True).click()
        expect(self.page).to_have_url(public + 'index.html?lang=en#works')
        expect(self.page.locator('html')).to_have_attribute('lang', 'en')
        expect(self.page.locator('#adminEntryLink')).not_to_be_visible()


if __name__ == '__main__':
    unittest.main()
