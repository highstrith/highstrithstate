"""Tests for the creator resume page."""
import os
import unittest
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

BASE = os.environ.get('STUDIO_BASE_URL', 'http://127.0.0.1:3000')
ROOT = Path(__file__).resolve().parents[1]


class ResumePageSmoke(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime = sync_playwright().start()
        cls.browser = cls.runtime.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.runtime.stop()

    def setUp(self):
        self.context = self.browser.new_context(reduced_motion='reduce')
        self.page = self.context.new_page()
        self.errors = []
        self.page.on('pageerror', lambda error: self.errors.append(str(error)))

    def tearDown(self):
        self.context.close()

    def test_resume_default_view_loads(self):
        self.page.goto(BASE + '/resume.html')
        expect(self.page).to_have_title('林俊杰 · 个人简历与作品展厅 — Highstrith')
        expect(self.page.locator('#view-resume')).to_be_visible()
        expect(self.page.locator('.profile-name')).to_contain_text('林俊杰')
        expect(self.page.locator('.profile-tag-row .badge-dual-engine')).to_be_visible()
        # Verify large website showcase is present
        expect(self.page.locator('.browser-mockup-frame')).to_be_visible()
        expect(self.page.locator('.browser-address-bar')).to_contain_text('highstrith.github.io/highstrithstate')
        # Verify top nav links are removed
        expect(self.page.locator('.dual-nav-links')).not_to_be_attached()
        self.assertEqual(self.errors, [])

    def test_actions_and_links(self):
        self.page.goto(BASE + '/resume.html')
        # Check brand link to index.html
        brand_link = self.page.locator('.dual-brand')
        expect(brand_link).to_have_attribute('href', 'index.html')
        
        # Check direct link to main site in header actions
        main_site_btn = self.page.locator('.nav-actions a[href="index.html"]')
        expect(main_site_btn).to_be_visible()
        expect(main_site_btn).to_contain_text('进入主站')

        # Check hero button points directly to index.html#works
        hero_cinema_btn = self.page.locator('.hero-contacts-bar a[href="index.html#works"]')
        expect(hero_cinema_btn).to_be_visible()
        expect(hero_cinema_btn).to_contain_text('前往放映厅看片')
        self.assertEqual(self.errors, [])

    def test_language_toggle_and_copy(self):
        self.page.goto(BASE + '/resume.html')
        # Toggle language to EN
        self.page.locator('#langSwitch').click()
        expect(self.page.locator('#langSwitch')).to_have_text('中文')
        expect(self.page).to_have_title('Junjie Lin (Highstrith) · Interactive Resume & Works')
        
        # Toggle back to CN
        self.page.locator('#langSwitch').click()
        expect(self.page.locator('#langSwitch')).to_have_text('EN')
        self.assertEqual(self.errors, [])


if __name__ == '__main__':
    unittest.main()
