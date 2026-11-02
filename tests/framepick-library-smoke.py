"""Real browser paths for the public Framepick catalogue (no mock membership)."""
import os
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import framepick_layout as fp  # noqa: E402

from playwright.sync_api import sync_playwright, expect

BASE = os.environ.get('STUDIO_BASE_URL', 'http://127.0.0.1:3000').rstrip('/')


class FramepickLibrary(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime = sync_playwright().start()
        cls.browser = cls.runtime.chromium.launch(channel='chrome', headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.runtime.stop()

    def setUp(self):
        self.context = self.browser.new_context(viewport={'width': 1440, 'height': 1000}, reduced_motion='reduce')
        self.page = self.context.new_page()
        self.errors = []
        self.page.on('pageerror', lambda error: self.errors.append(str(error)))

    def tearDown(self):
        self.context.close()
        self.assertEqual(self.errors, [])

    def open(self, query=''):
        self.page.goto(BASE + fp.url(query), wait_until='load')

    def cards(self):
        return self.page.locator('#filmGrid [data-film]:visible')

    def test_search_category_and_source(self):
        self.open()
        expect(self.cards()).to_have_count(3)
        self.page.locator('#filmSearch').fill('Mx-Shell')
        expect(self.cards()).to_have_count(1)
        expect(self.cards()).to_contain_text('烬海棠')
        self.page.locator('#filmSearch').fill('')
        self.page.locator('#genreFilter').select_option('xianxia')
        expect(self.cards()).to_have_count(1)
        expect(self.cards()).to_contain_text('燕然')
        self.page.locator('#sourceFilter').select_option('bilibili')
        expect(self.cards()).to_have_count(0)
        expect(self.page.locator('#emptyState')).to_be_visible()
        self.page.locator('#resetFilters').click()
        expect(self.cards()).to_have_count(3)
        self.page.locator('[data-category="short"]').click()
        expect(self.cards()).to_have_count(0)
        self.page.locator('#resetFilters').click()
        self.page.locator('button[data-category="series"]').click()
        expect(self.cards()).to_have_count(3)

    def test_unknown_scores_and_paid_screenings_are_honest_empty_states(self):
        self.open()
        expect(self.page.locator('#filmGrid .score')).to_have_text(['待评', '待评', '待评'])
        self.page.locator('#scoreFilter').select_option('8')
        expect(self.cards()).to_have_count(0)
        expect(self.page.locator('#emptyState')).to_contain_text('评分')
        self.page.locator('#resetFilters').click()
        self.page.locator('#accessFilter').select_option('paid')
        expect(self.cards()).to_have_count(0)
        expect(self.page.locator('#emptyState')).to_contain_text('付费放映')
        self.page.locator('[data-membership]').first.click()
        expect(self.page.locator('#membershipDialog')).to_be_visible()
        expect(self.page.locator('#membershipDialog')).to_contain_text('尚未开放购票')
        self.assertEqual(self.page.locator('input[type="password"], input[name="card"], [data-vip-toggle]').count(), 0)
        self.page.keyboard.press('Escape')
        expect(self.page.locator('#membershipDialog')).not_to_be_visible()

    def test_cinema_and_creator_model_is_clear_without_fake_checkout(self):
        self.open()
        expect(self.page.locator('.intro-note')).to_contain_text('AI 电影线上影院')
        expect(self.page.locator('#membership')).to_contain_text('单片观影')
        expect(self.page.locator('#membership')).to_contain_text('3 元 / 5 元')
        expect(self.page.locator('#cinemaPlan')).to_contain_text('40 分钟内')
        expect(self.page.locator('#cinemaPlan')).to_contain_text('每笔有效订单')
        expect(self.page.locator('#cinemaPlan')).to_contain_text('创作者工作台尚未开放')
        expect(self.page.get_by_role('link', name='交流作品合作')).to_have_attribute('href', re.compile('^mailto:'))
        expect(self.page.locator('body')).not_to_contain_text('帧选 VIP')
        self.page.get_by_role('button', name='了解单片观影计划').click()
        expect(self.page.locator('#membershipDialog')).to_contain_text('观看期限')
        expect(self.page.locator('#membershipDialog')).to_contain_text('尚未开放购票')
        self.page.keyboard.press('Escape')
        self.open('?access=vip')
        expect(self.page.locator('#accessFilter')).to_have_value('paid')
        expect(self.cards()).to_have_count(0)
        expect(self.page.locator('#emptyState')).to_contain_text('付费放映')

    def test_rating_sort_is_numeric_and_unrated_stays_last(self):
        source = (fp.SITE_ROOT / 'index.html').read_text()
        for film_id, score in [('xianggu', '8.6'), ('jinhaitang', '10'), ('yanran', '')]:
            source, n = re.subn(r'(<article\b[^>]*data-film="' + film_id + r'"[^>]*data-score=")[^"]*(")',
                                lambda m: m[1] + score + m[2], source)
            self.assertEqual(n, 1, film_id)
        self.page.route(fp.is_index, lambda route: route.fulfill(body=source, content_type='text/html'))
        self.open()
        self.page.locator('#sortFilter').select_option('score')
        self.assertEqual(self.cards().evaluate_all('cards=>cards.map(c=>c.dataset.film)'), ['jinhaitang', 'xianggu', 'yanran'])
        self.page.locator('#scoreFilter').select_option('9')
        expect(self.cards()).to_have_count(1)
        expect(self.cards()).to_contain_text('烬海棠')

    def test_url_refresh_back_and_detail_focus(self):
        self.open('?q=燕然&source=douyin')
        expect(self.cards()).to_have_count(1)
        self.page.reload()
        expect(self.page.locator('#filmSearch')).to_have_value('燕然')
        opener = self.page.locator('button[data-open-film="yanran"]')
        opener.click()
        expect(self.page.locator('#filmDialog')).to_be_visible()
        expect(self.page.locator('#detailTitle')).to_have_text('燕然')
        expect(self.page.locator('#detailWatch')).to_have_attribute('href', 'https://www.douyin.com/video/7675665548755176758')
        self.assertIn('film=yanran', self.page.url)
        self.page.keyboard.press('Escape')
        expect(self.page.locator('#filmDialog')).not_to_be_visible()
        expect(opener).to_be_focused()
        self.page.go_forward()
        expect(self.page.locator('#filmDialog')).to_be_visible()
        self.page.go_back()
        expect(self.page.locator('#filmDialog')).not_to_be_visible()

    def test_deep_link_and_unknown_values_are_safe(self):
        self.open('?film=xianggu&source=bogus&rating=nope')
        expect(self.page.locator('#filmDialog')).to_be_visible()
        expect(self.page.locator('#detailTitle')).to_have_text('相骨')
        self.page.keyboard.press('Escape')
        expect(self.page.locator('#filmDialog')).not_to_be_visible()
        expect(self.cards()).to_have_count(3)
        self.page.locator('#filmSearch').fill('<img src=x onerror=alert(1)>')
        expect(self.cards()).to_have_count(0)
        expect(self.page.locator('#emptyState img')).to_have_count(0)

    def test_bookmarks_persist_and_storage_failure_is_nonfatal(self):
        self.open()
        save = self.page.locator('[data-save-film="jinhaitang"]').first
        save.click()
        expect(save).to_have_attribute('aria-pressed', 'true')
        self.page.reload()
        expect(self.page.locator('[data-save-film="jinhaitang"]').first).to_have_attribute('aria-pressed', 'true')
        self.page.locator('#savedToggle').click()
        expect(self.cards()).to_have_count(1)
        self.page.locator('[data-save-film="jinhaitang"]').first.click()
        expect(self.cards()).to_have_count(0)
        expect(self.page.locator('#emptyState')).to_contain_text('收藏')
        blocked = self.browser.new_context()
        self.addCleanup(blocked.close)
        blocked.add_init_script("Object.defineProperty(window,'localStorage',{get(){throw new DOMException('blocked','SecurityError')}})")
        page = blocked.new_page()
        page.goto(BASE + fp.url())
        page.locator('[data-save-film="xianggu"]').first.click()
        expect(page.locator('#notice')).to_contain_text('本次浏览')
        page.locator('#savedToggle').click()
        expect(page.locator('#filmGrid [data-film]:visible')).to_have_count(1)

    def test_responsive_nojs_and_file_mode(self):
        self.open()
        for width in [320, 390, 820, 1440, 1920]:
            self.page.set_viewport_size({'width': width, 'height': 900})
            self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'), width)
            self.page.locator('button[data-open-film="xianggu"]').click()
            expect(self.page.locator('#filmDialog')).to_be_visible()
            self.assertLessEqual(self.page.locator('#filmDialog').bounding_box()['width'], width)
            self.page.keyboard.press('Escape')
        context = self.browser.new_context(java_script_enabled=False, viewport={'width': 320, 'height': 844})
        self.addCleanup(context.close)
        page = context.new_page()
        page.goto(BASE + fp.url())
        expect(page.locator('#filmGrid [data-film]')).to_have_count(3)
        expect(page.locator('#filmGrid .watch')).to_have_count(3)
        expect(page.locator('#filmSearch')).not_to_be_visible()
        expect(page.get_by_role('link', name='橘小桔的主页')).to_be_visible()
        self.page.goto((fp.SITE_ROOT / 'index.html').as_uri())
        self.page.locator('#filmSearch').fill('相骨')
        expect(self.cards()).to_have_count(1)

    def test_keyboard_bookmark_focus_survives_saving_and_removing(self):
        self.open()
        save = self.page.locator('button[data-save-film="jinhaitang"]').first
        save.focus()
        self.page.keyboard.press('Enter')
        expect(save).to_have_attribute('aria-pressed', 'true')
        expect(save).to_be_focused()
        self.page.locator('#savedToggle').click()
        save.focus()
        self.page.keyboard.press('Enter')
        expect(self.cards()).to_have_count(0)
        expect(self.page.locator('#resetFilters')).to_be_focused()

    def test_mobile_controls_keep_accessible_names(self):
        self.page.set_viewport_size({'width': 390, 'height': 844})
        self.open()
        expect(self.page.locator('#savedToggle')).to_have_accessible_name(re.compile('我的收藏'))
        expect(self.page.locator('#sortFilter')).to_have_accessible_name('排序')


if __name__ == '__main__':
    unittest.main()
