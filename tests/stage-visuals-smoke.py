"""Player focus and in-page anchors.

The hero pointer tilt and its radial light were dropped with the redesign, so
those checks are retired here rather than left failing; the works grid and the
player dialog keep the behaviour they describe.
"""
import os
import unittest
from playwright.sync_api import sync_playwright

BASE = os.environ.get('STUDIO_BASE_URL', 'http://127.0.0.1:3000').rstrip('/')


class StageVisuals(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(channel='chrome', headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def page(self, **options):
        page = self.browser.new_page(viewport={'width': 1440, 'height': 900}, **options)
        self.addCleanup(page.close)
        page.goto(BASE + '/', wait_until='domcontentloaded')
        page.locator('.work-card').first.wait_for()
        return page

    def test_player_focus_survives_fast_reopen(self):
        page = self.page()
        card = page.locator('.work-card').first
        card.click()
        page.wait_for_function("() => document.querySelector('#workPlayer').open")
        self.assertTrue(page.evaluate("document.querySelector('#workPlayer').contains(document.activeElement)"))
        page.keyboard.press('Escape')
        page.wait_for_function("() => !document.querySelector('#workPlayer').open")
        # Focus goes back to the card that opened it, so the grid stays usable.
        self.assertTrue(page.evaluate("document.activeElement === document.querySelector('.work-card')"))
        card.click()
        page.wait_for_function("() => document.querySelector('#workPlayer').open")
        self.assertTrue(page.evaluate("document.querySelector('#workPlayer').contains(document.activeElement)"))
        page.keyboard.press('Escape')
        page.wait_for_function("() => !document.querySelector('#workPlayer').open")

    def test_direct_contact_anchor_lands_without_breaking_the_grid(self):
        page = self.page()
        page.locator('.main-nav a[href="#contact"], nav a[href="#contact"]').first.click()
        page.wait_for_function("document.querySelector('#contact').getBoundingClientRect().top < innerHeight")
        self.assertFalse(page.evaluate('document.documentElement.scrollWidth > innerWidth'))
        self.assertTrue(page.locator('.works-grid').count())


if __name__ == '__main__':
    unittest.main()
