"""Real browser contracts for per-work comments.

Run: python3 -u tests/comments-smoke.py -v
The public site must be running on STUDIO_BASE_URL (default :3000).

Comments are only reachable when STUDIO_COMMENT_CONFIG.envId is filled in, so the
default build has to stay byte-identical in behaviour: no comment entry, no request
to the comment CDN. Network interception supplies a filled-in config and a stub
comment widget so the catalogue, the accordion and the failure path can be
exercised without a live CloudBase environment.
"""
import json
import os
import unittest

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.environ.get("STUDIO_BASE_URL", "http://127.0.0.1:3000").rstrip("/")
CATALOG = json.loads(open(os.path.join(ROOT, "data/works.json"), encoding="utf-8").read())
HIDDEN_IDS = {"featured-giant-wheel"}
VISIBLE = [work for work in CATALOG if work["id"] not in HIDDEN_IDS]

CONFIG_ROUTE = "**/assets/comment-config.js*"
WIDGET_ROUTE = "**/twikoo.all.min.js*"
TOGGLE = "#worksGrid .comment-toggle"
PANEL = "#worksGrid .comment-panel"

ENABLED_CONFIG = """window.STUDIO_COMMENT_CONFIG = {
  envId: 'env-testcomments',
  region: 'ap-shanghai',
  funcName: 'twikoo',
  version: '2.0.13',
};
"""

STUB_WIDGET = """window.__twikooInit = window.__twikooInit || [];
window.__twikooCounts = window.__twikooCounts || [];
window.twikoo = {
  init: function (options) {
    window.__twikooInit.push(options);
    var host = document.querySelector(options.el || '#twikoo');
    if (host) host.innerHTML = '<div class="twikoo"><div class="tk-comments">stub</div></div>';
    return Promise.resolve();
  },
  getCommentsCount: function (options) {
    window.__twikooCounts.push(options.urls.slice());
    return Promise.resolve(options.urls.map(function (url) { return { url: url, count: 3 }; }));
  },
};
"""


def open_studio(browser, config=None, widget=None):
    """Open the public catalogue with an optional config or widget override."""
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    if config is not None:
        page.route(CONFIG_ROUTE, lambda route: route.fulfill(
            status=200, content_type="application/javascript; charset=utf-8", body=config))
    if widget is not None:
        page.route(WIDGET_ROUTE, lambda route: route.fulfill(
            status=200, content_type="application/javascript; charset=utf-8", body=widget)
            if widget else route.abort())
    return page


class CommentsDisabledByDefault(unittest.TestCase):
    def test_catalogue_has_no_comment_entry_without_configuration(self):
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            widget_requests = []
            page = open_studio(browser)
            page.on("request", lambda request: widget_requests.append(request.url)
                    if "twikoo.all.min.js" in request.url else None)
            page.goto(BASE + "/", wait_until="load")
            page.wait_for_selector("#worksGrid .work-card")
            page.wait_for_timeout(2500)

            self.assertEqual(len(VISIBLE), page.locator("#worksGrid .work-card").count())
            self.assertEqual(0, page.locator(TOGGLE).count(),
                             "comment entries must stay hidden until an environment is configured")
            self.assertEqual([], widget_requests, "the comment widget must not load before it is used")
            browser.close()


