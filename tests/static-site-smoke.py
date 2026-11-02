"""Exercise the published Pages file set without serve.js or the works API."""
import functools
import http.server
import json
import shutil
import tempfile
import threading
import unittest
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
CATALOG = json.loads((ROOT / 'data/works.json').read_text())
# The fallback is sorted by creation date and drops the hidden work.
VISIBLE = sorted((work for work in CATALOG if work['id'] != 'featured-giant-wheel'),
                 key=lambda work: work.get('createdAt') or '', reverse=True)


class QuietStaticHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def copyfile(self, source, outputfile):
        try:
            super().copyfile(source, outputfile)
        except (BrokenPipeError, ConnectionResetError):
            # A browser legitimately cancels a preview when the modal opens.
            pass


class StaticPagesFiles(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory(prefix='portfolio-static-')
        public = Path(cls.directory.name)
        shutil.copy(ROOT / 'index.html', public / 'index.html')
        shutil.copytree(ROOT / 'data', public / 'data')
        (public / 'assets').symlink_to(ROOT / 'assets', target_is_directory=True)
        cls.server = http.server.ThreadingHTTPServer(
            ('127.0.0.1', 0), functools.partial(QuietStaticHandler, directory=cls.directory.name))
        thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        thread.start()
        cls.thread = thread
        cls.address = f'http://127.0.0.1:{cls.server.server_port}'
        cls.runtime = sync_playwright().start()
        cls.browser = cls.runtime.chromium.launch(channel='chrome', headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.runtime.stop()
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()
        cls.directory.cleanup()

    def page(self, **options):
        page = self.browser.new_page(**options)
        self.addCleanup(page.context.close)
        return page

    def test_desktop_streams_previews_until_a_work_is_opened(self):
        page = self.page(viewport={'width': 1440, 'height': 1100})
        media = []
        missing = []
        page.on('request', lambda request: media.append(request.url) if '.mp4' in request.url else None)
        page.on('response', lambda response: missing.append(response.url) if response.status == 404 and '/assets/' in response.url else None)
        page.goto(self.address + '/#works', wait_until='domcontentloaded')
        page.wait_for_function("document.querySelector('.work-card video')?.currentTime > 0")
        self.assertTrue(media, 'the grid should preview at least one work')
        self.assertTrue(all(url.endswith('-preview.mp4') for url in media), media)
        page.locator('.work-card').first.click()
        page.wait_for_function("document.querySelector('#workPlayerVideo').currentTime > 0")
        # The attribute resolves against the page, so compare by suffix.
        self.assertTrue(page.locator('#workPlayerVideo').get_attribute('src').endswith(VISIBLE[0]['webVideo']))
        page.keyboard.press('Escape')
        page.locator('#langSwitch').click()
        expect(page.locator('#worksTitle')).to_have_text('All works')
        self.assertFalse(missing, missing)

    def test_phones_load_nothing_until_a_work_is_opened(self):
        for motion in ('no-preference', 'reduce'):
            with self.subTest(motion=motion):
                page = self.page(viewport={'width': 390, 'height': 844}, is_mobile=True,
                                 has_touch=True, reduced_motion=motion)
                requests = []
                page.on('request', lambda request: requests.append(request.url) if '.mp4' in request.url else None)
                page.goto(self.address + '/#works', wait_until='domcontentloaded')
                page.locator('.work-card').first.wait_for()
                page.wait_for_timeout(500)
                self.assertEqual([url for url in requests if not url.endswith('-preview.mp4')], [])
                page.locator('.work-card').first.click()
                page.wait_for_function("document.querySelector('#workPlayerVideo').currentTime > 0")
                self.assertTrue(page.locator('#workPlayerVideo').get_attribute('src').endswith(VISIBLE[0]['mobileVideo']))

    def test_without_javascript_every_public_work_is_still_linked(self):
        page = self.page(viewport={'width': 390, 'height': 844}, java_script_enabled=False)
        page.goto(self.address, wait_until='domcontentloaded')
        expect(page.locator('.no-js-work')).to_have_count(len(VISIBLE))
        for index, work in enumerate(VISIBLE):
            self.assertEqual(page.locator('.no-js-work').nth(index).get_attribute('href'),
                             work['webVideo'] or work['video'])


if __name__ == '__main__':
    unittest.main()
