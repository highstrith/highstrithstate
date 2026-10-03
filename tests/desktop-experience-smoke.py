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
            self.assertEqual(page.locator(".stage-card").first.get_attribute("data-work-id"), "work-lying-down-20261001")
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


if __name__ == "__main__":
    unittest.main()
