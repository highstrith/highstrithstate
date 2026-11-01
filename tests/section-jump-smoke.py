"""The floating chapter navigator reaches real sections and both page boundaries."""
import os
import unittest
from playwright.sync_api import sync_playwright, expect

BASE = os.environ.get('STUDIO_BASE_URL', 'http://127.0.0.1:3000').rstrip('/')
SECTIONS = ['flyWorks', 'works', 'in-progress', 'stills', 'projects', 'filmRecommendations', 'about', 'contact']


class SectionJump(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime = sync_playwright().start()
        cls.browser = cls.runtime.chromium.launch(channel='chrome', headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.runtime.stop()

    def page(self, width=1440, height=900, motion='reduce', javascript=True):
        page = self.browser.new_page(viewport={'width': width, 'height': height},
                                     reduced_motion=motion, java_script_enabled=javascript)
        self.addCleanup(page.context.close)
        page.goto(BASE, wait_until='load')
        if javascript:
            page.wait_for_selector('.work-card')
        return page

    def open(self, page):
        page.locator('#sectionJump > summary').click()
        expect(page.locator('#sectionJump')).to_have_attribute('open', '')

    def test_each_chapter_link_lands_at_its_section_and_closes_the_panel(self):
        page = self.page()
        expect(page.locator('#sectionJump')).to_have_count(1)
        for section in SECTIONS:
            self.open(page)
            page.locator(f'#sectionJump a[href="#{section}"]').click()
            expect(page.locator('#sectionJump')).not_to_have_attribute('open', '')
            expect(page).to_have_url(BASE + '/#' + section)
            expect(page.locator('#' + section)).to_be_focused()
            # The immersive screening keeps the existing header inset; the
            # other chapters already include their own header clearance.
            expected_top = 110 if section == 'flyWorks' else 0
            self.assertAlmostEqual(page.locator('#' + section).bounding_box()['y'], expected_top, delta=2)
        self.open(page)
        expect(page.locator('#sectionJump a[href="#contact"]')).to_have_attribute('aria-current', 'location')

    def test_top_bottom_use_quick_existing_scroll_and_respect_reduced_motion(self):
        for motion in ['reduce', 'no-preference']:
            page = self.page(motion=motion)
            self.open(page)
            page.locator('#sectionJump a[href="#pageBottom"]').click()
            page.wait_for_function('Math.abs(scrollY + innerHeight - document.documentElement.scrollHeight)<3')
            self.open(page)
            page.locator('#sectionJump a[href="#home"]').click()
            page.wait_for_function('scrollY<2')
            expect(page.locator('#home')).to_be_focused()
            page.close()

    def test_keyboard_escape_outside_click_and_language_theme(self):
        page = self.page()
        toggle = page.locator('#sectionJump > summary')
        toggle.focus()
        page.keyboard.press('Enter')
        page.keyboard.press('Tab')
        expect(page.locator('#sectionJump a[href="#home"]')).to_be_focused()
        page.keyboard.press('Escape')
        expect(toggle).to_be_focused()
        expect(page.locator('#sectionJump')).not_to_have_attribute('open', '')
        self.open(page)
        page.locator('#heroTitle').click()
        expect(page.locator('#sectionJump')).not_to_have_attribute('open', '')
        page.locator('#langSwitch').click()
        self.open(page)
        expect(page.locator('#sectionJump a[href="#pageBottom"]')).to_have_text('Bottom')
        expect(page.locator('#sectionJump a[href="#projects"]')).to_contain_text('Director Workbench')
        light = toggle.evaluate('e=>getComputedStyle(e).backgroundColor')
        page.locator('#themeToggle').click()
        self.assertNotEqual(light, toggle.evaluate('e=>getComputedStyle(e).backgroundColor'))

    def test_small_screens_and_no_script_keep_a_usable_menu(self):
        for width, height in [(320, 568), (390, 844), (844, 390)]:
            page = self.page(width, height)
            self.open(page)
            for selector in ['#sectionJump > summary', '#sectionJump nav']:
                box = page.locator(selector).bounding_box()
                self.assertGreaterEqual(box['x'], 8)
                self.assertGreaterEqual(box['y'], 8)
                self.assertLessEqual(box['x'] + box['width'], width - 8)
                self.assertLessEqual(box['y'] + box['height'], height - 8)
            self.assertGreaterEqual(page.locator('#sectionJump > summary').bounding_box()['height'], 44)
            self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'), width)
            page.close()
        page = self.page(390, 844, javascript=False)
        self.open(page)
        expect(page.locator('#sectionJump a[data-jump-section]')).to_have_count(8)
        page.locator('#sectionJump a[href="#projects"]').click()
        expect(page.locator('#projects')).to_be_in_viewport()


if __name__ == '__main__':
    unittest.main()
