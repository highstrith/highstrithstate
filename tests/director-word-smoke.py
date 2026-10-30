"""The Hero and Director headings respond locally to a mouse."""
import os
import unittest
from playwright.sync_api import sync_playwright, expect

BASE = os.environ.get('STUDIO_BASE_URL', 'http://127.0.0.1:3000')


class DirectorWord(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime = sync_playwright().start()
        cls.browser = cls.runtime.chromium.launch(channel='chrome', headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.runtime.stop()

    def page(self, **options):
        page = self.browser.new_page(viewport={'width': 1440, 'height': 900}, **options)
        self.addCleanup(page.close)
        page.goto(BASE, wait_until='domcontentloaded')
        page.locator('.tools-preview').scroll_into_view_if_needed()
        page.wait_for_function("document.querySelector('.tools-preview-copy').classList.contains('rv-in')")
        page.wait_for_timeout(500)
        return page

    def test_nearby_letters_stretch_and_return_without_moving_layout(self):
        page = self.page()
        expect(page.locator('#toolsTitle .director-letter')).to_have_count(5)
        heading = page.locator('#toolsTitle')
        original = heading.bounding_box()
        intro = page.locator('[data-i18n="toolsIntro"]').bounding_box()
        first = heading.locator('.director-letter').first.bounding_box()
        page.mouse.move(first['x'] + first['width']/2, first['y'] + first['height']/2)
        page.wait_for_timeout(220)
        scales = heading.locator('.director-letter').evaluate_all("els => els.map(e => new DOMMatrix(getComputedStyle(e).transform).m22)")
        self.assertGreater(scales[0], 1.08)
        self.assertGreater(scales[0], scales[-1] + .04)
        self.assertAlmostEqual(original['height'], heading.bounding_box()['height'], delta=1)
        self.assertAlmostEqual(intro['y'], page.locator('[data-i18n="toolsIntro"]').bounding_box()['y'], delta=1)
        page.mouse.move(10, 10)
        page.wait_for_timeout(850)
        self.assertTrue(all(value == 'none' for value in heading.locator('.director-letter').evaluate_all('els => els.map(e => getComputedStyle(e).transform)')))
        self.assertEqual(page.locator('#studioCursor').count(), 0)
        self.assertNotEqual(page.locator('body').evaluate('e => getComputedStyle(e).cursor'), 'none')

    def test_translation_reduce_and_project_link_remain_correct(self):
        page = self.page()
        page.locator('#langSwitch').click()
        expect(page.locator('#toolsTitle')).to_have_text('Director’s workbench')
        expect(page.locator('#toolsTitle')).to_have_attribute('aria-label', 'Director’s workbench')
        expect(page.locator('#heroTitle')).to_have_attribute('aria-label', 'Imagination, in motion')
        self.assertGreater(page.locator('#toolsTitle .director-letter').count(), 10)
        page.locator('#toolsTitle').hover()
        page.emulate_media(reduced_motion='reduce')
        page.wait_for_timeout(150)
        self.assertTrue(all(value == 'none' for value in page.locator('.director-letter').evaluate_all('els => els.map(e => getComputedStyle(e).transform)')))
        page.locator('.tools-preview-copy .text-link').click()
        page.wait_for_url('**/projects.html?lang=en#directorTitle')
        self.assertEqual(page.locator('.director-letter').count(), 0)

    def test_touch_and_failed_script_keep_static_readable_title(self):
        page = self.page(is_mobile=True, has_touch=True)
        page.locator('#toolsTitle').dispatch_event('pointermove', {'pointerType': 'touch', 'clientX': 200, 'clientY': 200})
        self.assertEqual(page.locator('.director-letter[style]').count(), 0)
        self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'), 1440)
        fallback = self.browser.new_page()
        self.addCleanup(fallback.close)
        fallback.route('**/director-word.js*', lambda route: route.abort())
        fallback.goto(BASE, wait_until='domcontentloaded')
        expect(fallback.locator('#toolsTitle')).to_have_text('导演工作台')
        self.assertEqual(fallback.locator('.director-letter').count(), 0)

    def test_hero_letters_ripple_restore_and_keep_independent_filters(self):
        page = self.page()
        hero = page.locator('#heroTitle')
        expect(hero.locator('.director-letter')).to_have_count(7)
        hero.scroll_into_view_if_needed()
        page.wait_for_timeout(700)
        first = hero.locator('.director-letter').first
        first.hover()
        page.wait_for_timeout(220)
        self.assertGreater(first.evaluate('e => new DOMMatrix(getComputedStyle(e).transform).m22'), 1.08)
        self.assertTrue(all(value == 'none' for value in page.locator('#toolsTitle .director-letter').evaluate_all('els => els.map(e => getComputedStyle(e).transform)')))
        page.mouse.move(10, 10)
        page.wait_for_timeout(850)
        self.assertTrue(all(value == 'none' for value in hero.locator('.director-letter').evaluate_all('els => els.map(e => getComputedStyle(e).transform)')))
        ids = page.locator('.elastic-word-filters filter').evaluate_all('els => els.map(e => e.id)')
        self.assertEqual(len(ids), 12)
        self.assertEqual(len(set(ids)), len(ids))
        page.locator('#langSwitch').click()
        expect(hero).to_have_text('Imagination, in motion')
        expect(hero).to_have_attribute('aria-label', 'Imagination, in motion')
        self.assertGreater(hero.locator('.director-letter').count(), 10)
        self.assertEqual(hero.locator('.rv-line').count(), 0)


if __name__ == '__main__':
    unittest.main()
