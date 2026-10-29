"""Six films per page, complete search, persistent page and later-film stills."""
import json
import os
import re
import unittest
from pathlib import Path
from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BASE = os.environ.get('STUDIO_BASE_URL', 'http://127.0.0.1:3000').rstrip('/')
WORKS = sorted([w for w in json.loads((ROOT/'data/works.json').read_text()) if w['id'] != 'featured-giant-wheel'], key=lambda w:w.get('createdAt',''), reverse=True)


class CataloguePages(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime = sync_playwright().start()
        cls.browser = cls.runtime.chromium.launch(channel='chrome', headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.runtime.stop()

    def page(self, suffix='/index.html#works', **options):
        page = self.browser.new_page(viewport={'width': 1440, 'height': 1000}, reduced_motion='reduce', **options)
        self.addCleanup(page.context.close)
        page.goto(BASE+suffix, wait_until='load')
        expect(page.locator('.no-js-work' if options.get('java_script_enabled') is False else '.work-card')).to_have_count(len(WORKS))
        return page

    def ids(self, page):
        return page.locator('.work-card:visible').evaluate_all('cards=>cards.map(card=>card.dataset.workId)')

    def test_pages_cover_all_films_without_duplicates(self):
        page = self.page()
        expect(page.locator('.work-card:visible')).to_have_count(6)
        expect(page.locator('#worksPages a')).to_have_count(4)
        expect(page.locator('#worksPagination [aria-current="page"]')).to_have_text('1')
        expect(page.locator('#worksCount')).to_have_text('1–6 / 20 部作品')
        visited = self.ids(page)
        for number in [2,3,4]:
            page.locator(f'#worksPages [data-page="{number}"]').click()
            self.assertEqual(self.ids(page), [w['id'] for w in WORKS[(number-1)*6:number*6]])
            expect(page.locator('#worksTitle')).to_be_focused()
            expect(page.locator('#worksPagination [aria-current="page"]')).to_have_text(str(number))
            visited += self.ids(page)
        self.assertEqual(visited, [w['id'] for w in WORKS])
        self.assertEqual(len(set(visited)),20)
        expect(page.locator('#worksPagination [data-direction="next"]')).to_have_attribute('aria-disabled','true')
        page.locator('#worksPagination [data-direction="previous"]').click()
        self.assertEqual(self.ids(page), [w['id'] for w in WORKS[12:18]])

    def test_global_search_resets_page_and_single_results_hide_controls(self):
        page = self.page('/index.html?page=4#works')
        expect(page.locator('.work-card:visible')).to_have_count(2)
        page.locator('#workSearch').fill('Prove It')
        self.assertEqual(self.ids(page), ['featured-prove-it'])
        expect(page.locator('#worksPagination')).not_to_be_visible()
        self.assertNotIn('page=',page.url)
        page.locator('#workSearch').fill('no-such-film-xyz')
        expect(page.locator('#emptyState')).to_be_visible()
        expect(page.locator('#worksPagination')).not_to_be_visible()
        page.locator('#resetFilters').click()
        self.assertEqual(self.ids(page),[w['id'] for w in WORKS[:6]])

    def test_language_view_refresh_and_browser_back_keep_page(self):
        page = self.page('/index.html?page=3#works')
        expected = self.ids(page)
        self.assertEqual(expected, [w['id'] for w in WORKS[12:18]])
        page.locator('#langSwitch').click()
        page.locator('[data-view="list"]').click()
        self.assertEqual(self.ids(page),expected)
        expect(page.locator('#worksPagination')).to_have_attribute('aria-label','Work pages')
        page.reload(wait_until='load')
        expect(page.locator('.work-card')).to_have_count(20)
        self.assertEqual(self.ids(page),expected)
        expect(page.locator('html')).to_have_attribute('lang','en')
        page.locator('#worksPages [data-page="4"]').click()
        page.locator('#langSwitch').click()
        expect(page.locator('html')).to_have_attribute('lang','zh-CN')
        page.go_back()
        self.assertEqual(self.ids(page),expected)
        expect(page.locator('html')).to_have_attribute('lang','en')
        page.locator('[data-filter="motion"]').click()
        expect(page.locator('#worksPagination [aria-current="page"]')).to_have_text('1')

    def test_later_films_supply_four_new_stills(self):
        page = self.page()
        expect(page.locator('#stillsGrid .still-card')).to_have_count(8)
        images = page.locator('#stillsGrid img').evaluate_all('images=>images.map(image=>image.src)')
        self.assertEqual(len(set(images)),8)
        self.assertTrue(all('/assets/stills/catalogue-' in source for source in images[4:]))
        page.locator('[data-still="4"]').click()
        expect(page.locator('#stillViewerPosition')).to_have_text('05 / 08')
        expect(page.locator('#stillViewerTitle')).to_have_text('酒馆光影')
        page.keyboard.press('Escape')
        captures = os.environ.get('PAGES_CAPTURE_DIR')
        if captures:
            output=Path(captures);output.mkdir(parents=True,exist_ok=True)
            page.locator('#works').evaluate('section=>section.scrollIntoView({behavior:"instant"})')
            page.mouse.move(0,0)
            page.locator('#works').screenshot(path=str(output/'page-one.png'),style='.site-header,.skip-link{visibility:hidden!important}')
            page.locator('#worksPages [data-page="3"]').click()
            for image in page.locator('.work-item:visible img').all():
                image.scroll_into_view_if_needed();image.evaluate('image=>image.decode()')
            page.locator('#works').evaluate('section=>section.scrollIntoView({behavior:"instant"})')
            page.mouse.move(0,0)
            page.locator('#works').screenshot(path=str(output/'page-three.png'),style='.site-header,.skip-link{visibility:hidden!important}')
            for image in page.locator('#stillsGrid img').all():
                image.scroll_into_view_if_needed();image.evaluate('image=>image.decode()')
            page.locator('#stills').screenshot(path=str(output/'stills.png'),style='.site-header,.skip-link{visibility:hidden!important}')

    def test_filtered_url_restores_the_same_results_after_reload(self):
        page=self.page()
        page.locator('[data-filter="motion"]').click()
        page.locator('#worksPages [data-page="2"]').click()
        expected=self.ids(page)
        self.assertIn('category=motion',page.url)
        page.reload(wait_until='load')
        expect(page.locator('.work-card')).to_have_count(20)
        self.assertEqual(self.ids(page),expected)
        expect(page.locator('[data-filter="motion"]')).to_have_attribute('aria-pressed','true')
        shared=self.browser.new_page(reduced_motion='reduce')
        self.addCleanup(shared.context.close)
        shared.goto(page.locator('#worksPages [aria-current="page"]').get_attribute('href'),wait_until='load')
        expect(shared.locator('.work-card')).to_have_count(20)
        self.assertEqual(self.ids(shared),expected)
        page.locator('[data-filter="all"]').click()
        page.locator('#workSearch').fill('Prove It')
        expect(page.locator('.work-card:visible')).to_have_count(1)
        expect(page).to_have_url(re.compile(r'[?&]q=Prove'))
        page.reload(wait_until='load')
        expect(page.locator('.work-card')).to_have_count(20)
        self.assertEqual(self.ids(page),['featured-prove-it'])
        expect(page.locator('#workSearch')).to_have_value('Prove It')

    def test_mobile_controls_and_no_script_catalogue(self):
        page=self.page()
        for width in [320,390,820]:
            page.set_viewport_size({'width':width,'height':1000})
            page.locator('#worksPagination').scroll_into_view_if_needed()
            self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'),width)
            for link in page.locator('#worksPagination a').all():
                self.assertGreaterEqual(link.bounding_box()['height'],44)
        page2=self.page(java_script_enabled=False)
        expect(page2.locator('.no-js-work')).to_have_count(20)
        expect(page2.locator('#worksPagination')).not_to_be_visible()


if __name__=='__main__':
    unittest.main()
