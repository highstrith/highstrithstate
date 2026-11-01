"""The floating chapter navigator reaches real sections and both page boundaries."""
import os
import unittest
from playwright.sync_api import sync_playwright, expect

BASE = os.environ.get('STUDIO_BASE_URL', 'http://127.0.0.1:3000').rstrip('/')
SECTIONS = ['flyWorks', 'works', 'in-progress', 'stills', 'projects', 'filmRecommendations', 'about', 'contact']


class SectionJump(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime = sync_playwright().start()
        cls.browser = cls.runtime.chromium.launch(channel='chrome', headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.runtime.stop()

    def page(self, width=1440, height=900, motion='reduce', javascript=True):
        page = self.browser.new_page(viewport={'width': width, 'height': height},
                                     reduced_motion=motion, java_script_enabled=javascript)
        self.addCleanup(page.context.close)
        page.goto(BASE, wait_until='load')
        if javascript:
            page.wait_for_selector('.work-card')
        return page

    def open(self, page):
        page.locator('#sectionJump > summary').click()
        expect(page.locator('#sectionJump')).to_have_attribute('open', '')

    def test_each_chapter_link_lands_at_its_section_and_closes_the_panel(self):
        page = self.page()
        expect(page.locator('#sectionJump')).to_have_count(1)
        for section in SECTIONS:
            self.open(page)
            page.locator(f'#sectionJump a[href="#{section}"]').click()
            expect(page.locator('#sectionJump')).not_to_have_attribute('open', '')
            expect(page).to_have_url(BASE + '/#' + section)
            expect(page.locator('#' + section)).to_be_focused()
            # The immersive screening keeps the existing header inset; the
            # other chapters already include their own header clearance.
            expected_top = 110 if section == 'flyWorks' else 0
            self.assertAlmostEqual(page.locator('#' + section).bounding_box()['y'], expected_top, delta=2)
        self.open(page)
        expect(page.locator('#sectionJump a[href="#contact"]')).to_have_attribute('aria-current', 'location')

    def test_top_bottom_use_quick_existing_scroll_and_respect_reduced_motion(self):
        for motion in ['reduce', 'no-preference']:
            page = self.page(motion=motion)
            self.open(page)
            page.locator('#sectionJump a[href="#pageBottom"]').click()
            page.wait_for_function('Math.abs(scrollY + innerHeight - document.documentElement.scrollHeight)<3')
            self.open(page)
            page.locator('#sectionJump a[href="#home"]').click()
            page.wait_for_function('scrollY<2')
            expect(page.locator('#home')).to_be_focused()
            page.close()

    def test_keyboard_escape_outside_click_and_language_theme(self):
        page = self.page()
        toggle = page.locator('#sectionJump > summary')
        toggle.focus()
        page.keyboard.press('Enter')
        page.keyboard.press('Tab')
        expect(page.locator('#sectionJump a[href="#home"]')).to_be_focused()
        page.keyboard.press('Escape')
        expect(toggle).to_be_focused()
        expect(page.locator('#sectionJump')).not_to_have_attribute('open', '')
        self.open(page)
        page.locator('#heroTitle').click()
        expect(page.locator('#sectionJump')).not_to_have_attribute('open', '')
        page.locator('#langSwitch').click()
        self.open(page)
        expect(page.locator('#sectionJump a[href="#pageBottom"]')).to_have_text('Bottom')
        expect(page.locator('#sectionJump a[href="#projects"]')).to_contain_text('Director Workbench')
        light = toggle.evaluate('e=>getComputedStyle(e).backgroundColor')
        page.locator('#themeToggle').click()
        self.assertNotEqual(light, toggle.evaluate('e=>getComputedStyle(e).backgroundColor'))

    def test_small_screens_and_no_script_keep_a_usable_menu(self):
        for width, height in [(320, 568), (390, 844), (844, 390)]:
            page = self.page(width, height)
            self.open(page)
            for selector in ['#sectionJump > summary', '#sectionJump nav']:
                box = page.locator(selector).bounding_box()
                self.assertGreaterEqual(box['x'], 8)
                self.assertGreaterEqual(box['y'], 8)
                self.assertLessEqual(box['x'] + box['width'], width - 8)
                self.assertLessEqual(box['y'] + box['height'], height - 8)
            self.assertGreaterEqual(page.locator('#sectionJump > summary').bounding_box()['height'], 44)
            self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'), width)
            page.close()
        page = self.page(390, 844, javascript=False)
        self.open(page)
        expect(page.locator('#sectionJump a[data-jump-section]')).to_have_count(8)
        page.locator('#sectionJump a[href="#projects"]').click()
        expect(page.locator('#projects')).to_be_in_viewport()

    def test_collapsed_control_shows_the_existing_logo_without_visible_words(self):
        page = self.page()
        toggle = page.locator('#sectionJump > summary')
        expect(toggle).to_have_text('')
        expect(toggle).to_have_accessible_name('展开区块导航')
        self.assertEqual(toggle.locator('svg path').get_attribute('d'),
                         page.locator('.brand-mark path').get_attribute('d'))
        self.open(page)
        expect(page.locator('#sectionJump nav')).to_be_visible()

    def test_jump_eases_in_and_out_while_screening_cards_stay_frozen(self):
        page = self.page(motion='no-preference')
        page.wait_for_selector('.fly-card', state='attached')
        self.open(page)
        page.evaluate('''()=>{
          window.jumpSamples=[];
          document.addEventListener('click',function start(event){
            if(!event.target.closest('#sectionJump a[href="#contact"]'))return;
            document.removeEventListener('click',start,true);
            const began=performance.now();
            function sample(now){
              jumpSamples.push({t:now-began,y:scrollY,
                cards:[...document.querySelectorAll('.fly-card')].map(e=>e.style.cssText).join('|')});
              if(now-began<950)requestAnimationFrame(sample);
              else window.jumpSampleDone=true;
            }
            requestAnimationFrame(sample);
          },true);
        }''')
        page.locator('#sectionJump a[href="#contact"]').click()
        page.wait_for_function('window.jumpSampleDone')
        samples = page.evaluate('jumpSamples')
        end = samples[-1]['y']
        moving = [s for s in samples if s['y'] > 0 and s['y'] < end * .999]
        self.assertGreater(len(moving), 5)
        finish = next(s['t'] for s in samples if s['y'] >= end * .999)
        quarter = min(samples, key=lambda s: abs(s['t'] - finish * .25))['y'] / end
        three_quarters = min(samples, key=lambda s: abs(s['t'] - finish * .75))['y'] / end
        self.assertLess(quarter, .3, 'A jump should start gently, not at its maximum velocity')
        self.assertGreater(three_quarters, .7)
        self.assertLess(finish, 800)
        self.assertEqual(len({s['cards'] for s in moving}), 1, 'Passing the screening must not play the spiral')
        page.evaluate('''()=>{
          const e=document.querySelector('#flyWorks');
          scrollTo({top:scrollY+e.getBoundingClientRect().top+(e.offsetHeight-innerHeight)*.3,behavior:'instant'});
        }''')
        page.wait_for_timeout(300)
        before = page.locator('.fly-card').first.get_attribute('style')
        page.evaluate('scrollBy({top:180,behavior:"instant"})')
        page.wait_for_function('(before)=>document.querySelector(".fly-card").getAttribute("style")!==before', arg=before)

    def test_manual_input_cancels_a_jump_and_releases_the_screening(self):
        page = self.page(motion='no-preference')
        self.open(page)
        page.locator('#sectionJump a[href="#contact"]').evaluate('e=>e.click()')
        page.wait_for_function('scrollY>5')
        page.keyboard.press('Escape')
        position = page.evaluate('scrollY')
        page.wait_for_timeout(700)
        self.assertAlmostEqual(page.evaluate('scrollY'), position, delta=2)
        self.assertFalse(page.locator('html').evaluate('e=>e.classList.contains("anchor-jumping")'))


if __name__ == '__main__':
    unittest.main()
