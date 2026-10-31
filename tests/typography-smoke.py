"""Reading order and text containment while display type scales across devices."""
import os
import unittest
from playwright.sync_api import sync_playwright, expect

BASE = os.environ.get('STUDIO_BASE_URL', 'http://127.0.0.1:3000').rstrip('/')


class Typography(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime = sync_playwright().start()
        cls.browser = cls.runtime.chromium.launch(channel='chrome', headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.runtime.stop()

    def test_portfolio_headlines_and_descriptions_do_not_collide_in_either_language(self):
        page = self.browser.new_page(reduced_motion='reduce')
        self.addCleanup(page.context.close)
        for width in [320, 390, 820, 1191, 1440, 1920]:
            page.set_viewport_size({'width': width, 'height': 1000})
            for language in ['cn', 'en']:
                page.goto(BASE + ('/?lang=en' if language == 'en' else '/'), wait_until='domcontentloaded')
                expect(page.locator('#heroTitle .director-letter')).not_to_have_count(0)
                metrics = page.evaluate('''() => {
                  const rect=e=>{const r=e.getBoundingClientRect();return {x:r.x,y:r.y,right:r.right,bottom:r.bottom}};
                  const headline=document.querySelector('#heroTitle'), description=document.querySelector('.hero-description');
                  return {width:innerWidth,scroll:document.documentElement.scrollWidth,
                    title:rect(headline),copy:rect(description),screen:rect(document.querySelector('.hero-feature')),
                    clipped:[...document.querySelectorAll('#heroTitle,#toolsTitle')].filter(e=>e.scrollWidth>e.clientWidth+2).map(e=>e.id)};
                }''')
                self.assertLessEqual(metrics['scroll'], width, (width, language))
                self.assertEqual(metrics['clipped'], [], (width, language))
                a, b = metrics['title'], metrics['copy']
                self.assertTrue(a['right'] <= b['x'] or a['bottom'] <= b['y'], (width, language, metrics))
                self.assertLessEqual(max(a['bottom'], b['bottom']), metrics['screen']['y'])
                page.locator('#themeToggle').click()
                expect(page.locator('html')).to_have_attribute('data-theme', 'dark')
                page.locator('#themeToggle').click()
                expect(page.locator('html')).to_have_attribute('data-theme', 'light')

    def test_film_index_lead_uses_available_space_and_mobile_reading_order(self):
        page = self.browser.new_page(reduced_motion='reduce')
        self.addCleanup(page.context.close)
        for width in [320, 390, 820, 1191, 1440]:
            page.set_viewport_size({'width': width, 'height': 1000})
            page.goto(BASE + '/reel/', wait_until='domcontentloaded')
            metrics = page.evaluate('''() => {
              const rect=s=>{const e=document.querySelector(s),r=e.getBoundingClientRect();return {x:r.x,y:r.y,right:r.right,bottom:r.bottom}};
              return {title:rect('.hero h1'),copy:rect('.lede'),ledger:rect('.ledger'),image:rect('.feature'),
                overflow:document.documentElement.scrollWidth>innerWidth,
                clipped:[...document.querySelectorAll('h1,h2,h3,.lede,.desc')].some(e=>e.scrollWidth>e.clientWidth+2)};
            }''')
            self.assertFalse(metrics['overflow'], (width, metrics))
            self.assertFalse(metrics['clipped'], (width, metrics))
            if width > 820:
                self.assertGreaterEqual(metrics['copy']['x'], metrics['title']['right'])
            else:
                self.assertGreaterEqual(metrics['copy']['y'], metrics['title']['bottom'])
            self.assertGreaterEqual(metrics['ledger']['y'], max(metrics['title']['bottom'], metrics['copy']['bottom']))
            self.assertGreaterEqual(metrics['image']['y'], metrics['ledger']['bottom'])
            expect(page.locator('article')).to_have_count(3)
            expect(page.locator('.watch')).to_have_count(3)


if __name__ == '__main__':
    unittest.main()
