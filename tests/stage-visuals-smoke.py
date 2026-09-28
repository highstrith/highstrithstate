"""Stage regressions against the real Chromium renderer and native animations.

Breaks caught: cropped/retinted media, misaligned rows, oversized Hero, replayed
entrances, animations surviving a motion-setting change, and stale player exits.
The recorder forwards Element.animate unchanged; it never substitutes animations.
Run with serve.js on :3000: python3 tests/stage-visuals-smoke.py
"""
import json
import unittest
from pathlib import Path
from playwright.sync_api import sync_playwright

CATALOG = json.loads((Path(__file__).resolve().parents[1] / "data/works.json").read_text())
RECORDER = """window.motionRecords = [];
const nativeAnimate = Element.prototype.animate;
Element.prototype.animate = function(frames, options) {
  const animation = nativeAnimate.call(this, frames, options);
  window.motionRecords.push({element: this, frames, options, animation});
  return animation;
};"""


class StageVisuals(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime = sync_playwright().start()
        cls.browser = cls.runtime.chromium.launch(channel="chrome", headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.runtime.stop()

    def page(self, record=False, **options):
        page = self.browser.new_page(**options)
        page.set_default_timeout(10000)
        self.addCleanup(page.close)
        if record:
            page.add_init_script(RECORDER)
        return page

    def ready(self, page, hash=""):
        page.goto("http://127.0.0.1:3000/" + hash, wait_until="domcontentloaded")
        page.wait_for_function("document.querySelectorAll('.work-card').length === 8")
        page.wait_for_function("document.querySelector('.work-card source')?.dataset.src.includes('optimized')")

    def test_layout_keeps_complete_media_and_first_screen_work_visible(self):
        for width, height in [(1440, 900), (820, 950), (390, 844), (320, 760)]:
            with self.subTest(width=width):
                page = self.page(viewport={"width": width, "height": height}, reduced_motion="reduce")
                self.ready(page)
                page.evaluate("document.fonts.ready")
                for lang in ("cn", "en"):
                    if lang == "en":
                        page.locator("#langSwitch").click()
                    self.assertFalse(page.evaluate("document.documentElement.scrollWidth > innerWidth"))
                    hero_height = page.locator(".hero").bounding_box()["height"]
                    if width > 700:
                        self.assertTrue(540 <= hero_height <= 580, hero_height)
                    elif width == 390:
                        self.assertTrue(450 <= hero_height <= 480, hero_height)
                    self.assertLess(page.locator(".hero .cta-row").bounding_box()["y"] + page.locator(".hero .cta-row").bounding_box()["height"], height)
                    frame = page.locator(".video-shell").first.bounding_box()
                    if width in (1440, 390):
                        self.assertGreaterEqual(min(frame["height"], height - frame["y"]), 80 if width == 1440 else 60)
                    rows = page.locator(".work-card").evaluate_all("""cards => cards.map(card => {
                      const frame = card.querySelector('.video-shell').getBoundingClientRect();
                      const info = card.querySelector('.work-info').getBoundingClientRect();
                      return {top: frame.top, ratio: frame.width / frame.height, info: info.top};
                    })""")
                    for row in rows:
                        self.assertAlmostEqual(row["ratio"], 16 / 9, places=2)
                    first_row = [r for r in rows if abs(r["top"] - rows[0]["top"]) < 1]
                    self.assertLess(max(r["info"] for r in first_row) - min(r["info"] for r in first_row), 1)
                    media = page.locator(".work-poster, .work-video").evaluate_all("els => els.map(e => {const s=getComputedStyle(e);return [s.objectFit,s.filter,s.transform]})")
                    self.assertTrue(all(s == ["contain", "none", "none"] for s in media), media)
                    self.assertEqual(page.locator(".video-shell").first.evaluate("e => getComputedStyle(e, '::before').content"), "none")
                    typography = page.locator(".work-card").first.evaluate("""e => ['h3','.work-meta p','.work-description'].map(s => parseFloat(getComputedStyle(e.querySelector(s)).fontSize))""")
                    self.assertTrue(all(got >= want for got, want in zip(typography, [16, 13, 14])), typography)
                    description = page.locator(".work-description").first
                    self.assertEqual(description.evaluate("e => e.scrollHeight <= e.clientHeight"), True)
                page.close()

    def test_card_text_has_readable_contrast_and_hover_preserves_picture(self):
        page = self.page(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
        self.ready(page, "#works")
        contrast = page.locator(".work-card").first.evaluate("""card => {
          const rgb = value => value.match(/[\\d.]+/g).map(Number);
          const bg = rgb(getComputedStyle(card).backgroundColor);
          const luminance = values => values.slice(0,3).map(v=>v/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4).reduce((sum,v,i)=>sum+v*[.2126,.7152,.0722][i],0);
          return [...card.querySelectorAll('.work-info p')].map(e=>{
            const fg=rgb(getComputedStyle(e).color), alpha=fg[3]??1;
            const blended=fg.slice(0,3).map((v,i)=>alpha*v+(1-alpha)*bg[i]);
            return (luminance(blended)+.05)/(luminance(bg)+.05);
          });
        }""")
        self.assertTrue(all(value >= 4.5 for value in contrast), contrast)
        card = page.locator(".work-card").first
        card.hover()
        self.assertEqual(card.locator(".work-poster").evaluate("e => getComputedStyle(e).transform"), "none")
        self.assertEqual(card.evaluate("e => getComputedStyle(e).borderRadius"), "16px")
        card.focus()
        self.assertNotEqual(card.evaluate("e => getComputedStyle(e).outlineStyle"), "none")

    def test_hero_runs_once_and_catalogue_language_paging_do_not_replay_it(self):
        page = self.page(record=True, viewport={"width": 1440, "height": 900})
        pending = []
        page.route("**/api/works", lambda route: pending.append(route))
        self.ready(page)
        page.wait_for_function("motionRecords.filter(r=>r.element.matches('.hero-title-line')).length === 2")
        hero = page.evaluate("motionRecords.filter(r=>r.element.closest('.hero')).map(r=>({duration:r.options.duration,delay:r.options.delay||0,frames:r.frames}))")
        self.assertEqual([r["duration"] for r in hero[:2]], [650, 650])
        self.assertEqual([r["delay"] for r in hero[:2]], [0, 100])
        self.assertEqual(hero[0]["frames"][0]["transform"], "translateY(48px)")
        self.assertLessEqual(max(r["duration"] + r["delay"] for r in hero), 1100)
        before = len(hero)
        pending[0].fulfill(json={"works": CATALOG})
        page.wait_for_function("document.querySelector('.work-card h3').textContent === 'AI患者'")
        page.locator("#langSwitch").click()
        page.locator(".works-page-button[data-page='2']").first.click()
        page.locator(".works-page-button[data-page='1']").first.click()
        self.assertEqual(page.evaluate("motionRecords.filter(r=>r.element.closest('.hero')).length"), before)

    def test_mobile_hero_finishes_within_budget(self):
        page = self.page(record=True, viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
        self.ready(page)
        page.wait_for_function("motionRecords.some(r=>r.element.matches('.hero-title-line'))")
        hero = page.evaluate("motionRecords.filter(r=>r.element.closest('.hero')).map(r=>({duration:r.options.duration,delay:r.options.delay||0,frames:r.frames}))")
        self.assertEqual(hero[0]["frames"][0]["transform"], "translateY(24px)")
        self.assertLessEqual(max(r["duration"] + r["delay"] for r in hero), 850)

    def test_entrances_cancel_on_live_reduced_motion_and_stay_visible(self):
        page = self.page(record=True, viewport={"width": 1440, "height": 900})
        self.ready(page)
        page.wait_for_function("motionRecords.some(r=>r.animation.playState === 'running')")
        page.emulate_media(reduced_motion="reduce")
        page.wait_for_function("motionRecords.every(r=>r.animation.playState !== 'running')")
        self.assertTrue(page.locator(".hero-title-line, .hero-visual, .reveal").evaluate_all("els=>els.every(e=>getComputedStyle(e).opacity==='1')"))
        page.emulate_media(reduced_motion="no-preference")
        page.evaluate("scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(550)
        self.assertTrue(page.locator('.reveal').evaluate_all("els=>els.every(e=>getComputedStyle(e).opacity==='1')"))

        page = self.page(record=True, viewport={"width": 1440, "height": 900})
        self.ready(page)
        page.locator("#contact").scroll_into_view_if_needed()
        page.wait_for_function("motionRecords.some(r=>r.element.closest('#contact'))")
        count = page.evaluate("motionRecords.length")
        page.emulate_media(reduced_motion="reduce")
        page.wait_for_function("motionRecords.every(r=>r.animation.playState !== 'running')")
        page.emulate_media(reduced_motion="no-preference")
        page.evaluate("scrollTo(0, 0); scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(550)
        self.assertEqual(page.evaluate("motionRecords.length"), count)

    def test_card_entrance_is_once_per_work_even_after_language_and_return_scroll(self):
        page = self.page(record=True, viewport={"width": 1440, "height": 900})
        self.ready(page)
        page.locator(".work-card").nth(4).scroll_into_view_if_needed()
        page.wait_for_function("motionRecords.filter(r=>r.element.matches('.work-card')).length === 8")
        card_records = page.evaluate("motionRecords.filter(r=>r.element.matches('.work-card')).map(r=>({id:r.element.dataset.workId,delay:r.options.delay,duration:r.options.duration,frames:r.frames}))")
        self.assertEqual(sorted(r["delay"] for r in card_records[:4]), [0, 50, 100, 150])
        self.assertTrue(all(r["duration"] == 450 and r["frames"][0]["transform"] == "translateY(20px)" for r in card_records))
        page.locator("#langSwitch").click()
        page.evaluate("scrollTo(0, 0)")
        page.locator(".work-card").nth(4).scroll_into_view_if_needed()
        page.wait_for_timeout(600)
        self.assertEqual(page.evaluate("motionRecords.filter(r=>r.element.matches('.work-card')).length"), 8)
        self.assertTrue(page.locator(".work-card").evaluate_all("els=>els.every(e=>getComputedStyle(e).opacity==='1')"))

    def test_direct_anchor_and_animation_failure_keep_target_visible(self):
        for setup in ("", "Element.prototype.animate = undefined", "Element.prototype.animate = function(){throw Error('unavailable')} ", "window.IntersectionObserver = undefined"):
            with self.subTest(setup=setup):
                page = self.page(record=True, viewport={"width": 390, "height": 844})
                if setup:
                    page.add_init_script(setup)
                self.ready(page, "#works")
                self.assertTrue(page.locator("#works .section-head, .work-card").evaluate_all("els=>els.every(e=>getComputedStyle(e).opacity==='1' && getComputedStyle(e).transform==='none')"))
                self.assertEqual(page.evaluate("motionRecords.filter(r=>r.element.closest('#works')).length"), 0)
                self.assertEqual(page.evaluate("motionRecords.filter(r=>r.element.closest('.hero')).length"), 0)
                page.close()

    def test_animation_exception_cancels_the_scene_and_keeps_later_content_visible(self):
        page = self.page(record=True, viewport={"width": 1440, "height": 900})
        page.add_init_script("""const recordedAnimate = Element.prototype.animate;
          let calls = 0;
          Element.prototype.animate = function(...args) {
            if (++calls === 2) throw Error('animation engine failed');
            return recordedAnimate.apply(this, args);
          };""")
        self.ready(page)
        self.assertTrue(page.evaluate("motionRecords.every(r=>r.animation.playState === 'idle')"))
        self.assertTrue(page.locator('.hero-title-line, .hero-visual, .hero .lede, .hero .cta-row').evaluate_all("els=>els.every(e=>getComputedStyle(e).opacity==='1')"))
        count = page.evaluate('motionRecords.length')
        page.locator('#contact').scroll_into_view_if_needed()
        page.wait_for_timeout(100)
        self.assertEqual(page.evaluate('motionRecords.length'), count)
        self.assertTrue(page.locator('#contact .reveal').evaluate_all("els=>els.every(e=>getComputedStyle(e).opacity==='1')"))

    def test_hidden_page_cancels_native_animations_and_restore_does_not_replay(self):
        page = self.page(record=True, viewport={"width": 1440, "height": 900})
        self.ready(page)
        page.wait_for_function("motionRecords.some(r=>r.animation.playState === 'running')")
        # Playwright keeps controlled tabs visible even after another tab is activated.
        # Inject only the public visibility signal; animations and page handlers stay native.
        page.evaluate("""Object.defineProperty(document, 'hidden', {configurable:true, value:true});
          document.dispatchEvent(new Event('visibilitychange'));""")
        self.assertTrue(page.evaluate("motionRecords.every(r=>r.animation.playState === 'idle')"))
        self.assertTrue(page.locator('.hero-title-line, .hero-visual, .reveal').evaluate_all("els=>els.every(e=>getComputedStyle(e).opacity==='1')"))
        count = page.evaluate('motionRecords.filter(r=>r.element.closest(".hero")).length')
        page.evaluate("""delete document.hidden; document.dispatchEvent(new Event('visibilitychange'));
          scrollTo(0, document.body.scrollHeight); scrollTo(0, 0);""")
        page.wait_for_timeout(100)
        self.assertEqual(page.evaluate('motionRecords.filter(r=>r.element.closest(".hero")).length'), count)

    def test_player_exit_cleans_immediately_and_cannot_close_a_new_session(self):
        page = self.page(record=True, viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
        self.ready(page, "#works")
        page.locator(".work-card").first.click()
        page.wait_for_function("document.querySelector('#workPlayerVideo').currentTime > 0")
        opening = page.evaluate("motionRecords.filter(r=>r.element.closest('#workPlayer')).map(r=>r.options.duration)")
        self.assertEqual(opening, [220, 220])
        state = page.evaluate("""() => {
          document.querySelector('#workPlayerClose').click();
          const player=document.querySelector('#workPlayer'), video=document.querySelector('#workPlayerVideo');
          const closed={src:video.getAttribute('src'),inert:document.querySelector('.shell').inert,hidden:player.getAttribute('aria-hidden'),pointer:getComputedStyle(player).pointerEvents,focus:document.activeElement===document.querySelector('.work-card')};
          document.querySelectorAll('.work-card')[1].click();
          return closed;
        }""")
        self.assertEqual(state, {"src": None, "inert": False, "hidden": "true", "pointer": "none", "focus": True})
        page.wait_for_function("document.querySelector('#workPlayerVideo').currentTime > 0")
        page.wait_for_timeout(350)
        self.assertEqual(page.locator("#workPlayer").get_attribute("aria-hidden"), "false")
        self.assertTrue(page.locator(".shell").evaluate("e=>e.inert"))
        self.assertEqual(page.locator("#workPlayer").get_attribute("data-state"), "ready")
        self.assertTrue(page.evaluate("motionRecords.some(r=>r.element.closest('#workPlayer') && r.options.duration===140)"))
        page.locator("#workPlayerClose").click()
        page.emulate_media(reduced_motion="reduce")
        page.wait_for_function("getComputedStyle(document.querySelector('#workPlayer')).display === 'none'")
        self.assertTrue(page.locator(".work-card").nth(1).evaluate("e=>document.activeElement===e"))
        self.assertFalse(page.locator("#workPlayer").is_visible())

    def test_no_javascript_frames_keep_original_picture(self):
        page = self.page(viewport={"width": 390, "height": 844}, java_script_enabled=False)
        page.goto("http://127.0.0.1:3000/", wait_until="domcontentloaded")
        self.assertEqual(page.locator(".no-js-work").count(), 13)
        frame = page.locator(".no-js-work img").first
        self.assertEqual(frame.evaluate("e=>getComputedStyle(e).objectFit"), "contain")
        box = frame.bounding_box()
        self.assertAlmostEqual(box["width"] / box["height"], 16 / 9, places=2)
        self.assertFalse(page.evaluate("document.documentElement.scrollWidth > innerWidth"))

    def test_delayed_fullscreen_exit_cannot_reset_a_reopened_player_orientation(self):
        for reopen in (True, False):
            with self.subTest(reopen=reopen):
                page = self.page(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
                # Keep native fullscreen changes; defer only completion of the public exit API.
                page.add_init_script("""const nativeExitFullscreen = document.exitFullscreen.bind(document);
                  document.exitFullscreen = () => {
                    const nativeExit = nativeExitFullscreen();
                    return new Promise((resolve, reject) => {
                      window.completeFullscreenExit = async () => {
                        try { await nativeExit; resolve(); }
                        catch (error) { reject(error); }
                        await Promise.resolve();
                      };
                    });
                  };""")
                self.ready(page, '#works')
                page.locator('.work-card').first.click()
                page.locator('#workPlayerOrientation').click()
                page.wait_for_function("document.fullscreenElement === document.querySelector('#workPlayer')")
                page.wait_for_function("document.querySelector('#workPlayer').dataset.orientation === 'landscape'")
                page.locator('#workPlayerClose').click()
                self.assertEqual(page.locator('#workPlayerVideo').get_attribute('src'), None)
                self.assertFalse(page.locator('.shell').evaluate('e=>e.inert'))
                page.wait_for_function("typeof window.completeFullscreenExit === 'function' && !document.fullscreenElement")

                if reopen:
                    page.locator('.work-card').nth(1).click()
                    page.locator('#workPlayerOrientation').click()
                    page.wait_for_function("document.fullscreenElement === document.querySelector('#workPlayer')")
                    page.wait_for_function("document.querySelector('#workPlayer').dataset.orientation === 'landscape'")
                    before = page.locator('#workPlayer').evaluate("""e=>({orientation:e.dataset.orientation, hidden:e.getAttribute('aria-hidden'), cssLandscape:e.classList.contains('is-css-landscape'), label:document.querySelector('#workPlayerOrientation').getAttribute('aria-label'), title:document.querySelector('#workPlayerOrientation').title})""")
                    self.assertEqual(before['orientation'], 'landscape')
                    self.assertEqual(before['label'], '切换竖屏播放')
                    self.assertEqual(before['hidden'], 'false')

                page.evaluate('window.completeFullscreenExit()')
                if reopen:
                    after = page.locator('#workPlayer').evaluate("""e=>({orientation:e.dataset.orientation, hidden:e.getAttribute('aria-hidden'), cssLandscape:e.classList.contains('is-css-landscape'), label:document.querySelector('#workPlayerOrientation').getAttribute('aria-label'), title:document.querySelector('#workPlayerOrientation').title})""")
                    self.assertEqual(after, before, 'old fullscreen exit must not roll back the new orientation or UI')
                    self.assertTrue(page.locator('.shell').evaluate('e=>e.inert'))
                    self.assertIsNotNone(page.locator('#workPlayerVideo').get_attribute('src'))
                    page.locator('#workPlayerClose').click()
                    page.wait_for_function("!document.fullscreenElement")
                    page.evaluate('window.completeFullscreenExit()')

                self.assertEqual(page.locator('#workPlayer').get_attribute('data-orientation'), 'portrait')
                self.assertEqual(page.locator('#workPlayerOrientation').get_attribute('aria-label'), '切换横屏播放')
                self.assertFalse(page.locator('#workPlayer').evaluate("e=>e.classList.contains('is-css-landscape')"))
                self.assertEqual(page.locator('#workPlayer').get_attribute('aria-hidden'), 'true')
                page.close()


if __name__ == "__main__":
    unittest.main()
