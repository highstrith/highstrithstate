"""Behavior contracts for the experimental gallery upgrade. Run against serve.js."""
import os
import re
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

    def test_floating_header_keeps_centered_navigation_and_compact_menu(self):
        page = self.browser.new_page(viewport={'width': 1440, 'height': 900}, reduced_motion='reduce')
        self.addCleanup(page.close)
        for path in ['/', '/projects.html', '/in-progress.html']:
            page.goto(BASE + path, wait_until='domcontentloaded')
            expect(page.locator('html')).to_have_class(re.compile('shell-ready'))
            for width in [1440, 1024, 820, 390, 320]:
                page.set_viewport_size({'width': width, 'height': 900})
                for language in ['cn', 'en']:
                    if language == 'en': page.locator('#langSwitch').click()
                    header = page.locator('.site-header')
                    metrics = header.evaluate('''e => {
                      const r=e.getBoundingClientRect(), s=getComputedStyle(e);
                      return {x:r.x, right:r.right, radius:parseFloat(s.borderRadius), height:r.height,
                        background:s.backgroundColor, overflow:document.documentElement.scrollWidth>innerWidth};
                    }''')
                    self.assertGreaterEqual(metrics['x'], 10)
                    self.assertLessEqual(metrics['right'], width - 10)
                    self.assertGreaterEqual(metrics['radius'], 12)
                    self.assertLessEqual(metrics['height'], 80)
                    self.assertFalse(metrics['overflow'], (path, width, language))
                    self.assertEqual(metrics['background'], 'rgb(244, 244, 240)')
                    if width > 800:
                        nav = page.locator('.main-nav').bounding_box()
                        self.assertAlmostEqual(nav['x'] + nav['width']/2, width/2, delta=2)
                        brand = page.locator('.brand').bounding_box()
                        actions = page.locator('.header-actions').bounding_box()
                        self.assertLess(brand['x'] + brand['width'], nav['x'])
                        self.assertLess(nav['x'] + nav['width'], actions['x'])
                    else:
                        page.locator('#menuToggle').click()
                        expect(page.locator('.main-nav')).to_be_visible()
                        page.locator('.nav-collection summary').click()
                        expect(page.locator('.nav-submenu')).to_be_visible()
                        self.assertLessEqual(page.locator('.nav-submenu').bounding_box()['width'], width-20)
                        page.keyboard.press('Escape')
                        page.keyboard.press('Escape')
                        expect(page.locator('.main-nav')).not_to_be_visible()
                        expect(page.locator('#menuToggle')).to_be_focused()
                page.locator('#langSwitch').click()
            page.locator('.brand').evaluate('e=>window.scrollTo(0,500)')
            self.assertGreaterEqual(page.locator('.site-header').bounding_box()['y'], 10)

    def test_theme_switch_persists_across_pages_and_keeps_media_original(self):
        page = self.browser.new_page(viewport={'width': 1440, 'height': 900}, reduced_motion='reduce')
        self.addCleanup(page.close)
        page.goto(BASE + '/', wait_until='domcontentloaded')
        expect(page.locator('#themeToggle')).to_be_visible()
        expect(page.locator('html')).to_have_attribute('data-theme', 'light')
        poster = page.locator('#heroPoster').get_attribute('src')
        page.locator('#themeToggle').click()
        expect(page.locator('html')).to_have_attribute('data-theme', 'dark')
        expect(page.locator('#themeToggle')).to_have_attribute('aria-pressed', 'true')
        expect(page.locator('#themeToggle')).to_have_attribute('aria-label', '切换到浅色模式')
        for selector in ['html', '.site-header']:
            self.assertEqual(page.locator(selector).evaluate('e=>getComputedStyle(e).backgroundColor'), 'rgb(17, 18, 20)')
        self.assertEqual(page.locator('#heroPoster').get_attribute('src'), poster)
        self.assertEqual(page.locator('#heroPoster').evaluate('e=>getComputedStyle(e).filter'), 'none')
        page.locator('#langSwitch').click()
        expect(page.locator('#themeToggle')).to_have_attribute('aria-label', 'Switch to light mode')
        page.reload(wait_until='domcontentloaded')
        expect(page.locator('html')).to_have_attribute('data-theme', 'dark')
        for path in ['/projects.html?lang=en', '/in-progress.html?lang=en']:
            page.goto(BASE + path, wait_until='domcontentloaded')
            expect(page.locator('html')).to_have_attribute('data-theme', 'dark')
            expect(page.locator('#themeToggle')).to_have_attribute('aria-label', 'Switch to light mode')
        page.locator('#themeToggle').focus()
        page.keyboard.press('Space')
        expect(page.locator('html')).to_have_attribute('data-theme', 'light')
        page.goto(BASE + '/', wait_until='domcontentloaded')
        expect(page.locator('html')).to_have_attribute('data-theme', 'light')

    def test_theme_storage_failure_does_not_break_switching(self):
        page = self.browser.new_page(viewport={'width': 390, 'height': 844})
        self.addCleanup(page.close)
        page.add_init_script("Object.defineProperty(window,'localStorage',{get(){throw new Error('unavailable')}})")
        page.goto(BASE + '/', wait_until='domcontentloaded')
        page.locator('#themeToggle').click()
        expect(page.locator('html')).to_have_attribute('data-theme', 'dark')
        page.locator('#themeToggle').click()
        expect(page.locator('html')).to_have_attribute('data-theme', 'light')

    def test_header_internal_navigation_uses_current_tab(self):
        page = self.browser.new_page(viewport={'width': 1440, 'height': 900}, reduced_motion='reduce')
        self.addCleanup(page.close)
        for path in ['/', '/projects.html', '/in-progress.html']:
            page.goto(BASE + path, wait_until='domcontentloaded')
            for link in page.locator('.site-header a').all():
                expect(link).to_have_attribute('target', '_self')
            page.locator('.main-nav > a[href^="projects.html"]').click()
            expect(page).to_have_url(re.compile('/projects.html'))
            self.assertEqual(len(page.context.pages), 1)
            page.locator('.main-nav a[href*="#about"]').click()
            expect(page).to_have_url(re.compile('index.html.*#about'))
            self.assertEqual(len(page.context.pages), 1)

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

    def test_gallery_has_landscape_aligned_rows_and_filtered_reflow(self):
        page = self.page(viewport={'width': 1440, 'height': 900}, reduced_motion='reduce')
        boxes = page.locator('#worksGrid .work-media').evaluate_all('els => els.slice(0,3).map(e=>{const r=e.getBoundingClientRect();return {top:r.y,height:r.height};})')
        self.assertTrue(all(abs(box['top'] - boxes[0]['top']) < 1 for box in boxes))
        self.assertTrue(all(abs(box['height'] - boxes[0]['height']) < 1 for box in boxes))
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
        expect(page.locator('.nav-collection summary')).to_be_focused()
        page.keyboard.press('Enter')
        page.keyboard.press('Tab')
        expect(page.locator('.main-nav [data-progress-section]')).to_be_focused()
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
            if section == 'stills':
                page.locator('.nav-collection summary').click()
            page.locator('.main-nav a[href="#%s"]' % section).click()
            expect(page.locator('.main-nav a[aria-current="true"]')).to_have_attribute('href', '#' + section)
        page.locator('.brand').click()
        expect(page.locator('.main-nav a[aria-current="true"]')).to_have_count(0)


if __name__ == '__main__':
    unittest.main()
