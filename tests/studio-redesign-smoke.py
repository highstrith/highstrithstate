"""Real browser contracts for the studio redesign.

Run: python3 tests/studio-redesign-smoke.py -v
The public site must be running on STUDIO_BASE_URL (default :3000).
The admin test copies serve.js/admin.html into a disposable directory and never
writes the real catalogue or uploads. Network interception is limited to the
static-host simulation and an intentional full-video failure for retry coverage.
"""
import json
import os
import re
import shutil
import socket
import subprocess
import tempfile
import time
import unittest
from contextlib import contextmanager
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlsplit
from urllib.request import urlopen

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BASE = os.environ.get("STUDIO_BASE_URL", "http://127.0.0.1:3000").rstrip("/")
CATALOG = json.loads((ROOT / "data/works.json").read_text())
CARDS = "#worksGrid .work-card"
SOURCE_COUNT = """videos => videos.filter(v => v.getAttribute('src') ||
    [...v.querySelectorAll('source')].some(s => s.getAttribute('src'))).length"""


@contextmanager
def disposable_admin():
    """Exercise the production server and admin UI on isolated real files."""
    with tempfile.TemporaryDirectory(prefix="studio-admin-") as directory:
        root = Path(directory)
        for name in ("serve.js", "admin.html"):
            shutil.copy2(ROOT / name, root / name)
        (root / "data").mkdir()
        (root / "data/works.json").write_text("[]\n")
        fixture = next(w for w in CATALOG if w["id"] == "added-render-test")
        shutil.copy2(ROOT / (fixture.get("previewVideo") or fixture["video"]), root / "input.mp4")
        shutil.copy2(ROOT / fixture["poster"], root / "input.jpg")
        with socket.socket() as reservation:
            reservation.bind(("127.0.0.1", 0))
            port = reservation.getsockname()[1]
        address = "http://127.0.0.1:%s" % port
        with (root / "server.log").open("w+") as log:
            process = subprocess.Popen(
                [shutil.which("node") or "node", "serve.js"], cwd=root,
                env=dict(os.environ, PORT=str(port)), stdout=log, stderr=log,
            )
            try:
                deadline = time.monotonic() + 8
                while True:
                    try:
                        with urlopen(address + "/api/works", timeout=1) as response:
                            if response.status == 200:
                                break
                    except (URLError, TimeoutError):
                        pass
                    if process.poll() is not None or time.monotonic() > deadline:
                        log.seek(0)
                        raise AssertionError("Temporary admin server did not start: " + log.read())
                    time.sleep(0.03)
                yield root, address
            finally:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)


