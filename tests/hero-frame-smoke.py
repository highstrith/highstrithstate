"""Hero frame regressions in real Chrome with native image/video metadata.

Run against the existing server: python3 tests/hero-frame-smoke.py -v
STUDIO_BASE_URL overrides :3000; HERO_FRAME_CAPTURE_DIR saves screenshots
and compact frame/state observations. No catalogue or media files are changed.
"""
import json
import os
import unittest
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import expect, sync_playwright


BASE = os.environ.get('STUDIO_BASE_URL', 'http://127.0.0.1:3000').rstrip('/')
ROOT = Path(__file__).resolve().parents[1]
WORKS = {work['id']: work for work in json.loads((ROOT / 'data/works.json').read_text())}
CAPTURES = os.environ.get('HERO_FRAME_CAPTURE_DIR')
TOLERANCE = 1

# Observe every rendered frame, retaining changes only. This catches a one-frame
# native-media/intrinsic-size jump that a single post-click measurement misses.
PROBE = """(() => {
  const probe = window.__heroFrameProbe = {samples: [], phase: 'initial', errors: 0};
  document.addEventListener('error', event => {
    if (event.target.id === 'heroPreview') probe.errors++;
  }, true);
  let previous;
  const rect = element => {
    const box = element.getBoundingClientRect();
    return {x: box.x + scrollX, y: box.y + scrollY, width: box.width, height: box.height};
  };
  function observe() {
    const frame = document.querySelector('.feature-screen');
    const poster = document.querySelector('#heroPoster');
    const video = document.querySelector('#heroPreview');
    const picks = document.querySelectorAll('#featureControls .hero-pick');
    if (frame && poster && video && picks.length === 5) {
      const sample = {
        phase: probe.phase,
        work: document.querySelector('#featureControls [aria-pressed="true"]')?.dataset.feature,
        frame: rect(frame), poster: rect(poster), video: rect(video),
        whole: rect(document.querySelector('.hero-feature')),
        sidebar: rect(document.querySelector('.feature-bottom')),
        posterFit: getComputedStyle(poster).objectFit,
        videoFit: getComputedStyle(video).objectFit,
        posterSize: [poster.naturalWidth, poster.naturalHeight],
        videoSize: [video.videoWidth, video.videoHeight],
        ready: video.readyState, source: video.getAttribute('src'),
        previewing: document.querySelector('.hero-feature').classList.contains('is-previewing'),
      };
      const signature = JSON.stringify(sample);
      if (signature !== previous) {
        probe.samples.push(sample);
        previous = signature;
      }
    }
    requestAnimationFrame(observe);
  }
  requestAnimationFrame(observe);
})();"""


