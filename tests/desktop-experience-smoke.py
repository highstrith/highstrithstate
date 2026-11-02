"""Desktop exhibition behaviour against the real local site."""
import os
import unittest
from playwright.sync_api import sync_playwright

BASE = os.environ.get('STUDIO_BASE_URL', 'http://127.0.0.1:3000').rstrip('/')
# Six works lay out per page; the rest wait for pagination.
PAGE_SIZE = 6
# The hidden work never reaches the public catalogue.
HIDDEN_TITLE = '巨轮空降'


class DesktopExperience(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(channel='chrome', headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def page(self, width=1440, height=900, **options):
        page = self.browser.new_page(viewport={'width': width, 'height': height}, **options)
        self.addCleanup(page.close)
        page.goto(BASE + '/', wait_until='domcontentloaded')
        page.locator('.work-card').first.wait_for()
        return page

    def test_catalogue_opens_the_player_and_returns_to_the_same_place(self):
        page = self.page()
        self.assertEqual(page.locator('.work-card').first.get_attribute('data-work-id'), 'work-reset-day-20261007')
        self.assertEqual(page.locator('.work-card', has_text=HIDDEN_TITLE).count(), 0)
        card = page.locator('.work-card').nth(PAGE_SIZE - 1)
        card.scroll_into_view_if_needed()
        position = page.evaluate('window.scrollY')
        card.click()
        page.wait_for_function("() => { const video = document.querySelector('#workPlayerVideo');"
                               " return video.readyState >= 2 && !video.paused && video.currentTime > 0; }", timeout=15000)
        self.assertTrue(page.locator('#workPlayer').evaluate('dialog => dialog.open'))
        page.locator('#workPlayerClose').click()
        page.wait_for_function("() => !document.querySelector('#workPlayer').open")
        # Closing hands the page back where the visitor left it, not at the top.
        self.assertLess(abs(page.evaluate('window.scrollY') - position), 160)
        self.assertTrue(page.locator('.works-grid').is_visible())

    def test_reduced_motion_keeps_the_page_still_and_quiet(self):
        page = self.page(reduced_motion='reduce')
        self.assertEqual(page.locator('.work-card video').evaluate_all(
            'videos => videos.filter(video => video.currentSrc).length'), 0)
        # The featured stage animates with transforms; reduced motion leaves it flat.
        self.assertIn(page.locator('.fly-stage').evaluate('stage => getComputedStyle(stage).transform'),
                      ('none', 'matrix(1, 0, 0, 1, 0, 0)'))

    def test_card_text_stays_inside_its_card_in_both_languages(self):
        for width, height in [(1280, 720), (1440, 900), (1920, 1080)]:
            page = self.page(width, height)
            for language in ['zh', 'en']:
                if language == 'en':
                    page.locator('#langSwitch').click()
                with self.subTest(width=width, language=language):
                    overflow = page.evaluate("""() => [...document.querySelectorAll('.work-card')].slice(0, 6)
                        .flatMap(card => [...card.querySelectorAll('.work-title, .work-description, .work-category')]
                            .filter(text => text.scrollWidth > text.clientWidth + 1)
                            .map(text => text.textContent.trim()))""")
                    self.assertEqual(overflow, [], overflow)

    def test_repeated_works_anchor_keeps_the_layout_intact(self):
        page = self.page(width=1280, height=720)
        for _ in range(3):
            page.locator('.main-nav a[href="#works"], nav a[href="#works"]').first.click()
        self.assertFalse(page.evaluate('document.documentElement.scrollWidth > innerWidth'))
        self.assertTrue(page.locator('.works-grid').is_visible())


if __name__ == '__main__':
    unittest.main()
