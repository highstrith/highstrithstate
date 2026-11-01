"""Real requests and native playback: only visible media may auto-preview."""
import os
import unittest
from playwright.sync_api import expect, sync_playwright

BASE = os.environ.get('STUDIO_BASE_URL', 'http://127.0.0.1:3000').rstrip('/')


class ViewportMedia(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime = sync_playwright().start()
        cls.browser = cls.runtime.chromium.launch(channel='chrome', headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.runtime.stop()

    def page(self, width=1440, **options):
        page = self.browser.new_page(viewport={'width': width, 'height': 1000},
                                     is_mobile=width < 700, has_touch=width < 700, **options)
        self.addCleanup(page.close)
        page.set_default_timeout(10000)
        requests = []
        page.on('request', lambda r: requests.append(r.url) if r.resource_type == 'media' else None)
        page.goto(BASE + '/', wait_until='networkidle')
        expect(page.locator('#worksGrid .work-card')).to_have_count(20)
        return page, requests

    def test_initial_hero_only_then_visible_card_then_offscreen_release(self):
        for width in [1440, 390]:
            with self.subTest(width=width):
                page, requests = self.page(width)
                page.wait_for_function('document.querySelector("#heroPreview").currentTime > 0')
                self.assertEqual(page.locator('#worksGrid video[src]').count(), 0)
                self.assertTrue(requests)
                self.assertTrue(all('-preview.mp4' in url for url in requests))
                page.locator('#worksGrid .work-card:visible').first.scroll_into_view_if_needed()
                page.wait_for_function('document.querySelector("#worksGrid video[src]")?.currentTime > 0')
                self.assertIsNone(page.locator('#heroPreview').get_attribute('src'))
                self.assertEqual(page.locator('#worksGrid video[src]').count(), 1)
                self.assertTrue(page.locator('#worksGrid video[src]').evaluate('''video => {
                  const r = video.getBoundingClientRect();
                  return r.top < innerHeight && r.bottom > 0;
                }'''))
                page.locator('#contact').scroll_into_view_if_needed()
                page.wait_for_function('!document.querySelector("video[src]")')

    def test_pause_stays_paused_across_scroll_selection_and_language(self):
        page, requests = self.page()
        page.locator('#featurePreviewToggle').click()
        expect(page.locator('#featurePreviewToggle')).to_have_attribute('aria-pressed', 'true')
        page.locator('.hero-pick').nth(1).click()
        page.locator('#langSwitch').click()
        page.locator('#worksGrid .work-card:visible').first.scroll_into_view_if_needed()
        page.wait_for_timeout(200)
        before = len(requests)
        page.locator('#worksGrid .work-card:visible').first.hover()
        page.wait_for_timeout(300)
        self.assertEqual(page.locator('video[src]').count(), 0)
        self.assertEqual(len(requests), before)
        page.locator('#worksGrid .work-card:visible').first.click()
        page.wait_for_function('document.querySelector("#workPlayerVideo").currentTime > 0')
        self.assertEqual(page.locator('#worksGrid video[src]').count(), 0)
        page.locator('#workPlayerClose').click()
        page.wait_for_function('!document.querySelector("video[src]")')

    def test_resize_releases_a_preview_that_leaves_the_viewport(self):
        page, _ = self.page()
        page.locator('#worksGrid .work-card:visible').first.evaluate('''card => {
          window.scrollTo({top: card.getBoundingClientRect().top + scrollY - 600, behavior:'instant'});
        }''')
        page.wait_for_function('document.querySelector("#worksGrid video[src]")?.currentTime > 0')
        page.set_viewport_size({'width': 1440, 'height': 240})
        page.wait_for_function('!document.querySelector("video[src]")', timeout=2000)

    def test_reduced_motion_and_save_data_allow_manual_full_playback(self):
        for data_saver in [False, True]:
            with self.subTest(saveData=data_saver):
                page = self.browser.new_page(viewport={'width': 390, 'height': 1000},
                    is_mobile=True, has_touch=True, reduced_motion='no-preference' if data_saver else 'reduce')
                self.addCleanup(page.close)
                if data_saver:
                    page.add_init_script('Object.defineProperty(navigator, "connection", {value:{saveData:true}})')
                media = []
                page.on('request', lambda r: media.append(r.url) if r.resource_type == 'media' else None)
                page.goto(BASE + '/', wait_until='networkidle')
                page.locator('#worksGrid .work-card:visible').first.scroll_into_view_if_needed()
                page.wait_for_timeout(300)
                self.assertEqual(media, [])
                page.locator('#worksGrid .work-card:visible').first.click()
                page.wait_for_function('document.querySelector("#workPlayerVideo").currentTime > 0')
                self.assertTrue(page.locator('#workPlayerVideo').get_attribute('src').endswith('-mobile.mp4'))

    def test_preview_control_uses_theme_text(self):
        page, _ = self.page()
        for _ in range(2):
            colors = page.locator('#featurePreviewToggle').evaluate('''button => {
              const sample = document.createElement('span'); sample.style.color = 'var(--ink)';
              button.parentElement.append(sample);
              const colors = [getComputedStyle(button).color, getComputedStyle(sample).color];
              sample.remove(); return colors;
            }''')
            self.assertEqual(*colors)
            page.locator('#themeToggle').click()


if __name__ == '__main__':
    unittest.main()
