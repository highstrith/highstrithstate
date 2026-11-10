"""Media, contact and local management checks for the desktop exhibition."""
import os
import unittest
from playwright.sync_api import sync_playwright, expect

BASE = os.environ.get('STUDIO_BASE_URL', 'http://127.0.0.1:3000').rstrip('/')
# The hidden work never reaches the public grid, and the admin page also lists it.
import json as _catalogue_json
from pathlib import Path as _catalogue_path
_CATALOGUE_FOR_TESTS = _catalogue_json.loads((_catalogue_path(__file__).resolve().parents[1] / 'data/works.json').read_text())
_VISIBLE_FOR_TESTS = sorted((_w for _w in _CATALOGUE_FOR_TESTS if _w['id'] != 'featured-giant-wheel'), key=lambda _w: _w.get('createdAt', ''), reverse=True)
PUBLIC_WORKS = len(_VISIBLE_FOR_TESTS)
MANAGED_WORKS = len(_CATALOGUE_FOR_TESTS)
FIRST_WORK_ID = _VISIBLE_FOR_TESTS[0]['id']

class ExhibitionMedia(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime = sync_playwright().start()
        cls.browser = cls.runtime.chromium.launch(channel='chrome', headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.runtime.stop()

    def page(self, path='/'):
        page = self.browser.new_page(viewport={'width': 1440, 'height': 900})
        self.addCleanup(page.context.close)
        page.goto(BASE + path, wait_until='domcontentloaded')
        return page

    def test_visible_cards_stream_previews_without_missing_assets(self):
        page = self.page('/#works')
        missing = []
        page.on('response', lambda response: missing.append(response.url) if response.status == 404 and '/assets/' in response.url else None)
        expect(page.locator('.work-card').first).to_be_visible()
        page.wait_for_function("document.querySelector('.work-card img')?.naturalWidth > 0")
        page.wait_for_function("document.querySelector('.work-card video')?.currentTime > 0")
        # Cards play in the viewport only: twenty cards must not mean twenty downloads.
        loaded = page.evaluate("[...document.querySelectorAll('.work-card video')].filter(video => video.currentSrc).length")
        self.assertGreaterEqual(loaded, 1)
        self.assertLess(loaded, PUBLIC_WORKS)
        self.assertFalse(missing, missing)

    def test_section_jump_reaches_works_and_keeps_playback_scoped(self):
        page = self.page()
        # The chapter navigator is a <details>; its links only exist once opened.
        page.locator('#sectionJump > summary').click()
        page.locator('#sectionJump a[href="#works"]').click()
        page.wait_for_function("document.querySelector('#works').getBoundingClientRect().top < innerHeight")
        loaded = page.evaluate("[...document.querySelectorAll('.work-card video')].filter(video => video.currentSrc).length")
        self.assertLess(loaded, PUBLIC_WORKS)

    def test_contact_social_row_opens_the_wechat_qr_dialog(self):
        page = self.page()
        expect(page.locator('.social-links > *')).to_have_count(4)
        expect(page.locator('.social-links a[href="https://b23.tv/VFqS3Tj"]')).to_have_count(1)
        page.locator('button[data-qr-title="微信"]').click()
        expect(page.locator('#social-qr-dialog')).to_have_js_property('open', True)
        expect(page.locator('#social-qr-account')).to_have_text('Gw1sgdsj_787')

    def test_admin_lists_every_work_and_keeps_both_language_fields(self):
        page = self.page('/admin.html')
        page.wait_for_function(f"document.querySelectorAll('.manage-card').length === {MANAGED_WORKS}")
        self.assertEqual(page.locator('#uploadCnDescInput').count(), 1)
        self.assertEqual(page.locator('#uploadEnDescInput').count(), 1)


if __name__ == '__main__':
    unittest.main()
