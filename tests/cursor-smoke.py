"""Reading text stays an arrow; links and real fields keep their native affordances."""
import os
import unittest
from playwright.sync_api import sync_playwright, expect

BASE = os.environ.get('STUDIO_BASE_URL', 'http://127.0.0.1:3000').rstrip('/')


class ReadingCursor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime = sync_playwright().start()
        cls.browser = cls.runtime.chromium.launch(channel='chrome', headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.runtime.stop()

    def page(self, path):
        page = self.browser.new_page(viewport={'width': 1440, 'height': 900}, reduced_motion='reduce')
        self.addCleanup(page.context.close)
        page.goto(BASE + path, wait_until='load')
        return page

    def test_public_page_copy_uses_an_arrow_including_nested_heading_letters(self):
        for path in ['/', '/projects.html', '/in-progress.html', '/resume.html', '/reel/']:
            with self.subTest(path=path):
                page = self.page(path)
                text = page.locator('h1, h1 span, h2, h2 span, p').filter(visible=True)
                self.assertGreater(text.count(), 0)
                for element in text.all():
                    # Text inside a real link/button inherits its interactive cursor.
                    if element.evaluate('e=>!!e.closest("a[href], button")'):
                        continue
                    self.assertEqual(element.evaluate('e=>getComputedStyle(e).cursor'), 'default',
                                     (path, element.text_content()[:40]))
                page.close()

    def test_links_buttons_and_image_zoom_keep_their_action_cursors(self):
        page = self.page('/')
        for selector, cursor in [('a[href]', 'pointer'), ('#themeToggle', 'pointer'),
                                 ('.still-media', 'zoom-in'), ('.home-progress-card', 'zoom-in')]:
            self.assertEqual(page.locator(selector).first.evaluate('e=>getComputedStyle(e).cursor'), cursor)
        page = self.page('/reel/')
        for selector in ['.bar nav a', '.watch', '.card-media']:
            self.assertEqual(page.locator(selector).first.evaluate('e=>getComputedStyle(e).cursor'), 'pointer')

    def test_actual_fields_stay_editable_and_reading_text_can_still_be_selected(self):
        page = self.page('/')
        search = page.locator('#workSearch')
        self.assertEqual(search.evaluate('e=>getComputedStyle(e).cursor'), 'text')
        search.fill('重置')
        expect(search).to_have_value('重置')
        page = self.page('/admin.html')
        for selector in ['#uploadCnTitleInput', '#uploadCnDescInput']:
            field = page.locator(selector)
            self.assertEqual(field.evaluate('e=>getComputedStyle(e).cursor'), 'text')
            field.fill('测试文字')
            expect(field).to_have_value('测试文字')
        page = self.page('/reel/')
        paragraph = page.locator('.lede')
        box = paragraph.bounding_box()
        page.mouse.dblclick(box['x'] + 18, box['y'] + 12)
        self.assertTrue(page.evaluate('!!getSelection().toString().trim()'))
        self.assertFalse(paragraph.evaluate('e=>e.isContentEditable'))


if __name__ == '__main__':
    unittest.main()
