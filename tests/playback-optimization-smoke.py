"""Real browser regressions: full sources, parallel previews, and player recovery.

Run with serve.js on :3000. Only network failure and autoplay denial are injected;
media elements, rendering, keyboard handling and playback are real browser behavior.
"""
import json
import unittest
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
CATALOG = json.loads((ROOT / "data/works.json").read_text())
PREVIEW = "assets/works/creative-3.mp4"
FULL = "assets/works/prove-it.mp4"
MOBILE = "assets/works/render-test.mp4"
FIXTURE = [dict(work, cnTitle="Fixture " + work["cnTitle"], previewVideo=PREVIEW, webVideo=FULL, mobileVideo=MOBILE) for work in CATALOG]


class PlaybackOptimization(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime = sync_playwright().start()
        cls.browser = cls.runtime.chromium.launch(channel="chrome", headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.runtime.stop()

    def page(self, **options):
        page = self.browser.new_page(**options)
        page.set_default_timeout(12000)
        self.addCleanup(page.close)
        page.route("**/api/works", lambda route: route.fulfill(json={"works": FIXTURE}))
        return page

    def ready(self, page):
        page.goto("http://127.0.0.1:3000/#works", wait_until="domcontentloaded")
        page.wait_for_function("document.querySelector('.work-card h3')?.textContent === 'Fixture AI患者'")
        self.assertEqual(page.locator(".work-card source").first.get_attribute("data-src"), PREVIEW, 'gallery must load the preview instead of the original')

    def test_all_visible_desktop_previews_use_preview_source(self):
        page = self.page(viewport={"width": 1440, "height": 1500})
        requested = []
        page.on("request", lambda request: requested.append(request.url) if ".mp4" in request.url else None)
        self.ready(page)
        page.locator("#works").scroll_into_view_if_needed()
        page.wait_for_function("[...document.querySelectorAll('.work-video')].length === 8 && [...document.querySelectorAll('.work-video')].every(v => !v.paused && v.currentTime > 0)")
        self.assertTrue(all(url.endswith(PREVIEW) for url in requested), requested)
        page.locator(".work-card").first.click()
        page.wait_for_function("document.querySelector('#workPlayerVideo').currentSrc.endsWith('assets/works/prove-it.mp4')")
        self.assertTrue(page.locator(".work-video").evaluate_all("vs => vs.every(v => v.paused)"))
        page.evaluate("window.dispatchEvent(new Event('scroll'))")
        self.assertTrue(page.locator(".work-video").evaluate_all("vs => vs.every(v => v.paused)"))
        page.keyboard.press("Escape")
        page.wait_for_function("[...document.querySelectorAll('.work-video')].every(v => !v.paused)")
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_function("[...document.querySelectorAll('.work-video')].every(v => v.paused && v.readyState === 0 && !v.querySelector('source').getAttribute('src'))")
        page.set_viewport_size({"width": 1440, "height": 1500})
        page.emulate_media(reduced_motion="reduce")
        page.wait_for_function("[...document.querySelectorAll('.work-video')].every(v => v.paused && !v.querySelector('source').getAttribute('src'))")
        page.locator(".work-card").first.click()
        page.wait_for_function("document.querySelector('#workPlayerVideo').currentTime > 0")

    def test_mobile_and_reduced_motion_manual_full_playback(self):
        for motion in ("no-preference", "reduce"):
            with self.subTest(motion=motion):
                page = self.page(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, reduced_motion=motion)
                requested = []
                page.on("request", lambda request: requested.append(request.url) if ".mp4" in request.url else None)
                self.ready(page)
                self.assertEqual(requested, [])
                page.locator(".work-card").first.click()
                page.wait_for_function("document.querySelector('#workPlayerVideo').currentSrc.endsWith('assets/works/render-test.mp4') && document.querySelector('#workPlayerVideo').currentTime > 0")
                self.assertFalse(page.locator("#workPlayerVideo").evaluate("v => v.paused"))
                page.keyboard.press("Escape")
                self.assertTrue(page.locator(".work-card").first.evaluate("e => e === document.activeElement"))

    def test_missing_preview_stays_on_poster_and_manual_still_works(self):
        page = self.page(viewport={"width": 1440, "height": 900})
        page.route("**/api/works", lambda route: route.fulfill(json={"works": [dict(w, previewVideo="") for w in FIXTURE]}))
        requested = []
        page.on("request", lambda request: requested.append(request.url) if ".mp4" in request.url else None)
        page.goto("http://127.0.0.1:3000/#works", wait_until="domcontentloaded")
        page.wait_for_function("document.querySelector('.work-card source')?.dataset.src === ''")
        self.assertEqual(requested, [])
        page.locator(".work-card").first.click()
        page.wait_for_function("document.querySelector('#workPlayerVideo').currentTime > 0")

    def test_failed_full_video_can_retry_and_switch_without_stale_state(self):
        page = self.page(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
        blocked = {"value": True}
        page.route("**/" + MOBILE, lambda route: route.fulfill(status=404, body="missing") if blocked["value"] else route.continue_())
        self.ready(page)
        page.locator(".work-card").first.click()
        page.wait_for_function("document.querySelector('#workPlayer').dataset.state === 'error'")
        self.assertTrue(page.locator("#workPlayerAction").is_visible())
        blocked["value"] = False
        page.locator("#workPlayerAction").click()
        page.wait_for_function("document.querySelector('#workPlayerVideo').currentTime > 0")
        page.keyboard.press("Escape")
        page.locator(".work-card").nth(1).click()
        page.keyboard.press("Escape")
        page.locator(".work-card").nth(2).click()
        page.wait_for_function("document.querySelector('#workPlayerVideo').currentTime > 0 && document.querySelector('#workPlayer').dataset.state === 'ready'")
        page.keyboard.press("Escape")
        self.assertTrue(page.locator(".work-card").nth(2).evaluate("e => e === document.activeElement"))

    def test_autoplay_denial_offers_user_play(self):
        page = self.page(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
        page.add_init_script("""const nativePlay = HTMLMediaElement.prototype.play;
          let blocked = true;
          HTMLMediaElement.prototype.play = function() {
            if (this.id === 'workPlayerVideo' && blocked) { blocked = false; return Promise.reject(new DOMException('Blocked', 'NotAllowedError')); }
            return nativePlay.call(this);
          };""")
        self.ready(page)
        page.locator(".work-card").first.click()
        page.wait_for_function("document.querySelector('#workPlayer').dataset.state === 'needs-play'")
        page.locator("#workPlayerAction").click()
        page.wait_for_function("document.querySelector('#workPlayerVideo').currentTime > 0")

    def test_slow_loading_is_visible_and_close_clears_its_session(self):
        page = self.page(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
        blocked = {"value": True}
        pending = []
        def handle(route):
            if blocked["value"]:
                pending.append(route)
            else:
                route.continue_()
        page.route("**/" + MOBILE, handle)
        self.ready(page)
        page.locator(".work-card").first.click()
        self.assertEqual(page.locator("#workPlayer").get_attribute("data-state"), "loading")
        self.assertTrue(page.locator("#workPlayerStatus").is_visible())
        page.wait_for_function("document.querySelector('#workPlayer').dataset.state === 'slow'", timeout=20000)
        page.keyboard.press("Escape")
        self.assertEqual(page.locator("#workPlayer").get_attribute("data-state"), "idle")
        blocked["value"] = False
        for route in pending:
            route.abort()
        page.locator(".work-card").nth(1).click()
        page.wait_for_function("document.querySelector('#workPlayerVideo').currentTime > 0 && document.querySelector('#workPlayer').dataset.state === 'ready'")

    def test_no_javascript_has_visible_content_and_all_work_links(self):
        page = self.page(viewport={"width": 390, "height": 844}, java_script_enabled=False)
        page.goto("http://127.0.0.1:3000/", wait_until="domcontentloaded")
        self.assertEqual(page.locator(".hero-copy").evaluate("e => getComputedStyle(e).opacity"), "1")
        self.assertEqual(page.locator(".topbar").evaluate("e => getComputedStyle(e).opacity"), "1")
        self.assertEqual(page.locator(".no-js-work").count(), 13)
        self.assertTrue(page.locator(".no-js-work").first.get_attribute("href").endswith(".mp4"))
        self.assertFalse(page.evaluate("document.documentElement.scrollWidth > innerWidth"))


if __name__ == "__main__":
    unittest.main()
