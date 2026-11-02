"""Real browser regressions: full sources, parallel previews, and player recovery.

Run with serve.js on :3000. Only network failure and autoplay denial are injected;
media elements, rendering, keyboard handling and playback are real browser behavior.
"""
import json
import time
import unittest
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
CATALOG = json.loads((ROOT / "data/works.json").read_text())
PREVIEW = "assets/works/creative-3.mp4"
FULL = "assets/works/prove-it.mp4"
MOBILE = "assets/works/render-test.mp4"
FIXTURE = [dict(work, cnTitle="Fixture " + work["cnTitle"], previewVideo=PREVIEW, webVideo=FULL, mobileVideo=MOBILE) for work in CATALOG]
# The status line is empty and hidden once a film is actually playing; only the
# working / blocked / broken states carry a name.
PLAYING = ("document.querySelector('#workPlayerVideo').currentTime > 0"
           " && document.querySelector('#workPlayerStatus').hidden")


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

    def wait_for_css(self, page, expression, timeout=8000):
        """Poll from the driver: on a scriptless page requestAnimationFrame never runs,
        so wait_for_function would never make progress."""
        deadline = time.monotonic() + timeout / 1000
        while time.monotonic() < deadline:
            if page.evaluate(expression):
                return
            page.wait_for_timeout(120)
        self.fail("condition never became true: " + expression)

    def ready(self, page, expect_preview=True):
        page.goto("http://127.0.0.1:3000/#works", wait_until="domcontentloaded")
        # The fixture renames every work, so any rendered title proves the route won.
        page.wait_for_function("document.querySelector('.work-card .work-title')?.textContent.startsWith('Fixture ')")
        # Previews are set straight on the element now: the card in view streams the
        # preview file, never the full video.
        if expect_preview:
            page.wait_for_function("src => [...document.querySelectorAll('.work-card video')]"
                                   ".some(video => video.getAttribute('src')?.endsWith(src))", arg=PREVIEW)

    def test_only_current_desktop_work_previews_and_player_uses_full_source(self):
        page = self.page(viewport={"width": 1440, "height": 1500})
        requested = []
        page.on("request", lambda request: requested.append(request.url) if ".mp4" in request.url else None)
        self.ready(page)
        page.wait_for_function("document.querySelector('.work-card video[src]')?.currentTime > 0")
        self.assertEqual(page.locator(".work-card video[src]").count(), 1)
        self.assertTrue(all(url.endswith(PREVIEW) for url in requested), requested)
        page.locator(".work-card").first.click()
        page.wait_for_function("document.querySelector('#workPlayerVideo').currentSrc.endsWith('assets/works/prove-it.mp4')")
        self.assertTrue(page.locator(".work-card video").evaluate_all("vs => vs.every(v => v.paused)"))
        page.evaluate("window.dispatchEvent(new Event('scroll'))")
        self.assertTrue(page.locator(".work-card video").evaluate_all("vs => vs.every(v => v.paused)"))
        page.keyboard.press("Escape")
        page.wait_for_function("document.querySelector('.work-card video[src]')?.currentTime > 0")
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_function("[...document.querySelectorAll('.work-card video')].every(v => v.paused && v.readyState === 0 && !v.getAttribute('src'))")
        page.set_viewport_size({"width": 1440, "height": 1500})
        page.emulate_media(reduced_motion="reduce")
        page.wait_for_function("[...document.querySelectorAll('.work-card video')].every(v => v.paused && !v.getAttribute('src'))")
        page.locator(".work-card").first.click()
        page.wait_for_function("document.querySelector('#workPlayerVideo').currentTime > 0")

    def test_mobile_and_reduced_motion_manual_full_playback(self):
        for motion in ("no-preference", "reduce"):
            with self.subTest(motion=motion):
                page = self.page(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, reduced_motion=motion)
                requested = []
                page.on("request", lambda request: requested.append(request.url) if ".mp4" in request.url else None)
                self.ready(page, expect_preview=motion != "reduce")
                # A phone only streams the visible preview until a work is opened.
                self.assertTrue(all(url.endswith(PREVIEW) for url in requested), requested)
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
        page.wait_for_function("document.querySelector('.work-card .work-title')?.textContent.startsWith('Fixture ')")
        # Without a preview file the gallery must fall back to the poster silently.
        self.assertEqual(requested, [])
        page.locator(".work-card").first.click()
        page.wait_for_function("document.querySelector('#workPlayerVideo').currentTime > 0")

    def test_failed_full_video_can_retry_and_switch_without_stale_state(self):
        page = self.page(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
        blocked = {"value": True}
        page.route("**/" + MOBILE, lambda route: route.fulfill(status=404, body="missing") if blocked["value"] else route.continue_())
        self.ready(page)
        page.locator(".work-card").first.click()
        page.wait_for_function("document.querySelector('#workPlayerStatus').dataset.state === 'error'")
        self.assertTrue(page.locator("#workPlayerAction").is_visible())
        blocked["value"] = False
        page.locator("#workPlayerAction").click()
        page.wait_for_function("document.querySelector('#workPlayerVideo').currentTime > 0")
        page.keyboard.press("Escape")
        page.locator(".work-card").nth(1).click()
        page.keyboard.press("Escape")
        page.locator(".work-card").nth(2).click()
        page.wait_for_function(PLAYING)
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
        page.wait_for_function("document.querySelector('#workPlayerStatus').dataset.state === 'restricted'")
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
        # Buffering and loading are both "working on it" states for the visitor.
        self.assertIn(page.locator("#workPlayerStatus").get_attribute("data-state"), ("loading", "buffering"))
        self.assertTrue(page.locator("#workPlayerStatus").is_visible())
        page.wait_for_function("document.querySelector('#workPlayerStatus').dataset.state === 'slow'", timeout=20000)
        page.keyboard.press("Escape")
        # Closing tears the session down: no status text left behind for the next film.
        self.assertEqual(page.locator("#workPlayerStatus").get_attribute("data-state"), "")
        self.assertTrue(page.locator("#workPlayerStatus").is_hidden())
        self.assertTrue(page.locator("#workPlayerVideo").evaluate("v => v.paused && !v.getAttribute('src')"))
        blocked["value"] = False
        for route in pending:
            route.abort()
        page.locator(".work-card").nth(1).click()
        page.wait_for_function(PLAYING)

    def test_no_javascript_has_visible_content_and_all_work_links(self):
        page = self.page(viewport={"width": 390, "height": 844}, java_script_enabled=False)
        page.goto("http://127.0.0.1:3000/", wait_until="load")
        # Without scripts the fallback grid still has to be laid out by CSS, otherwise
        # the raw poster widths decide the page width.
        self.wait_for_css(page, "getComputedStyle(document.querySelector('noscript .works-grid')).display === 'grid'")
        # The hero reveal is a CSS animation: without scripts it must still finish.
        self.wait_for_css(page, "parseFloat(getComputedStyle(document.querySelector('#heroTitle')).opacity) > 0.99")
        self.assertGreaterEqual(float(page.locator("#heroTitle").evaluate("e => getComputedStyle(e).opacity")), 0.99)
        self.assertGreaterEqual(float(page.locator(".site-header").evaluate("e => getComputedStyle(e).opacity")), 0.99)
        self.assertEqual(page.locator(".no-js-work").count(), 20)
        self.assertTrue(page.locator(".no-js-work").first.get_attribute("href").endswith(".mp4"))
        self.assertFalse(page.evaluate("document.documentElement.scrollWidth > innerWidth"))


if __name__ == "__main__":
    unittest.main()
