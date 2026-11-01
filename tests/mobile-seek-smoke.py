"""Use real media and CDP touch input to scrub the current film before touchend."""
import os
import re
import unittest
from playwright.sync_api import sync_playwright, expect

BASE = os.environ.get('STUDIO_BASE_URL', 'http://127.0.0.1:3000').rstrip('/')


class MobileSeek(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime = sync_playwright().start()
        cls.browser = cls.runtime.chromium.launch(channel='chrome', headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.runtime.stop()

    def page(self, width=390, height=844, english=False, portrait=False):
        page = self.browser.new_page(viewport={'width': width, 'height': height},
                                     is_mobile=True, has_touch=True, reduced_motion='reduce')
        self.addCleanup(page.context.close)
        page.goto(BASE + ('/?lang=en#works' if english else '/#works'), wait_until='load')
        if portrait:
            page.locator('#featureControls button').last.click()
            page.locator('[data-hero-play]').click()
        else:
            page.locator('.work-card').first.click()
        page.wait_for_function('''()=>{
          const v=document.querySelector('#workPlayerVideo');return v.readyState>=2&&v.duration>0;
        }''')
        return page

    def position(self, page, time=20, playing=False):
        page.locator('#workPlayerVideo').evaluate('(v,t)=>{v.pause();v.currentTime=t}', time)
        page.wait_for_function('!document.querySelector("#workPlayerVideo").seeking')
        if playing:
            page.locator('#workPlayerVideo').evaluate('v=>v.play()')
            page.wait_for_function('!document.querySelector("#workPlayerVideo").paused')

    def touch(self, session, kind, x=None, y=None):
        points = [] if kind in ['touchEnd', 'touchCancel'] else [{'x': x, 'y': y}]
        session.send('Input.dispatchTouchEvent', {'type': kind, 'touchPoints': points})

    def test_ten_second_buttons_seek_exactly_and_clamp_to_film_boundaries(self):
        page = self.page()
        self.position(page)
        page.locator('#playerForward10').click()
        page.wait_for_function('!document.querySelector("#workPlayerVideo").seeking')
        self.assertAlmostEqual(page.locator('#workPlayerVideo').evaluate('v=>v.currentTime'), 30, delta=.15)
        self.assertTrue(page.locator('#workPlayerVideo').evaluate('v=>v.paused'))
        page.locator('#playerRewind10').click()
        self.assertAlmostEqual(page.locator('#workPlayerVideo').evaluate('v=>v.currentTime'), 20, delta=.15)
        self.position(page, 3)
        page.locator('#playerRewind10').click()
        self.assertAlmostEqual(page.locator('#workPlayerVideo').evaluate('v=>v.currentTime'), 0, delta=.15)
        duration = page.locator('#workPlayerVideo').evaluate('v=>v.duration')
        self.position(page, duration - 2)
        page.locator('#playerForward10').click()
        self.assertAlmostEqual(page.locator('#workPlayerVideo').evaluate('v=>v.currentTime'), duration, delta=.15)

    def test_swipe_updates_a_real_video_frame_before_release_and_keeps_the_same_work(self):
        page = self.page()
        self.position(page)
        title = page.locator('#playerTitle').inner_text()
        source = page.locator('#workPlayerVideo').get_attribute('src')
        box = page.locator('#workPlayerVideo').bounding_box()
        x, y = box['x'] + box['width'] * .3, box['y'] + box['height'] * .35
        touch = page.context.new_cdp_session(page)
        page.locator('#workPlayerVideo').evaluate('''v=>{
          window.seekFramePresented=false;
          v.requestVideoFrameCallback(function frame(t,m){
            if(m.mediaTime>21) window.seekFramePresented=true;
            else v.requestVideoFrameCallback(frame);
          });
        }''')
        self.touch(touch, 'touchStart', x, y)
        self.touch(touch, 'touchMove', x + box['width'] * .18, y + 2)
        page.wait_for_function('document.querySelector("#workPlayerVideo").currentTime>21')
        page.wait_for_function('window.seekFramePresented')
        expect(page.locator('#workPlayer')).to_have_class(re.compile('is-scrubbing'))
        self.assertTrue(page.locator('#workPlayerVideo').evaluate('v=>v.paused'))
        self.touch(touch, 'touchEnd')
        expect(page.locator('#playerTitle')).to_have_text(title)
        expect(page.locator('#workPlayerVideo')).to_have_attribute('src', source)
        self.assertTrue(page.locator('#workPlayerVideo').evaluate('v=>v.paused'))

    def test_release_restores_playback_and_vertical_gestures_do_not_start_scrubbing(self):
        page = self.page()
        self.position(page, 25, playing=True)
        box = page.locator('#workPlayerVideo').bounding_box()
        x, y = box['x'] + box['width'] * .65, box['y'] + box['height'] * .3
        touch = page.context.new_cdp_session(page)
        self.touch(touch, 'touchStart', x, y)
        self.touch(touch, 'touchMove', x - box['width'] * .15, y)
        page.wait_for_function('document.querySelector("#workPlayerVideo").currentTime<24')
        self.touch(touch, 'touchEnd')
        page.wait_for_function('!document.querySelector("#workPlayerVideo").paused')
        self.touch(touch, 'touchStart', x, y)
        self.touch(touch, 'touchMove', x + 3, y + 70)
        self.assertFalse(page.locator('#workPlayer').evaluate('e=>e.classList.contains("is-scrubbing")'))
        self.touch(touch, 'touchEnd')

    def test_controls_fit_portrait_landscape_and_english_labels(self):
        for width, height in [(320, 740), (390, 844), (844, 390)]:
            for portrait in [False, True]:
                page = self.page(width, height, english=True, portrait=portrait)
                if portrait:
                    self.assertTrue(page.locator('#workPlayer').evaluate('e=>e.classList.contains("is-portrait")'))
                expect(page.locator('#playerRewind10')).to_have_accessible_name('Back 10 seconds')
                expect(page.locator('#playerForward10')).to_have_accessible_name('Forward 10 seconds')
                for selector in ['#playerRewind10', '#playerForward10']:
                    expect(page.locator(selector)).to_be_in_viewport(ratio=1)
                    self.assertGreaterEqual(page.locator(selector).bounding_box()['height'], 44)
                self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'), width)
                page.close()

    def test_native_control_strip_is_excluded_and_close_discards_an_active_gesture(self):
        page = self.page()
        self.position(page)
        box = page.locator('#workPlayerVideo').bounding_box()
        touch = page.context.new_cdp_session(page)
        x, y = box['x'] + box['width'] * .3, box['y'] + box['height'] - 18
        self.touch(touch, 'touchStart', x, y)
        self.touch(touch, 'touchMove', x + 70, y)
        self.assertFalse(page.locator('#workPlayer').evaluate('e=>e.classList.contains("is-scrubbing")'))

        self.touch(touch, 'touchEnd')
        y = box['y'] + box['height'] * .35
        self.touch(touch, 'touchStart', x, y)
        self.touch(touch, 'touchMove', x + 70, y)
        page.wait_for_function('document.querySelector("#workPlayer").classList.contains("is-scrubbing")')
        page.locator('#workPlayerClose').click()
        self.touch(touch, 'touchEnd')
        page.locator('.work-card').nth(1).click()
        page.wait_for_function('document.querySelector("#workPlayerVideo").readyState>=2')
        self.assertLess(page.locator('#workPlayerVideo').evaluate('v=>v.currentTime'), 5)
        self.assertFalse(page.locator('#workPlayer').evaluate('e=>e.classList.contains("is-scrubbing")'))

    def test_ten_second_buttons_keep_native_keyboard_activation(self):
        page = self.page()
        self.position(page)
        page.locator('#playerForward10').focus()
        page.keyboard.press('Space')
        self.assertAlmostEqual(page.locator('#workPlayerVideo').evaluate('v=>v.currentTime'), 30, delta=.2)
        self.assertTrue(page.locator('#workPlayerVideo').evaluate('v=>v.paused'))


if __name__ == '__main__':
    unittest.main()
