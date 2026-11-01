"""Real network and playback checks for the job-application portfolio.

Run against serve.js; STUDIO_BASE_URL can select an isolated server.
"""
import os
import unittest
from playwright.sync_api import expect, sync_playwright

BASE = os.environ.get('STUDIO_BASE_URL', 'http://127.0.0.1:3000').rstrip('/')


class ClickToLoad(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime = sync_playwright().start()
        cls.browser = cls.runtime.chromium.launch(channel='chrome', headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.runtime.stop()

    def page(self, **options):
        page = self.browser.new_page(**options)
        self.addCleanup(page.close)
        page.set_default_timeout(8000)
        requests = []
        page.on('request', lambda request: requests.append(request.url)
                if request.resource_type == 'media' else None)
        page.goto(BASE + '/', wait_until='networkidle')
        expect(page.locator('#worksGrid .work-card')).to_have_count(20)
        return page, requests

    def test_browsing_does_not_request_video_on_desktop_or_mobile(self):
        for width, mobile in [(1440, False), (390, True)]:
            with self.subTest(width=width):
                page, requests = self.page(viewport={'width': width, 'height': 1000},
                                           is_mobile=mobile, has_touch=mobile)
                self.assertEqual(requests, [], 'initial page must only fetch images and documents')
                expect(page.locator('#featurePreviewToggle')).to_have_accessible_name('播放预览')
                expect(page.locator('#heroPoster')).to_be_visible()
                page.locator('.hero-pick').nth(1).click()
                page.locator('#langSwitch').click()
                expect(page.locator('#featurePreviewToggle')).to_have_accessible_name('Play preview')
                card = page.locator('#worksGrid .work-card:visible').first
                card.hover()
                card.focus()
                page.wait_for_timeout(500)
                self.assertEqual(requests, [], 'selection, language, hover and focus must not fetch video')
                self.assertEqual(page.locator('video[src]').count(), 0)

    def test_preview_requires_click_and_pause_survives_selection(self):
        page, requests = self.page(viewport={'width': 1440, 'height': 1000})
        self.assertEqual(requests, [])
        toggle = page.locator('#featurePreviewToggle')
        toggle.click()
        page.wait_for_function('document.querySelector("#heroPreview").currentTime > 0')
        self.assertTrue(requests)
        expect(toggle).to_have_accessible_name('暂停预览')
        toggle.click()
        expect(toggle).to_have_accessible_name('播放预览')
        page.locator('.hero-pick').nth(1).click()
        page.locator('#langSwitch').click()
        page.wait_for_timeout(150)
        before = len(requests)
        card = page.locator('#worksGrid .work-card:visible').first
        card.hover()
        card.focus()
        page.wait_for_timeout(500)
        self.assertEqual(len(requests), before)
        self.assertEqual(page.locator('video[src]').count(), 0)

    def test_preview_control_uses_readable_theme_text_in_both_themes(self):
        page, _ = self.page(viewport={'width': 1440, 'height': 1000})
        for _ in range(2):
            colors = page.locator('#featurePreviewToggle').evaluate('''button => {
              const sample = document.createElement('span');
              sample.style.color = 'var(--ink)';
              button.parentElement.append(sample);
              const colors = [getComputedStyle(button).color, getComputedStyle(sample).color];
              sample.remove();
              return colors;
            }''')
            self.assertEqual(colors[0], colors[1], 'preview action must use the readable text color')
            page.locator('#themeToggle').click()

    def test_click_opens_real_full_video_and_close_does_not_start_preview(self):
        for width, mobile in [(1440, False), (390, True)]:
            with self.subTest(width=width):
                page, requests = self.page(viewport={'width': width, 'height': 1000},
                                           is_mobile=mobile, has_touch=mobile)
                self.assertEqual(requests, [])
                page.locator('#worksGrid .work-card:visible').first.click()
                expect(page.locator('#workPlayer')).to_be_visible()
                page.wait_for_function('document.querySelector("#workPlayerVideo").currentTime > 0')
                source = page.locator('#workPlayerVideo').get_attribute('src')
                self.assertTrue(source.endswith('-mobile.mp4' if mobile else '-web.mp4'), source)
                self.assertTrue(requests)
                page.locator('#workPlayerClose').click()
                expect(page.locator('#workPlayer')).not_to_be_visible()
                page.wait_for_timeout(300)
                self.assertEqual(page.locator('video[src]').count(), 0)


if __name__ == '__main__':
    unittest.main()
