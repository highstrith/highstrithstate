"""Home production strip: real imagery, continuous motion and accessible browsing.

Run against the existing server with ``python3 tests/production-strip-smoke.py``.
Set PRODUCTION_STRIP_CAPTURE_DIR to save desktop, phone and image-viewer captures.
"""
import os
import re
import unittest
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import expect, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
BASE = os.environ.get('STUDIO_BASE_URL', 'http://127.0.0.1:3000').rstrip('/')
GROUP = '#in-progress .home-progress-grid'
CARDS = GROUP + ' .home-progress-card[data-home-progress]'
STRIP = '#homeProgressStrip'
TRACK = '#homeProgressTrack'
TOGGLE = '#productionStripToggle'


class ProductionStrip(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime = sync_playwright().start()
        cls.browser = cls.runtime.chromium.launch(channel='chrome', headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.runtime.stop()

    def page(self, motion='no-preference', width=1440, **options):
        page = self.browser.new_page(
            viewport={'width': width, 'height': 900},
            reduced_motion=motion,
            **options,
        )
        page.set_default_timeout(5000)
        self.addCleanup(page.context.close)
        return page

    def ready(self, page):
        page.goto(BASE + '/index.html#in-progress', wait_until='networkidle')
        expect(page.locator(STRIP)).to_be_visible(timeout=2000)
        page.locator(STRIP).evaluate('node => node.scrollIntoView({block:"center", behavior:"instant"})')
        expect(page.locator(CARDS)).to_have_count(15)
        page.wait_for_function('''selector => [...document.querySelectorAll(selector + ' img')]
            .every(image => image.getAttribute('src'))''', arg=CARDS)
        page.mouse.move(2, 2)
        page.locator('#homeProgressTitle').evaluate('node => node.focus({preventScroll:true})')
        # Entrances may finish after the anchor is reached; motion assertions use
        # the track itself, never the card entrance/hover transforms.
        page.wait_for_timeout(250)

    def x(self, page):
        return page.locator(TRACK).evaluate('node => new DOMMatrixReadOnly(getComputedStyle(node).transform).m41')

    def assert_stopped(self, page):
        page.wait_for_timeout(100)
        before = self.x(page)
        page.wait_for_timeout(450)
        self.assertAlmostEqual(self.x(page), before, delta=.75, msg='The paused image strip still moves')

    def assert_moves_right(self, page):
        before = self.x(page)
        page.wait_for_timeout(500)
        advance = self.x(page) - before
        cycle = page.locator(GROUP).evaluate('node => node.getBoundingClientRect().width')
        if advance < -cycle / 2:
            advance += cycle
        self.assertGreater(advance, 2, 'Images should travel from left to right')

    def capture(self, page, name):
        directory = os.environ.get('PRODUCTION_STRIP_CAPTURE_DIR')
        if directory:
            output = Path(directory)
            output.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(output / name))

    def test_fifteen_distinct_real_images_form_one_compact_row(self):
        page = self.page(motion='reduce')
        page.goto(BASE + '/', wait_until='networkidle')
        # This assertion intentionally runs before requiring the new wrapper: the
        # previous nine-card grid must fail for the actual missing content.
        expect(page.locator(CARDS)).to_have_count(15, timeout=1500)
        self.ready(page)
        cards = page.locator(CARDS)
        sources = cards.evaluate_all('links => links.map(link => new URL(link.href).pathname)')
        self.assertEqual(len(set(sources)), 15, 'Loop copies must not count as new production images')
        self.assertTrue(all('/assets/progress/weishizhinuo/' in source for source in sources))
        for link in cards.all():
            self.assertTrue((ROOT / link.get_attribute('href')).is_file())
        bounds = cards.evaluate_all('links => links.map(link => { const r = link.getBoundingClientRect(); return {x:r.x,y:r.y,w:r.width,h:r.height}; })')
        self.assertLess(max(item['y'] for item in bounds) - min(item['y'] for item in bounds), 2)
        self.assertTrue(all(bounds[index + 1]['x'] > bounds[index]['x'] for index in range(14)))
        images = cards.locator('img').evaluate_all('images => images.map(image => { const r = image.getBoundingClientRect(); return {w:r.width,h:r.height,fit:getComputedStyle(image).objectFit,src:image.getAttribute("src")}; })')
        self.assertTrue(all(image['src'].endswith('-thumb.webp') for image in images))
        self.assertTrue(all(0 < image['w'] <= 260 and 0 < image['h'] <= 180 for image in images))
        self.assertTrue(all(image['fit'] == 'contain' for image in images), 'Production images should retain the complete composition')

    def test_auto_motion_goes_right_and_copy_seam_matches_the_normal_gap(self):
        page = self.page()
        self.ready(page)
        self.assert_moves_right(page)
        copies = page.locator(TRACK + ' [data-strip-copy]')
        self.assertGreater(copies.count(), 0, 'A loop needs a repeated sequence before its end')
        originals = page.locator(CARDS).evaluate_all('links => links.map(link => link.getAttribute("href"))')
        for copy in copies.all():
            expect(copy).to_have_attribute('aria-hidden', 'true')
            self.assertEqual(copy.locator('a').evaluate_all('links => links.map(link => link.getAttribute("href"))'), originals)
            self.assertTrue(copy.evaluate('node => node.inert || [...node.querySelectorAll("a,button,[tabindex]")].every(child => child.tabIndex < 0)'), 'Repeated images must not add another fifteen keyboard stops')
        seam = page.locator(TRACK).evaluate('''track => {
            const groups = [...track.children].filter(node => node.querySelector('.home-progress-card'));
            const cards = group => [...group.querySelectorAll('.home-progress-card')].map(node => node.getBoundingClientRect());
            const first = cards(groups[0]), next = cards(groups[1]);
            return {normal:first[1].left-first[0].right, seam:next[0].left-first.at(-1).right};
        }''')
        self.assertGreaterEqual(seam['normal'], 0)
        self.assertAlmostEqual(seam['seam'], seam['normal'], delta=2, msg='The loop join should have the same spacing as adjacent images')
        self.capture(page, 'production-strip-desktop.png')
        # The visible repeated sequence must open the same fifteen-image gallery
        # and return focus to the real card, rather than a hidden keyboard copy.
        page.locator(STRIP).hover(position={'x': 20, 'y': 20})
        copies.first.locator('a').first.click()
        expect(page.locator('#stillViewerPosition')).to_have_text('01 / 15')
        page.keyboard.press('Escape')
        expect(page.locator('#stillViewer')).not_to_be_visible()
        expect(page.locator(CARDS).first).to_be_focused()

    def test_manual_pause_persists_through_language_and_resumes(self):
        page = self.page()
        self.ready(page)
        toggle = page.locator(TOGGLE)
        expect(toggle).to_have_attribute('aria-pressed', 'false')
        toggle.click()
        expect(toggle).to_have_attribute('aria-pressed', 'true')
        self.assert_stopped(page)
        page.locator('#langSwitch').click()
        expect(page.locator('html')).to_have_attribute('lang', 'en')
        expect(toggle).to_have_attribute('aria-pressed', 'true')
        expect(toggle).to_have_accessible_name(re.compile(r'resume|continue', re.I))
        page.locator(STRIP).evaluate('node => node.scrollIntoView({block:"center", behavior:"instant"})')
        self.assert_stopped(page)
        toggle.click()
        expect(toggle).to_have_attribute('aria-pressed', 'false')
        page.mouse.move(2, 2)
        self.assert_moves_right(page)

    def test_complete_loop_resets_without_a_visual_jump_or_empty_strip(self):
        page = self.page()
        page.clock.install()
        self.ready(page)
        cycle = page.locator(TRACK).evaluate('''track => {
            const groups = [...track.children].filter(node => node.querySelector('.home-progress-card'));
            return groups[1].querySelector('.home-progress-card').getBoundingClientRect().left
                - groups[0].querySelector('.home-progress-card').getBoundingClientRect().left;
        }''')
        self.assertGreater(cycle, 1000)
        previous = self.x(page)
        advances = []
        wrapped = False
        # Advance browser time in small steps, preserving GSAP's normal frame
        # callbacks and lag handling. No production tween is sought or changed.
        for _ in range(4000):
            page.clock.fast_forward(250)
            current = self.x(page)
            delta = current - previous
            if delta < -cycle / 2:
                residual = delta + cycle
                self.assertGreater(len(advances), 0, 'The strip did not move before repeating')
                usual = sorted(advances)[len(advances) // 2]
                self.assertAlmostEqual(residual, usual, delta=max(5, usual), msg='The new loop starts at a different visual position')
                wrapped = True
                break
            if delta > .01:
                advances.append(delta)
            previous = current
        self.assertTrue(wrapped, 'The automatic image sequence never repeated')
        coverage = page.locator(STRIP).evaluate('''strip => {
            const frame = strip.getBoundingClientRect();
            const cards = [...strip.querySelectorAll('.home-progress-card')]
                .map(node => node.getBoundingClientRect())
                .filter(rect => rect.right > frame.left && rect.left < frame.right);
            return {count:cards.length, left:Math.min(...cards.map(rect=>rect.left)),
                right:Math.max(...cards.map(rect=>rect.right)), frameLeft:frame.left, frameRight:frame.right};
        }''')
        self.assertGreater(coverage['count'], 1)
        self.assertLessEqual(coverage['left'], coverage['frameLeft'] + 40)
        self.assertGreaterEqual(coverage['right'], coverage['frameRight'] - 40)

    def test_hover_and_keyboard_focus_pause_until_the_visitor_leaves(self):
        page = self.page()
        self.ready(page)
        page.locator(STRIP).hover(position={'x': 20, 'y': 20})
        self.assert_stopped(page)
        expect(page.locator(TOGGLE)).to_have_attribute('aria-pressed', 'false')
        page.mouse.move(2, 2)
        self.assert_moves_right(page)
        first = page.locator(CARDS).first
        first.focus()
        expect(first).to_be_focused()
        self.assert_stopped(page)
        page.locator(TOGGLE).focus()
        self.assert_moves_right(page)

    def test_reduced_motion_is_manual_and_last_image_keeps_fifteen_image_navigation(self):
        page = self.page(motion='reduce')
        self.ready(page)
        self.assert_stopped(page)
        expect(page.locator(TRACK + ' [data-strip-copy]')).to_have_count(0)
        strip = page.locator(STRIP)
        self.assertGreater(strip.evaluate('node => node.scrollWidth'), strip.evaluate('node => node.clientWidth'))
        before = strip.evaluate('node => node.scrollLeft')
        strip.hover()
        page.mouse.wheel(700, 0)
        page.wait_for_function('([selector, before]) => document.querySelector(selector).scrollLeft > before + 50', arg=[STRIP, before])
        self.assert_stopped(page)
        last = page.locator(CARDS).last
        last.scroll_into_view_if_needed()
        last.click()
        expect(page.locator('#stillViewer')).to_be_visible()
        expect(page.locator('#stillViewerPosition')).to_have_text('15 / 15')
        page.wait_for_function('document.querySelector("#stillViewerImage").naturalWidth > 0')
        self.capture(page, 'production-strip-last-image.png')
        page.keyboard.press('ArrowRight')
        expect(page.locator('#stillViewerPosition')).to_have_text('01 / 15')
        page.keyboard.press('ArrowLeft')
        expect(page.locator('#stillViewerPosition')).to_have_text('15 / 15')
        page.go_back()
        expect(page.locator('#stillViewer')).not_to_be_visible()
        expect(last).to_be_focused()
        expect(last).to_be_in_viewport()
        expect(page.locator('body')).not_to_have_class(re.compile(r'\bmodal-open\b'))
        page.locator('[data-still="0"]').click()
        expect(page.locator('#stillViewerPosition')).to_have_text('01 / 08')

    def test_motion_preference_change_keeps_the_focused_image_visible(self):
        page = self.page(width=390)
        self.ready(page)
        last = page.locator(CARDS).last
        last.focus()
        expect(last).to_be_focused()
        expect(last).to_be_in_viewport()
        page.emulate_media(reduced_motion='reduce')
        expect(last).to_be_focused()
        expect(last).to_be_in_viewport()
        self.assert_stopped(page)
        page.emulate_media(reduced_motion='no-preference')
        expect(last).to_be_focused()
        expect(last).to_be_in_viewport()
        self.assert_stopped(page)

    def test_resize_and_phone_keep_motion_inside_the_page_in_both_languages(self):
        page = self.page()
        self.ready(page)
        for width in [1920, 1440, 820, 390, 320, 1440]:
            page.set_viewport_size({'width': width, 'height': 900})
            page.locator(STRIP).evaluate('node => node.scrollIntoView({block:"center", behavior:"instant"})')
            page.mouse.move(2, 2)
            page.wait_for_timeout(100)
            for language in ['cn', 'en']:
                if (page.locator('html').get_attribute('lang') == 'en') != (language == 'en'):
                    page.locator('#langSwitch').click()
                self.assertTrue(page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'), (width, language))
                bounds = page.locator(STRIP).bounding_box()
                self.assertGreaterEqual(bounds['x'], -1)
                self.assertLessEqual(bounds['x'] + bounds['width'], width + 1)
                expect(page.locator(CARDS)).to_have_count(15)
        phone = self.page(width=390, is_mobile=True, has_touch=True, device_scale_factor=2)
        self.ready(phone)
        self.assert_moves_right(phone)
        self.capture(phone, 'production-strip-phone.png')

    def test_no_script_and_motion_library_failure_keep_all_images_reachable(self):
        page = self.page(motion='reduce', java_script_enabled=False)
        page.goto((ROOT / 'index.html').as_uri() + '#in-progress', wait_until='load')
        expect(page.locator(CARDS)).to_have_count(15, timeout=1500)
        self.assertTrue(page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'))
        # The file/no-script page retains all twenty works. Cancel the long
        # initial smooth anchor scroll before interacting far down that page.
        page.locator(STRIP).evaluate('node => node.scrollIntoView({block:"center", behavior:"instant"})')
        last = page.locator(CARDS).last
        expected_path = urlsplit(last.get_attribute('href')).path
        last.scroll_into_view_if_needed()
        last.click()
        self.assertTrue(urlsplit(page.url).path.endswith(expected_path))
        fallback = self.page()
        fallback.route('**/assets/vendor/gsap-3.15.0/**', lambda route: route.abort())
        self.ready(fallback)
        last = fallback.locator(CARDS).last
        last.scroll_into_view_if_needed()
        last.click()
        expect(fallback.locator('#stillViewerPosition')).to_have_text('15 / 15')
        fallback.keyboard.press('Escape')
        expect(fallback.locator('#stillViewer')).not_to_be_visible()
        expect(last).to_be_focused()


if __name__ == '__main__':
    unittest.main()
