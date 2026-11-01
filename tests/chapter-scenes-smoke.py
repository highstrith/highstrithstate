"""Three visual chapters retain their real content, controls and fallbacks."""
import os
import io
import re
import unittest
from PIL import Image
from playwright.sync_api import sync_playwright, expect

BASE = os.environ.get('STUDIO_BASE_URL', 'http://127.0.0.1:3000').rstrip('/')


class ChapterScenes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime = sync_playwright().start()
        cls.browser = cls.runtime.chromium.launch(channel='chrome', headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.runtime.stop()

    def page(self, width=1440, height=900, language='cn', javascript=True):
        page = self.browser.new_page(viewport={'width': width, 'height': height},
                                     reduced_motion='reduce', java_script_enabled=javascript)
        self.addCleanup(page.context.close)
        page.goto(BASE + ('/?lang=en' if language == 'en' else '/'), wait_until='load')
        return page

    def test_real_scene_fills_production_chapter_and_opens_the_existing_gallery(self):
        page = self.page()
        scene = page.locator('#in-progress .production-scene img')
        expect(scene).to_have_count(1)
        expect(scene).to_have_attribute('loading', 'lazy')
        section = page.locator('#in-progress')
        section.evaluate('e=>e.scrollIntoView({behavior:"instant"})')
        scene.evaluate('e=>e.decode()')
        a, b = section.bounding_box(), scene.bounding_box()
        self.assertAlmostEqual(a['width'], 1440, delta=1)
        self.assertAlmostEqual(a['width'], b['width'], delta=1)
        self.assertAlmostEqual(a['height'], b['height'], delta=1)
        page.locator('[data-production-feature]').click()
        expect(page.locator('#stillViewer')).to_be_visible()
        expect(page.locator('#stillViewerPosition')).to_have_text('01 / 15')
        expect(page.locator('#stillViewerImage')).to_have_attribute('src', BASE + '/assets/progress/weishizhinuo/forest-city.webp')
        page.keyboard.press('Escape')
        expect(page.locator('[data-production-feature]')).to_be_focused()
        page.go_forward()
        expect(page.locator('#stillViewer')).to_be_visible()
        page.keyboard.press('ArrowRight')
        expect(page.locator('#stillViewerPosition')).to_have_text('02 / 15')
        page.go_back()
        expect(page.locator('#stillViewer')).not_to_be_visible()
        expect(page.locator('[data-production-feature]')).to_be_focused()
        expect(page.locator('.home-progress-grid [data-home-progress]')).to_have_count(15)

    def test_workbench_has_a_real_foreground_detail_and_films_have_a_featured_cover(self):
        page = self.page()
        detail = page.locator('.tools-preview-detail img')
        expect(detail).to_have_count(1)
        expect(detail).to_have_attribute('src', 'assets/progress/weishizhinuo/director-storyboard-thumb.webp')
        expect(page.locator('.tools-preview-detail')).to_have_attribute('aria-hidden', 'true')
        covers = page.locator('.film-recommendation-card')
        first, second, third = [card.bounding_box() for card in covers.all()]
        self.assertGreater(first['width'], second['width'] * 1.4)
        self.assertGreater(first['height'], second['height'] * 1.8)
        self.assertAlmostEqual(second['x'], third['x'], delta=1)
        self.assertGreater(third['y'], second['y'])
        for card in covers.all():
            expect(card).to_have_attribute('href', 'reel/')

    def test_responsive_bilingual_chapters_keep_reading_order_and_controls(self):
        for width, height in [(320, 740), (390, 844), (820, 1180), (1440, 600), (1920, 1080)]:
            for language in ['cn', 'en']:
                page = self.page(width, height, language)
                self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'), width)
                expect(page.locator('[data-production-feature]')).to_have_text('View scene image' if language == 'en' else '查看场景大图')
                for selector in ['#in-progress', '#projects', '#filmRecommendations']:
                    section = page.locator(selector)
                    section.evaluate('e=>e.scrollIntoView({behavior:"instant"})')
                    self.assertTrue(section.evaluate('''e=>[...e.querySelectorAll('h2,p')].every(n=>n.scrollWidth<=n.clientWidth+2)'''), (width, language, selector))
                    title = section.locator('h2').bounding_box()
                    self.assertGreaterEqual(title['x'], 0, (width, language, selector))
                    self.assertLessEqual(title['x'] + title['width'], width + 1)
                if width < 801:
                    self.assertEqual(page.locator('.tools-preview-image').evaluate('e=>getComputedStyle(e).transform'), 'none')
                page.locator('#themeToggle').click()
                expect(page.locator('html')).to_have_attribute('data-theme', 'dark')
                self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'), width)
                page.close()

    def test_ambient_backgrounds_form_full_bleed_chapters_without_new_images(self):
        page = self.page()
        for selector in ['.hero', '#works', '#stills', '#contact']:
            section = page.locator(selector)
            style = section.evaluate('''e=>{
                const s=getComputedStyle(e,'::before');
                return {image:s.backgroundImage,left:parseFloat(s.left),right:parseFloat(s.right),content:s.content};
            }''')
            self.assertNotEqual(style['content'], 'none', selector)
            self.assertIn('radial-gradient', style['image'], selector)
            box = section.bounding_box()
            self.assertAlmostEqual(box['x'] + style['left'], 0, delta=1, msg=selector)
            self.assertAlmostEqual(box['width'] - style['left'] - style['right'], 1440, delta=1, msg=selector)
        for selector in ['#projects', '#filmRecommendations']:
            self.assertIn('radial-gradient', page.locator(selector).evaluate('e=>getComputedStyle(e).backgroundImage'), selector)
        page.locator('#themeToggle').click()
        expect(page.locator('html')).to_have_attribute('data-theme', 'dark')
        self.assertIn('radial-gradient', page.locator('#works').evaluate('e=>getComputedStyle(e,"::before").backgroundImage'))
        self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'), 1440)

    def test_light_chapters_are_visibly_light_and_dark_chapters_are_dark(self):
        # Catch fixed dark canvases and white text leaking into light mode.
        # Sample rendered pixels so different-but-equally-dark gradients fail.
        def luminance(rgb):
            values = [v / 255 for v in rgb[:3]]
            values = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in values]
            return sum(v * weight for v, weight in zip(values, [.2126, .7152, .0722]))

        for width, height in [(390, 844), (1440, 900)]:
            page = self.page(width, height)
            for theme in ['light', 'dark']:
                if theme == 'dark':
                    page.locator('#themeToggle').evaluate('e=>e.click()')
                expect(page.locator('html')).to_have_attribute('data-theme', theme)
                for selector, copy in [
                    ('#in-progress', 'h2, h3, .home-progress-summary > p, .text-link, .home-progress-card h4, .production-strip-controls button'),
                    ('#stills', 'h2, .section-label, .still-card h3, .still-card p'),
                    ('#about', 'h2, .about-content p, .practice-list, .text-link'),
                ]:
                    section = page.locator(selector)
                    section.evaluate('e=>e.scrollIntoView({behavior:"instant",block:"start"})')
                    if selector == '#in-progress':
                        page.locator('.production-scene img').evaluate('e=>e.decode()')
                    page.wait_for_function('''()=>[...document.querySelectorAll('#in-progress img')]
                        .filter(e=>e.currentSrc).every(e=>e.complete)''')
                    pixels = Image.open(io.BytesIO(page.screenshot())).convert('RGB')
                    # The production scene deliberately exposes photography on
                    # the right; judge its reading canvas on the left.
                    edges = [8] if selector == '#in-progress' else [8, width - 9]
                    canvas = [luminance(pixels.getpixel((x, y)))
                              for x in edges for y in [180, 420, 650]]
                    if theme == 'light':
                        self.assertGreater(min(canvas), .6, (width, selector, theme, canvas))
                    else:
                        self.assertLess(max(canvas), .12, (width, selector, theme, canvas))
                    colors = section.locator(copy).evaluate_all('es=>es.map(e=>getComputedStyle(e).color)')
                    for color in colors:
                        fg = luminance([float(v) for v in re.findall(r'[\d.]+', color)[:3]])
                        for bg in canvas:
                            contrast = (max(fg, bg) + .05) / (min(fg, bg) + .05)
                            self.assertGreaterEqual(contrast, 4.5, (width, selector, theme, color, contrast))
                page.reload(wait_until='load')
                expect(page.locator('html')).to_have_attribute('data-theme', theme)
            page.close()

    def test_no_script_retains_scene_link_and_film_entries(self):
        page = self.page(390, 844, javascript=False)
        expect(page.locator('[data-production-feature]')).to_have_attribute('href', 'assets/progress/weishizhinuo/forest-city.webp')
        expect(page.locator('.film-recommendation-card')).to_have_count(3)
        expect(page.locator('.home-progress-grid [data-home-progress]')).to_have_count(15)

    def test_theme_mouse_click_keeps_the_current_chapter_in_place(self):
        page = self.page()
        page.emulate_media(reduced_motion='no-preference')
        page.goto(BASE + '/#filmRecommendations', wait_until='networkidle')
        page.wait_for_timeout(600)
        top = page.locator('#filmRecommendations').bounding_box()['y']
        for theme in ['dark', 'light']:
            button = page.locator('#themeToggle').bounding_box()
            page.mouse.click(button['x'] + button['width'] / 2, button['y'] + button['height'] / 2)
            expect(page.locator('html')).to_have_attribute('data-theme', theme)
            page.wait_for_timeout(600)
            self.assertAlmostEqual(page.locator('#filmRecommendations').bounding_box()['y'], top, delta=2)


if __name__ == '__main__':
    unittest.main()
