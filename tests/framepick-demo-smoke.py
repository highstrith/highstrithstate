"""Framepick simulated orders in a real browser.

The paid-looking flow is always labelled as a simulation: it uses isolated demo
products, a local account and server-persisted demo orders, never a payment API.
Static hosting and service failures must leave free discovery untouched.
"""
import functools
import http.server
import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import framepick_layout as fp  # noqa: E402

from playwright.sync_api import sync_playwright, expect  # noqa: E402

WIDTHS = [320, 390, 820, 1440, 1920]
PASSWORD = 'framepick-test-pw'
DEMO_KEY = 'framepick:demo:orders:v1'


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


class BrowserBase(unittest.TestCase):
    def make_page(self):
        self.context = self.browser.new_context(viewport={'width': 1440, 'height': 900}, reduced_motion='reduce')
        self.addCleanup(self.context.close)
        page = self.context.new_page()
        page.set_default_timeout(12000)
        self.errors = []
        page.on('pageerror', lambda error: self.errors.append(str(error)))
        self.page = page
        return page

    def tearDown(self):
        self.assertEqual(self.errors, [])


class FramepickSimulatedOrders(BrowserBase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='framepick-orders-browser-')
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        cls.base = f'http://127.0.0.1:{port}'
        cls.server = subprocess.Popen(['node', 'serve-framepick.js'], env={**os.environ,
            'PORT': str(port),
            'FRAMEPICK_ACCOUNTS_DATA_DIR': str(Path(cls.temp.name) / 'accounts'),
            'FRAMEPICK_ORDERS_DATA_DIR': str(Path(cls.temp.name) / 'orders')},
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        for _ in range(100):
            try:
                urllib.request.urlopen(cls.base + '/').close()
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

    def open_page(self, query=''):
        page = self.make_page()
        page.goto(self.base + '/' + query.lstrip('/'), wait_until='load')
        return page

    def unique_email(self, name):
        return f'{name}-{int(time.time() * 1000)}@example.com'

    def register(self, name='viewer'):
        page = self.page
        page.locator('#accountSwitch').click()
        page.locator('#accountEmail').fill(self.unique_email(name))
        page.locator('#accountPassword').fill(PASSWORD)
        page.locator('#accountNickname').fill('演示观众')
        page.locator('#accountSubmit').click()
        expect(page.locator('#accountDialog')).not_to_be_visible()
        expect(page.locator('#accountEntry')).to_have_attribute('data-signed-in', 'true')

    def open_purchase(self, price=3):
        # 页面目前只保留一个演示入口（3 元档，data-demo-price 标价）。传 price 是历史参数：
        # 若将来恢复多档，会挑对应档；现在回落到唯一入口，价格以按钮上的标价为准。
        opener = self.page.locator(f'[data-demo-purchase][data-demo-price="{price}"]')
        if not opener.count():
            opener = self.page.locator('[data-demo-purchase]').first
        self.demo_price = int(opener.get_attribute('data-demo-price') or price)
        opener.click()
        expect(self.page.locator('#purchaseDialog')).to_be_visible()

    def create_order(self):
        self.page.locator('#purchaseAction').click()
        expect(self.page.locator('#purchaseChip')).to_have_text('未支付')
        self.assertIn('演示订单', self.page.locator('#purchaseBody').inner_text())

    def test_service_status_marks_orders_local_simulated_and_never_real_payment(self):
        page = self.open_page()
        expect(page.locator('#prototypeBar')).to_contain_text('模拟')
        page.locator('#statusOpen').click()
        rows = page.locator('#statusList .status-row')
        expect(rows).to_have_count(10)
        payment = page.locator('#statusList .status-row', has_text='单片购票与订单')
        expect(payment.locator('.state-chip')).to_have_text('本地演示 · 正式未部署')
        self.assertIn('服务端保存', payment.inner_text())
        self.assertIn('不会扣款', payment.inner_text())
        cinema = page.locator('#statusList .status-row', has_text='我的影院')
        expect(cinema.locator('.state-chip')).to_have_text('本地演示 · 正式未部署')
        self.assertIn('授权正片播放仍未接入', cinema.inner_text())

    def test_paid_flow_is_server_backed_recoverable_and_explicitly_simulated(self):
        page = self.open_page()
        self.open_purchase(3)
        expect(page.locator('#purchaseChip')).to_have_text('未登录')
        self.assertIn('授权期内反复观看', page.locator('.purchase-rights').inner_text())
        self.assertIn('不是永久拥有', page.locator('.purchase-rights').inner_text())
        self.assertNotIn('48 小时租赁', page.locator('.purchase-rights').inner_text().replace('也不是 48 小时租赁', ''))
        page.locator('#purchaseAction').click()
        expect(page.locator('#accountDialog')).to_be_visible()
        self.register('paid')
        expect(page.locator('#purchaseDialog')).to_be_visible()
        expect(page.locator('#purchaseChip')).to_have_text('未支付')
        self.create_order()
        self.assertIn('3.00', page.locator('#purchaseMeta').inner_text())
        self.assertIn('30 天', page.locator('#purchaseMeta').inner_text())

        page.locator('#purchaseSimulate').click()
        expect(page.locator('#purchaseChip')).to_have_text('确认中')
        page.reload(wait_until='load')
        self.open_purchase(3)
        expect(page.locator('#purchaseChip')).to_have_text('确认中')
        page.locator('#purchaseAction').click()
        expect(page.locator('#purchaseChip')).to_have_text('已支付（模拟）')
        self.assertIn('不会扣款', page.locator('#purchaseBody').inner_text())
        self.assertIn('模拟授权至', page.locator('#purchaseMeta').inner_text())
        page.locator('#purchaseClose').click()
        rows = page.locator('#cinemaList .cinema-row')
        expect(rows).to_have_count(1)
        expect(rows.first.locator('.state-chip')).to_have_text('已支付（模拟）')
        self.assertIn('不产生真实付款、放映权益或创作者分账', rows.first.inner_text())
        self.assertIsNone(page.evaluate(f"() => localStorage.getItem('{DEMO_KEY}')"))

        page.reload(wait_until='load')
        expect(page.locator('#cinemaList .cinema-row')).to_have_count(1)
        expect(page.locator('#cinemaList .cinema-row .state-chip')).to_have_text('已支付（模拟）')

    def test_failed_and_cancelled_orders_remain_visible_without_rights(self):
        page = self.open_page()
        page.locator('#accountEntry').click()
        self.register('states')
        self.open_purchase(5)
        self.create_order()
        self.assertIn(f'{self.demo_price}.00', page.locator('#purchaseMeta').inner_text())
        page.locator('#purchaseFail').click()
        expect(page.locator('#purchaseChip')).to_have_text('失败（模拟）')
        self.assertIn('没有扣款', page.locator('#purchaseBody').inner_text())
        page.locator('#purchaseSecondary').click()
        expect(page.locator('#purchaseChip')).to_have_text('已取消')
        page.locator('#purchaseClose').click()
        row = page.locator('#cinemaList .cinema-row').first
        expect(row.locator('.state-chip')).to_have_text('已取消')
        self.assertIn('无模拟观影权益', row.inner_text())
        page.reload(wait_until='load')
        expect(page.locator('#cinemaList .cinema-row .state-chip')).to_have_text('已取消')

    def test_login_returns_to_purchase_without_losing_filters_or_touching_real_films(self):
        page = self.open_page()
        page.locator('#filmSearch').fill('相骨')
        expect(page.locator('#filmGrid [data-film]:visible')).to_have_count(1)
        before = page.locator('#filmGrid [data-film]').count()
        self.open_purchase(3)
        page.locator('#purchaseAction').click()
        self.register('context')
        expect(page.locator('#purchaseDialog')).to_be_visible()
        expect(page.locator('#filmSearch')).to_have_value('相骨')
        self.assertIn('q=', page.url)
        page.locator('#purchaseClose').click()
        expect(page.locator('#filmGrid [data-film]')).to_have_count(before)
        self.assertEqual(page.locator('#filmGrid [data-access="paid"]').count(), 0)
        self.assertNotIn('演示影片', page.locator('#filmGrid').inner_text())

    def test_mobile_layout_and_unbuilt_service_labels_survive_order_ui(self):
        page = self.open_page()
        for width in WIDTHS:
            with self.subTest(width=width):
                page.set_viewport_size({'width': width, 'height': 900})
                page.wait_for_timeout(100)
                self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'), width + 1)
        for selector, label in (('#accountDialog', '本地演示 · 非线上账号'),
                                ('#creatorDialog', '演示 · 未接入'),
                                ('#membershipDialog', '演示 · 未接入')):
            with self.subTest(selector=selector):
                expect(page.locator(f'{selector} .state-chip').first).to_have_text(label)


class FramepickOrdersOffline(BrowserBase):
    @classmethod
    def setUpClass(cls):
        cls.server = http.server.ThreadingHTTPServer(('127.0.0.1', 0),
            functools.partial(QuietHandler, directory=str(fp.SITE_SERVE_ROOT)))
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

    def test_undeployed_orders_do_not_block_free_browsing_or_guest_reviews(self):
        page = self.make_page()
        page.goto(self.base + fp.url(), wait_until='load')
        page.locator('[data-demo-purchase]').first.click()
        expect(page.locator('#purchaseDialog')).to_be_visible()
        expect(page.locator('#purchaseBody')).to_contain_text('订单服务尚未')
        expect(page.locator('#purchaseAction')).to_be_disabled()
        page.locator('#purchaseClose').click()
        cards = page.locator('#filmGrid [data-film]')
        self.assertGreaterEqual(cards.count(), 3)
        expect(page.locator('#filmGrid .watch')).to_have_count(cards.count())
        page.locator('#filmGrid .details-button').first.click()
        expect(page.locator('#filmDialog')).to_be_visible()
        page.locator('#reviewsTab').click()
        expect(page.locator('#reviewForm')).to_be_visible()


if __name__ == '__main__':
    unittest.main()
