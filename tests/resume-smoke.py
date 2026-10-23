"""Tests for the interactive dual-mode resume page."""
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
        self.assertEqual(self.errors, [])

    def test_switch_to_cinema_and_back(self):
        self.page.goto(BASE + '/resume.html')
        # Switch to cinema via segmented tab
        self.page.locator('#tabCinema').click()
        expect(self.page.locator('#view-cinema')).to_be_visible()
        expect(self.page.locator('#view-resume')).to_have_attribute('hidden', '')
        expect(self.page.locator('.cinema-work-card').first).to_be_visible()
        
        # Switch back to resume via top back button in cinema
        self.page.locator('.cinema-back-btn').click()
        expect(self.page.locator('#view-resume')).to_be_visible()
        expect(self.page.locator('#view-cinema')).to_have_attribute('hidden', '')
        self.assertEqual(self.errors, [])

    def test_cinema_play_and_close(self):
        self.page.goto(BASE + '/resume.html#cinema')
        expect(self.page.locator('#view-cinema')).to_be_visible()
        # Click first work play button
        self.page.locator('.cinema-work-card button[data-play]').first.click()
        expect(self.page.locator('#resumePlayer')).to_have_attribute('open', '')
        
        # Close player
        self.page.locator('#resumePlayerClose').click()
        expect(self.page.locator('#resumePlayer')).not_to_have_attribute('open', '')
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
