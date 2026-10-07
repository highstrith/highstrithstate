"""Desktop exhibition behavior against the real local site on port 3000."""
import unittest
from playwright.sync_api import sync_playwright


class DesktopExperience(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(channel="chrome", headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def test_stage_catalogue_and_player_return(self):
        page = self.browser.new_page(viewport={"width": 1440, "height": 900})
        try:
            page.goto("http://127.0.0.1:3000/", wait_until="domcontentloaded")
            page.locator(".stage-card").first.wait_for()
            self.assertEqual(page.locator(".stage-card").count(), 5)
            self.assertEqual(page.locator(".stage-card").first.get_attribute("data-work-id"), "work-reset-day-20261007")
            self.assertEqual(page.locator(".stage-card").nth(1).get_attribute("data-work-id"), "work-lying-down-20261001")
            self.assertEqual(page.locator(".stage-card").nth(2).get_attribute("data-work-id"), "featured-prove-it")
            self.assertEqual(page.locator(".stage-card").nth(3).get_attribute("data-work-id"), "featured-approach")
            self.assertEqual(page.locator(".stage-card").nth(4).get_attribute("data-work-id"), "featured-exported-film")
            self.assertEqual(page.locator(".stage-card", has_text="街头篮球").count(), 0)
            self.assertEqual(page.locator(".catalogue-card").count(), 14)
            page.locator("[data-stage-jump='3']").click()
            page.wait_for_function("document.querySelector('.stage-root').dataset.activeIndex === '3'")
            page.locator(".stage-root [data-open-catalogue]").click()
            self.assertTrue(page.locator("#workCatalogue").is_visible())
            self.assertTrue(page.locator(".stage-card .work-video").evaluate_all("videos => videos.every(video => video.paused)"))
            page.locator(".catalogue-card").last.scroll_into_view_if_needed()
            catalogue_position = page.locator("#workCatalogue").evaluate("e => e.scrollTop")
            page.locator(".catalogue-card").last.click()
            self.assertTrue(page.locator("#workPlayer").evaluate("el => el.classList.contains('is-open')"))
            page.locator("#workPlayerClose").click()
            self.assertTrue(page.locator("#workCatalogue").is_visible())
            self.assertAlmostEqual(page.locator("#workCatalogue").evaluate("e => e.scrollTop"), catalogue_position, delta=2)
            page.keyboard.press("Escape")
            self.assertFalse(page.locator("#workCatalogue").is_visible())
            self.assertEqual(page.locator(".stage-root").get_attribute("data-active-index"), "3")
        finally:
            page.close()

    def test_reduced_motion_uses_vertical_list(self):
        page = self.browser.new_page(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
        try:
            page.goto("http://127.0.0.1:3000/", wait_until="domcontentloaded")
            page.locator(".stage-card").first.wait_for()
            self.assertEqual(page.locator(".stage-viewport").evaluate("e => getComputedStyle(e).position"), "relative")
            self.assertEqual(page.locator(".stage-track").evaluate("e => getComputedStyle(e).transform"), "none")
            self.assertEqual(page.locator(".stage-card .work-video source[src]").count(), 0)
        finally:
            page.close()

    def test_stage_text_stays_above_controls_in_both_languages(self):
        # A taller media frame or unbounded title must not cover navigation.
        for width, height in [(1280, 720), (1440, 900), (1920, 1080)]:
            page = self.browser.new_page(viewport={"width": width, "height": height})
            try:
                page.goto("http://127.0.0.1:3000/", wait_until="domcontentloaded")
                page.locator(".stage-card").first.wait_for()
                page.evaluate("() => Promise.race([document.fonts.ready, new Promise(resolve => setTimeout(resolve, 5000))])")
                for language in ["zh-CN", "en"]:
                    if language == "en":
                        page.locator('button[aria-label="切换语言"]').click()
                    page.locator('.nav a[href="#works"]').click()
                    for index in range(5):
                        with self.subTest(width=width, language=language, work=index):
                            page.locator(f'[data-stage-jump="{index}"]').click()
                            page.wait_for_function("i => document.querySelector('.stage-root').dataset.activeIndex === String(i)", arg=index)
                            bounds = page.evaluate("""i => {
                                const card = document.querySelectorAll('.stage-card')[i];
                                const texts = [...card.querySelectorAll('h3, .work-meta, .work-description')];
                                return {
                                    bottom: Math.max(...texts.map(e => e.getBoundingClientRect().bottom)),
                                    controls: document.querySelector('.stage-controls').getBoundingClientRect().top,
                                    overflow: texts.some(e => e.scrollWidth > e.clientWidth + 1)
                                };
                            }""", index)
                            self.assertLessEqual(bounds["bottom"] + 16, bounds["controls"], bounds)
                            self.assertFalse(bounds["overflow"], bounds)
            finally:
                page.close()

    def test_repeated_works_anchor_keeps_controls_in_view(self):
        page = self.browser.new_page(viewport={"width": 1280, "height": 720})
        try:
            page.goto("http://127.0.0.1:3000/#works", wait_until="domcontentloaded")
            page.locator(".stage-card").first.wait_for()
            page.locator('.nav a[href="#works"]').click()
            bounds = page.locator(".stage-controls").bounding_box()
            self.assertLessEqual(bounds["y"] + bounds["height"], 720)
        finally:
            page.close()


if __name__ == "__main__":
    unittest.main()
