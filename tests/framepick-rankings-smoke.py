"""Public ranking behavior, using a read-only static fixture and explicit snapshots."""
import functools
import http.server
import json
import threading
import time
import unittest
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


class FramepickRankings(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(QuietHandler, directory=str(ROOT)))
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
            self.page.route('**/ranking-data.js*', lambda route: route.fulfill(body='window.FRAMEPICK_RANKING_DATA=' + json.dumps(snapshot), content_type='application/javascript'))
        if source is not None:
            self.page.route('**/reel/', lambda route: route.fulfill(body=source, content_type='text/html'))
        self.page.goto(self.base + '/reel/')

    def test_three_home_rankings_and_daily_detail_return_focus(self):
        source = (ROOT / 'reel/index.html').read_text().replace('data-date="2026-10-31"', 'data-date="2026-11-01"', 1)
        self.open(source=source)
        expect(self.page.locator('#rankings')).to_be_visible()
        expect(self.page.locator('#rankingDaily [data-ranking-film]')).to_have_count(3)
        expect(self.page.locator('#rankingDaily [data-ranking-film]').first).to_contain_text('相骨')
        expect(self.page.locator('#dailyRankingStatus')).to_contain_text('今日暂无新收录')
        expect(self.page.locator('#rankingPopular')).to_contain_text('本站有效播放')
        expect(self.page.locator('#rankingPopular')).to_contain_text('尚未接通')
        expect(self.page.locator('#rankingAcclaimed')).to_contain_text('至少 5 人')
        trigger = self.page.locator('#rankingDaily [data-ranking-film]').first
        trigger.click()
        expect(self.page.locator('#detailTitle')).to_have_text('相骨')
        self.page.keyboard.press('Escape')
        expect(self.page.locator('#filmDialog')).not_to_be_visible()
        expect(trigger).to_be_focused()

    def test_popular_uses_current_ten_day_station_snapshot_only(self):
        snapshot = {'available': True, 'windowStart': '2026-10-24', 'windowEnd': '2026-11-02', 'updatedAt': '2026-11-02T00:00:00Z',
                    'films': [{'filmId': 'xianggu', 'effectivePlays': 50}, {'filmId': 'jinhaitang', 'effectivePlays': 300}, {'filmId': 'yanran', 'effectivePlays': 0}]}
        self.open(snapshot)
        rows = self.page.locator('#rankingPopular [data-ranking-film]')
        expect(rows).to_have_count(2)
        self.assertEqual(rows.evaluate_all('(rows)=>rows.map(row=>row.dataset.rankingFilm)'), ['jinhaitang', 'xianggu'])
        expect(rows.first).to_contain_text('300')
        expect(self.page.locator('#popularRankingStatus')).to_contain_text('10.24')
        expect(self.page.locator('#popularRankingStatus')).to_contain_text('11.02')

    def test_stale_wrong_window_and_invalid_snapshot_never_rank(self):
        for snapshot in [
            {'available': True, 'windowStart': '2026-10-23', 'windowEnd': '2026-11-01', 'updatedAt': '2026-11-01T22:00:00Z', 'films': [{'filmId': 'xianggu', 'effectivePlays': 900}]},
            {'available': True, 'windowStart': '2026-10-25', 'windowEnd': '2026-11-02', 'updatedAt': '2026-11-02T00:00:00Z', 'films': [{'filmId': 'xianggu', 'effectivePlays': 900}]},
            {'available': True, 'windowStart': '2026-10-24', 'windowEnd': '2026-11-02', 'updatedAt': '2026-11-02T00:00:00Z', 'films': [{'filmId': 'xianggu', 'effectivePlays': -1}]},
        ]:
            self.open(snapshot)
            expect(self.page.locator('#rankingPopular [data-ranking-film]')).to_have_count(0)
            expect(self.page.locator('#popularRankingStatus')).to_contain_text('数据暂不可用')
            self.page.unroute('**/ranking-data.js*')

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
          window.fetch = (url, options) => String(url).endsWith('/summary')
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
        expect(self.page.locator('#cinemaPlan')).to_contain_text('40 分钟')
        expect(self.page.locator('#cinemaPlan')).to_contain_text('3–5 元')
        expect(self.page.locator('#cinemaPlan')).to_contain_text('尚未开放')
        self.page.goto((ROOT / 'reel/index.html').as_uri())
        expect(self.page.locator('#rankingDaily [data-ranking-film]')).to_have_count(3)
        expect(self.page.locator('#rankingPopular [data-ranking-film]')).to_have_count(0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
