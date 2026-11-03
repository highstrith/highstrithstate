"""Public ranking behavior, using a read-only static fixture and explicit snapshots."""
import functools
import http.server
import re
import sys
import threading
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import framepick_layout as fp  # noqa: E402

from playwright.sync_api import sync_playwright, expect


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


class FramepickRankings(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Combined layout serves the repo root and visits /reel/; standalone serves the site root.
        cls.server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(QuietHandler, directory=str(fp.SITE_SERVE_ROOT)))
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = 'http://127.0.0.1:' + str(cls.server.server_port)
        cls.runtime = sync_playwright().start()
        cls.browser = cls.runtime.chromium.launch(channel='chrome', headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.runtime.stop()
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def setUp(self):
        self.context = self.browser.new_context(viewport={'width': 1440, 'height': 1000}, reduced_motion='reduce')
        self.addCleanup(self.context.close)
        self.page = self.context.new_page()
        self.errors = []
        self.page.on('pageerror', lambda error: self.errors.append(str(error)))
        self.page.clock.install(time=1793577600)  # Python API uses seconds: 2026-11-02 00:00 UTC.
        # These tests are read-only: no review service exists in this fixture.
        self.page.route('**/api/framepick/**', lambda route: route.fulfill(status=503, json={'error': 'Fixture offline'}))

    def tearDown(self):
        self.assertEqual(self.errors, [])

    def open(self, snapshot=None, source=None):
        if snapshot is not None:
            self.page.route('**/api/framepick/outbound/summary', lambda route: route.fulfill(json=snapshot))
        if source is not None:
            self.page.route(fp.is_index, lambda route: route.fulfill(body=source, content_type='text/html'))
        self.page.goto(self.base + fp.url())

    def test_daily_board_lists_today_only_without_any_dates(self):
        # Move every card's intake date onto the frozen "today" (2026-11-02).
        source = (fp.SITE_ROOT / 'index.html').read_text()
        today = '2026-11-02'
        for day in ['2026-10-31', '2026-11-03']:
            source = source.replace(f'data-date="{day}"', f'data-date="{today}"')
        self.open(source=source)
        expect(self.page.locator('#rankings')).to_be_visible()
        # 所有卡片的收录日期都被挪到了"今天"，所以今日榜条数 = 全部卡片数（片库会增长，不写死）。
        # 榜单最多列 8 条，超出的数字写照在状态行与脚注里。
        expected = self.page.locator('#filmGrid [data-film]').count()
        shown = min(expected, 8)
        rows = self.page.locator('#rankingDaily [data-ranking-film]')
        expect(rows).to_have_count(shown)
        expect(self.page.locator('#dailyRankingStatus')).to_have_text(f'今日新收录 {expected} 部')
        if expected > 8:
            expect(self.page.locator('#dailyRankingMore')).to_contain_text(f'其余 {expected - 8} 部')
        else:
            expect(self.page.locator('#dailyRankingMore')).to_be_hidden()
        # 收录日期只用于分组，条目上不出现任何日期。
        labels = rows.evaluate_all("(rows)=>rows.map(row=>row.innerText)")
        for label in labels:
            self.assertNotIn('收录', label)
            self.assertIsNone(re.search(r'\d{1,2}\.\d{1,2}|\d{4}-\d{2}', label), label)
        trigger = rows.first
        trigger.click()
        expect(self.page.locator('#detailTitle')).to_have_text('相骨')
        self.page.keyboard.press('Escape')
        expect(self.page.locator('#filmDialog')).not_to_be_visible()
        expect(trigger).to_be_focused()

    def test_a_long_daily_board_does_not_stretch_the_empty_ones(self):
        # 一天收录十几部时，没有数据的两栏若跟着最高的那栏撑高，页面就只剩左边一列有内容。
        source = (fp.SITE_ROOT / 'index.html').read_text()
        for day in ['2026-10-31', '2026-11-03']:
            source = source.replace(f'data-date="{day}"', 'data-date="2026-11-02"')
        self.open(source=source)
        heights = self.page.evaluate("""() => Object.fromEntries(
            [...document.querySelectorAll('.ranking-board')]
              .map((board) => [board.id, Math.round(board.getBoundingClientRect().height)]))""")
        self.assertGreater(heights['rankingDaily'], heights['rankingPopular'] * 2, '今日榜是有内容的那一栏，不该和空栏一样高')
        self.assertLess(heights['rankingPopular'], 400, heights)
        self.assertLess(heights['rankingAcclaimed'], 400, heights)
        # 只有一栏有内容时：它占满整行，空的两栏并排退到下一行，不留大片空白。
        self.assertIn('is-single', self.page.locator('.ranking-columns').get_attribute('class') or '')
        boxes = self.page.evaluate("""() => Object.fromEntries(
            [...document.querySelectorAll('.ranking-board')]
              .map((board) => { const box = board.getBoundingClientRect();
                return [board.id, { x: Math.round(box.x), y: Math.round(box.y), w: Math.round(box.width) }]; }))""")
        self.assertGreater(boxes['rankingDaily']['w'], boxes['rankingPopular']['w'] * 1.5, boxes)
        self.assertEqual(boxes['rankingPopular']['y'], boxes['rankingAcclaimed']['y'], boxes)
        # 空榜仍然要说清为什么是空的（文案随服务是否可用而变），不能靠留白含糊过去。
        for selector in ['#popularRankingStatus', '#acclaimedRankingStatus']:
            text = self.page.locator(selector).text_content().strip()
            self.assertGreater(len(text), 4, f'{selector} 必须给出空榜原因，当前：{text!r}')

    def test_daily_board_is_empty_when_nothing_was_added_today(self):
        # Cards are dated 2026-10-31 / 2026-11-03; the clock is frozen on 11-02.
        self.open()
        expect(self.page.locator('#rankingDaily [data-ranking-film]')).to_have_count(0)
        expect(self.page.locator('#dailyRankingStatus')).to_have_text('今日暂无新收录。')
        expect(self.page.locator('#rankingPopular')).to_contain_text('去重跳转次数')
        expect(self.page.locator('#rankingPopular')).to_contain_text('暂不可用')
        expect(self.page.locator('#rankingAcclaimed')).to_contain_text('至少 5 人')

    def test_detail_shows_the_original_release_date(self):
        self.open()
        self.page.locator('#filmGrid [data-film="pinzi"] .details-button').click()
        expect(self.page.locator('#detailPublished')).to_have_text('原片发布于 2026.02.03')
        self.page.keyboard.press('Escape')
        self.page.locator('#filmGrid [data-film="yanran"] .details-button').click()
        # Month precision stays month precision; no invented day.
        expect(self.page.locator('#detailPublished')).to_have_text('原片发布于 2026.08')

    def test_popular_uses_current_ten_day_outbound_counts_only(self):
        snapshot = {'metric': 'outbound-clicks', 'windowStart': '2026-10-24', 'windowEnd': '2026-11-02', 'updatedAt': '2026-11-02T00:00:00Z',
                    'films': [{'filmId': 'xianggu', 'outboundClicks': 50}, {'filmId': 'jinhaitang', 'outboundClicks': 300}, {'filmId': 'yanran', 'outboundClicks': 0}]}
        self.open(snapshot)
        rows = self.page.locator('#rankingPopular [data-ranking-film]')
        expect(rows).to_have_count(2)
        self.assertEqual(rows.evaluate_all('(rows)=>rows.map(row=>row.dataset.rankingFilm)'), ['jinhaitang', 'xianggu'])
        expect(rows.first).to_contain_text('300')
        expect(self.page.locator('#popularRankingStatus')).to_contain_text('10.24')
        expect(self.page.locator('#popularRankingStatus')).to_contain_text('11.02')

    def test_stale_wrong_window_and_invalid_snapshot_never_rank(self):
        for snapshot in [
            {'metric': 'outbound-clicks', 'windowStart': '2026-10-23', 'windowEnd': '2026-11-01', 'updatedAt': '2026-11-01T22:00:00Z', 'films': [{'filmId': 'xianggu', 'outboundClicks': 900}]},
            {'metric': 'outbound-clicks', 'windowStart': '2026-10-25', 'windowEnd': '2026-11-02', 'updatedAt': '2026-11-02T00:00:00Z', 'films': [{'filmId': 'xianggu', 'outboundClicks': 900}]},
            {'metric': 'outbound-clicks', 'windowStart': '2026-10-24', 'windowEnd': '2026-11-02', 'updatedAt': '2026-11-02T00:00:00Z', 'films': [{'filmId': 'xianggu', 'outboundClicks': -1}]},
            {'metric': 'effective-plays', 'windowStart': '2026-10-24', 'windowEnd': '2026-11-02', 'updatedAt': '2026-11-02T00:00:00Z', 'films': [{'filmId': 'xianggu', 'outboundClicks': 900}]},
        ]:
            self.open(snapshot)
            expect(self.page.locator('#rankingPopular [data-ranking-film]')).to_have_count(0)
            expect(self.page.locator('#popularRankingStatus')).to_contain_text('数据暂不可用')
            self.page.unroute('**/api/framepick/outbound/summary')

    def test_live_outbound_tolerates_small_clock_skew_but_rejects_far_future(self):
        self.page.clock.set_fixed_time(1793577600)
        snapshot = {'metric': 'outbound-clicks', 'windowStart': '2026-10-24', 'windowEnd': '2026-11-02',
                    'updatedAt': '2026-11-02T00:00:05Z', 'films': [{'filmId': 'xianggu', 'outboundClicks': 5}]}
        self.open(snapshot)
        expect(self.page.locator('#rankingPopular [data-ranking-film="xianggu"]')).to_contain_text('5 次原作跳转')
        self.page.unroute('**/api/framepick/outbound/summary')
        snapshot['updatedAt'] = '2026-11-02T00:02:00Z'
        self.open(snapshot)
        expect(self.page.locator('#rankingPopular [data-ranking-film]')).to_have_count(0)
        expect(self.page.locator('#popularRankingStatus')).to_contain_text('数据暂不可用')

    def test_acclaimed_excludes_single_vote_and_orders_with_sample_weight(self):
        self.open()
        self.page.evaluate("""window.dispatchEvent(new CustomEvent('framepick:review-summary', {detail:{available:true, films:[
          {filmId:'xianggu',averageRating:10,ratingCount:1},
          {filmId:'jinhaitang',averageRating:8.8,ratingCount:100},
          {filmId:'yanran',averageRating:9.5,ratingCount:5}
        ]}}))""")
        rows = self.page.locator('#rankingAcclaimed [data-ranking-film]')
        expect(rows).to_have_count(2)
        self.assertEqual(rows.evaluate_all('(rows)=>rows.map(row=>row.dataset.rankingFilm)'), ['jinhaitang', 'yanran'])
        expect(rows.first).to_contain_text('8.8')
        expect(rows.first).to_contain_text('100 人')
        self.page.evaluate("window.dispatchEvent(new CustomEvent('framepick:review-summary',{detail:{available:false,films:[]}}))")
        expect(rows).to_have_count(0)

    def test_early_rating_summary_is_applied_after_catalogue_ready(self):
        # Resolve the review client's real fetch path before the deferred main
        # script is delivered. Its catalogue-ready replay then precedes ours.
        self.page.add_init_script("""const originalFetch = window.fetch;
          window.fetch = (url, options) => String(url).endsWith('/api/framepick/summary')
            ? Promise.resolve(new Response(JSON.stringify({films:[{filmId:'xianggu',averageRating:9,ratingCount:5}]}), {status:200,headers:{'Content-Type':'application/json'}}))
            : originalFetch(url, options);""")
        def slow_main(route):
            response = route.fetch()
            time.sleep(1)
            route.fulfill(response=response)
        self.page.route('**/framepick.js*', slow_main)
        self.open()
        expect(self.page.locator('#filmGrid [data-film="xianggu"] .community-score')).to_contain_text('9.0 / 10 · 5 人评分')
        expect(self.page.locator('#rankingAcclaimed [data-ranking-film="xianggu"]')).to_have_count(1)
        expect(self.page.locator('#rankingAcclaimed')).to_contain_text('9.0 / 10 · 5 人评分')

    def test_summary_refresh_in_detail_keeps_ranking_return_focus(self):
        self.open()
        self.page.evaluate("window.dispatchEvent(new CustomEvent('framepick:review-summary',{detail:{available:true,films:[{filmId:'xianggu',averageRating:9,ratingCount:5}]}}))")
        trigger = self.page.locator('#rankingAcclaimed [data-ranking-film="xianggu"]')
        trigger.click()
        self.page.get_by_role('tab', name='站内评价', exact=True).click()
        self.page.evaluate("window.dispatchEvent(new CustomEvent('framepick:review-summary',{detail:{available:true,films:[{filmId:'xianggu',averageRating:9,ratingCount:6}]}}))")
        self.page.keyboard.press('Escape')
        expect(self.page.locator('#filmDialog')).not_to_be_visible()
        expect(trigger).to_be_focused()

    def test_mobile_file_and_creator_plans_are_honest(self):
        self.page.set_viewport_size({'width': 320, 'height': 760})
        self.open()
        self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
        expect(self.page.locator('#cinemaPlan')).to_contain_text('完整故事与视听完成度')
        expect(self.page.locator('#membership')).to_contain_text('3 元 / 5 元')
        expect(self.page.locator('#cinemaPlan')).to_contain_text('尚未开放')
        self.page.goto((fp.SITE_ROOT / 'index.html').as_uri())
        # 今日更新只算今天收录的，数量随片库规模与时钟变化，不写死。
        expect(self.page.locator('#rankingDaily')).to_be_visible()
        expect(self.page.locator('#dailyRankingStatus')).to_contain_text('今日')
        expect(self.page.locator('#rankingPopular [data-ranking-film]')).to_have_count(0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
