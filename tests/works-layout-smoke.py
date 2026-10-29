"""Film catalogue layout: native proportions, aligned rows and stable order."""
import os
import unittest
from pathlib import Path
from playwright.sync_api import expect, sync_playwright

BASE = os.environ.get('STUDIO_BASE_URL', 'http://127.0.0.1:3000').rstrip('/')


class WorksLayout(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime = sync_playwright().start()
        cls.browser = cls.runtime.chromium.launch(channel='chrome', headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.runtime.stop()

    def page(self):
        page = self.browser.new_page(viewport={'width': 1440, 'height': 1000}, reduced_motion='reduce')
        self.addCleanup(page.context.close)
        page.goto(BASE + '/index.html#works', wait_until='load')
        expect(page.locator('#worksGrid .work-card')).to_have_count(20)
        return page

    def rows(self, page):
        boxes = page.locator('#worksGrid .work-item:visible').evaluate_all('items => items.map(item => { const r=item.querySelector(".work-media").getBoundingClientRect(); return {id:item.querySelector("button").dataset.workId, x:r.x,y:r.y,w:r.width,h:r.height, ratio:Number(item.style.getPropertyValue("--media-aspect"))}; })')
        rows = []
        for box in boxes:
            if not rows or abs(rows[-1][0]['y'] - box['y']) > 1:
                rows.append([])
            rows[-1].append(box)
        return rows

    def test_gallery_rows_align_and_preserve_native_media(self):
        page = self.page()
        output = os.environ.get('WORKS_CAPTURE_DIR')
        if output:
            Path(output).mkdir(parents=True, exist_ok=True)
            for image in page.locator('#worksGrid img').all():
                image.scroll_into_view_if_needed()
                image.evaluate('image=>image.decode()')
            page.mouse.move(0, 0)
            page.locator('#works').scroll_into_view_if_needed()
            page.locator('#worksGrid').screenshot(path=str(Path(output) / 'gallery.png'), style='.site-header, .skip-link { visibility: hidden !important; }')
            page.locator('#works').evaluate('section=>section.scrollIntoView({behavior:"instant"})')
            page.screenshot(path=str(Path(output) / 'desktop.png'))
        width = page.locator('#worksGrid').bounding_box()['width']
        rows = self.rows(page)
        self.assertGreaterEqual(len(rows[0]), 3)
        self.assertLessEqual(len(rows), 8)
        for row in rows:
            for box in row:
                self.assertAlmostEqual(box['w']/box['h'], box['ratio'], delta=.01)
                self.assertLessEqual(box['h'], 301)
                self.assertAlmostEqual(box['h'], row[0]['h'], delta=1)
            if row is not rows[-1]:
                self.assertGreater(row[-1]['x'] + row[-1]['w'] - row[0]['x'], width * .97)

    def test_filter_resize_and_view_switch_preserve_sequence(self):
        page = self.page()
        original = page.locator('.work-card').evaluate_all('cards=>cards.map(card=>card.dataset.workId)')
        page.locator('[data-filter="motion"]').click()
        filtered = page.locator('.work-card:visible').evaluate_all('cards=>cards.map(card=>card.dataset.workId)')
        self.assertEqual(filtered, [key for key in original if key in filtered])
        page.locator('[data-view="list"]').click()
        expect(page.locator('#worksGrid')).to_have_class('works-grid is-list')
        page.set_viewport_size({'width': 820, 'height': 1000})
        page.locator('[data-view="gallery"]').click()
        for row in self.rows(page):
            for box in row:
                self.assertAlmostEqual(box['h'], row[0]['h'], delta=1)
        page.locator('#workSearch').fill('一次善意')
        expect(page.locator('.work-card:visible')).to_have_count(1)
        box = self.rows(page)[0][0]
        self.assertLess(box['w'], box['h'])
        self.assertLessEqual(box['h'], 301)

    def test_mobile_portrait_layout_is_compact_and_bilingual(self):
        page = self.page()
        for width in [320, 390, 600, 820, 1440, 1920]:
            page.set_viewport_size({'width': width, 'height': 1000})
            for language in ['cn', 'en']:
                if (page.locator('html').get_attribute('lang') == 'en') != (language == 'en'):
                    page.locator('#langSwitch').click()
                self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'), width)
                if width <= 600:
                    for item in page.locator('.work-item.is-portrait').all():
                        media = item.locator('.work-media').bounding_box()
                        caption = item.locator('.work-caption').bounding_box()
                        self.assertLessEqual(media['height'], 340)
                        self.assertGreaterEqual(caption['x'], media['x'] + media['width'])
        output = os.environ.get('WORKS_CAPTURE_DIR')
        if output:
            page.set_viewport_size({'width': 390, 'height': 1000})
            page.locator('#langSwitch').click()
            for image in page.locator('#worksGrid img').all():
                image.scroll_into_view_if_needed()
                image.evaluate('image=>image.decode()')
            page.mouse.move(0, 0)
            page.locator('#works').screenshot(path=str(Path(output) / 'mobile.png'), style='.site-header, .skip-link { visibility: hidden !important; }')
            page.locator('[data-work-id="eagle-act-of-kindness"]').scroll_into_view_if_needed()
            page.screenshot(path=str(Path(output) / 'mobile-portrait.png'))


if __name__ == '__main__':
    unittest.main()
