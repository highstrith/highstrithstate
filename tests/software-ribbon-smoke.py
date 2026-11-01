"""The footer tools become a quiet logo ribbon, with eight accessible originals."""
import os
import unittest
from playwright.sync_api import sync_playwright, expect

BASE = os.environ.get('STUDIO_BASE_URL', 'http://127.0.0.1:3000').rstrip('/')
TOOLS = {'davinci-resolve', 'blender', 'unreal-engine', 'photoshop', 'premiere-pro', 'after-effects', 'jianying', 'chatgpt'}


class SoftwareRibbon(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime = sync_playwright().start()
        cls.browser = cls.runtime.chromium.launch(channel='chrome', headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.runtime.stop()

    def page(self, width=1440, motion='no-preference', javascript=True):
        page = self.browser.new_page(viewport={'width': width, 'height': 900},
                                     reduced_motion=motion, java_script_enabled=javascript)
        self.addCleanup(page.context.close)
        page.goto(BASE, wait_until='load')
        page.locator('.footer-software').scroll_into_view_if_needed()
        return page

    def test_all_eight_tools_have_quiet_vector_logos_and_accessible_names(self):
        page = self.page()
        tools = page.locator('#softwareLogoSet [data-software]')
        expect(tools).to_have_count(8)
        self.assertEqual(set(tools.evaluate_all('es=>es.map(e=>e.dataset.software)')), TOOLS)
        for tool in tools.all():
            expect(tool).to_have_attribute('role', 'img')
            self.assertTrue(tool.get_attribute('aria-label'))
            expect(tool.locator('svg path')).not_to_have_count(0)
            self.assertLessEqual(tool.locator('svg').bounding_box()['width'], 36)
            self.assertLess(float(tool.locator('svg').evaluate('e=>getComputedStyle(e).opacity')), .8)
        expect(page.locator('.footer-software .software-tag')).to_have_count(0)
        expect(page.locator('#softwareLogoSet [data-software="unreal-engine"]')).to_contain_text('UE5')

    def test_slow_loop_pauses_and_survives_language_switch_without_losing_logos(self):
        page = self.page()
        track = page.locator('#softwareLogoTrack')
        page.mouse.move(5, 5)
        before = track.evaluate('e=>getComputedStyle(e).transform')
        page.wait_for_timeout(300)
        self.assertNotEqual(before, track.evaluate('e=>getComputedStyle(e).transform'))
        page.locator('#softwareLogoWindow').hover()
        held = track.evaluate('e=>getComputedStyle(e).transform')
        page.wait_for_timeout(200)
        self.assertEqual(held, track.evaluate('e=>getComputedStyle(e).transform'))
        page.locator('#softwareRibbonToggle').click()
        expect(page.locator('#softwareRibbonToggle')).to_have_attribute('aria-pressed', 'true')
        page.locator('#langSwitch').click()
        expect(page.locator('#softwareLogoSet svg')).to_have_count(8)
        expect(page.locator('#softwareLogoSet [data-software="jianying"]')).to_have_attribute('aria-label', 'Jianying')
        expect(page.locator('#softwareRibbonToggle')).to_have_accessible_name('Resume software logo scrolling')
        expect(page.locator('[data-software-copy]')).to_have_attribute('aria-hidden', 'true')
        expect(page.locator('[data-software-copy] svg')).to_have_count(8)

    def test_mobile_and_themes_keep_the_ribbon_inside_the_page(self):
        for width in [320, 390, 820, 1440]:
            page = self.page(width)
            for theme in ['light', 'dark']:
                if theme == 'dark': page.locator('#themeToggle').click()
                self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'), width)
            page.close()

    def test_reduced_motion_and_no_script_keep_all_logos_manually_browsable(self):
        for javascript in [True, False]:
            page = self.page(390, motion='reduce', javascript=javascript)
            expect(page.locator('#softwareLogoSet svg')).to_have_count(8)
            expect(page.locator('[data-software-copy]')).to_have_count(0)
            expect(page.locator('#softwareRibbonToggle')).not_to_be_visible()
            viewport = page.locator('#softwareLogoWindow')
            self.assertEqual(viewport.evaluate('e=>getComputedStyle(e).overflowX'), 'auto')
            viewport.evaluate('e=>e.scrollLeft=e.scrollWidth')
            self.assertGreater(viewport.evaluate('e=>e.scrollLeft'), 0)


if __name__ == '__main__':
    unittest.main()
