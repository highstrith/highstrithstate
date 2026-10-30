"""Real hover/focus contrast, row isolation and touch fallbacks."""
import os
import unittest
from playwright.sync_api import sync_playwright, expect

BASE = os.environ.get('STUDIO_BASE_URL', 'http://127.0.0.1:3000')


class ContactRows(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime = sync_playwright().start()
        cls.browser = cls.runtime.chromium.launch(channel='chrome', headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.runtime.stop()

    def page(self, width=1440, touch=False, motion='no-preference'):
        page = self.browser.new_page(viewport={'width': width, 'height': 1000},
                                     has_touch=touch, is_mobile=touch, reduced_motion=motion)
        self.addCleanup(page.close)
        page.goto(BASE + '/#contact', wait_until='domcontentloaded')
        expect(page.locator('#contact .social-links > *')).to_have_count(4)
        page.locator('.social-row').scroll_into_view_if_needed()
        return page

    def colors(self, item):
        return item.evaluate('e => [getComputedStyle(e).backgroundColor, getComputedStyle(e).color]')

    def test_hover_inverts_whole_row_and_restores_without_layout_shift(self):
        page = self.page()
        links = page.locator('#contact .social-links > *')
        boxes = [item.bounding_box() for item in links.all()]
        self.assertTrue(all(b['width'] > 1000 for b in boxes))
        self.assertGreater(boxes[1]['y'], boxes[0]['y'])
        links.first.hover()
        page.wait_for_timeout(230)
        self.assertEqual(self.colors(links.first), ['rgb(23, 25, 24)', 'rgb(244, 244, 240)'])
        for selector in ['.social-name', '.social-hint']:
            self.assertEqual(links.first.locator(selector).evaluate('e => getComputedStyle(e).color'), 'rgb(244, 244, 240)')
        self.assertNotEqual(self.colors(links.nth(1))[0], 'rgb(23, 25, 24)')
        self.assertEqual(boxes[0], links.first.bounding_box())
        page.mouse.move(10, 100)
        page.wait_for_timeout(230)
        self.assertEqual(self.colors(links.first)[1], 'rgb(23, 25, 24)')

    def test_keyboard_and_email_copy_share_readable_active_state(self):
        page = self.page()
        # Use actual keyboard focus so mouse clicks do not leave a sticky row.
        page.locator('#copyEmail').focus()
        page.keyboard.press('Tab')
        page.keyboard.press('Shift+Tab')
        row = page.locator('.contact-email-group')
        self.assertAlmostEqual(row.bounding_box()['width'], page.locator('.social-links').bounding_box()['width'], delta=1)
        page.wait_for_timeout(230)
        self.assertEqual(self.colors(row)[0], 'rgb(23, 25, 24)')
        for selector in ['.contact-email', '.copy-email']:
            self.assertEqual(row.locator(selector).evaluate('e => getComputedStyle(e).color'), 'rgb(244, 244, 240)')
        expect(page.locator('.contact-email')).to_have_attribute('href', 'mailto:highstrith@gmail.com')
        expect(page.locator('.contact-details a')).to_have_attribute('href', 'tel:+8618020169750')

    def test_small_screens_bilingual_and_reduce_keep_rows_usable(self):
        for width in [320, 390, 820]:
            page = self.page(width, touch=True, motion='reduce')
            for language in ['cn', 'en']:
                if language == 'en': page.locator('#langSwitch').click()
                self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'), width)
                rows = page.locator('#contact .social-links > *')
                for row in rows.all():
                    self.assertGreaterEqual(row.bounding_box()['height'], 56)
                rows.first.click()
                expect(page.locator('#social-qr-dialog')).to_be_visible()
                page.locator('#socialQrClose').click()
                expect(rows.first).to_be_focused()


if __name__ == '__main__':
    unittest.main()
