"""Mobile playback: cards stay quiet, the dialog plays the phone-sized file."""
import os
import unittest
from playwright.sync_api import sync_playwright, expect

BASE = os.environ.get('STUDIO_BASE_URL', 'http://127.0.0.1:3000').rstrip('/')


class MobilePlayer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime = sync_playwright().start()
        cls.browser = cls.runtime.chromium.launch(channel='chrome', headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.runtime.stop()

    def page(self, motion):
        page = self.browser.new_page(viewport={'width': 390, 'height': 844}, is_mobile=True,
                                     has_touch=True, reduced_motion=motion)
        self.addCleanup(page.context.close)
        page.set_default_timeout(15000)
        page.goto(BASE + '/#works', wait_until='domcontentloaded')
        page.locator('.work-card').first.wait_for()
        return page

    def play(self, page, index):
        card = page.locator('.work-card').nth(index)
        card.scroll_into_view_if_needed()
        card.click()
        page.wait_for_function("() => { const video = document.querySelector('#workPlayerVideo');"
                               " return video.readyState >= 2 && !video.paused && video.currentTime > 0; }", timeout=15000)
        return page.locator('#workPlayerVideo').evaluate(
            "video => ({ src: video.currentSrc, readyState: video.readyState, networkState: video.networkState,"
            " paused: video.paused, error: video.error?.message, currentTime: video.currentTime })")

    def test_phone_previews_stay_scoped_to_the_visible_card(self):
        # Reduced motion is the data-saving switch: nothing streams on a phone.
        quiet = self.page('reduce').locator('.work-card video').evaluate_all(
            "videos => videos.filter(video => video.currentSrc).length")
        self.assertEqual(quiet, 0)
        # Otherwise only the card nearest the viewport centre previews, never all 20.
        playing = self.page('no-preference').locator('.work-card video').evaluate_all(
            "videos => videos.filter(video => video.currentSrc).length")
        self.assertLessEqual(playing, 1)

    def test_dialog_plays_and_closes_in_both_motion_modes(self):
        for motion in ('no-preference', 'reduce'):
            with self.subTest(motion=motion):
                page = self.page(motion)
                # Only the six cards of the current page are laid out.
                for index in (0, 3):
                    state = self.play(page, index)
                    # The dialog is opened with showModal(): there is no aria-hidden to assert.
                    self.assertTrue(page.locator('#workPlayer').evaluate('dialog => dialog.open'))
                    expect(page.locator('#workPlayerVideo')).to_be_visible()
                    self.assertGreaterEqual(state['readyState'], 2)
                    self.assertFalse(state['paused'])
                    self.assertGreater(state['currentTime'], 0)
                    self.assertIsNone(state['error'], state)
                    self.assertTrue(state['src'], state)
                    page.locator('#workPlayerClose').click()
                    expect(page.locator('#workPlayer')).to_have_js_property('open', False)


if __name__ == '__main__':
    unittest.main()
