"""Exercise the real published site against a separate CORS/Range media origin."""
import functools
import http.server
import json
import mimetypes
import os
from pathlib import Path
import re
import shlex
import subprocess
import tempfile
import threading
import unittest
from urllib.parse import unquote, urlsplit
from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]


class QuietFiles(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass


class MediaFiles(http.server.BaseHTTPRequestHandler):
    root = None

    def log_message(self, *_):
        pass

    def serve(self, body):
        relative = unquote(urlsplit(self.path).path).removeprefix('/media/')
        file = (self.root / relative).resolve()
        if not file.is_relative_to(self.root) or not file.is_file():
            self.send_error(404)
            return
        size = file.stat().st_size
        match = re.fullmatch(r'bytes=(\d+)-(\d*)', self.headers.get('Range', ''))
        start = int(match[1]) if match else 0
        end = min(size - 1, int(match[2])) if match and match[2] else size - 1
        if start > end:
            self.send_error(416)
            return
        self.send_response(206 if match else 200)
        self.send_header('Content-Type', mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
        self.send_header('Content-Length', str(end - start + 1))
        self.send_header('Accept-Ranges', 'bytes')
        self.send_header('Access-Control-Allow-Origin', '*')
        if match:
            self.send_header('Content-Range', f'bytes {start}-{end}/{size}')
        self.end_headers()
        if body:
            try:
                with file.open('rb') as stream:
                    stream.seek(start)
                    remaining = end - start + 1
                    while remaining:
                        chunk = stream.read(min(65536, remaining))
                        if not chunk:
                            break
                        self.wfile.write(chunk)
                        remaining -= len(chunk)
            except (BrokenPipeError, ConnectionResetError):
                pass

    def do_GET(self):
        self.serve(True)

    def do_HEAD(self):
        self.serve(False)


class MediaCdn(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='portfolio-cdn-browser-')
        root = Path(cls.temp.name)
        cls.site = root / 'pages' / 'highstrithstate'
        cls.media = root / 'media'
        workflow = (ROOT / '.github/workflows/pages.yml').read_text()
        block = re.search(r'      - name: Prepare site\n        run: \|\n((?:          [^\n]*(?:\n|$))*)', workflow)[1]
        script = re.sub(r'^ {10}', '', block, flags=re.M)
        script = re.sub(r'\bpublic\b', shlex.quote(str(cls.site)), script)
        subprocess.run(['/bin/bash', '-e', '-o', 'pipefail', '-c', script], cwd=ROOT, check=True)
        MediaFiles.root = cls.media.resolve()
        cls.cdn = http.server.ThreadingHTTPServer(('127.0.0.1', 0), MediaFiles)
        cls.cdn_url = f'http://127.0.0.1:{cls.cdn.server_port}/media/'
        subprocess.run(['node', str(ROOT / 'scripts/prepare-media-cdn.mjs'), '--site', str(cls.site),
                        '--media-dir', str(cls.media), '--base', cls.cdn_url], check=True)
        handler = functools.partial(QuietFiles, directory=str(root / 'pages'))
        cls.pages = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
        cls.base = f'http://127.0.0.1:{cls.pages.server_port}/highstrithstate/'
        for server in [cls.cdn, cls.pages]:
            threading.Thread(target=server.serve_forever, daemon=True).start()
        cls.runtime = sync_playwright().start()
        cls.browser = cls.runtime.chromium.launch(channel='chrome', headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.runtime.stop()
        cls.pages.shutdown()
        cls.cdn.shutdown()
        cls.temp.cleanup()

    def test_static_dynamic_posters_and_native_playback_use_cdn_but_code_stays_on_pages(self):
        page = self.browser.new_page(viewport={'width': 390, 'height': 1000}, is_mobile=True, has_touch=True)
        self.addCleanup(page.close)
        requests, errors = [], []
        page.on('request', lambda r: requests.append((r.resource_type, r.url)))
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.goto(self.base, wait_until='networkidle')
        expect(page.locator('#worksGrid .work-card')).to_have_count(20)
        page.wait_for_function('document.querySelector("#heroPreview").currentTime > 0')
        self.assertTrue(page.locator('#heroPoster').evaluate('i=>i.currentSrc').startswith(self.cdn_url))
        self.assertTrue(page.locator('#heroPreview').get_attribute('src').startswith(self.cdn_url))
        page.locator('#worksGrid .work-card:visible').first.click()
        page.wait_for_function('document.querySelector("#workPlayerVideo").currentTime > 0')
        self.assertTrue(page.locator('#workPlayerVideo').get_attribute('src').startswith(self.cdn_url))
        page.locator('#workPlayerClose').click()
        page.locator('#stillsGrid .still-media').first.click()
        page.wait_for_function('document.querySelector("#stillViewerImage").naturalWidth > 0')
        self.assertTrue(page.locator('#stillViewerImage').get_attribute('src').startswith(self.cdn_url))
        self.assertTrue(all(url.startswith(self.base) for kind, url in requests if kind in ['script', 'stylesheet']))
        self.assertTrue(all(url.startswith(self.cdn_url) for kind, url in requests if kind in ['image', 'media']))
        self.assertEqual(errors, [])

    def test_subpages_and_no_script_links_keep_working(self):
        page = self.browser.new_page(java_script_enabled=False)
        self.addCleanup(page.close)
        page.goto(self.base)
        self.assertTrue(page.locator('.no-js-work').first.get_attribute('href').startswith(self.cdn_url))
        page.goto(self.base + 'reel/')
        self.assertTrue(page.locator('img').first.get_attribute('src').startswith(self.cdn_url + 'reel/img/'))
        page.goto(self.base + 'projects.html')
        self.assertTrue(page.locator('img').first.get_attribute('src').startswith(self.cdn_url))
        page.goto(self.base + 'resume.html')
        pdf = page.locator('a[href*="lin-junjie-resume.pdf"]').first
        self.assertFalse(pdf.get_attribute('href').startswith(self.cdn_url))

    def test_catalogue_cannot_request_an_unconfigured_media_origin(self):
        page = self.browser.new_page()
        self.addCleanup(page.close)
        works = json.loads((self.site / 'data/works.json').read_text())
        for work in works:
            for field in ['poster', 'previewVideo', 'webVideo', 'mobileVideo', 'video']:
                work[field] = 'https://blocked.invalid/assets/untrusted.mp4'
        page.route('**/data/works.json', lambda route: route.fulfill(json=works))
        requested = []
        page.on('request', lambda request: requested.append(request.url))
        page.goto(self.base, wait_until='networkidle')
        expect(page.locator('#worksGrid .work-card')).to_have_count(20)
        page.locator('#worksGrid .work-card:visible').first.click()
        expect(page.locator('#workPlayer')).to_be_visible()
        self.assertFalse(page.locator('#workPlayerVideo').get_attribute('src'))
        self.assertFalse(any('blocked.invalid' in url for url in requested))


if __name__ == '__main__':
    unittest.main()
