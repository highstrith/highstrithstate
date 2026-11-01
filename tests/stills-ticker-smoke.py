"""Ticker Loop presents the eight real stills without changing the image viewer."""
import os
import unittest
from playwright.sync_api import sync_playwright, expect

BASE = os.environ.get('STUDIO_BASE_URL', 'http://127.0.0.1:3000').rstrip('/')


class StillsTicker(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime = sync_playwright().start()
        cls.browser = cls.runtime.chromium.launch(channel='chrome', headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.runtime.stop()

    def page(self, width=1440, motion='no-preference', random=None):
        page = self.browser.new_page(viewport={'width': width, 'height': 900}, reduced_motion=motion)
        self.addCleanup(page.context.close)
        if random is not None:
            page.add_init_script('Math.random=()=>'+str(random))
        page.goto(BASE + '/#stills', wait_until='load')
        expect(page.locator('#stillsGrid .still-card')).to_have_count(8)
        return page

    def test_three_tilted_rows_contain_all_eight_images_in_shuffled_order(self):
        orders = []
        for random in [.01, .99]:
            page = self.page(random=random)
            expect(page.locator('#stillsGrid .still-ticker-row')).to_have_count(3)
            order = page.locator('#stillsGrid .still-card [data-still]').evaluate_all('es=>es.map(e=>Number(e.dataset.still))')
            self.assertEqual(sorted(order), list(range(8)))
            orders.append(order)
            plane = page.locator('.still-ticker-plane')
            self.assertNotEqual(plane.evaluate('e=>getComputedStyle(e).transform'), 'none')
            page.locator('#langSwitch').click()
            expect(page.locator('#stillsGrid .still-ticker-row')).to_have_count(3)
            self.assertEqual(page.locator('#stillsGrid .still-card [data-still]').evaluate_all('es=>es.map(e=>Number(e.dataset.still))'), order)
            page.close()
        self.assertNotEqual(*orders)

    def test_moving_rows_pause_for_hover_and_explicit_control(self):
        page = self.page()
        stage = page.locator('#stillsGrid')
        stage.evaluate('e=>e.scrollIntoView({behavior:"instant",block:"center"})')
        page.mouse.move(5, 5)
        track = page.locator('.still-ticker-track').first
        before = track.evaluate('e=>getComputedStyle(e).transform')
        page.wait_for_timeout(250)
        self.assertNotEqual(before, track.evaluate('e=>getComputedStyle(e).transform'))
        stage.hover(position={'x': 100, 'y': 100})
        held = track.evaluate('e=>getComputedStyle(e).transform')
        page.wait_for_timeout(250)
        self.assertEqual(held, track.evaluate('e=>getComputedStyle(e).transform'))
        page.locator('#stillsTickerToggle').click()
        expect(page.locator('#stillsTickerToggle')).to_have_attribute('aria-pressed', 'true')
        page.locator('#langSwitch').click()
        expect(page.locator('#stillsTickerToggle')).to_have_attribute('aria-pressed', 'true')
        expect(page.locator('#stillsTickerToggle')).to_have_text('Resume motion')

    def test_original_and_repeated_cards_open_the_correct_existing_viewer(self):
        page = self.page()
        stage = page.locator('#stillsGrid')
        stage.evaluate('e=>e.scrollIntoView({behavior:"instant",block:"center"})')
        original = page.locator('[data-still="4"]')
        original.focus()
        page.keyboard.press('Enter')
        expect(page.locator('#stillViewerTitle')).to_have_text('酒馆光影')
        expect(page.locator('#stillViewerPosition')).to_have_text('05 / 08')
        page.keyboard.press('Escape')
        expect(original).to_be_focused()
        echo = page.locator('[data-ticker-echo="4"]').first
        echo.evaluate('e=>e.click()')
        expect(page.locator('#stillViewer')).to_be_visible()
        expect(page.locator('#stillViewerTitle')).to_have_text('酒馆光影')
        page.keyboard.press('ArrowRight')
        expect(page.locator('#stillViewerPosition')).to_have_text('06 / 08')
        page.keyboard.press('Escape')
        expect(original).to_be_focused()

    def test_mobile_themes_and_reduced_motion_have_no_horizontal_page_overflow(self):
        for width in [320, 390, 820, 1440]:
            page = self.page(width)
            for theme in ['light', 'dark']:
                if theme == 'dark': page.locator('#themeToggle').click()
                self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'), width)
            page.close()
        page = self.page(390, motion='reduce')
        expect(page.locator('.still-ticker-row')).to_have_count(0)
        expect(page.locator('[data-still]')).to_have_count(8)
        page.locator('[data-still="0"]').click()
        expect(page.locator('#stillViewerPosition')).to_have_text('01 / 08')

    def test_resize_and_motion_preference_keep_the_focused_image_reachable(self):
        page = self.page()
        image = page.locator('[data-still="7"]')
        image.focus()
        page.set_viewport_size({'width': 390, 'height': 900})
        expect(image).to_be_focused()
        page.emulate_media(reduced_motion='reduce')
        expect(page.locator('.still-ticker-row')).to_have_count(0)
        expect(image).to_be_focused()
        expect(image).to_be_in_viewport()
        page.keyboard.press('Enter')
        expect(page.locator('#stillViewerPosition')).to_have_text('08 / 08')

    def test_first_real_pointer_click_does_not_move_the_card_before_release(self):
        page = self.page()
        stage = page.locator('#stillsGrid')
        stage.evaluate('e=>e.scrollIntoView({behavior:"instant",block:"center"})')
        stage.hover(position={'x': 50, 'y': 50})
        image = page.locator('.still-ticker-row').first.locator('.still-card button').nth(2)
        index = int(image.get_attribute('data-still'))
        before = image.bounding_box()
        page.mouse.move(before['x'] + before['width'] / 2, before['y'] + before['height'] / 2)
        page.mouse.down()
        pressed = image.bounding_box()
        self.assertAlmostEqual(before['x'], pressed['x'], delta=2)
        self.assertAlmostEqual(before['y'], pressed['y'], delta=2)
        page.mouse.up()
        expect(page.locator('#stillViewer')).to_be_visible()
        expect(page.locator('#stillViewerPosition')).to_have_text(f'{index + 1:02} / 08')


if __name__ == '__main__':
    unittest.main()
