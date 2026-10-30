"""Real-browser checks for the scroll-driven portfolio spiral."""
import math
import os
import unittest
from playwright.sync_api import sync_playwright, expect

BASE = os.environ.get('STUDIO_BASE_URL', 'http://127.0.0.1:3000')


class FlyVortex(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime = sync_playwright().start()
        cls.browser = cls.runtime.chromium.launch(channel='chrome', headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.runtime.stop()

    def page(self, width=1440, motion='no-preference'):
        page = self.browser.new_page(viewport={'width': width, 'height': 900}, reduced_motion=motion)
        self.addCleanup(page.close)
        page.goto(BASE, wait_until='domcontentloaded')
        page.wait_for_function("document.querySelectorAll('#flyField .fly-card').length > 0")
        return page

    def seek(self, page, progress):
        page.evaluate('''p => {
          const section = document.querySelector('#flyWorks');
          scrollTo({top: section.getBoundingClientRect().top + scrollY +
            p * (section.offsetHeight - innerHeight), behavior: 'instant'});
        }''', progress)
        page.wait_for_timeout(800)
        return page.evaluate('''() => {
          const head = document.querySelector('.fly-head').getBoundingClientRect();
          const stage = document.querySelector('#flyStage').getBoundingClientRect();
          return {head: [head.x, head.y], stage: [stage.x, stage.y],
            cards: [...document.querySelectorAll('.fly-card')].map(card => {
              const box = card.getBoundingClientRect(), style = getComputedStyle(card);
              return {x: box.x + box.width/2, y: box.y + box.height/2,
                transform: style.transform, opacity: +style.opacity};
            })};
        }''')

    def test_spiral_turns_while_advancing_and_reverses(self):
        page = self.page()
        a, b = self.seek(page, .28), self.seek(page, .38)
        # A fixed XY flight only scales radius; a spiral changes polar angle.
        turns = []
        for first, second in zip(a['cards'], b['cards']):
            if min(first['opacity'], second['opacity']) < .2:
                continue
            angles = [math.atan2(card['y']-450, card['x']-720) for card in [first, second]]
            turns.append(abs(math.atan2(math.sin(angles[1]-angles[0]), math.cos(angles[1]-angles[0]))))
        self.assertTrue(turns)
        self.assertGreater(min(turns), .08, 'Images must orbit the title as they approach')
        self.assertAlmostEqual(a['head'][1], b['head'][1], delta=1)
        self.assertAlmostEqual(a['stage'][1], 0, delta=1)
        self.assertEqual(page.locator('#flyField').evaluate('e => [e.scrollLeft, e.scrollTop]'), [0, 0])
        reverse = self.seek(page, .28)
        for before, after in zip(a['cards'], reverse['cards']):
            self.assertAlmostEqual(before['x'], after['x'], delta=3)
            self.assertAlmostEqual(before['y'], after['y'], delta=3)

    def test_resize_and_reduced_motion_keep_images_browsable(self):
        page = self.page()
        self.seek(page, .4)
        page.set_viewport_size({'width': 390, 'height': 844})
        expect(page.locator('#flyWorks')).not_to_have_class('fly-section fly-motion')
        self.assertLess(page.locator('#flyWorks').bounding_box()['height'], 700)
        page.locator('#flyWorks').evaluate("e => e.scrollIntoView({behavior: 'instant'})")
        expect(page.locator('#flyField .fly-card').first).to_be_visible()
        expect(page.locator('#flyField .fly-card').first).to_be_in_viewport()
        self.assertEqual(page.locator('#flyField').evaluate('e => getComputedStyle(e).overflowX'), 'auto')
        page.locator('#flyField').evaluate('e => e.scrollLeft = e.scrollWidth')
        self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'), 390)
        page.set_viewport_size({'width': 1440, 'height': 900})
        page.emulate_media(reduced_motion='reduce')
        expect(page.locator('#flyWorks')).not_to_have_class('fly-section fly-motion')
        self.assertLess(page.locator('#flyWorks').bounding_box()['height'], 700)
        self.assertEqual(page.locator('.fly-card').first.evaluate('e => getComputedStyle(e).transform'), 'none')
        page.emulate_media(reduced_motion='no-preference')
        expect(page.locator('#flyWorks')).to_have_class('fly-section fly-motion')
        self.assertGreater(page.locator('#flyWorks').bounding_box()['height'], 2000)
        self.assertEqual(page.locator('#flyField').evaluate('e => e.scrollLeft'), 0)

    def test_catalogue_language_and_exit(self):
        page = self.page()
        self.assertEqual(page.locator('#flyField img').count(), page.locator('#worksGrid .work-card').count())
        page.locator('#langSwitch').click()
        expect(page.locator('#flyTitle')).to_have_text('Selected films')
        self.assertEqual(page.locator('.fly-title').first.inner_text(), page.locator('#worksGrid .work-title').first.inner_text())
        self.seek(page, .5)
        page.locator('.fly-more').click()
        page.wait_for_timeout(700)
        self.assertLess(abs(page.locator('#worksTitle').bounding_box()['y']), 450)
        expect(page.locator('#worksGrid .work-item:not([hidden])')).to_have_count(6)


if __name__ == '__main__':
    unittest.main()
