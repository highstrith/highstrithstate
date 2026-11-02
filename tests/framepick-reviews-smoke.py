"""Guest reviews against a real HTTP handler and an isolated disposable database.

No test writes to the preview's review data. Only failure/race paths intercept
requests; shared-review, edit, refresh, pagination and delete use the real API.
"""
import json
import os
import re
import socket
import subprocess
import tempfile
import time
import unittest
import urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = r"""
const http = require('node:http'), fs = require('node:fs'), path = require('node:path');
const root = process.env.FRAMEPICK_ROOT;
const modulePath = path.join(root, 'server/framepick-reviews.cjs');
const handler = fs.existsSync(modulePath) ? require(modulePath).createReviewHandler({
  dataDir: process.env.FRAMEPICK_TEST_DATA, filmIds: ['xianggu','jinhaitang','yanran'], cooldownMs: 0
}) : async () => false;
http.createServer(async (req,res) => {
  try {
    const url = new URL(req.url, 'http://' + req.headers.host);
    if(await handler(req,res,url)) return;
    const file = path.join(root,url.pathname.endsWith('/') ? url.pathname+'index.html' : url.pathname);
    if (!file.startsWith(root + path.sep)) {res.writeHead(403);res.end();return;}
    const types={'.html':'text/html','.js':'application/javascript','.css':'text/css','.webp':'image/webp'};
    const body=await fs.promises.readFile(file);
    res.writeHead(200,{'Content-Type':types[path.extname(file)] || 'application/octet-stream'});res.end(body);
  } catch (error) {res.writeHead(404);res.end('Missing: '+error.message);}
}).listen(Number(process.env.PORT),'127.0.0.1');
"""


