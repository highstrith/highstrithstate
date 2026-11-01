"""Real browser contracts for the studio redesign.

Run: python3 tests/studio-redesign-smoke.py -v
The public site must be running on STUDIO_BASE_URL (default :3000).
The admin test copies serve.js/admin.html/admin.css into a disposable directory
and never writes the real catalogue or uploads. Network interception supplies a
future-upload fixture, simulates static hosting, and fails or delays real media
requests to exercise retry and interrupted playback.
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
HIDDEN_IDS = {"featured-giant-wheel"}
VISIBLE = sorted(
    (work for work in CATALOG if work["id"] not in HIDDEN_IDS),
    key=lambda work: work.get("createdAt", ""), reverse=True,
)
FEATURE_REPLACEMENTS = {
    "work-lying-down-20261001": "featured-prove-it",
    "added-creative-3": "work-1783863606674-7ta9sp",
    "added-visual-study": "featured-exported-film",
    "added-title-render": "featured-timeline-1",
}
FEATURED = []
for work in VISIBLE:
    replacement = FEATURE_REPLACEMENTS.get(work["id"])
    if replacement:
        work = next(item for item in CATALOG if item["id"] == replacement)
    if not any(item["id"] == work["id"] for item in FEATURED):
        FEATURED.append(work)
FEATURED = FEATURED[:5]
CARDS = "#worksGrid .work-card"
SOURCE_COUNT = """videos => videos.filter(v => v.getAttribute('src') ||
    [...v.querySelectorAll('source')].some(s => s.getAttribute('src'))).length"""


@contextmanager
def disposable_admin(catalogue=None):
    """Exercise the production server and admin UI on isolated real files."""
    with tempfile.TemporaryDirectory(prefix="studio-admin-") as directory:
        root = Path(directory)
        for name in ("serve.js", "admin.html", "admin.css"):
            shutil.copy2(ROOT / name, root / name)
        (root / "data").mkdir()
        (root / "data/works.json").write_text(json.dumps(catalogue or [], ensure_ascii=False) + "\n")
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
        def close_page():
            if not page.is_closed():
                page.unroute_all(behavior="ignoreErrors")
                page.close()
        self.addCleanup(close_page)
        return page

    def ready(self, page, url=None):
        page.goto(url or BASE + "/", wait_until="domcontentloaded")
        expect(page.locator(CARDS)).to_have_count(len(VISIBLE))

    def assert_public_catalogue(self, page, expected=VISIBLE):
        self.assertEqual(
            page.locator(CARDS).evaluate_all("cards => cards.map(c => c.dataset.workId)"),
            [work["id"] for work in expected],
        )
        for hidden in (work for work in CATALOG if work["id"] in HIDDEN_IDS):
            expect(page.locator("main [data-work-id='%s']" % hidden["id"])).to_have_count(0)
            expect(page.locator("main")).not_to_contain_text(hidden["cnTitle"])

    def assert_count(self, page, count):
        expect(page.locator(CARDS + ":visible")).to_have_count(min(count, 6))
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

    def hold_media(self, page, source):
        pending = []
        page.route("**/" + source, lambda route: pending.append(route))
        def abort_held():
            while pending:
                pending.pop(0).abort()
        self.addCleanup(abort_held)
        return pending

    def release_media(self, page, source, pending, content_type):
        self.assertTrue(pending, "The real media request must be held before release")
        body = (ROOT / source).read_bytes()
        while pending:
            pending.pop(0).fulfill(status=200, body=body, content_type=content_type)
        page.unroute("**/" + source)

    def test_filters_search_and_language_keep_all_works_reachable(self):
        page = self.page(viewport={"width": 1440, "height": 900})
        self.ready(page)
        self.assert_count(page, len(VISIBLE))
        self.assert_public_catalogue(page)
        self.assertTrue(page.locator(CARDS).evaluate_all("cards => cards.every(c => c.tagName === 'BUTTON')"))
        expect(page.locator("#workSearch")).to_have_attribute("type", "search")
        for category in ("story", "motion", "edit"):
            with self.subTest(category=category):
                page.locator("#workFilters [data-filter='%s']" % category).click()
                page.wait_for_function("""({selector, total}) => {
                  const cards = [...document.querySelectorAll(selector)].filter(c => c.getClientRects().length);
                  return cards.length > 0 && cards.length < total;
                }""", arg={"selector": CARDS, "total": len(VISIBLE)})
                self.assert_count(page, page.locator(CARDS + ":visible").count())
        page.locator("#workFilters [data-filter='all']").click()
        self.assert_count(page, len(VISIBLE))
        page.locator("#workSearch").fill("趴着办公早该知道")
        self.assert_count(page, 1)
        expect(page.locator(CARDS + ":visible")).to_contain_text("趴着办公早该知道")
        page.locator("#workSearch").fill("does-not-exist-unique-query")
        self.assert_count(page, 0)
        page.locator("#workSearch").fill("")
        self.assert_count(page, len(VISIBLE))
        page.locator("#langSwitch").click()
        expect(page.locator("html")).to_have_attribute("lang", "en")
        expect(page.locator(CARDS).first).to_contain_text(VISIBLE[0]["enTitle"])
        page.locator("#workSearch").fill(VISIBLE[0]["enTitle"])
        self.assert_count(page, 1)

    def test_footer_software_and_confirmed_work_tags_are_readable_in_both_languages(self):
        page = self.page(viewport={"width": 320, "height": 844}, is_mobile=True, has_touch=True, reduced_motion="reduce")
        fixture = [dict(work, software=['blender', 'after-effects', 'blender', '<script>']) if work['id'] == VISIBLE[0]['id'] else work for work in CATALOG]
        page.route("**/api/works", lambda route: route.fulfill(json={"works": fixture}))
        self.ready(page)
        expect(page.locator("#softwareLogoSet [data-software]")).to_have_count(8)
        expect(page.locator("#softwareLogoSet svg")).to_have_count(8)
        card = page.locator(CARDS).first
        expect(card.locator(".work-software .software-tag")).to_have_text(['Blender', 'After Effects · AE'])
        expect(card.locator(".work-software-label")).to_have_text('制作软件')
        expect(page.locator(CARDS).nth(1).locator(".work-software")).to_have_count(0)
        page.locator("#langSwitch").click()
        expect(card.locator(".work-software-label")).to_have_text('Made with')
        expect(card.locator(".work-software .software-tag")).to_have_text(['Blender', 'After Effects'])
        expect(page.locator('.footer-software [data-software="jianying"]')).to_have_text('Jianying')
        card.click()
        expect(page.locator('#playerSoftware .software-tag')).to_have_text(['Blender', 'After Effects'])
        expect(page.locator('#playerSoftware .work-software-label')).to_have_text('Made with')
        page.locator('#workPlayerClose').click()
        page.locator(CARDS).nth(1).click()
        expect(page.locator('#playerSoftware')).not_to_be_visible()
        page.locator('#workPlayerClose').click()
        page.locator(".footer-software").scroll_into_view_if_needed()
        self.assertLessEqual(page.evaluate("document.documentElement.scrollWidth"), 321)

    def test_admin_software_selection_persists_and_can_be_cleared(self):
        with disposable_admin([CATALOG[-1]]) as (root, address):
            page = self.page(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
            page.goto(address + "/admin.html", wait_until="domcontentloaded")
            page.locator('[data-edit-work]').click()
            page.locator('#softwareChoices input[value="blender"]').check()
            page.locator('#softwareChoices input[value="after-effects"]').check()
            page.locator('#uploadSubmit').click()
            expect(page.locator('#uploadStatus')).to_have_attribute('data-tone', 'success')
            stored = json.loads((root / 'data/works.json').read_text())[0]
            self.assertEqual(stored['software'], ['blender', 'after-effects'])
            page.reload(wait_until="domcontentloaded")
            page.locator('[data-edit-work]').click()
            expect(page.locator('#softwareChoices input[value="blender"]')).to_be_checked()
            page.locator('#softwareChoices input[value="blender"]').uncheck()
            page.locator('#softwareChoices input[value="after-effects"]').uncheck()
            page.locator('#uploadSubmit').click()
            expect(page.locator('#uploadStatus')).to_have_attribute('data-tone', 'success')
            self.assertEqual(json.loads((root / 'data/works.json').read_text())[0]['software'], [])
            self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'), 391)

    def test_desktop_cards_preview_on_hover_or_focus_when_visible(self):
        page = self.page(viewport={"width": 1440, "height": 1000})
        self.ready(page)
        self.assertEqual(page.locator(CARDS + " video").evaluate_all(SOURCE_COUNT), 0)
        first, second = page.locator(CARDS).nth(0), page.locator(CARDS).nth(1)
        first.hover()
        page.wait_for_function("""suffix => [...document.querySelectorAll('#worksGrid video')]
          .some(v => v.currentSrc.endsWith(suffix) && v.currentTime > 0 && !v.paused)""", arg=VISIBLE[0]["previewVideo"])
        self.assertLessEqual(page.locator(CARDS + " video").evaluate_all(SOURCE_COUNT), 1)
        second.hover()
        page.wait_for_function("""suffix => [...document.querySelectorAll('#worksGrid video')]
          .some(v => v.currentSrc.endsWith(suffix) && v.currentTime > 0 && !v.paused)""", arg=VISIBLE[1]["previewVideo"])
        self.assertLessEqual(page.locator(CARDS + " video").evaluate_all(SOURCE_COUNT), 1)
        page.mouse.move(0, 0)
        first.focus()
        page.wait_for_function("""suffix => [...document.querySelectorAll('#worksGrid video')]
          .some(v => v.currentSrc.endsWith(suffix) && !v.paused)""", arg=VISIBLE[0]["previewVideo"])
        self.assertLessEqual(page.locator(CARDS + " video").evaluate_all(SOURCE_COUNT), 1)

    def test_desktop_player_uses_full_media_and_returns_keyboard_focus(self):
        page = self.page(viewport={"width": 1440, "height": 900})
        self.ready(page)
        card = page.locator(CARDS).first
        card.focus()
        card.press("Enter")
        expect(page.locator("dialog#workPlayer")).to_be_visible()
        self.assert_playing(page, VISIBLE[0].get("webVideo") or VISIBLE[0]["video"])
        self.assertTrue(page.locator("video:not(#workPlayerVideo)").evaluate_all("vs => vs.every(v => v.paused)"))
        page.keyboard.press("Escape")
        self.assert_closed_with_focus(page, card)
        card.press("Space")
        self.assert_playing(page, VISIBLE[0].get("webVideo") or VISIBLE[0]["video"])
        page.locator("#workPlayerClose").click()
        self.assert_closed_with_focus(page, card)

    def test_hero_preview_pauses_for_player_and_reduced_motion(self):
        page = self.page(viewport={"width": 1440, "height": 900})
        self.ready(page)
        page.wait_for_function("document.querySelector('#heroPreview')?.currentTime > 0")
        hero_button = page.locator("[data-hero-play]").first
        # The desktop badge follows the pointer; activate its real keyboard path.
        hero_button.focus()
        hero_button.press('Enter')
        expect(page.locator("#workPlayer")).to_be_visible()
        page.wait_for_function("document.querySelector('#heroPreview').paused")
        page.locator("#workPlayerClose").click()
        expect(hero_button).to_be_focused()
        page.emulate_media(reduced_motion="reduce")
        page.wait_for_function("document.querySelector('#heroPreview').paused")
        hero_button.click()
        page.wait_for_function("document.querySelector('#workPlayerVideo').currentTime > 0")

    def test_feature_switches_follow_newest_visible_films_and_play_full_media(self):
        page = self.page(viewport={"width": 1440, "height": 900})
        self.ready(page)
        controls = page.locator("#featureControls button[data-feature]")
        featured = FEATURED
        expect(controls).to_have_count(len(featured))
        for index, work in enumerate(featured):
            with self.subTest(work=work["id"]):
                controls.nth(index).click()
                expect(page.locator("#featureTitle")).to_have_text(work["cnTitle"])
                page.wait_for_function("""suffix => {
                    const video = document.querySelector('#heroPreview');
                    return video.currentSrc.endsWith(suffix) && video.currentTime > 0 && !video.paused;
                }""", arg=work["previewVideo"])
                hero_button = page.locator("[data-hero-play]").first
                hero_button.focus()
                hero_button.press('Enter')
                self.assert_playing(page, work.get("webVideo") or work["video"])
                page.locator("#workPlayerClose").click()
                self.assert_closed_with_focus(page, hero_button)

    def test_mobile_hero_plays_only_in_view(self):
        page = self.page(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
        self.ready(page)
        def assert_preview(source):
            page.wait_for_function("""suffix => {
                const video = document.querySelector('#heroPreview');
                return video.currentSrc.endsWith(suffix) && video.currentTime > 0 && !video.paused && video.muted && video.playsInline;
            }""", arg=source)
            self.assertEqual(page.locator(CARDS + " video").evaluate_all(SOURCE_COUNT), 0)
        assert_preview(FEATURED[0]["previewVideo"])
        page.locator("#featureControls button").nth(1).click()
        assert_preview(FEATURED[1]["previewVideo"])
        page.locator("[data-hero-play]").click()
        self.assert_playing(page, FEATURED[1].get("mobileVideo") or FEATURED[1]["video"])
        self.assertEqual(page.locator("#heroPreview").evaluate_all(SOURCE_COUNT), 0)
        page.locator("#workPlayerClose").click()
        assert_preview(FEATURED[1]["previewVideo"])
        page.locator(CARDS + ":visible").last.scroll_into_view_if_needed()
        page.wait_for_function("!document.querySelector('#heroPreview').getAttribute('src')")
        self.assertLessEqual(page.locator(CARDS + " video").evaluate_all(SOURCE_COUNT), 1)
        page.locator("#heroTitle").scroll_into_view_if_needed()
        assert_preview(FEATURED[1]["previewVideo"])
        page.emulate_media(reduced_motion="reduce")
        page.wait_for_function("!document.querySelector('#heroPreview').getAttribute('src')")

    def test_hero_play_badge_follows_pointer_and_returns_home(self):
        page = self.page(viewport={"width": 1440, "height": 900})
        self.ready(page)
        screen = page.locator(".feature-screen").bounding_box()
        badge = page.locator("[data-hero-play]").first
        home = badge.bounding_box()
        self.assertAlmostEqual(home["x"] + home["width"] / 2, screen["x"] + screen["width"] / 2, delta=1)
        self.assertAlmostEqual(home["y"] + home["height"] / 2, screen["y"] + screen["height"] * .45, delta=1)

        target = (screen["x"] + screen["width"] * .3, screen["y"] + screen["height"] * .35)
        page.mouse.move(*target, steps=4)
        page.wait_for_function("""([x, y]) => {
            const box = document.querySelector('[data-hero-play]').getBoundingClientRect();
            return Math.abs(box.x + box.width / 2 - x) < 1.5 && Math.abs(box.y + box.height / 2 - y) < 1.5;
        }""", arg=[target[0], target[1]])

        page.mouse.move(screen["x"] + screen["width"] - 4, screen["y"] + screen["height"] - 4, steps=3)
        page.wait_for_timeout(700)
        corner = badge.bounding_box()
        self.assertGreaterEqual(corner["x"], screen["x"])
        self.assertGreaterEqual(corner["y"], screen["y"])
        self.assertLessEqual(corner["x"] + corner["width"], screen["x"] + screen["width"] + .5)
        self.assertLessEqual(corner["y"] + corner["height"], screen["y"] + screen["height"] + .5)

        badge.click()
        expect(page.locator("#social-qr-dialog")).not_to_be_visible()
        expect(page.locator("#workPlayer")).to_be_visible()
        page.keyboard.press("Escape")
        page.wait_for_timeout(200)

        page.mouse.move(5, 5, steps=3)
        page.wait_for_function("""() => {
            const badge = document.querySelector('[data-hero-play]');
            const hero = document.querySelector('.hero-feature');
            return !badge.getAttribute('style') && !hero.classList.contains('is-play-follow');
        }""")
        back = badge.bounding_box()
        self.assertAlmostEqual(back["x"] + back["width"] / 2, screen["x"] + screen["width"] / 2, delta=1.5)

    def test_hero_play_badge_stays_put_for_touch_input(self):
        page = self.page(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
        self.ready(page)
        box = page.locator(".feature-screen").bounding_box()
        page.touchscreen.tap(box["x"] + 24, box["y"] + 24)
        page.wait_for_timeout(300)
        self.assertFalse(page.locator(".hero-feature.is-play-follow").count())
        self.assertFalse(page.locator("[data-hero-play]").first.get_attribute("style"))

    def test_hero_rotates_after_ten_seconds_of_real_muted_mobile_playback(self):
        page = self.page(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
        self.ready(page)
        page.wait_for_function("document.querySelector('#heroPreview').currentTime > 0")
        first = page.locator('#featureControls button').first
        expect(first).to_have_attribute('aria-pressed', 'true')
        started = time.monotonic()
        page.wait_for_function("""suffix => {
          const video = document.querySelector('#heroPreview');
          return video.currentSrc.endsWith(suffix) && video.currentTime > 0 && !video.paused;
        }""", arg=FEATURED[1]['previewVideo'], timeout=15000)
        elapsed = time.monotonic() - started
        self.assertGreater(elapsed, 8.5)
        self.assertLess(elapsed, 13.5)
        expect(page.locator('#featureTitle')).to_have_text(FEATURED[1]['cnTitle'])
        expect(page.locator('#featureControls button').nth(1)).to_have_attribute('aria-pressed', 'true')
        self.assertTrue(page.locator('#heroPreview').evaluate('v => v.muted && v.defaultMuted && v.playsInline'))
        self.assertEqual(page.locator(CARDS + ' video').evaluate_all(SOURCE_COUNT), 0)

    def test_hero_hover_changes_film_and_revisits_use_another_moving_segment(self):
        page = self.page(viewport={"width": 1440, "height": 900})
        self.ready(page)
        page.wait_for_function("document.querySelector('#heroPreview').currentTime > 0")
        picks = page.locator('#featureControls button')
        picks.nth(3).hover()
        expect(picks.nth(3)).to_have_attribute('aria-pressed', 'true')
        page.wait_for_function("""suffix => {
          const video = document.querySelector('#heroPreview');
          return video.currentSrc.endsWith(suffix) && video.currentTime > 0 && !video.paused;
        }""", arg=FEATURED[3]['previewVideo'])
        picks.first.hover()
        expect(picks.first).to_have_attribute('aria-pressed', 'true')
        page.wait_for_function("document.querySelector('#heroPreview').currentTime > 10 && !document.querySelector('#heroPreview').paused")
        # The second window must continue moving, and pausing must not consume
        # its ten-second screening allowance through a wall-clock timer.
        paused_at = page.locator('#heroPreview').evaluate('v => { v.pause(); return v.currentTime; }')
        page.wait_for_timeout(10300)
        expect(picks.first).to_have_attribute('aria-pressed', 'true')
        self.assertAlmostEqual(page.locator('#heroPreview').evaluate('v => v.currentTime'), paused_at, delta=.1)
        page.locator('#heroPreview').evaluate('v => { v.playbackRate = 4; return v.play(); }')
        page.wait_for_function("document.querySelector('#featureControls button:nth-child(2)').getAttribute('aria-pressed') === 'true'")
        page.locator('#heroPreview').evaluate('v => { v.pause(); }')
        picks.nth(4).focus()
        expect(picks.nth(4)).to_have_attribute('aria-pressed', 'true')
        picks.nth(4).click()
        expect(page.locator('#workPlayer')).not_to_be_visible()
        self.assertLessEqual(page.locator('video:not(#workPlayerVideo)').evaluate_all(SOURCE_COUNT), 1)
        page.wait_for_function("document.querySelector('#heroPreview').currentTime > 0 && !document.querySelector('#heroPreview').paused")
        page.locator('#heroPreview').evaluate('v => { v.playbackRate = 4; }')
        page.wait_for_function("document.querySelector('#featureControls button:first-child').getAttribute('aria-pressed') === 'true'")
        expect(page.locator('#featureTitle')).to_have_text(FEATURED[0]['cnTitle'])

    def test_short_hero_preview_advances_when_real_clip_ends(self):
        page = self.page(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
        short = next(work for work in CATALOG if work['id'] == 'added-render-test')
        fixture = [dict(work, previewVideo=short['previewVideo']) if work['id'] == FEATURED[0]['id'] else work for work in CATALOG]
        page.route('**/api/works', lambda route: route.fulfill(json={'works': fixture}))
        self.ready(page)
        page.wait_for_function("document.querySelector('#heroPreview').currentTime > 0")
        duration = page.locator('#heroPreview').evaluate('v => v.duration')
        self.assertLess(duration, 10)
        page.wait_for_function("document.querySelector('#featureControls button:nth-child(2)').getAttribute('aria-pressed') === 'true'", timeout=int((duration + 3) * 1000))
        expect(page.locator('#featureTitle')).to_have_text(FEATURED[1]['cnTitle'])

    def test_public_links_and_work_cards_have_no_decorative_arrows(self):
        page = self.page(viewport={"width": 390, "height": 844}, reduced_motion='reduce')
        self.ready(page)
        for language in ('cn', 'en'):
            if language == 'en':
                page.locator('#langSwitch').click()
            self.assertNotRegex(page.locator('body').inner_text(), '[↗↘→←↑↓↖↙⟶➜➝]')
            expect(page.locator('.card-play')).to_have_count(0)
        expect(page.locator('.contact-email')).to_have_attribute('href', 'mailto:highstrith@gmail.com')
        expect(page.locator('.footer-top a')).to_have_attribute('href', '#home')

    def test_mobile_feature_controls_do_not_overlap_picture_or_title(self):
        for width in (320, 390, 600, 700, 800):
            page = self.page(viewport={"width": width, "height": 844}, is_mobile=True, has_touch=True, reduced_motion="reduce")
            self.ready(page)
            for language in ("cn", "en"):
                if language == "en":
                    page.locator("#langSwitch").click()
                for index in range(5):
                    page.locator("#featureControls button").nth(index).click()
                    page.locator("#heroPoster").evaluate("image => image.decode()")
                    poster = page.locator("#heroPoster").bounding_box()
                    info = page.locator(".feature-info").bounding_box()
                    controls = page.locator("#featureControls").bounding_box()
                    self.assertGreaterEqual(info["y"], poster["y"] + poster["height"])
                    self.assertGreaterEqual(controls["y"], info["y"] + info["height"])
                    self.assertAlmostEqual(poster["width"] / poster["height"], 16 / 9, delta=.02)
                    for button in page.locator("#featureControls button").all():
                        box = button.bounding_box()
                        self.assertGreaterEqual(box["width"], 44)
                        self.assertGreaterEqual(box["height"], 44)
                self.assertLessEqual(page.evaluate("document.documentElement.scrollWidth"), width + 1)
            page.close()

    def test_reduced_motion_does_not_load_preview_video(self):
        for width in (390, 1440):
            with self.subTest(width=width):
                page = self.page(viewport={"width": width, "height": 844}, is_mobile=True, has_touch=True, reduced_motion="reduce")
                requests = []
                page.on("request", lambda request: requests.append(request.url) if ".mp4" in request.url else None)
                self.ready(page)
                page.locator(CARDS + ":visible").last.scroll_into_view_if_needed()
                # A short observation window detects delayed eager video requests.
                page.wait_for_timeout(250)
                self.assertEqual(requests, [])
                self.assertEqual(page.locator("video").evaluate_all(SOURCE_COUNT), 0)
                card = page.locator(CARDS).first
                card.click()
                self.assert_playing(page, VISIBLE[0].get("mobileVideo") or VISIBLE[0]["video"])
                self.assertTrue(all(url.endswith(VISIBLE[0].get("mobileVideo") or VISIBLE[0]["video"]) for url in requests), requests)
                page.locator("#workPlayerClose").click()
                self.assert_closed_with_focus(page, card)

    def test_cold_mobile_initial_images_stay_within_network_budget(self):
        # A new page owns a fresh context. Count real HTTP transfers, including
        # any duplicate image downloads; no image responses are intercepted.
        page = self.page(viewport={"width": 390, "height": 844},
                         device_scale_factor=2, is_mobile=True, has_touch=True)
        network = page.context.new_cdp_session(page)
        network.send("Network.enable")
        network.send("Network.setCacheDisabled", {"cacheDisabled": True})
        network.send("Network.setBypassServiceWorker", {"bypass": True})
        requests, images = [], {}

        def requested(event):
            requests.append(event["request"]["url"])
            if event.get("type") == "Image":
                images[event["requestId"]] = {"url": event["request"]["url"], "bytes": 0}

        def received(event):
            if event.get("type") == "Image":
                image = images.setdefault(event["requestId"], {"bytes": 0})
                image.update(url=event["response"]["url"], status=event["response"]["status"])

        def transferred(event):
            if event["requestId"] in images:
                images[event["requestId"]]["bytes"] += event.get("encodedDataLength", 0)

        def finished(event):
            if event["requestId"] in images:
                images[event["requestId"]].update(bytes=event["encodedDataLength"], finished=True)

        network.on("Network.requestWillBeSent", requested)
        network.on("Network.responseReceived", received)
        network.on("Network.dataReceived", transferred)
        network.on("Network.loadingFinished", finished)
        self.ready(page)
        page.locator("#heroPoster").evaluate("image => image.decode()")
        page.wait_for_load_state("networkidle", timeout=30000)
        hero_url = page.locator("#heroPoster").evaluate("image => image.currentSrc")
        hero_id = next((key for key, image in images.items() if image.get("url") == hero_url), None)
        self.assertIsNotNone(hero_id, "The cold Hero must arrive through the real HTTP network")
        # naturalWidth is density-corrected with srcset. Decode the response
        # bytes already received to check physical pixels without another fetch.
        hero_body = network.send("Network.getResponseBody", {"requestId": hero_id})
        hero_width = page.evaluate("""async response => {
            const bytes = response.base64Encoded
                ? Uint8Array.from(atob(response.body), char => char.charCodeAt(0))
                : new TextEncoder().encode(response.body);
            const image = await createImageBitmap(new Blob([bytes]));
            const width = image.width;
            image.close();
            return width;
        }""", hero_body)
        image_bytes = sum(image["bytes"] for image in images.values())
        report = {"imageBytes": image_bytes, "heroPhysicalWidth": hero_width,
                  "images": list(images.values())}
        print("Cold mobile initial image network: " + json.dumps(report, ensure_ascii=False), flush=True)
        self.assertEqual(page.evaluate("window.scrollY"), 0, "Measure the initial view without scrolling")
        video_requests = [url for url in requests if urlsplit(url).path.lower().endswith(".mp4")]
        self.assertTrue(video_requests, "The visible Hero may request its lightweight preview")
        self.assertTrue(all(url.endswith(FEATURED[0]['previewVideo']) for url in video_requests), video_requests)
        self.assertGreaterEqual(hero_width, 700, "A lightweight Hero must remain sharp at mobile DPR 2")
        self.assertTrue(all(image.get("finished") and image.get("status") == 200
                            for image in images.values()), report)
        budget = 400 * 1024
        large_pngs = {work["poster"] for work in CATALOG
                      if work["poster"].lower().endswith(".png")
                      and (ROOT / work["poster"]).stat().st_size > budget}
        self.assertEqual([url for url in requests if any(
            urlsplit(url).path.endswith("/" + poster) for poster in large_pngs)], [], report)
        self.assertLessEqual(image_bytes, budget, report)

    def test_failed_full_video_retries_same_full_source(self):
        page = self.page(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
        blocked = {"value": True}
        source = VISIBLE[0].get("mobileVideo") or VISIBLE[0]["video"]
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
        self.assert_playing(page, VISIBLE[2].get("mobileVideo") or VISIBLE[2]["video"])

    def test_pausing_during_mobile_video_load_leaves_playback_action_available(self):
        page = self.page(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
        source = VISIBLE[0].get("mobileVideo") or VISIBLE[0]["video"]
        pending = self.hold_media(page, source)
        self.ready(page)
        with page.expect_request("**/" + source):
            page.locator(CARDS).first.click()
        expect(page.locator("#workPlayerStatus")).to_be_visible()
        page.evaluate("document.querySelector('#workPlayerVideo').pause()")
        self.release_media(page, source, pending, "video/mp4")
        page.wait_for_function("""() => {
            const video = document.querySelector('#workPlayerVideo');
            return video.readyState === 4 && video.paused;
        }""")
        page.wait_for_function("""() => {
            const status = document.querySelector('#workPlayerStatus');
            const action = document.querySelector('#workPlayerAction');
            return status.hidden || (!action.hidden && action.getClientRects().length > 0);
        }""")
        action = page.locator("#workPlayerAction")
        if action.is_visible():
            action.click()
        else:
            page.locator("#workPlayerVideo").press("Space")
        self.assert_playing(page, source)

    def test_rapid_player_close_and_reopen_keeps_the_latest_session_playing(self):
        page = self.page(viewport={"width": 1440, "height": 900})
        self.ready(page)
        page.locator(CARDS).first.click()
        expect(page.locator("#workPlayer")).to_be_visible()
        page.evaluate("""() => {
            const cards = document.querySelectorAll('#worksGrid .work-card');
            const close = document.querySelector('#workPlayerClose');
            close.click();
            cards[1].click();
            close.click();
            cards[2].click();
        }""")
        self.assert_playing(page, VISIBLE[2].get("webVideo") or VISIBLE[2]["video"])
        expect(page.locator("#workPlayer")).to_be_visible()
        playing_time = page.locator("#workPlayerVideo").evaluate("video => video.currentTime")
        page.wait_for_function("""start => {
            const video = document.querySelector('#workPlayerVideo');
            return !video.paused && video.currentTime > start + 0.2;
        }""", arg=playing_time)
        page.locator("#workPlayerClose").click()
        self.assert_closed_with_focus(page, page.locator(CARDS).nth(2))

    def test_future_upload_enters_first_without_losing_older_visible_works(self):
        page = self.page(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
        future = dict(VISIBLE[0], id="future-upload-fixture", createdAt="2099-01-01T00:00:00.000Z", cnTitle="将来上传作品", enTitle="Future upload")
        fixture = [*reversed(CATALOG), future]
        # The local API wraps its catalogue; the static JSON deliberately stays
        # unchanged so falling through the API cannot pass this assertion.
        page.route("**/api/works", lambda route: route.fulfill(json={"works": fixture}))
        page.goto(BASE + "/", wait_until="domcontentloaded")
        expected = sorted(
            (work for work in fixture if work["id"] not in HIDDEN_IDS),
            key=lambda work: work.get("createdAt", ""), reverse=True,
        )
        expect(page.locator(CARDS)).to_have_count(len(expected))
        self.assert_public_catalogue(page, expected)
        expect(page.locator(CARDS).first).to_contain_text("将来上传作品")
        expect(page.locator("#featureControls button[data-feature]").first).to_have_attribute("data-feature", future["id"])
        expect(page.locator("#featureTitle")).to_have_text(future["cnTitle"])

    def test_file_mode_keeps_sorted_catalogue_and_manual_playback_available(self):
        page = self.page(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, reduced_motion="reduce")
        requests = []
        page.on("request", lambda request: requests.append(request.url))
        self.ready(page, (ROOT / "index.html").as_uri())
        self.assert_public_catalogue(page)
        self.assert_count(page, len(VISIBLE))
        self.assertFalse(any("/api/works" in url or "/data/works.json" in url or ".mp4" in url for url in requests), requests)
        page.locator("#langSwitch").click()
        expect(page.locator(CARDS).first).to_contain_text(VISIBLE[0]["enTitle"])
        card = page.locator(CARDS).first
        card.click()
        source = VISIBLE[0].get("mobileVideo") or VISIBLE[0]["video"]
        self.assert_playing(page, source)
        self.assertTrue(page.locator("#workPlayerVideo").evaluate("video => video.currentSrc.startsWith('file:')"))
        page.locator("#workPlayerClose").click()
        self.assert_closed_with_focus(page, card)

    def test_background_music_requires_its_toggle_and_pauses_for_full_video(self):
        page = self.page(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
        self.ready(page)
        toggle = page.locator("#musicToggle")
        music = page.locator("#bgMusic")
        expect(toggle).to_have_attribute("aria-pressed", "false")

        self.assertTrue(music.evaluate("audio => audio.paused && audio.currentTime === 0"))
        card = page.locator(CARDS).first
        card.click()
        self.assert_playing(page, VISIBLE[0].get("webVideo") or VISIBLE[0]["video"])
        self.assertTrue(music.evaluate("audio => audio.paused"))
        page.locator("#workPlayerClose").click()
        self.assert_closed_with_focus(page, card)
        self.assertTrue(music.evaluate("audio => audio.paused"))
        expect(toggle).to_have_attribute("aria-pressed", "false")
        toggle.click()
        page.wait_for_function("""() => {
            const audio = document.querySelector('#bgMusic');
            return audio.currentTime > 0 && !audio.paused;
        }""")
        expect(toggle).to_have_attribute("aria-pressed", "true")
        self.assertAlmostEqual(music.evaluate("audio => audio.volume"), 0.16, places=2)
        card.click()
        self.assert_playing(page, VISIBLE[0].get("webVideo") or VISIBLE[0]["video"])
        page.wait_for_function("document.querySelector('#bgMusic').paused")
        paused_time = music.evaluate("audio => audio.currentTime")
        page.locator("#workPlayerClose").click()
        self.assert_closed_with_focus(page, card)
        page.wait_for_function("""start => {
            const audio = document.querySelector('#bgMusic');
            return !audio.paused && audio.currentTime > start;
        }""", arg=paused_time)
        toggle.click()
        page.wait_for_function("document.querySelector('#bgMusic').paused")
        expect(toggle).to_have_attribute("aria-pressed", "false")

    def test_pending_music_play_preserves_intent_across_player_and_fast_toggles(self):
        page = self.page(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
        source = "assets/background-music.mp3"
        pending = self.hold_media(page, source)
        self.ready(page)
        toggle = page.locator("#musicToggle")
        with page.expect_request("**/" + source):
            toggle.click()
        expect(toggle).to_have_attribute("aria-pressed", "true")
        page.locator(CARDS).first.click()
        self.assert_playing(page, VISIBLE[0].get("webVideo") or VISIBLE[0]["video"])
        page.wait_for_function("document.querySelector('#bgMusic').paused")
        expect(toggle).to_have_attribute("aria-pressed", "true")
        page.locator("#workPlayerClose").click()
        self.release_media(page, source, pending, "audio/mpeg")
        page.wait_for_function("""() => {
            const audio = document.querySelector('#bgMusic');
            return audio.currentTime > 0 && !audio.paused;
        }""")
        expect(toggle).to_have_attribute("aria-pressed", "true")
        toggle.click()
        expect(toggle).to_have_attribute("aria-pressed", "false")
        pending = self.hold_media(page, source)
        with page.expect_request("**/" + source):
            off_state = page.evaluate("""() => {
                document.querySelector('#bgMusic').load();
                const button = document.querySelector('#musicToggle');
                button.click();
                button.click();
                const off = button.getAttribute('aria-pressed');
                button.click();
                return off;
            }""")
        self.assertEqual(off_state, "false")
        expect(toggle).to_have_attribute("aria-pressed", "true")
        self.release_media(page, source, pending, "audio/mpeg")
        page.wait_for_function("""() => {
            const audio = document.querySelector('#bgMusic');
            return audio.currentTime > 0 && !audio.paused;
        }""")
        expect(toggle).to_have_attribute("aria-pressed", "true")
        toggle.click()
        page.wait_for_function("document.querySelector('#bgMusic').paused")
        expect(toggle).to_have_attribute("aria-pressed", "false")

    def test_contact_social_rows_only_load_full_qr_on_click(self):
        page = self.page(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
        requests = []
        page.on("request", lambda request: requests.append(request.url) if "/assets/social/" in request.url else None)
        self.ready(page)
        links = page.locator("#contact [data-qr-image]")
        self.assertEqual(links.count(), 3)
        self.assertEqual(requests, [], "QR images must remain lazy until interaction")
        self.assertGreaterEqual(
            page.locator("#contact .social-name").first.evaluate("el => parseFloat(getComputedStyle(el).fontSize)"),
            17, "Contact social names must stay visually prominent",
        )
        wechat = page.locator('#contact [data-qr-title="微信"]')
        red = page.locator('#contact [data-qr-title="小红书"]')
        preview = page.locator("#social-qr-preview")
        expect(preview).not_to_be_visible()
        page.locator("#contact").scroll_into_view_if_needed()
        page.wait_for_timeout(200)
        wechat.hover()
        expect(preview).not_to_be_visible()
        self.assertEqual(requests, [], 'Hover should only invert the row, without loading a thumbnail')
        red.hover()
        expect(preview).not_to_be_visible()
        self.assertEqual(requests, [])
        red.click()
        dialog = page.locator("#social-qr-dialog")
        expect(dialog).to_be_visible()
        expect(dialog.locator('img')).to_have_attribute('src', re.compile(r'xiaohongshu-qr\.jpg$'))
        expect(page.locator("#social-qr-title")).to_have_text("小红书")
        page.wait_for_function("document.querySelector('#social-qr-dialog img').naturalWidth > 0")
        self.assertTrue(page.locator("#social-qr-dialog img").evaluate("img => img.complete && img.naturalWidth > 0"))
        page.keyboard.press("Escape")
        expect(dialog).not_to_be_visible()
        expect(red).to_be_focused()
        page.locator("#langSwitch").click()
        expect(wechat).to_contain_text("WeChat")
        expect(wechat.locator(".social-hint")).to_have_text("View QR code")
        bili = page.locator('#contact a[href="https://b23.tv/VFqS3Tj"]')
        expect(bili).to_contain_text("Bilibili")
        expect(bili.locator(".social-hint")).to_have_text("Open profile")

    def test_contact_social_links_mobile_bilingual_layout(self):
        expected_names = {
            "cn": ["微信", "抖音", "小红书", "哔哩哔哩"],
            "en": ["WeChat", "Douyin", "Xiaohongshu", "Bilibili"],
        }
        for width in (320, 390, 820):
            with self.subTest(width=width):
                page = self.page(viewport={"width": width, "height": 900}, has_touch=True,
                                 is_mobile=width < 700, reduced_motion="reduce")
                self.ready(page)
                links = page.locator("#contact .social-links > *")
                self.assertEqual(links.count(), 4)
                self.assertLessEqual(page.evaluate("document.documentElement.scrollWidth"), width + 1)
                for language in ("cn", "en"):
                    if language == "en":
                        page.locator("#langSwitch").click()
                    self.assertEqual(
                        [links.nth(index).locator(".social-name").inner_text() for index in range(4)],
                        expected_names[language],
                    )
                    last = links.nth(3).bounding_box()
                    self.assertGreaterEqual(last["x"], -0.5)
                    self.assertLessEqual(last["x"] + last["width"], width + 1)
                    first = links.first.bounding_box()
                    self.assertGreaterEqual(first["height"], 44, "Social tap targets must stay at least 44px tall")
                    qr = page.locator('#contact [data-qr-title="微信"]')
                    qr.click()
                    expect(page.locator("#social-qr-dialog")).to_be_visible()
                    self.assertLessEqual(
                        page.locator("#social-qr-dialog").bounding_box()["width"], width,
                    )
                    page.locator("#socialQrClose").click()
                    expect(qr).to_be_focused()
                page.close()

    def test_layout_and_contacts_at_supported_widths(self):
        for width in (320, 390, 820, 1440, 1920):
            with self.subTest(width=width):
                page = self.page(viewport={"width": width, "height": 900}, reduced_motion="reduce")
                self.ready(page)
                for language in ("cn", "en"):
                    with self.subTest(language=language):
                        if language == "en":
                            page.locator("#langSwitch").click()
                        page.locator(CARDS + ":visible").last.scroll_into_view_if_needed()
                        self.assertLessEqual(page.evaluate("document.documentElement.scrollWidth"), width + 1)
                        expect(page.locator("#workSearch")).to_be_visible()
                        expect(page.locator("#adminEntryLink")).to_be_visible()
                self.assertEqual(page.locator("#contact [data-qr-image]").count(), 3)
                self.assertEqual(page.locator('#contact a[href="https://b23.tv/VFqS3Tj"]').count(), 1)
                qr = page.locator("#contact [data-qr-image]").first
                qr.click()
                expect(page.locator("#social-qr-dialog")).to_be_visible()
                image = page.locator("#social-qr-dialog img")
                expect(image).to_be_visible()
                image.evaluate("img => img.decode()")
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
            if path.removeprefix("/portfolio/").startswith("api/") or path.startswith("/api/"):
                api_requests.append(path)
                route.fulfill(status=404, body="Static hosting has no API")
            elif path.endswith("/data/works.json"):
                route.fulfill(status=404, body="Exercise the embedded catalogue fallback")
            else:
                relative = path.removeprefix("/portfolio/")
                route.fulfill(response=route.fetch(url=BASE + "/" + relative))

        page.route("https://studio.example/**", static_route)
        self.ready(page, public)
        self.assert_public_catalogue(page)
        expect(page.locator("#adminEntryLink")).not_to_be_visible()
        self.assertEqual(api_requests, [])
        page.locator(CARDS).first.click()
        self.assert_playing(page, VISIBLE[0].get("webVideo") or VISIBLE[0]["video"])
        nojs = self.page(viewport={"width": 390, "height": 844}, java_script_enabled=False)
        nojs.route("https://studio.example/**", static_route)
        nojs.goto(public, wait_until="load")
        expect(nojs.locator(".no-js-work")).to_have_count(len(VISIBLE))
        expect(nojs.locator(".no-js-work").first).to_be_visible()
        for index, work in enumerate(VISIBLE):
            link = nojs.locator(".no-js-work").nth(index)
            self.assertEqual(link.get_attribute("href"), work.get("webVideo") or work["video"])
            expect(link).to_contain_text(work["cnTitle"])
        expect(nojs.locator("main")).not_to_contain_text("巨轮空降")
        self.assertLessEqual(nojs.evaluate("document.documentElement.scrollWidth"), 391)

    def test_admin_retains_hidden_work_and_all_raw_catalogue_entries(self):
        with disposable_admin(CATALOG) as (root, address):
            page = self.page(viewport={"width": 1440, "height": 1000})
            css_response = []
            page.on("response", lambda response: css_response.append(response.status) if urlsplit(response.url).path == "/admin.css" else None)
            page.goto(address + "/admin.html", wait_until="domcontentloaded")
            expect(page.locator(".manage-card")).to_have_count(len(CATALOG))
            expect(page.locator("#heroWorkCount")).to_have_text(str(len(CATALOG)))
            self.assertCountEqual(
                page.locator(".manage-card").evaluate_all("cards => cards.map(c => c.dataset.workId)"),
                [work["id"] for work in CATALOG],
            )
            expect(page.locator(".manage-card[data-work-id='featured-giant-wheel']")).to_contain_text("巨轮空降")
            self.assertEqual(css_response, [200])
            self.assertEqual(json.loads((root / "data/works.json").read_text()), CATALOG)

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
            preview = page.locator("#manageList .manage-preview")
            preview.hover()
            page.wait_for_function("""() => {
                const video = document.querySelector('#manageList .manage-preview video');
                return video.currentTime > 0 && !video.paused;
            }""")
            page.mouse.move(0, 0)
            page.wait_for_function("document.querySelector('#manageList .manage-preview video').paused")
            preview.hover()
            page.wait_for_function("""() => {
                const video = document.querySelector('#manageList .manage-preview video');
                return video.currentTime > 0 && !video.paused;
            }""")
            page.emulate_media(reduced_motion="reduce")
            page.wait_for_function("document.querySelector('#manageList .manage-preview video').paused")
            page.reload(wait_until="domcontentloaded")
            expect(page.locator(".manage-card")).to_contain_text("浏览器上传回归")
            page.locator("#manageList .manage-preview").hover()
            page.wait_for_timeout(250)
            self.assertEqual(page.locator("#manageList .manage-preview video").evaluate_all(SOURCE_COUNT), 0)
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
