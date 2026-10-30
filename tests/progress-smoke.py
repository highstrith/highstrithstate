"""In-progress page: authentic new imagery, bilingual links and image viewing."""
import json
import os
import re
import unittest
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BASE = os.environ.get('STUDIO_BASE_URL', 'http://127.0.0.1:3000').rstrip('/')


class ProgressPage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime = sync_playwright().start()
        cls.browser = cls.runtime.chromium.launch(channel='chrome', headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.runtime.stop()

    def page(self, **options):
        page = self.browser.new_page(viewport={'width': 1440, 'height': 900}, reduced_motion='reduce', **options)
        page.set_default_timeout(5000)
        self.addCleanup(page.context.close)
        return page

    def ready(self, page):
        page.goto(BASE + '/in-progress.html', wait_until='load')
        expect(page.locator('.progress-gallery a')).to_have_count(15, timeout=1500)

    def test_home_links_to_progress_and_keeps_separate_still_gallery(self):
        page = self.page()
        page.goto(BASE + '/')
        expect(page.locator('.main-nav [data-progress-section]')).to_have_count(1, timeout=1500)
        expect(page.locator('#stillsGrid .still-card')).to_have_count(8)
        self.assertTrue(page.locator('#stillsGrid img').evaluate_all('images => images.every(image => image.src.includes("/assets/stills/"))'))
        page.locator('.nav-collection summary').click()
        page.locator('.main-nav [data-progress-section]').click()
        expect(page).to_have_url(BASE + '/#in-progress')
        expect(page.locator('.home-progress-grid')).to_be_visible()
        page.locator('#in-progress [data-progress-link]').click()
        expect(page).to_have_url(BASE + '/in-progress.html')
        expect(page.locator('h1')).to_have_text('正在制作')
        expect(page.locator('#progressProjectTitle')).to_have_text('《未识之诺》')
        expect(page.locator('.progress-gallery a')).to_have_count(15)
        expect(page.locator('video, audio')).to_have_count(0)
        sources = page.locator('.progress-gallery img').evaluate_all('images => images.map(image => new URL(image.src).pathname)')
        self.assertEqual(len(set(sources)), 15)
        self.assertTrue(all('/assets/progress/weishizhinuo/' in source for source in sources))
        self.assertFalse(any(entry['name'].endswith('.mp4') for entry in page.evaluate('performance.getEntriesByType("resource").map(e=>({name:e.name}))')))

    def test_language_survives_home_project_and_progress_navigation(self):
        page = self.page()
        self.ready(page)
        page.locator('#langSwitch').click()
        expect(page.locator('h1')).to_have_accessible_name('In progress')
        expect(page.locator('[aria-current="page"]')).to_have_attribute('href', 'in-progress.html?lang=en')
        page.locator('.main-nav [data-projects-link]').click()
        expect(page).to_have_url(BASE + '/projects.html?lang=en')
        expect(page.locator('h1')).to_have_text('Projects & apps')
        page.locator('.nav-collection summary').click()
        page.locator('.main-nav a[href*="#in-progress"]').click()
        expect(page.locator('html')).to_have_attribute('lang', 'en')
        page.locator('#in-progress [data-progress-link]').click()
        expect(page).to_have_url(BASE + '/in-progress.html?lang=en')
        expect(page.locator('h1')).to_have_accessible_name('In progress')
        page.locator('.main-nav [data-home-link]').first.click()
        expect(page.locator('html')).to_have_attribute('lang', 'en')
        page.locator('.nav-collection summary').click()
        page.locator('.main-nav [data-progress-section]').click()
        page.locator('#in-progress [data-progress-link]').click()
        expect(page.locator('h1')).to_have_accessible_name('In progress')

    def test_full_images_keyboard_navigation_and_focus_return(self):
        page = self.page()
        self.ready(page)
        first = page.locator('.progress-gallery a').first
        first.click()
        expect(page.locator('#progressViewer')).to_be_visible()
        expect(page.locator('#progressViewerTitle')).to_have_text('森林湖岸都市')
        page.wait_for_function('document.querySelector("#progressViewerImage").naturalWidth > 0')
        page.keyboard.press('ArrowRight')
        expect(page.locator('#progressViewerTitle')).to_have_text('许知微')
        page.keyboard.press('ArrowLeft')
        expect(page.locator('#progressViewerTitle')).to_have_text('森林湖岸都市')
        page.keyboard.press('Escape')
        expect(page.locator('#progressViewer')).not_to_be_visible()
        expect(first).to_be_focused()
        expect(page.locator('body')).not_to_have_class(re.compile(r'\bmodal-open\b'))
        page.locator('#langSwitch').click()
        page.locator('.progress-gallery a').last.click()
        expect(page.locator('#progressViewerTitle')).to_have_text('Shot detailing')
        expect(page.locator('#progressViewerClose')).to_have_attribute('aria-label', 'Close image')
        for width in [320, 390]:
            page.set_viewport_size({'width': width, 'height': 844})
            for selector in ['#progressViewerClose', '#progressOriginal']:
                bounds = page.locator(selector).bounding_box()
                self.assertGreaterEqual(bounds['x'], 0)
                self.assertLessEqual(bounds['x'] + bounds['width'], width)
                self.assertGreaterEqual(bounds['height'], 44)

    def test_all_sizes_images_and_mobile_keyboard_menu(self):
        page = self.page()
        self.ready(page)
        for width in [320, 390, 820, 1440, 1920]:
            page.set_viewport_size({'width': width, 'height': 900})
            for language in ['cn', 'en']:
                if (page.locator('html').get_attribute('lang') == 'en') != (language == 'en'):
                    page.locator('#langSwitch').click()
                self.assertTrue(page.evaluate('document.documentElement.scrollWidth <= innerWidth'), (width, language))
            for image in page.locator('.progress-gallery img').all():
                image.scroll_into_view_if_needed()
                image.evaluate('image=>image.decode()')
        page.set_viewport_size({'width': 390, 'height': 844})
        page.locator('#menuToggle').click()
        expect(page.locator('.main-nav a').first).to_be_focused()
        page.keyboard.press('Tab')
        expect(page.locator('.nav-collection summary')).to_be_focused()
        page.keyboard.press('Enter')
        page.keyboard.press('Tab')
        expect(page.locator('.main-nav [data-progress-link]')).to_be_focused()
        page.keyboard.press('Escape')
        expect(page.locator('.nav-collection summary')).to_be_focused()
        page.keyboard.press('Escape')
        expect(page.locator('#menuToggle')).to_be_focused()

    def test_file_and_no_script_keep_images_and_links_available(self):
        page = self.page(java_script_enabled=False)
        page.goto((ROOT / 'in-progress.html').as_uri(), wait_until='load')
        expect(page.locator('h1')).to_have_text('正在制作')
        links = page.locator('.progress-gallery a')
        expect(links).to_have_count(15, timeout=1500)
        for link in links.all():
            self.assertTrue((ROOT / link.get_attribute('href')).is_file())
        self.assertTrue(page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
        links.first.click()
        self.assertTrue(urlsplit(page.url).path.endswith('forest-city.webp'))

    def test_home_progress_is_visible_and_uses_its_own_image_sequence(self):
        page = self.page()
        page.goto(BASE + '/', wait_until='load')
        expect(page.locator('#in-progress')).to_have_count(1, timeout=1500)
        expect(page.locator('.home-progress-grid .home-progress-card')).to_have_count(15)
        expect(page.locator('.home-progress-grid')).to_be_visible()
        first = page.locator('.home-progress-card').first
        first.click()
        expect(page.locator('#stillViewerTitle')).to_have_text('森林湖岸都市')
        expect(page.locator('#stillViewerPosition')).to_have_text('01 / 15')
        page.keyboard.press('ArrowRight')
        expect(page.locator('#stillViewerTitle')).to_have_text('高空投送')
        page.keyboard.press('Escape')
        expect(first).to_be_focused()
        page.locator('[data-still="0"]').click()
        expect(page.locator('#stillViewerTitle')).to_have_text('月下少年')
        expect(page.locator('#stillViewerPosition')).to_have_text('01 / 08')

    def test_production_contact_sheet_groups_and_full_sequence(self):
        page = self.page()
        self.ready(page)
        for group, count in [('assets', 6), ('storyboards', 5), ('workbench', 4)]:
            expect(page.locator('#production-' + group + ' .progress-gallery a')).to_have_count(count)
            expect(page.locator('#production-' + group + ' .progress-group-count')).to_have_text(str(count))
            page.locator('.progress-index a[href="#production-' + group + '"]').click()
            expect(page).to_have_url(BASE + '/in-progress.html#production-' + group)
        page.locator('.progress-gallery a').first.click()
        expect(page.locator('#progressViewerPosition')).to_have_text('01 / 15')
        page.keyboard.press('ArrowLeft')
        expect(page.locator('#progressViewerPosition')).to_have_text('15 / 15')
        expect(page.locator('#progressViewerTitle')).to_have_text('镜头细化')
        page.keyboard.press('Escape')
        page.locator('#langSwitch').click()
        expect(page.locator('.progress-index')).to_contain_text('Assets')
        expect(page.locator('.progress-group-count')).to_have_text(['6', '5', '4'])
        for link in page.locator('.progress-gallery a').all():
            image = link.locator('img')
            self.assertTrue(image.get_attribute('src').endswith('-thumb.webp'))
            self.assertTrue((ROOT / link.get_attribute('href')).is_file())

    def test_visible_return_links_preserve_home_section_and_language(self):
        page = self.page()
        self.ready(page)
        back = page.locator('.progress-return')
        expect(back).to_be_visible()
        self.assertLess(back.bounding_box()['y'], 250)
        expect(back).to_have_attribute('href', 'index.html#in-progress')
        page.locator('#langSwitch').click()
        expect(back).to_have_attribute('href', 'index.html?lang=en#in-progress')
        back.click()
        expect(page).to_have_url(BASE + '/index.html?lang=en#in-progress')
        expect(page.locator('#in-progress')).to_be_in_viewport()

    def test_browser_back_closes_picture_before_returning_home(self):
        page = self.page()
        page.goto(BASE + '/index.html?lang=en#in-progress')
        page.locator('#in-progress [data-progress-link]').click()
        first = page.locator('.progress-gallery a').first
        first.click()
        expect(page.locator('#progressViewerClose')).to_contain_text('Back to images')
        page.keyboard.press('ArrowRight')
        expect(page.locator('#progressViewerPosition')).to_have_text('02 / 15')
        page.go_back()
        expect(page.locator('#progressViewer')).not_to_be_visible()
        expect(first).to_be_focused()
        expect(page.locator('body')).not_to_have_class(re.compile(r'\bmodal-open\b'))
        self.assertIn('in-progress.html', page.url)
        page.go_forward()
        expect(page.locator('#progressViewer')).to_be_visible()
        expect(page.locator('#progressViewerPosition')).to_have_text('02 / 15')
        expect(page.locator('#progressViewerTitle')).to_have_text('Xu Zhiwei')
        page.locator('#progressViewerClose').click()
        expect(page.locator('#progressViewer')).not_to_be_visible()
        page.locator('#langSwitch').click()
        first.click()
        expect(page.locator('#progressViewerClose')).to_contain_text('返回图集')
        page.keyboard.press('Escape')
        page.keyboard.press('Escape')
        expect(page.locator('#progressViewer')).not_to_be_visible()
        page.go_back()
        expect(page).to_have_url(BASE + '/index.html?lang=en#in-progress')

    def test_home_image_browser_back_and_rapid_reopen_keep_the_page(self):
        page = self.page()
        page.goto(BASE + '/index.html#in-progress')
        first = page.locator('.home-progress-card').first
        first.click()
        expect(page.locator('#stillViewer')).to_be_visible()
        page.keyboard.press('ArrowRight')
        page.go_back()
        expect(page.locator('#stillViewer')).not_to_be_visible()
        expect(first).to_be_focused()
        page.go_forward()
        expect(page.locator('#stillViewerPosition')).to_have_text('02 / 15')
        expect(page.locator('#stillViewerTitle')).to_have_text('高空投送')
        page.keyboard.press('Escape')
        expect(page.locator('#stillViewer')).not_to_be_visible()
        first.click()
        page.keyboard.press('Escape')
        first.click()
        expect(page.locator('#stillViewer')).to_be_visible()
        page.locator('#stillViewerClose').click()
        expect(page.locator('#stillViewer')).not_to_be_visible()
        expect(page.locator('#in-progress')).to_be_in_viewport()

    def test_motion_library_failure_keeps_navigation_and_images_usable(self):
        page = self.page()
        page.emulate_media(reduced_motion='no-preference')
        page.route('**/assets/vendor/gsap-3.15.0/**', lambda route: route.abort())
        self.ready(page)
        expect(page.locator('.progress-return')).to_be_visible()
        first = page.locator('.progress-gallery a').first
        first.click()
        expect(page.locator('#progressViewer')).to_be_visible()
        page.locator('#progressViewerClose').click()
        expect(page.locator('#progressViewer')).not_to_be_visible()
        expect(first).to_be_focused()

    def test_production_motion_responds_to_hover_and_reduces_cleanly(self):
        page = self.page()
        page.emulate_media(reduced_motion='no-preference')
        self.ready(page)
        expect(page.locator('html')).to_have_class(re.compile(r'\bproduction-motion\b'))
        link = page.locator('.progress-gallery a').first
        link.scroll_into_view_if_needed()
        link.hover(position={'x': 20, 'y': 20})
        page.wait_for_function('getComputedStyle(document.querySelector(".progress-gallery a")).transform !== "none"')
        captures = os.environ.get('PROGRESS_CAPTURE_DIR')
        if captures:
            page.screenshot(path=str(Path(captures) / 'motion-hover.png'))
        first = page.locator('.progress-gallery img').first
        first.evaluate('image=>image.decode()')
        link.click()
        page.wait_for_function('document.querySelector("#progressViewerImage").naturalWidth > 0')
        if captures:
            expect(page.locator('#progressViewerImage')).to_be_visible()
            page.screenshot(path=str(Path(captures) / 'motion-viewer.png'))
        page.locator('#progressNext').click()
        expect(page.locator('#progressViewerTitle')).to_have_text('许知微')
        page.keyboard.press('Escape')
        page.emulate_media(reduced_motion='reduce')
        expect(page.locator('html')).not_to_have_class(re.compile(r'\bproduction-motion\b'))
        self.assertTrue(page.locator('.progress-gallery figure').evaluate_all('nodes=>nodes.every(node=>getComputedStyle(node).visibility!=="hidden" && getComputedStyle(node).opacity==="1")'))

    def test_top_work_navigation_dropdown_closes_and_restores_keyboard_focus(self):
        page = self.page()
        page.goto(BASE + '/', wait_until='load')
        dropdown = page.locator('.nav-collection')
        trigger = dropdown.locator('summary')
        expect(dropdown.locator('[data-progress-section]')).not_to_be_visible()
        trigger.click()
        expect(dropdown.locator('[data-progress-section]')).to_be_visible()
        expect(dropdown.locator('a[href="#stills"]')).to_be_visible()
        page.keyboard.press('Escape')
        expect(dropdown.locator('[data-progress-section]')).not_to_be_visible()
        expect(trigger).to_be_focused()
        trigger.click()
        page.locator('h1').click()
        expect(dropdown.locator('[data-progress-section]')).not_to_be_visible()

    def test_home_and_detail_production_images_use_compact_thumbnails(self):
        page = self.page()
        page.goto(BASE + '/', wait_until='load')
        page.wait_for_function('Array.from(document.querySelectorAll(".home-progress-card img")).every(image=>image.getAttribute("src"))')
        for image in page.locator('.home-progress-card img').all():
            bounds = image.bounding_box()
            self.assertLessEqual(bounds['width'], 260)
            self.assertLessEqual(bounds['height'], 180)
        captures = os.environ.get('PROGRESS_CAPTURE_DIR')
        if captures:
            output = Path(captures)
            output.mkdir(parents=True, exist_ok=True)
            page.locator('#in-progress').evaluate('section=>section.scrollIntoView({behavior:"instant"})')
            for image in page.locator('.home-progress-card img').all():
                image.evaluate('image=>image.decode()')
            page.screenshot(path=str(output / 'home.png'))
            page.locator('.nav-collection summary').click()
            page.screenshot(path=str(output / 'navigation.png'))
            page.set_viewport_size({'width': 390, 'height': 844})
            page.locator('#in-progress').evaluate('section=>section.scrollIntoView({behavior:"instant"})')
            page.locator('#in-progress').screenshot(path=str(output / 'home-mobile.png'))
            page.set_viewport_size({'width': 1440, 'height': 900})
        self.ready(page)
        for image in page.locator('.progress-gallery img').all():
            self.assertLessEqual(image.bounding_box()['width'], 430)
        if captures:
            for image in page.locator('.progress-gallery img').all():
                image.scroll_into_view_if_needed()
                image.evaluate('image=>image.decode()')
            page.evaluate('scrollTo(0,0)')
            page.screenshot(path=str(output / 'detail.png'), full_page=True)
            page.goto(BASE + '/projects.html', wait_until='load')
            page.screenshot(path=str(output / 'projects.png'))

    def test_landscape_cover_keeps_native_portrait_player(self):
        page = self.page()
        page.goto(BASE + '/', wait_until='load')
        page.locator('#workSearch').fill('AI 之后')
        card = page.locator('#worksGrid .work-card').filter(has=page.locator('img[src*="ddfc97d74e1f0d46"]'))
        expect(card).to_have_count(1)
        media = card.locator('.work-media')
        bounds = media.bounding_box()
        self.assertAlmostEqual(bounds['width']/bounds['height'], 16/9, delta=.01)
        card.click()
        page.wait_for_function('document.querySelector("#workPlayerVideo").videoHeight > 0')
        frame = page.locator('#workPlayerVideo').bounding_box()
        intrinsic = page.locator('#workPlayerVideo').evaluate('v=>v.videoWidth/v.videoHeight')
        self.assertAlmostEqual(frame['width']/frame['height'], intrinsic, delta=.02)
        self.assertLess(frame['width'], frame['height'])
        captures = os.environ.get('PROGRESS_CAPTURE_DIR')
        if captures:
            page.screenshot(path=str(Path(captures) / 'portrait-player.png'))
        page.keyboard.press('Escape')
        original = page.locator('.feature-screen').bounding_box()
        page.locator('#featureControls button').last.click()
        screen = page.locator('.feature-screen').bounding_box()
        self.assertAlmostEqual(screen['width'], original['width'], delta=1)
        self.assertAlmostEqual(screen['height'], original['height'], delta=1)
        if captures:
            page.screenshot(path=str(Path(captures) / 'portrait-feature.png'))

    def test_portrait_player_keeps_video_and_close_visible_on_landscape_phone(self):
        page = self.page(has_touch=True)
        page.set_viewport_size({'width': 844, 'height': 390})
        page.goto(BASE + '/', wait_until='load')
        page.locator('#workSearch').fill('一次善意')
        page.locator('[data-work-id="eagle-act-of-kindness"]').click()
        page.wait_for_function('document.querySelector("#workPlayerVideo").videoHeight > 0')
        frame = page.locator('#workPlayerVideo').bounding_box()
        intrinsic = page.locator('#workPlayerVideo').evaluate('video=>video.videoWidth/video.videoHeight')
        self.assertAlmostEqual(frame['width']/frame['height'], intrinsic, delta=.02)
        self.assertGreaterEqual(frame['y'], 0)
        self.assertLessEqual(frame['y'] + frame['height'], 390)
        close = page.locator('#workPlayerClose').bounding_box()
        self.assertLessEqual(close['y'] + close['height'], 390)
        self.assertGreaterEqual(page.locator('#workPlayer').bounding_box()['width'], 320)
        captures = os.environ.get('PROGRESS_CAPTURE_DIR')
        if captures:
            page.screenshot(path=str(Path(captures) / 'portrait-landscape.png'))

    def test_unoptimized_portrait_poster_uses_landscape_cover_without_video_preview(self):
        page = self.page(has_touch=True)
        fixture = json.loads((ROOT / 'data/works.json').read_text())
        work = next(work for work in fixture if work['id'] == 'eagle-act-of-kindness')
        work['poster'] = 'assets/stills/nezha-boy.jpg'
        page.route('**/api/works', lambda route: route.fulfill(json={'works': fixture}))
        video_requests = []
        page.on('request', lambda request: video_requests.append(request.url) if '.mp4' in request.url else None)
        page.goto(BASE + '/', wait_until='load')
        page.locator('#workSearch').fill('一次善意')
        card = page.locator('[data-work-id="eagle-act-of-kindness"]')
        card.scroll_into_view_if_needed()
        card.locator('img').evaluate('image=>image.decode()')
        frame = card.locator('.work-media').bounding_box()
        self.assertAlmostEqual(frame['width']/frame['height'], 16/9, delta=.02)
        self.assertEqual(card.locator('img').evaluate('image=>getComputedStyle(image).objectFit'), 'cover')
        self.assertEqual(video_requests, [])


if __name__ == '__main__':
    unittest.main()
