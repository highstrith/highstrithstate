"""Behavior contracts for the experimental gallery upgrade. Run against serve.js."""
import os
import unittest
from playwright.sync_api import expect, sync_playwright

BASE = os.environ.get('STUDIO_BASE_URL', 'http://127.0.0.1:3000').rstrip('/')


class ExhibitionUpgrade(unittest.TestCase):
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
        page.set_default_timeout(6000)
        self.addCleanup(page.close)
        page.goto(BASE + '/', wait_until='domcontentloaded')
        expect(page.locator('#worksGrid .work-card')).to_have_count(20)
        return page

    def test_directory_view_preserves_search_filter_and_language(self):
        page = self.page(viewport={'width': 1440, 'height': 900})
        expect(page.locator('[data-view="list"]')).to_have_count(1, timeout=1500)
        page.locator('#workSearch').fill('Prove')
        page.locator('[data-view="list"]').click()
        expect(page.locator('[data-view="list"]')).to_have_attribute('aria-pressed', 'true')
        expect(page.locator('#worksGrid .work-card:visible')).to_have_count(1)
        page.locator('#langSwitch').click()
        expect(page.locator('#workSearch')).to_have_value('Prove')
        expect(page.locator('[data-view="list"]')).to_have_attribute('aria-label', 'Directory view')
        expect(page.locator('#worksGrid .work-card:visible')).to_have_count(1)
        page.locator('#workSearch').fill('')
        page.locator('[data-filter="motion"]').click()
        count = page.locator('#worksGrid .work-card:visible').count()
        self.assertGreater(count, 0)
        page.locator('[data-view="gallery"]').click()
        self.assertEqual(page.locator('#worksGrid .work-card:visible').count(), count)

    def test_gallery_has_asymmetric_composition_and_filtered_reflow(self):
        page = self.page(viewport={'width': 1440, 'height': 900}, reduced_motion='reduce')
        widths = page.locator('#worksGrid .work-item').evaluate_all('els => els.slice(0,2).map(e=>e.getBoundingClientRect().width)')
        self.assertGreater(abs(widths[0] - widths[1]), 100)
        page.locator('[data-filter="motion"]').click()
        boxes = page.locator('#worksGrid .work-item:visible').evaluate_all('els => els.map(e=>({top:e.offsetTop,left:e.offsetLeft}))')
        self.assertEqual(boxes[0]['top'], boxes[1]['top'])
        self.assertLess(boxes[0]['left'], boxes[1]['left'])

    def test_still_viewer_navigates_zooms_and_returns_focus(self):
        page = self.page(viewport={'width': 1440, 'height': 900}, reduced_motion='reduce')
        expect(page.locator('[data-still="0"]')).to_have_count(1, timeout=1500)
        first = page.locator('[data-still="0"]')
        first.click()
        expect(page.locator('#stillViewer')).to_be_visible()
        expect(page.locator('#stillViewerTitle')).to_have_text('月下少年')
        page.wait_for_function('document.querySelector("#stillViewerImage").naturalWidth > 0')
        page.locator('#stillZoom').click()
        expect(page.locator('#stillZoom')).to_have_attribute('aria-pressed', 'true')
        page.keyboard.press('ArrowRight')
        expect(page.locator('#stillViewerTitle')).to_have_text('翡翠之刃')
        expect(page.locator('#stillZoom')).to_have_attribute('aria-pressed', 'false')
        page.keyboard.press('ArrowLeft')
        expect(page.locator('#stillViewerTitle')).to_have_text('月下少年')
        page.keyboard.press('Escape')
        expect(page.locator('#stillViewer')).not_to_be_visible()
        expect(first).to_be_focused()
        self.assertFalse(page.locator('body').evaluate('e=>e.classList.contains("modal-open")'))

    def test_preview_pause_survives_feature_selection(self):
        page = self.page(viewport={'width': 1440, 'height': 1000})
        expect(page.locator('#featurePreviewToggle')).to_have_count(1, timeout=1500)
        page.locator('#featurePreviewToggle').click()
        expect(page.locator('#featurePreviewToggle')).to_have_attribute('aria-pressed', 'true')
        page.locator('[data-feature="featured-prove-it"]').click()
        expect(page.locator('#featureTitle')).to_have_text('Prove It')
        self.assertIsNone(page.locator('#heroPreview').get_attribute('src'))
        page.locator('#featurePreviewToggle').click()
        page.wait_for_function('document.querySelector("#heroPreview").currentTime > 0')
        expect(page.locator('#featurePreviewToggle')).to_have_attribute('aria-pressed', 'false')
        progress = page.locator('.hero-pick[aria-pressed="true"]').evaluate('e=>Number(e.style.getPropertyValue("--preview-progress"))')
        self.assertGreaterEqual(progress, 0)
        self.assertLessEqual(progress, 1)

    def test_mobile_menu_closes_on_navigation_and_escape(self):
        page = self.page(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True, reduced_motion='reduce')
        expect(page.locator('#menuToggle')).to_have_count(1, timeout=1500)
        expect(page.locator('.main-nav')).not_to_be_visible()
        page.locator('#menuToggle').click()
        expect(page.locator('#menuToggle')).to_have_attribute('aria-expanded', 'true')
        expect(page.locator('.main-nav a').first).to_be_focused()
        page.keyboard.press('Tab')
        expect(page.locator('.main-nav a[href="#stills"]')).to_be_focused()
        expect(page.locator('.main-nav')).to_be_visible()
        page.locator('.main-nav a[href="#stills"]').click()
        expect(page.locator('#menuToggle')).to_have_attribute('aria-expanded', 'false')
        expect(page).to_have_url(BASE + '/#stills')
        page.locator('#menuToggle').click()
        page.keyboard.press('Escape')
        expect(page.locator('.main-nav')).not_to_be_visible()
        expect(page.locator('#menuToggle')).to_be_focused()

    def test_email_copy_has_truthful_confirmation(self):
        page = self.page(viewport={'width': 1440, 'height': 900}, reduced_motion='reduce')
        expect(page.locator('#copyEmail')).to_have_count(1, timeout=1500)
        page.context.grant_permissions(['clipboard-read', 'clipboard-write'])
        page.locator('#copyEmail').click()
        expect(page.locator('#siteNotice')).to_have_text('邮箱已复制')
        self.assertEqual(page.evaluate('navigator.clipboard.readText()'), 'highstrith@gmail.com')
        page.evaluate('() => { navigator.clipboard.writeText = () => Promise.reject(new Error("denied")); }')
        page.locator('#copyEmail').click()
        expect(page.locator('#siteNotice')).to_contain_text('highstrith@gmail.com')

    def test_responsive_views_and_english_still_viewer(self):
        page = self.page(viewport={'width': 390, 'height': 844}, reduced_motion='reduce')
        expect(page.locator('[data-view="list"]')).to_have_count(1, timeout=1500)
        for width in [320, 390, 820, 1440, 1920]:
            page.set_viewport_size({'width': width, 'height': 900})
            for view in ['list', 'gallery']:
                page.locator('[data-view="%s"]' % view).click()
                self.assertTrue(page.evaluate('document.documentElement.scrollWidth <= innerWidth'), (width, view))
        page.locator('#langSwitch').click()
        page.locator('[data-still="0"]').click()
        expect(page.locator('#stillViewerTitle')).to_have_text('Boy Under the Moon')
        expect(page.locator('#stillViewerClose')).to_have_attribute('aria-label', 'Close image viewer')
        for width in [320, 820, 1920]:
            page.set_viewport_size({'width': width, 'height': 900})
            rect = page.locator('#stillViewer').bounding_box()
            self.assertLessEqual(rect['width'], width)
        page.keyboard.press('Escape')
        self.assertEqual(page.locator('#worksGrid .work-card').count(), 20)

    def test_still_viewer_defers_original_and_pauses_requested_music(self):
        page = self.page(viewport={'width': 1440, 'height': 900}, reduced_motion='reduce')
        requests = page.evaluate('performance.getEntriesByType("resource").map(entry=>entry.name)')
        self.assertFalse(any(url.endswith('/assets/stills/nezha-boy.jpg') for url in requests))
        page.locator('#musicToggle').click()
        page.wait_for_function('!document.querySelector("#bgMusic").paused')
        page.locator('[data-still="0"]').click()
        self.assertTrue(page.locator('#bgMusic').evaluate('music=>music.paused'))
        expect(page.locator('#musicToggle')).to_have_attribute('aria-pressed', 'true')
        page.wait_for_function('document.querySelector("#stillViewerImage").naturalWidth === 1080')
        page.keyboard.press('Escape')
        page.wait_for_function('!document.querySelector("#bgMusic").paused')

    def test_touch_swipe_changes_still_without_accidental_zoom(self):
        page = self.page(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True, reduced_motion='reduce')
        page.locator('[data-still="0"]').tap()
        page.wait_for_function('document.querySelector("#stillViewerImage").naturalWidth > 0')
        bounds = page.locator('#stillViewerStage').bounding_box()
        touch = page.context.new_cdp_session(page)
        y = bounds['y'] + bounds['height'] / 2
        touch.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [{'x': 300, 'y': y}]})
        touch.send('Input.dispatchTouchEvent', {'type': 'touchMove', 'touchPoints': [{'x': 200, 'y': y}]})
        touch.send('Input.dispatchTouchEvent', {'type': 'touchMove', 'touchPoints': [{'x': 90, 'y': y}]})
        touch.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []})
        expect(page.locator('#stillViewerTitle')).to_have_text('翡翠之刃')
        expect(page.locator('#stillZoom')).to_have_attribute('aria-pressed', 'false')
        page.locator('#stillViewerClose').tap()
        expect(page.locator('#stillViewer')).not_to_be_visible()

    def test_navigation_tracks_long_sections_and_resets_at_home(self):
        page = self.page(viewport={'width': 1440, 'height': 900}, reduced_motion='reduce')
        for section in ['works', 'stills', 'about', 'contact']:
            page.locator('.main-nav a[href="#%s"]' % section).click()
            expect(page.locator('.main-nav a[aria-current="true"]')).to_have_attribute('href', '#' + section)
        page.locator('.brand').click()
        expect(page.locator('.main-nav a[aria-current="true"]')).to_have_count(0)


if __name__ == '__main__':
    unittest.main()