class FramepickReviews(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='framepick-browser-reviews-')
        fixture = Path(cls.temp.name) / 'fixture.cjs'
        fixture.write_text(FIXTURE)
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        cls.base = f'http://127.0.0.1:{port}'
        cls.server = subprocess.Popen(['node', str(fixture)], env={**os.environ, 'PORT': str(port),
            'FRAMEPICK_ROOT': str(ROOT), 'FRAMEPICK_TEST_DATA': str(Path(cls.temp.name) / 'private-data')},
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        for _ in range(100):
            try:
                urllib.request.urlopen(cls.base + '/reel/').close()
                break
            except OSError:
                time.sleep(.05)
        else:
            raise RuntimeError(cls.server.stderr.read().decode())
        cls.runtime = sync_playwright().start()
        cls.browser = cls.runtime.chromium.launch(channel='chrome', headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.runtime.stop()
        cls.server.terminate()
        cls.server.wait(timeout=5)
        cls.server.stderr.close()
        cls.temp.cleanup()

    def setUp(self):
        self.context = self.browser.new_context(viewport={'width': 1440, 'height': 1000}, reduced_motion='reduce')
        self.page = self.context.new_page()
        self.errors = []
        self.page.on('pageerror', lambda error: self.errors.append(str(error)))
        self.addCleanup(self.context.close)

    def tearDown(self):
        self.assertEqual(self.errors, [])

    def open_review(self, page=None, film='xianggu'):
        page = page or self.page
        page.goto(self.base + '/reel/?film=' + film)
        page.get_by_role('tab', name='站内评价', exact=True).click()
        expect(page.locator('#reviewForm')).to_be_visible()
        expect(page.locator('#reviewText')).to_be_enabled()
        return page

    def submit(self, page, text, rating='8', nickname='浏览器访客'):
        page.get_by_label('访客昵称').fill(nickname)
        page.get_by_label('我的评分').select_option(rating)
        page.get_by_label('评价正文').fill(text)
        page.locator('#reviewSubmit').click()
        expect(page.locator('#reviewStatus')).to_contain_text('已保存')

    def test_guest_entry_and_original_site_separation(self):
        self.page.goto(self.base + '/reel/')
        self.page.get_by_role('button', name='访客模式', exact=True).click()
        expect(self.page.locator('#guestDialog')).to_contain_text('浏览器')
        self.page.keyboard.press('Escape')
        expect(self.page.get_by_role('button', name='访客模式', exact=True)).to_be_focused()
        self.page.locator('button[data-open-film="xianggu"]').click()
        expect(self.page.get_by_role('tabpanel', name='作品介绍')).to_contain_text('帧选整理')
        self.page.get_by_role('tab', name='原平台评价', exact=True).click()
        panel = self.page.get_by_role('tabpanel', name='原平台评价')
        expect(panel).to_contain_text('原平台')
        expect(panel.get_by_role('link')).to_have_attribute('href', 'https://www.douyin.com/video/7675120105457487104')
        expect(panel.locator('form')).to_have_count(0)
        expect(self.page.locator('#detailScore')).to_contain_text('编辑评分：待评')

    def test_two_browsers_share_refresh_upsert_delete_and_rating_basis(self):
        other = self.browser.new_context()
        self.addCleanup(other.close)
        second = other.new_page()
        self.open_review()
        self.submit(self.page, '<img src=x onerror=alert(1)>第一条真实共享评价', '8', '甲访客')
        expect(self.page.locator('#reviewList')).to_contain_text('本人')
        expect(self.page.locator('#reviewList img')).to_have_count(0)
        self.open_review(second)
        expect(second.locator('#reviewList')).to_contain_text('第一条真实共享评价')
        expect(second.locator('#reviewList')).not_to_contain_text('本人')
        self.submit(second, '第二位访客的评价', '10', '乙访客')
        expect(second.locator('#reviewSummary')).to_contain_text('9.0')
        expect(second.locator('#reviewSummary')).to_contain_text('2 人评分')
        self.page.reload()
        self.page.get_by_role('tab', name='站内评价', exact=True).click()
        expect(self.page.locator('#reviewText')).to_have_value('<img src=x onerror=alert(1)>第一条真实共享评价')
        self.submit(self.page, '甲访客更新后的评价', '6', '甲访客')
        expect(self.page.locator('#reviewSummary')).to_contain_text('8.0')
        expect(self.page.locator('#reviewSummary')).to_contain_text('2 人评分')
        self.page.keyboard.press('Escape')
        self.page.locator('#scoreBasis').select_option('community')
        self.page.locator('#scoreFilter').select_option('8')
        expect(self.page.locator('#filmGrid [data-film]:visible')).to_have_count(1)
        expect(self.page.locator('#filmGrid [data-film]:visible')).to_have_attribute('data-film', 'xianggu')
        self.assertIn('scoreBasis=community', self.page.url)
        self.page.reload()
        expect(self.page.locator('#scoreBasis')).to_have_value('community')
        self.page.locator('button[data-open-film="xianggu"]').click()
        self.page.get_by_role('tab', name='站内评价', exact=True).click()
        expect(self.page.locator('#reviewDelete')).to_be_visible()
        self.page.locator('#reviewDelete').click()
        expect(self.page.locator('#reviewStatus')).to_contain_text('已撤回')
        expect(self.page.locator('#reviewSummary')).to_contain_text('10.0')
        expect(self.page.locator('#reviewSummary')).to_contain_text('1 人评分')
        self.open_review(second)
        second.locator('#reviewDelete').click()
        expect(second.locator('#reviewSummary')).to_contain_text('暂无站内评分')

    def test_failure_keeps_draft_and_never_claims_success(self):
        self.open_review(film='jinhaitang')
        self.page.route('**/api/framepick/films/jinhaitang/reviews', lambda route:
            route.fulfill(status=503, content_type='application/json', body=json.dumps({'error': '服务暂不可用'}))
            if route.request.method == 'POST' else route.continue_())
        self.page.get_by_label('评价正文').fill('失败后应当保留的草稿')
        self.page.locator('#reviewSubmit').click()
        expect(self.page.locator('#reviewError')).to_contain_text('服务暂不可用')
        expect(self.page.get_by_label('评价正文')).to_have_value('失败后应当保留的草稿')
        expect(self.page.locator('#reviewSubmit')).to_be_enabled()
        expect(self.page.locator('#reviewStatus')).not_to_contain_text('已保存')
        self.page.unroute('**/api/framepick/films/jinhaitang/reviews')
        self.page.get_by_label('评价正文').fill('重试前更新的草稿')
        self.page.locator('#reviewSubmit').click()
        expect(self.page.locator('#reviewStatus')).to_contain_text('已保存')
        expect(self.page.locator('#reviewList')).to_contain_text('重试前更新的草稿')
        self.page.locator('#reviewDelete').click()
        expect(self.page.locator('#reviewStatus')).to_contain_text('已撤回')

    def test_failed_write_during_switch_preserves_per_film_draft(self):
        self.open_review()
        self.page.route('**/api/framepick/films/xianggu/reviews', lambda route:
            route.fulfill(status=503, content_type='application/json', body='{"error":"暂时失败"}')
            if route.request.method == 'POST' else route.continue_())
        self.page.add_script_tag(content="""const beforeDelayFetch=window.fetch;window.fetch=async(...args)=>{
          const response=await beforeDelayFetch(...args);
          if(args[1]?.method==='POST'){
            const body=await response.text();await new Promise(resolve=>setTimeout(resolve,700));
            return new Response(body,{status:response.status,headers:response.headers});
          }return response;
        };""")
        self.page.get_by_label('评价正文').fill('相骨专属的失败草稿')
        with self.page.expect_request(lambda request: request.method == 'POST'):
            self.page.locator('#reviewSubmit').click()
        self.page.evaluate("history.replaceState({},'', '?film=yanran');window.dispatchEvent(new PopStateEvent('popstate'))")
        self.page.get_by_role('tab', name='站内评价', exact=True).click()
        expect(self.page.locator('#reviewText')).to_be_enabled()
        self.page.wait_for_timeout(850)
        expect(self.page.locator('#reviewError')).to_be_empty()
        expect(self.page.locator('#reviewText')).to_have_value('')
        self.page.evaluate("history.replaceState({},'', '?film=xianggu');window.dispatchEvent(new PopStateEvent('popstate'))")
        self.page.get_by_role('tab', name='站内评价', exact=True).click()
        expect(self.page.locator('#reviewText')).to_be_enabled()
        expect(self.page.locator('#reviewText')).to_have_value('相骨专属的失败草稿')
        self.page.unroute('**/api/framepick/films/xianggu/reviews')
        self.submit(self.page, '返回后修改并发布的草稿', '8', '草稿访客')
        expect(self.page.locator('#reviewList')).to_contain_text('返回后修改并发布的草稿')
        self.page.locator('#reviewDelete').click()
        expect(self.page.locator('#reviewStatus')).to_contain_text('已撤回')

    def test_delayed_initial_summary_cannot_replace_new_rating(self):
        self.page.add_init_script("""const baseFetch=window.fetch;window.fetch=(url,options)=>{
          const result=baseFetch(url,options);
          if(String(url).endsWith('/summary')) return result.then(async response=>{
            const body=await response.text();window.__oldSummaryReady=true;
            await new Promise(resolve=>setTimeout(resolve,1000));
            return new Response(body,{status:response.status,headers:response.headers});
          });return result;
        };""")
        self.open_review(film='yanran')
        self.page.wait_for_function('window.__oldSummaryReady === true')
        self.submit(self.page, '等待期间发布的新评分', '9', '新评分访客')
        self.page.wait_for_timeout(1100)
        self.page.keyboard.press('Escape')
        expect(self.page.locator('[data-film="yanran"] .community-score')).to_contain_text('9.0 / 10')
        self.open_review(film='yanran')
        self.page.locator('#reviewDelete').click()
        expect(self.page.locator('#reviewStatus')).to_contain_text('已撤回')

    def test_real_pagination_preserves_draft_and_score_only_can_be_edited(self):
        visitors = []
        for index in range(21):
            visitor = self.runtime.request.new_context(base_url=self.base)
            visitors.append(visitor)
            self.addCleanup(visitor.dispose)
            self.assertEqual(visitor.get('/api/framepick/session').status, 200)
            response = visitor.post('/api/framepick/films/jinhaitang/reviews', data={
                'nickname': f'分页访客{index}', 'text': f'分页评价{index}', 'rating': None})
            self.assertEqual(response.status, 200, response.text())
        self.open_review(film='jinhaitang')
        expect(self.page.locator('#reviewList .review-item')).to_have_count(20)
        expect(self.page.locator('#reviewSummary')).to_contain_text('暂无站内评分')
        self.page.get_by_label('评价正文').fill('翻页时仍保留草稿')
        self.page.locator('#reviewMore').click()
        expect(self.page.locator('#reviewList .review-item')).to_have_count(21)
        expect(self.page.get_by_label('评价正文')).to_have_value('翻页时仍保留草稿')
        expect(self.page.locator('#reviewMore')).not_to_be_visible()
        self.submit(self.page, '', '7', '只评分的访客')
        expect(self.page.locator('#reviewSummary')).to_contain_text('7.0 / 10 · 1 人评分')
        self.submit(self.page, '更新为只评价不评分', '', '只评分的访客')
        expect(self.page.locator('#reviewSummary')).to_contain_text('暂无站内评分')
        expect(self.page.locator('#reviewSummary')).to_contain_text('22 条评价')
        self.page.locator('#reviewDelete').click()
        expect(self.page.locator('#reviewStatus')).to_contain_text('已撤回')
        for visitor in visitors:
            self.assertEqual(visitor.delete('/api/framepick/films/jinhaitang/reviews').status, 200)

    def test_required_content_and_duplicate_submit(self):
        self.open_review(film='yanran')
        self.page.locator('#reviewSubmit').click()
        expect(self.page.locator('#reviewError')).to_contain_text('评分或评价正文')
        expect(self.page.locator('#reviewText')).to_be_focused()
        posts = []
        self.page.on('request', lambda request: posts.append(request.url) if request.method == 'POST' else None)
        self.page.add_script_tag(content="""const nativeReviewFetch=window.fetch;window.fetch=async(...args)=>{
          const response=await nativeReviewFetch(...args);
          if(args[1]?.method==='POST') await new Promise(resolve=>setTimeout(resolve,300));
          return response;
        };""")
        self.page.get_by_label('我的评分').select_option('5')
        self.page.get_by_label('评价正文').fill('只应发布一次')
        self.page.locator('#reviewSubmit').click()
        self.page.evaluate("document.querySelector('#reviewForm').dispatchEvent(new Event('submit',{cancelable:true,bubbles:true}))")
        expect(self.page.locator('#reviewSubmit')).to_be_disabled()
        expect(self.page.locator('#reviewStatus')).to_contain_text('已保存')
        self.assertEqual(len(posts), 1)
        self.page.locator('#reviewDelete').click()
        expect(self.page.locator('#reviewStatus')).to_contain_text('已撤回')

    def test_stale_requests_cannot_leak_into_another_film(self):
        visitor = self.runtime.request.new_context(base_url=self.base)
        self.addCleanup(visitor.dispose)
        self.assertEqual(visitor.get('/api/framepick/session').status, 200)
        self.assertEqual(visitor.post('/api/framepick/films/xianggu/reviews', data={
            'nickname': '相骨独有访客', 'text': '这条评价只属于相骨', 'rating': 9}).status, 200)
        self.page.add_init_script("""const originalFetch=window.fetch;window.fetch=(url,opts)=>{
          const result=originalFetch(url,opts);
          if(String(url).includes('/films/xianggu/reviews'))return result.then(async response=>{
            const body=await response.text();window.__reviewADelayed=true;
            await new Promise(resolve=>setTimeout(resolve,700));
            return new Response(body,{status:response.status,headers:response.headers});
          });return result;
        };""")
        self.page.goto(self.base + '/reel/?film=xianggu')
        with self.page.expect_request('**/api/framepick/films/xianggu/reviews?offset=0'):
            self.page.get_by_role('tab', name='站内评价', exact=True).click()
        self.page.wait_for_function('window.__reviewADelayed === true')
        self.page.evaluate("history.replaceState({},'', '?film=yanran');window.dispatchEvent(new PopStateEvent('popstate'))")
        expect(self.page.locator('#detailTitle')).to_have_text('燕然')
        self.page.get_by_role('tab', name='站内评价', exact=True).click()
        expect(self.page.locator('#reviewForm')).to_be_visible()
        self.page.wait_for_timeout(900)
        expect(self.page.locator('#reviewHeading')).to_contain_text('燕然')
        expect(self.page.locator('#reviewList')).not_to_contain_text('这条评价只属于相骨')
        expect(self.page.locator('#reviewSummary')).to_contain_text('暂无站内评分')
        expect(self.page.locator('#reviewError')).to_be_empty()
        self.assertEqual(visitor.delete('/api/framepick/films/xianggu/reviews').status, 200)

    def test_offline_file_and_static_host_do_not_publish(self):
        requests = []
        self.page.on('request', lambda request: requests.append(request.url))
        self.page.goto((ROOT / 'reel/index.html').as_uri() + '?film=xianggu')
        self.page.get_by_role('tab', name='站内评价', exact=True).click()
        expect(self.page.locator('#reviewAvailability')).to_contain_text('未配置')
        expect(self.page.locator('#reviewSubmit')).to_be_disabled()
        self.assertFalse(any('/api/framepick' in url for url in requests))
        self.page.route('http://framepick-static.test/**', lambda route: route.fulfill(
            path=str(ROOT / route.request.url.split('framepick-static.test/')[1].split('?')[0].replace('reel/', 'reel/', 1))
            if not route.request.url.split('?')[0].endswith('/reel/') else str(ROOT / 'reel/index.html')))
        self.page.goto('http://framepick-static.test/reel/?film=xianggu')
        self.page.get_by_role('tab', name='站内评价', exact=True).click()
        expect(self.page.locator('#reviewAvailability')).to_contain_text('未配置')
        expect(self.page.locator('#reviewSubmit')).to_be_disabled()
        self.assertFalse(any('/api/framepick' in url for url in requests))

    def test_mobile_tabs_keyboard_and_form_names(self):
        for width in [390, 320]:
            self.page.set_viewport_size({'width': width, 'height': 844})
            self.open_review(film='yanran')
            self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'), width)
            self.assertLessEqual(self.page.locator('#filmDialog').evaluate('(el)=>el.scrollWidth'), width)
            expect(self.page.get_by_label('访客昵称')).to_be_visible()
            expect(self.page.get_by_label('我的评分')).to_be_visible()
            self.page.get_by_role('tab', name='作品介绍', exact=True).focus()
            self.page.keyboard.press('ArrowRight')
            expect(self.page.get_by_role('tab', name='原平台评价', exact=True)).to_be_focused()
            self.page.keyboard.press('ArrowRight')
            expect(self.page.get_by_role('tab', name='站内评价', exact=True)).to_be_focused()
            expect(self.page.locator('#reviewForm')).to_be_visible()


if __name__ == '__main__':
    unittest.main()