class StudioRedesign(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime = sync_playwright().start()
        try:
            cls.browser = cls.runtime.chromium.launch(channel="chrome", headless=True)
        except Exception:
            cls.runtime.stop()
            raise

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.runtime.stop()

    def page(self, **options):
        page = self.browser.new_page(**options)
        page.set_default_timeout(8000)
        self.addCleanup(page.close)
        return page

    def ready(self, page, url=None):
        page.goto(url or BASE + "/", wait_until="domcontentloaded")
        expect(page.locator(CARDS)).to_have_count(14)

    def assert_count(self, page, count):
        expect(page.locator(CARDS + ":visible")).to_have_count(count)
        self.assertIn(page.locator("#worksCount").get_attribute("aria-live"), ("polite", "assertive"))
        expect(page.locator("#worksCount")).to_contain_text(re.compile(r"(?<!\d)%s(?!\d)" % count))

    def assert_playing(self, page, source):
        page.wait_for_function("""suffix => {
          const v = document.querySelector('#workPlayerVideo');
          return v && v.currentSrc.endsWith(suffix) && v.currentTime > 0 && !v.paused;
        }""", arg=source)

    def assert_closed_with_focus(self, page, target):
        expect(page.locator("#workPlayer")).not_to_be_visible()
        expect(target).to_be_focused()
        self.assertEqual(page.locator("#workPlayerVideo").evaluate_all(SOURCE_COUNT), 0)

    def test_filters_search_and_language_keep_all_works_reachable(self):
        page = self.page(viewport={"width": 1440, "height": 900})
        self.ready(page)
        self.assert_count(page, 14)
        self.assertTrue(page.locator(CARDS).evaluate_all("cards => cards.every(c => c.tagName === 'BUTTON')"))
        expect(page.locator("#workSearch")).to_have_attribute("type", "search")
        for category in ("story", "motion", "edit"):
            with self.subTest(category=category):
                page.locator("#workFilters [data-filter='%s']" % category).click()
                page.wait_for_function("""selector => {
                  const cards = [...document.querySelectorAll(selector)].filter(c => c.getClientRects().length);
                  return cards.length > 0 && cards.length < 14;
                }""", arg=CARDS)
                self.assert_count(page, page.locator(CARDS + ":visible").count())
        page.locator("#workFilters [data-filter='all']").click()
        self.assert_count(page, 14)
        page.locator("#workSearch").fill("趴着办公早该知道")
        self.assert_count(page, 1)
        expect(page.locator(CARDS + ":visible")).to_contain_text("趴着办公早该知道")
        page.locator("#workSearch").fill("does-not-exist-unique-query")
        self.assert_count(page, 0)
        page.locator("#workSearch").fill("")
        self.assert_count(page, 14)
        page.locator("#langSwitch").click()
        expect(page.locator("html")).to_have_attribute("lang", "en")
        expect(page.locator(CARDS).first).to_contain_text(CATALOG[0]["enTitle"])
        page.locator("#workSearch").fill(CATALOG[0]["enTitle"])
        self.assert_count(page, 1)

    def test_desktop_cards_preview_only_on_hover_or_focus(self):
        page = self.page(viewport={"width": 1440, "height": 1000})
        self.ready(page)
        self.assertEqual(page.locator(CARDS + " video").evaluate_all(SOURCE_COUNT), 0)
        first, second = page.locator(CARDS).nth(0), page.locator(CARDS).nth(1)
        first.hover()
        page.wait_for_function("""suffix => [...document.querySelectorAll('#worksGrid video')]
          .some(v => v.currentSrc.endsWith(suffix) && v.currentTime > 0 && !v.paused)""", arg=CATALOG[0]["previewVideo"])
        self.assertLessEqual(page.locator(CARDS + " video").evaluate_all(SOURCE_COUNT), 1)
        second.hover()
        page.wait_for_function("""suffix => [...document.querySelectorAll('#worksGrid video')]
          .some(v => v.currentSrc.endsWith(suffix) && v.currentTime > 0 && !v.paused)""", arg=CATALOG[1]["previewVideo"])
        self.assertLessEqual(page.locator(CARDS + " video").evaluate_all(SOURCE_COUNT), 1)
        page.mouse.move(0, 0)
        first.focus()
        page.wait_for_function("""suffix => [...document.querySelectorAll('#worksGrid video')]
          .some(v => v.currentSrc.endsWith(suffix) && !v.paused)""", arg=CATALOG[0]["previewVideo"])
        self.assertLessEqual(page.locator(CARDS + " video").evaluate_all(SOURCE_COUNT), 1)

    def test_desktop_player_uses_full_media_and_returns_keyboard_focus(self):
        page = self.page(viewport={"width": 1440, "height": 900})
        self.ready(page)
        card = page.locator(CARDS).first
        card.focus()
        card.press("Enter")
        expect(page.locator("dialog#workPlayer")).to_be_visible()
        self.assert_playing(page, CATALOG[0]["webVideo"] or CATALOG[0]["video"])
        self.assertTrue(page.locator("video:not(#workPlayerVideo)").evaluate_all("vs => vs.every(v => v.paused)"))
        page.keyboard.press("Escape")
        self.assert_closed_with_focus(page, card)
        card.press("Space")
        self.assert_playing(page, CATALOG[0]["webVideo"] or CATALOG[0]["video"])
        page.locator("#workPlayerClose").click()
        self.assert_closed_with_focus(page, card)

    def test_hero_preview_pauses_for_player_and_reduced_motion(self):
        page = self.page(viewport={"width": 1440, "height": 900})
        self.ready(page)
        page.wait_for_function("document.querySelector('#heroPreview')?.currentTime > 0")
        hero_button = page.locator("[data-hero-play]").first
        hero_button.click()
        expect(page.locator("#workPlayer")).to_be_visible()
        page.wait_for_function("document.querySelector('#heroPreview').paused")
        page.locator("#workPlayerClose").click()
        expect(hero_button).to_be_focused()
        page.emulate_media(reduced_motion="reduce")
        page.wait_for_function("document.querySelector('#heroPreview').paused")
        hero_button.click()
        page.wait_for_function("document.querySelector('#workPlayerVideo').currentTime > 0")

    def test_mobile_and_reduced_motion_do_not_load_preview_video(self):
        for motion in ("no-preference", "reduce"):
            with self.subTest(motion=motion):
                page = self.page(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, reduced_motion=motion)
                requests = []
                page.on("request", lambda request: requests.append(request.url) if ".mp4" in request.url else None)
                self.ready(page)
                page.locator(CARDS).last.scroll_into_view_if_needed()
                # A short observation window detects delayed eager video requests.
                page.wait_for_timeout(250)
                self.assertEqual(requests, [])
                self.assertEqual(page.locator("video").evaluate_all(SOURCE_COUNT), 0)
                card = page.locator(CARDS).first
                card.click()
                self.assert_playing(page, CATALOG[0]["mobileVideo"])
                self.assertTrue(all(url.endswith(CATALOG[0]["mobileVideo"]) for url in requests), requests)
                page.locator("#workPlayerClose").click()
                self.assert_closed_with_focus(page, card)

    def test_failed_full_video_retries_same_full_source(self):
        page = self.page(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
        blocked = {"value": True}
        source = CATALOG[0]["mobileVideo"]
        page.route("**/" + source, lambda route: route.fulfill(status=404, body="missing") if blocked["value"] else route.continue_())
        self.ready(page)
        page.locator(CARDS).first.click()
        expect(page.locator("#workPlayerStatus")).to_be_visible()
        expect(page.locator("#workPlayerAction")).to_be_visible()
        blocked["value"] = False
        page.locator("#workPlayerAction").click()
        self.assert_playing(page, source)
        page.locator("#workPlayerClose").click()
        page.locator(CARDS).nth(1).click()
        page.locator("#workPlayerClose").click()
        page.locator(CARDS).nth(2).click()
        self.assert_playing(page, CATALOG[2]["mobileVideo"])

    def test_layout_and_contacts_at_supported_widths(self):
        for width in (320, 390, 820, 1440, 1920):
            with self.subTest(width=width):
                page = self.page(viewport={"width": width, "height": 900}, reduced_motion="reduce")
                self.ready(page)
                for language in ("cn", "en"):
                    with self.subTest(language=language):
                        if language == "en":
                            page.locator("#langSwitch").click()
                        page.locator(CARDS).last.scroll_into_view_if_needed()
                        self.assertLessEqual(page.evaluate("document.documentElement.scrollWidth"), width + 1)
                        expect(page.locator("#workSearch")).to_be_visible()
                        expect(page.locator("#adminEntryLink")).to_be_visible()
                self.assertEqual(page.locator("[data-qr-image]").count(), 3)
                self.assertEqual(page.locator('a[href="https://b23.tv/VFqS3Tj"]').count(), 1)
                qr = page.locator("[data-qr-image]").first
                qr.click()
                expect(page.locator("#social-qr-dialog")).to_be_visible()
                image = page.locator("#social-qr-dialog img")
                expect(image).to_be_visible()
                self.assertTrue(image.evaluate("img => img.complete && img.naturalWidth > 0"))
                page.keyboard.press("Escape")
                expect(qr).to_be_focused()
                page.close()

    def test_static_subpath_and_no_script_keep_catalogue_available(self):
        public = "https://studio.example/portfolio/"
        page = self.page(viewport={"width": 1440, "height": 900})
        api_requests = []

        def static_route(route):
            path = urlsplit(route.request.url).path
            if path.startswith("/api/"):
                api_requests.append(path)
                route.fulfill(status=404, body="Static hosting has no API")
            else:
                relative = path.removeprefix("/portfolio/")
                route.fulfill(response=route.fetch(url=BASE + "/" + relative))

        page.route("https://studio.example/**", static_route)
        self.ready(page, public)
        expect(page.locator("#adminEntryLink")).not_to_be_visible()
        self.assertEqual(api_requests, [])
        page.locator(CARDS).first.click()
        self.assert_playing(page, CATALOG[0]["webVideo"] or CATALOG[0]["video"])
        nojs = self.page(viewport={"width": 390, "height": 844}, java_script_enabled=False)
        nojs.route("https://studio.example/**", static_route)
        nojs.goto(public, wait_until="domcontentloaded")
        expect(nojs.locator(".no-js-work")).to_have_count(14)
        expect(nojs.locator(".no-js-work").first).to_be_visible()
        for index, work in enumerate(CATALOG):
            link = nojs.locator(".no-js-work").nth(index)
            self.assertEqual(link.get_attribute("href"), work["webVideo"] or work["video"])
        self.assertLessEqual(nojs.evaluate("document.documentElement.scrollWidth"), 391)

    def test_admin_upload_edit_preview_and_delete_in_isolated_directory(self):
        with disposable_admin() as (root, address):
            page = self.page(viewport={"width": 1440, "height": 1000})
            page.goto(address + "/admin.html", wait_until="domcontentloaded")
            expect(page.locator("#heroWorkCount")).to_have_text("0")
            page.locator("#uploadCnTitleInput").fill("浏览器上传回归")
            page.locator("#uploadEnTitleInput").fill("Browser upload regression")
            page.locator("#uploadCnSubInput").fill("测试 / 影像")
            page.locator("#uploadEnSubInput").fill("TEST / FILM")
            page.locator("#uploadCnDescInput").fill("完整上传和持久化测试")
            page.locator("#uploadEnDescInput").fill("Real upload and persistence check")
            page.locator("#uploadVideoInput").set_input_files(str(root / "input.mp4"))
            page.locator("#uploadPosterInput").set_input_files(str(root / "input.jpg"))
            page.locator("#uploadSubmit").click()
            expect(page.locator(".manage-card")).to_have_count(1)
            expect(page.locator("#uploadStatus")).to_have_attribute("data-tone", "success")
            stored = json.loads((root / "data/works.json").read_text())[0]
            self.assertEqual((root / stored["video"]).read_bytes(), (root / "input.mp4").read_bytes())
            self.assertEqual((root / stored["poster"]).read_bytes(), (root / "input.jpg").read_bytes())
            self.assertEqual(stored["enDesc"], "Real upload and persistence check")
            page.reload(wait_until="domcontentloaded")
            expect(page.locator(".manage-card")).to_contain_text("浏览器上传回归")
            page.locator("[data-view-work]").click()
            page.wait_for_function("document.querySelector('#manageVideoPlayer').currentTime > 0")
            page.locator("#manageVideoClose").click()
            page.locator("[data-edit-work]").click()
            page.locator("#uploadCnTitleInput").fill("修改后的作品")
            page.locator("#uploadSubmit").click()
            expect(page.locator(".manage-card")).to_contain_text("修改后的作品")
            updated = json.loads((root / "data/works.json").read_text())[0]
            self.assertEqual(updated["id"], stored["id"])
            self.assertEqual(updated["video"], stored["video"])
            self.assertEqual(updated["poster"], stored["poster"])
            page.once("dialog", lambda dialog: dialog.accept())
            page.locator("[data-delete-work]").click()
            expect(page.locator(".manage-card")).to_have_count(0)
            self.assertEqual(json.loads((root / "data/works.json").read_text()), [])
            self.assertFalse((root / stored["video"]).exists())
            self.assertFalse((root / stored["poster"]).exists())
            page.close()


if __name__ == "__main__":
    unittest.main()
