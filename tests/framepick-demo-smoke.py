"""Framepick prototype states in a real browser.

The prototype must be honest: browsing features are real, while accounts, payment,
licensed playback and creator payouts are either local demos or not built. These
checks pin that labelling down and walk every checkout state the real flow will
need — without sending a single request and without claiming a real purchase.
"""
import functools
import http.server
import socket
import sys
import threading
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import framepick_layout as fp  # noqa: E402

from playwright.sync_api import sync_playwright, expect  # noqa: E402

WIDTHS = [320, 390, 820, 1440, 1920]
DEMO_KEY = 'framepick:demo:orders:v1'


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


class FramepickPrototype(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime = sync_playwright().start()
        cls.browser = cls.runtime.chromium.launch(channel='chrome', headless=True)
        handler = functools.partial(QuietHandler, directory=str(fp.SITE_SERVE_ROOT))
        cls.server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
        cls.port = cls.server.server_address[1]
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.browser.close()
        cls.runtime.stop()

    def page(self, **options):
        page = self.browser.new_page(**options)
        page.set_default_timeout(12000)
        self.addCleanup(page.close)
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.errors = errors
        page.goto(f'http://127.0.0.1:{self.port}' + fp.url(), wait_until='load')
        return page

    def test_prototype_bar_and_service_status_are_explicit(self):
        page = self.page(viewport={'width': 1440, 'height': 900})
        expect(page.locator('#prototypeBar')).to_be_visible()
        self.assertIn('未接入', page.locator('#prototypeBar').inner_text())
        page.locator('#statusOpen').click()
        expect(page.locator('#statusDialog')).to_be_visible()
        rows = page.locator('#statusList .status-row')
        expect(rows).to_have_count(10)
        payment = page.locator('#statusList .status-row', has_text='单片购票与支付')
        expect(payment.locator('.state-chip')).to_have_text('未接入')
        self.assertIn('不收任何费用', payment.inner_text())
        self.assertIn('商户号', payment.inner_text())
        reviews = page.locator('#statusList .status-row', has_text='访客评价与评分')
        expect(reviews.locator('.state-chip')).to_have_text('本地演示 · 正式未部署')
        self.assertEqual(page.errors, [])

    def test_demo_purchase_walks_every_checkout_state(self):
        page = self.page(viewport={'width': 1440, 'height': 900})
        page.evaluate(f"() => localStorage.removeItem('{DEMO_KEY}')")
        page.reload(wait_until='load')
        page.locator('[data-demo-purchase]').first.click()
        expect(page.locator('#purchaseDialog')).to_be_visible()
        # Not signed in: the flow stops and points at the optional account.
        expect(page.locator('#purchaseChip')).to_have_text('未登录')
        self.assertIn('演示', page.locator('#purchaseTitle').inner_text())
        self.assertIn('授权期内反复观看', page.locator('.purchase-rights').inner_text())
        self.assertIn('不是永久拥有', page.locator('.purchase-rights').inner_text())

        # The account module would dispatch this after a successful local sign-in.
        page.evaluate("window.dispatchEvent(new CustomEvent('framepick:account', { detail: { signedIn: true, account: { nickname: 'demo' } } }))")
        expect(page.locator('#purchaseChip')).to_have_text('未购买')
        page.locator('#purchaseAction').click()
        expect(page.locator('#purchaseChip')).to_have_text('支付中')
        expect(page.locator('#purchaseChip')).to_have_text('确认中')
        expect(page.locator('#purchaseChip')).to_have_text('已购 · 授权有效')
        self.assertIn('不代表真实付款', page.locator('#purchaseBody').inner_text())
        self.assertIn('授权至', page.locator('#purchaseMeta').inner_text())

        page.locator('#purchaseAction').click()  # 演示：申请退款
        expect(page.locator('#purchaseChip')).to_have_text('退款中')
        expect(page.locator('#purchaseChip')).to_have_text('已退款')

        page.locator('#purchaseAction').click()  # 重新演示购票
        expect(page.locator('#purchaseChip')).to_have_text('未购买')
        page.locator('#purchaseSimulate').click()
        expect(page.locator('#purchaseChip')).to_have_text('支付失败')
        self.assertIn('未产生任何费用', page.locator('#purchaseBody').inner_text())
        page.locator('#purchaseUnavailable').click()
        expect(page.locator('#purchaseChip')).to_have_text('暂时无法播放')
        self.assertIn('下架', page.locator('#purchaseBody').inner_text())
        self.assertEqual(page.errors, [])

    def test_cinema_shows_demo_entitlements_and_can_be_cleared(self):
        page = self.page(viewport={'width': 1440, 'height': 900})
        page.evaluate(f"""() => localStorage.setItem('{DEMO_KEY}', JSON.stringify([
          {{ id: 'demo-1', film: '演示影片 · 示例授权正片（非真实作品）', price: 3, state: 'active',
             createdAt: Date.now(), expiresAt: Date.now() + 30 * 86400000 }}
        ]))""")
        page.reload(wait_until='load')
        rows = page.locator('#cinemaList .cinema-row')
        expect(rows).to_have_count(1)
        expect(rows.first.locator('.state-chip')).to_have_text('已购 · 授权有效')
        self.assertIn('不产生真实付款或放映权益', rows.first.inner_text())
        page.locator('#cinemaList .cinema-row').first.locator('button', has_text='尝试播放').click()
        self.assertIn('未接入', page.locator('#cinemaNote').inner_text())
        page.locator('#cinemaClear').click()
        expect(rows).to_have_count(0)
        self.assertEqual(page.evaluate(f"() => localStorage.getItem('{DEMO_KEY}')"), '[]')
        self.assertIn('清除', page.locator('#cinemaNote').inner_text())
        self.assertTrue(page.locator('#cinemaEmpty').is_visible())
        self.assertEqual(page.errors, [])

    def test_demo_purchase_never_creates_a_real_library_entry(self):
        page = self.page(viewport={'width': 1440, 'height': 900})
        cards = page.locator('#filmGrid [data-film]')
        before = cards.count()
        page.locator('[data-demo-purchase]').first.click()
        page.locator('#purchaseClose').click()
        expect(page.locator('#filmGrid [data-film]')).to_have_count(before)
        self.assertEqual(page.locator('#filmGrid [data-access="paid"]').count(), 0)
        keys = page.evaluate("() => Object.keys(localStorage)")
        self.assertNotIn('framepick:saved:v1', keys)

    def test_no_horizontal_overflow_at_five_widths(self):
        page = self.page(viewport={'width': 1440, 'height': 900})
        for width in WIDTHS:
            with self.subTest(width=width):
                page.set_viewport_size({'width': width, 'height': 900})
                page.wait_for_timeout(120)
                self.assertLessEqual(
                    page.evaluate('document.documentElement.scrollWidth'),
                    page.evaluate('innerWidth') + 1,
                    f'horizontal overflow at {width}px')

    def test_every_unbuilt_dialog_carries_a_demo_chip(self):
        page = self.page(viewport={'width': 1440, 'height': 900})
        for selector, label in (('#accountDialog', '本地演示 · 非线上账号'),
                                ('#creatorDialog', '演示 · 未接入'),
                                ('#membershipDialog', '演示 · 未接入')):
            with self.subTest(selector=selector):
                chip = page.locator(f'{selector} .state-chip').first
                expect(chip).to_have_text(label)
        self.assertEqual(page.errors, [])


if __name__ == '__main__':
    unittest.main()