class HeroFrameSmoke(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime = sync_playwright().start()
        cls.browser = cls.runtime.chromium.launch(channel='chrome', headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.runtime.stop()

    def page(self, width, language='cn', route=None):
        page = self.browser.new_page(
            viewport={'width': width, 'height': 1100 if width > 800 else 844},
            is_mobile=width <= 800, has_touch=width <= 800,
            reduced_motion='no-preference',
        )
        self.addCleanup(page.close)
        page.set_default_timeout(10000)
        page.add_init_script(PROBE)
        if route:
            page.route('**/*', route)
        page.goto(BASE + ('/?lang=en' if language == 'en' else '/'), wait_until='domcontentloaded')
        expect(page.locator('#featureControls .hero-pick')).to_have_count(5)
        expect(page.locator('html')).to_have_attribute('lang', 'en' if language == 'en' else 'zh-CN')
        page.evaluate('document.fonts.ready')
        # Initial reveal intentionally scales the entire hero. Start the switch
        # contract after that animation, while leaving normal media motion on.
        page.wait_for_function("""() => {
          const hero = document.querySelector('.hero-feature');
          const style = getComputedStyle(hero);
          // Zero-distance parallax retains an identity matrix after the reveal.
          const settled = style.transform === 'none' || new DOMMatrix(style.transform).isIdentity;
          return hero.classList.contains('rv-in') && settled && style.opacity === '1';
        }""")
        page.evaluate("() => { window.__heroFrameProbe.samples = []; window.__heroFrameProbe.phase = 'stable-initial'; }")
        page.wait_for_function('window.__heroFrameProbe.samples.length > 0')
        return page

    def select(self, page, index, phase):
        page.evaluate('(phase) => { window.__heroFrameProbe.phase = phase; }', phase)
        pick = page.locator('#featureControls .hero-pick').nth(index)
        work_id = pick.get_attribute('data-feature')
        # Dispatch the real click handler without scrolling the screen offscreen
        # to reach the mobile controls (which would intentionally unload preview).
        pick.dispatch_event('click')
        expect(pick).to_have_attribute('aria-pressed', 'true')
        return WORKS[work_id]

    def playing(self, page, work):
        page.locator('#heroPoster').evaluate('image => image.decode()')
        page.wait_for_function("""suffix => {
          const video = document.querySelector('#heroPreview');
          return video.currentSrc.endsWith(suffix) && video.videoWidth > 0 &&
            video.videoHeight > 0 && video.currentTime > 0 && !video.paused;
        }""", arg=work['previewVideo'])
        # The outgoing canvas and incoming video each dissolve for 500ms.
        # Include both the transition and settled frames in the observation.
        page.wait_for_timeout(560)

    def assert_fixed_frame(self, page, label):
        samples = page.evaluate('window.__heroFrameProbe.samples')
        self.assertTrue(samples, 'No rendered hero frames observed')
        if CAPTURES:
            directory = Path(CAPTURES)
            directory.mkdir(parents=True, exist_ok=True)
            (directory / (label + '.json')).write_text(json.dumps(samples, ensure_ascii=False, indent=2))
            page.screenshot(path=str(directory / (label + '.png')), full_page=False)
        first = samples[0]['frame']
        failures = set()
        for sample in samples:
            frame = sample['frame']
            location = sample['work'] + '/' + sample['phase']
            if abs(frame['width'] - first['width']) > TOLERANCE or abs(frame['height'] - first['height']) > TOLERANCE:
                failures.add('%s: frame %.2f×%.2f changed from %.2f×%.2f' % (
                    location, frame['width'], frame['height'], first['width'], first['height']))
            if page.viewport_size['width'] <= 800 and abs(frame['height'] - frame['width'] * 9 / 16) > TOLERANCE:
                failures.add('%s: frame %.2f×%.2f is not 16:9' % (location, frame['width'], frame['height']))
            if page.viewport_size['width'] > 800:
                for region in ('whole', 'sidebar'):
                    original = samples[0][region]
                    if any(abs(sample[region][key] - original[key]) > TOLERANCE for key in ('width', 'height')):
                        failures.add('%s: %s resized from %s to %s' % (location, region, original, sample[region]))
            for layer in ('poster', 'video'):
                if any(abs(sample[layer][key] - frame[key]) > TOLERANCE for key in ('x', 'y', 'width', 'height')):
                    failures.add('%s: %s escaped the fixed frame: %s' % (location, layer, sample[layer]))
            if sample['posterFit'] != sample['videoFit']:
                failures.add('%s: poster/video fit differ: %s/%s' % (location, sample['posterFit'], sample['videoFit']))
        if failures:
            self.fail(label + '\n' + '\n'.join(sorted(failures)))

    def test_five_films_and_return_keep_frame_during_real_metadata_and_dissolves(self):
        for width in (1440, 1100, 820, 390):
            for language in ('cn', 'en'):
                with self.subTest(width=width, language=language):
                    page = self.page(width, language)
                    try:
                        loaded = []
                        for step, index in enumerate((0, 1, 2, 3, 4, 0)):
                            work = self.select(page, index, 'switch-%s' % step)
                            self.playing(page, work)
                            loaded.append(page.locator('#heroPreview').evaluate('v => [v.videoWidth, v.videoHeight]'))
                        # Test the actual portrait preview too, rather than a single
                        # landscape fixture standing in for every video aspect ratio.
                        self.assertTrue(any(height > width for width, height in loaded), loaded)
                        self.assert_fixed_frame(page, 'real-%s-%s' % (width, language))
                    finally:
                        page.close()

    def test_delayed_and_failed_previews_do_not_resize_poster_or_frame(self):
        for width in (1100, 390):
            for mode in ('delayed', 'failed'):
                with self.subTest(width=width, mode=mode):
                    pending = []
                    state = {'hold': True}

                    def media_route(route):
                        path = urlsplit(route.request.url).path
                        if not path.endswith('.mp4'):
                            route.continue_()
                        elif mode == 'failed':
                            route.abort('failed')
                        elif state['hold']:
                            pending.append(route)
                        else:
                            route.continue_()

                    page = self.page(width, route=media_route)
                    try:
                        for step, index in enumerate((0, 1, 2, 3, 4, 0)):
                            state['hold'] = True
                            errors_before = page.evaluate('window.__heroFrameProbe.errors')
                            work = self.select(page, index, 'switch-%s-%s' % (step, mode))
                            page.locator('#heroPoster').evaluate('image => image.decode()')
                            page.wait_for_timeout(650)
                            if mode == 'delayed':
                                self.assertTrue(pending, 'Expected a real media request held before metadata')
                                self.assertEqual(page.locator('#heroPreview').evaluate('v => v.readyState'), 0)
                                state['hold'] = False
                                while pending:
                                    pending.pop(0).continue_()
                                self.playing(page, work)
                            elif step:
                                page.wait_for_function('(before) => window.__heroFrameProbe.errors > before', arg=errors_before)
                                self.assertFalse(page.locator('#heroPreview').get_attribute('src'))
                        self.assert_fixed_frame(page, '%s-%s' % (mode, width))
                    finally:
                        page.close()


if __name__ == '__main__':
    unittest.main()