class CommentsEnabled(unittest.TestCase):
    def test_entry_shows_the_counted_comments_and_opens_on_demand(self):
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = open_studio(browser, config=ENABLED_CONFIG, widget=STUB_WIDGET)
            page.goto(BASE + "/", wait_until="load")
            page.wait_for_selector(TOGGLE)
            page.wait_for_function("document.querySelectorAll('.comment-toggle-count').length > 0"
                                   " && [...document.querySelectorAll('.comment-toggle-count')]"
                                   ".every(node => node.textContent.trim() === '3')")

            toggle = page.locator(TOGGLE).first
            self.assertEqual("3", toggle.locator(".comment-toggle-count").inner_text())
            self.assertEqual(0, page.evaluate("document.querySelectorAll('#worksGrid #twikoo').length"),
                             "no thread is mounted before the visitor asks for one")

            toggle.click()
            page.wait_for_selector(PANEL + ".is-open")
            self.assertEqual("true", toggle.get_attribute("aria-expanded"))
            self.assertIn("tk-comments", page.locator(PANEL + ".is-open").inner_html())

            inits = page.evaluate("window.__twikooInit.map(entry => entry.urls)")
            self.assertEqual([["/works/%s" % VISIBLE[0]["id"]]], inits,
                             "each work must open its own stable comment thread")
            self.assertEqual(1, page.evaluate("document.querySelectorAll('#worksGrid #twikoo').length"))
            browser.close()

    def test_opening_another_work_moves_the_single_thread(self):
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = open_studio(browser, config=ENABLED_CONFIG, widget=STUB_WIDGET)
            page.goto(BASE + "/", wait_until="load")
            page.wait_for_selector(TOGGLE)
            page.locator(TOGGLE).nth(0).click()
            page.wait_for_selector(PANEL + ".is-open")
            page.locator(TOGGLE).nth(1).click()
            page.wait_for_function("document.querySelectorAll('#worksGrid .comment-panel.is-open').length === 1"
                                   " && document.querySelectorAll('#worksGrid .comment-panel')[1].classList.contains('is-open')")

            self.assertEqual(1, page.locator(PANEL + ".is-open").count(),
                             "only one comment thread stays mounted at a time")
            inits = page.evaluate("window.__twikooInit.map(entry => entry.urls)")
            self.assertEqual(2, len(inits))
            self.assertEqual(["/works/%s" % VISIBLE[1]["id"]], inits[-1])
            browser.close()

    def test_closing_returns_the_entry_to_its_resting_label(self):
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = open_studio(browser, config=ENABLED_CONFIG, widget=STUB_WIDGET)
            page.goto(BASE + "/", wait_until="load")
            page.wait_for_selector(TOGGLE)
            toggle = page.locator(TOGGLE).first
            toggle.click()
            page.wait_for_selector(PANEL + ".is-open")
            toggle.click()
            page.wait_for_selector(PANEL, state="hidden")

            self.assertEqual(0, page.locator(PANEL + ".is-open").count())
            self.assertEqual("false", toggle.get_attribute("aria-expanded"))
            self.assertEqual(0, page.evaluate("document.querySelectorAll('#worksGrid #twikoo').length"))
            browser.close()

    def test_counts_are_fetched_for_every_visible_work_in_one_batch(self):
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = open_studio(browser, config=ENABLED_CONFIG, widget=STUB_WIDGET)
            page.goto(BASE + "/", wait_until="load")
            page.wait_for_selector(TOGGLE)
            page.wait_for_function("window.__twikooCounts.length > 0")

            batches = page.evaluate("window.__twikooCounts")
            self.assertEqual(1, len(batches), "counts must not fan out into one request per work")
            self.assertEqual(sorted("/works/%s" % work["id"] for work in VISIBLE),
                             sorted(batches[0]))
            browser.close()

    def test_filtering_hides_the_open_thread_without_breaking_the_catalogue(self):
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = open_studio(browser, config=ENABLED_CONFIG, widget=STUB_WIDGET)
            page.goto(BASE + "/", wait_until="load")
            page.wait_for_selector(TOGGLE)
            page.locator(TOGGLE).first.click()
            page.wait_for_selector(PANEL + ".is-open")
            page.fill("#workSearch", VISIBLE[-1]["cnTitle"][:4])
            page.wait_for_function("document.querySelectorAll('#worksGrid .work-item:not([hidden])').length === 1")

            self.assertEqual(0, page.locator(PANEL + ".is-open").count())
            self.assertEqual(1, page.locator("#worksGrid .work-item:not([hidden])").count())
            browser.close()

    def test_english_switch_keeps_the_entry_readable(self):
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = open_studio(browser, config=ENABLED_CONFIG, widget=STUB_WIDGET)
            page.goto(BASE + "/", wait_until="load")
            page.wait_for_selector(TOGGLE)
            chinese = page.locator(TOGGLE).first.locator(".comment-toggle-label").inner_text()
            page.click("#langSwitch")
            page.wait_for_function("document.documentElement.lang === 'en'")
            english = page.locator(TOGGLE).first.locator(".comment-toggle-label").inner_text()

            self.assertNotEqual("", chinese)
            self.assertNotEqual("", english)
            self.assertNotEqual(chinese, english)
            browser.close()


class CommentsFailQuietly(unittest.TestCase):
    def test_unreachable_widget_removes_the_entry_and_keeps_the_page_usable(self):
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = open_studio(browser, config=ENABLED_CONFIG, widget=None)
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(BASE + "/", wait_until="load")
            page.wait_for_selector("#worksGrid .work-card")
            page.wait_for_function("document.querySelectorAll('#worksGrid .work-item').length > 0"
                                   " && document.querySelectorAll('#worksGrid .comment-toggle').length === 0")

            self.assertEqual([], errors, "a missing comment service must not break the catalogue")
            page.locator("#worksGrid .work-card").first.click()
            page.wait_for_selector("#workPlayer[open]")
            browser.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)