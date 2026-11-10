"""Responsive public site and the local-file catalogue fallback."""
import os
import unittest
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

BASE = os.environ.get('STUDIO_BASE_URL', 'http://127.0.0.1:3000').rstrip('/')
ROOT = Path(__file__).resolve().parents[1]
# Twenty public works; the hidden one never reaches the grid or the fallback.
import json as _catalogue_json
from pathlib import Path as _catalogue_path
_CATALOGUE_FOR_TESTS = _catalogue_json.loads((_catalogue_path(__file__).resolve().parents[1] / 'data/works.json').read_text())
_VISIBLE_FOR_TESTS = sorted((_w for _w in _CATALOGUE_FOR_TESTS if _w['id'] != 'featured-giant-wheel'), key=lambda _w: _w.get('createdAt', ''), reverse=True)
PUBLIC_WORKS = len(_VISIBLE_FOR_TESTS)
MANAGED_WORKS = len(_CATALOGUE_FOR_TESTS)
FIRST_WORK_ID = _VISIBLE_FOR_TESTS[0]['id']

class SiteRedesign(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime = sync_playwright().start()
        cls.browser = cls.runtime.chromium.launch(channel='chrome', headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.runtime.stop()

    def page(self, width, height, **options):
        page = self.browser.new_page(viewport={'width': width, 'height': height}, **options)
        self.addCleanup(page.context.close)
        page.goto(BASE + '/', wait_until='domcontentloaded')
        page.locator('.work-card').first.wait_for()
        return page

    def test_desktop_layout_stays_inside_the_viewport_in_both_languages(self):
        for width, height in ((1280, 720), (1440, 900), (1920, 1080)):
            with self.subTest(width=width):
                page = self.page(width, height)
                self.assertEqual(page.locator('.work-card').count(), PUBLIC_WORKS)
                self.assertFalse(page.evaluate('document.documentElement.scrollWidth > innerWidth'))
                page.locator('.hero-avatar').scroll_into_view_if_needed()
                page.wait_for_function("document.querySelector('.hero-avatar')?.naturalWidth > 0")
                self.assertTrue(page.locator('.hero-avatar').evaluate('image => image.currentSrc').endswith('.webp'))
                page.locator('#langSwitch').click()
                expect(page.locator('#worksTitle')).to_have_text('All works')
                self.assertFalse(page.evaluate('document.documentElement.scrollWidth > innerWidth'))

    def test_narrow_screens_stack_the_grid_into_one_or_two_columns(self):
        for width, height, columns in ((820, 950, 2), (390, 844, 1), (320, 760, 1)):
            with self.subTest(width=width):
                page = self.page(width, height, is_mobile=width < 700, has_touch=width < 700)
                self.assertEqual(page.locator('.work-card').count(), PUBLIC_WORKS)
                self.assertEqual(page.evaluate(
                    "getComputedStyle(document.querySelector('.works-grid')).gridTemplateColumns.split(' ').length"), columns)
                self.assertFalse(page.evaluate('document.documentElement.scrollWidth > innerWidth'))
                page.locator('#langSwitch').click()
                self.assertFalse(page.evaluate('document.documentElement.scrollWidth > innerWidth'))

    def test_the_management_entry_stays_hidden_off_the_local_host(self):
        page = self.browser.new_page(viewport={'width': 1280, 'height': 800})
        self.addCleanup(page.context.close)
        page.route('https://portfolio.example/**', lambda route: route.fulfill(
            response=route.fetch(url=route.request.url.replace('https://portfolio.example', BASE))))
        # Requests still in flight would otherwise error while the page is closing.
        self.addCleanup(page.unroute_all, behavior='ignoreErrors')
        page.goto('https://portfolio.example/', wait_until='domcontentloaded')
        page.locator('.work-card').first.wait_for()
        expect(page.locator('#adminEntryLink')).to_be_hidden()

    def test_opening_the_page_from_disk_still_lists_every_public_work(self):
        page = self.browser.new_page(viewport={'width': 1280, 'height': 800}, java_script_enabled=False)
        self.addCleanup(page.context.close)
        page.goto((ROOT / 'index.html').as_uri(), wait_until='domcontentloaded')
        # The <noscript> catalogue is the only thing file:// visitors get.
        expect(page.locator('.no-js-work')).to_have_count(PUBLIC_WORKS)
        self.assertEqual(page.locator('.no-js-work', has_text='巨轮空降').count(), 0)


if __name__ == '__main__':
    unittest.main()
