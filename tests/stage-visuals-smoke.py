"""Visual interaction lifecycle for the desktop exhibition."""
import unittest
from playwright.sync_api import sync_playwright


class StageVisuals(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(channel="chrome", headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def page(self, **options):
        page = self.browser.new_page(**options)
        self.addCleanup(page.close)
        page.goto("http://127.0.0.1:3000/", wait_until="domcontentloaded")
        page.locator(".stage-card").first.wait_for()
        return page

    def test_hero_pointer_and_reduced_motion(self):
        page = self.page(viewport={"width": 1440, "height": 900})
        page.mouse.move(1100, 350)
        page.wait_for_function("document.querySelector('.hero-visual').style.transform.includes('rotateY')")
        page.emulate_media(reduced_motion="reduce")
        page.wait_for_function("document.querySelector('.hero-visual').style.transform === ''")
        page.wait_for_function("getComputedStyle(document.querySelector('.stage-track')).transform === 'none'")
        page.emulate_media(reduced_motion="no-preference")
        page.wait_for_function("document.querySelector('.hero-visual').style.transform.includes('rotateY')")

    def test_stage_reverse_scroll_and_direct_contact(self):
        page = self.page(viewport={"width": 1440, "height": 900})
        page.locator("[data-stage-jump='4']").click()
        page.wait_for_function("document.querySelector('.stage-root').dataset.activeIndex === '4'")
        self.assertEqual(page.locator("#stageProgress").inner_text(), "05 / 05")
        page.locator("[data-stage-jump='1']").click()
        page.wait_for_function("document.querySelector('.stage-root').dataset.activeIndex === '1'")
        self.assertEqual(page.locator(".stage-card[tabindex='0']").count(), 1)
        page.locator(".nav a[href='#contact']").click()
        page.wait_for_function("document.querySelector('#contact').getBoundingClientRect().top < innerHeight")

    def test_hero_light_tracks_pointer_and_disables_when_inactive(self):
        page = self.page(viewport={"width": 1440, "height": 900})
        light = "getComputedStyle(document.querySelector('.hero'), '::after')"
        page.mouse.move(1050, 420)
        page.wait_for_function(f"Number({light}.opacity) > .9")
        first = page.evaluate(f"{light}.backgroundImage")
        self.assertIn("radial-gradient", first)
        self.assertEqual(page.evaluate(f"{light}.pointerEvents"), "none")
        page.mouse.move(450, 650)
        page.wait_for_function(f"() => {light}.backgroundImage !== " + repr(first))
        page.mouse.move(500, 45)  # Fixed navigation is outside the Hero.
        page.wait_for_function(f"Number({light}.opacity) === 0")
        page.mouse.move(1000, 430)
        page.wait_for_function(f"Number({light}.opacity) > .9")
        page.emulate_media(reduced_motion="reduce")
        page.wait_for_function(f"{light}.display === 'none'")
        page.emulate_media(reduced_motion="no-preference")
        page.set_viewport_size({"width": 390, "height": 844})
        self.assertEqual(page.evaluate(f"{light}.content"), "none")

    def test_player_focus_survives_fast_reopen(self):
        page = self.page(viewport={"width": 1440, "height": 900})
        first = page.locator(".stage-card").first
        first.click()
        self.assertTrue(page.locator("#workPlayer").evaluate("e => e.classList.contains('is-open')"))
        page.keyboard.press("Escape")
        self.assertTrue(first.evaluate("e => e === document.activeElement"))
        first.click()
        self.assertTrue(page.locator("#workPlayer").evaluate("e => e.classList.contains('is-open')"))
        self.assertTrue(page.locator(".shell").evaluate("e => e.inert"))
        page.keyboard.press("Escape")
        self.assertFalse(page.locator(".shell").evaluate("e => e.inert"))


if __name__ == "__main__":
    unittest.main()
