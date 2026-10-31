"""Homepage chapters keep independent space without clipping real content."""
import os
import unittest
from playwright.sync_api import sync_playwright, expect

BASE = os.environ.get('STUDIO_BASE_URL', 'http://127.0.0.1:3000').rstrip('/')


class HomeModules(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime = sync_playwright().start()
        cls.browser = cls.runtime.chromium.launch(channel='chrome', headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.runtime.stop()

    def page(self, width, height, language='cn', javascript=True):
        page = self.browser.new_page(viewport={'width': width, 'height': height},
                                     reduced_motion='reduce', java_script_enabled=javascript)
        self.addCleanup(page.context.close)
        page.goto(BASE + ('/?lang=en' if language == 'en' else '/'), wait_until='domcontentloaded')
        if javascript:
            page.wait_for_selector('#toolsTitle .director-letter', state='attached')
        else:
            page.wait_for_load_state('load')
        return page

    def test_desktop_chapters_and_director_screen_have_room_and_balanced_columns(self):
        for width, height in [(1024, 768), (1440, 900), (1920, 1080)]:
            for language in ['cn', 'en']:
                with self.subTest(width=width, language=language):
                    page = self.page(width, height, language)
                    dimensions = page.evaluate('''() => {
                      const box=s=>document.querySelector(s).getBoundingClientRect().toJSON();
                      return {projects:box('#projects'),copy:box('.tools-preview-copy'),image:box('.tools-preview-image'),
                        chapters:['#works','#in-progress','#stills','#about','#contact'].map(s=>[s,box(s)]),
                        overflow:document.documentElement.scrollWidth>innerWidth};
                    }''')
                    self.assertFalse(dimensions['overflow'])
                    stage, copy, image = [dimensions[k] for k in ['projects', 'copy', 'image']]
                    self.assertGreaterEqual(stage['height'], height - 1)
                    self.assertLessEqual(stage['height'], height * 1.2)
                    self.assertGreaterEqual(image['width'], copy['width'] * 1.3)
                    self.assertGreaterEqual(image['x'], copy['right'] + 24)
                    for content in [copy, image]:
                        self.assertGreaterEqual(content['y'], stage['y'] + 96)
                        self.assertLessEqual(content['bottom'], stage['bottom'] - 64)
                    for selector, chapter in dimensions['chapters']:
                        self.assertGreaterEqual(chapter['height'], height - 1, selector)
                    page.locator('.main-nav a[href="#projects"]').click()
                    self.assertAlmostEqual(page.locator('#projects').bounding_box()['y'], 0, delta=1)
                    expect(page.locator('#toolsTitle')).to_be_in_viewport()
                    expect(page.locator('.tools-preview-image')).to_be_in_viewport(ratio=.98)
                    page.locator('#themeToggle').click()
                    expect(page.locator('html')).to_have_attribute('data-theme', 'dark')
                    self.assertEqual(page.locator('#projects').bounding_box()['height'], stage['height'])
                    page.close()

    def test_phone_tablet_and_short_windows_keep_content_in_order(self):
        for width, height in [(320, 740), (390, 844), (820, 1180), (1440, 600)]:
            for language in ['cn', 'en']:
                with self.subTest(width=width, language=language):
                    page = self.page(width, height, language)
                    metrics = page.evaluate('''() => {
                      const box=s=>document.querySelector(s).getBoundingClientRect().toJSON();
                      return {stage:box('#projects'),copy:box('.tools-preview-copy'),image:box('.tools-preview-image'),
                        sections:[...document.querySelectorAll('#home > section')].map(e=>e.getBoundingClientRect().toJSON()),
                        clipped:[...document.querySelectorAll('#toolsTitle,.tools-preview-copy p')].some(e=>e.scrollWidth>e.clientWidth+2),
                        overflow:document.documentElement.scrollWidth>innerWidth};
                    }''')
                    self.assertFalse(metrics['overflow'])
                    self.assertFalse(metrics['clipped'])
                    if width < 1000:
                        self.assertGreaterEqual(metrics['image']['y'], metrics['copy']['bottom'] + 24)
                    self.assertLessEqual(metrics['image']['bottom'], metrics['stage']['bottom'] - 40)
                    for first, second in zip(metrics['sections'], metrics['sections'][1:]):
                        self.assertGreaterEqual(second['y'], first['bottom'] - 1)
                    if width < 801:
                        self.assertLess(metrics['stage']['height'], height * 1.4)
                        page.locator('#menuToggle').click()
                        page.locator('.main-nav a[href="#projects"]').click()
                        self.assertAlmostEqual(page.locator('#projects').bounding_box()['y'], 0, delta=1)
                        self.assertGreaterEqual(page.locator('#toolsTitle').bounding_box()['y'],
                                                page.locator('.site-header').bounding_box()['height'] + 12)
                    page.close()

    def test_without_scripts_director_still_has_its_own_readable_section(self):
        page = self.page(1440, 900, javascript=False)
        self.assertGreaterEqual(page.locator('#projects').bounding_box()['height'], 900)
        expect(page.locator('#toolsTitle')).to_have_text('导演工作台')
        link = page.locator('.tools-preview-copy [data-projects-link]').first
        self.assertEqual(link.get_attribute('href'), 'projects.html#directorTitle')
        page.locator('.main-nav a[href="#projects"]').click()
        expect(page.locator('#projects')).to_be_in_viewport(ratio=.999)
        expect(page.locator('#toolsTitle')).to_be_in_viewport()
        self.assertAlmostEqual(page.locator('#projects').bounding_box()['y'], 0, delta=1)
        expect(link).to_be_in_viewport()


if __name__ == '__main__':
    unittest.main()
