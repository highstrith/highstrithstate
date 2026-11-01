"""Tests for the creator resume page."""
import os
import io
import re
import unicodedata
import unittest
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
from pypdf import PdfReader

BASE = os.environ.get('STUDIO_BASE_URL', 'http://127.0.0.1:3000')
ROOT = Path(__file__).resolve().parents[1]


class ResumePageSmoke(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime = sync_playwright().start()
        cls.browser = cls.runtime.chromium.launch(channel='chrome', headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.runtime.stop()

    def setUp(self):
        self.context = self.browser.new_context(reduced_motion='reduce')
        self.page = self.context.new_page()
        self.errors = []
        self.page.on('pageerror', lambda error: self.errors.append(str(error)))

    def tearDown(self):
        self.context.close()

    def test_resume_default_view_loads(self):
        self.page.goto(BASE + '/resume.html')
        expect(self.page).to_have_title('林俊杰 · 创作者档案与个人简历 — Highstrith')
        expect(self.page.locator('#view-resume')).to_be_visible()
        expect(self.page.locator('.profile-name')).to_contain_text('林俊杰')
        expect(self.page.locator('.profile-tag-row .badge-dual-engine')).to_be_visible()
        # Verify large website showcase is present
        expect(self.page.locator('.browser-mockup-frame')).to_be_visible()
        expect(self.page.locator('.browser-address-bar')).to_contain_text('highstrith.github.io/highstrithstate')
        # Verify top nav links are removed
        expect(self.page.locator('.dual-nav-links')).not_to_be_attached()
        self.assertEqual(self.errors, [])

    def test_actions_and_links(self):
        self.page.goto(BASE + '/resume.html')
        # Check brand link to index.html
        brand_link = self.page.locator('.dual-brand')
        expect(brand_link).to_have_attribute('href', 'index.html')
        
        # Check direct link to main site in header actions
        main_site_btn = self.page.locator('.nav-actions a[href="index.html"]')
        expect(main_site_btn).to_be_visible()
        expect(main_site_btn).to_contain_text('进入主站')

        # Check hero button points directly to index.html#works
        hero_cinema_btn = self.page.locator('.hero-contacts-bar a[href="index.html#works"]')
        expect(hero_cinema_btn).to_be_visible()
        expect(hero_cinema_btn).to_contain_text('前往放映厅看片')
        self.assertEqual(self.errors, [])

    def test_language_toggle_and_copy(self):
        self.page.goto(BASE + '/resume.html')
        # Toggle language to EN
        self.page.locator('#langSwitch').click()
        expect(self.page.locator('#langSwitch')).to_have_text('中文')
        expect(self.page).to_have_title('Junjie Lin (Highstrith) · Creator Profile & Resume')
        
        # Toggle back to CN
        self.page.locator('#langSwitch').click()
        expect(self.page.locator('#langSwitch')).to_have_text('EN')
        self.assertEqual(self.errors, [])

    def test_current_tools_projects_and_downloadable_pdf(self):
        self.page.goto(BASE + '/resume.html')
        body = self.page.locator('#view-resume')
        for text in ['MiniMax H3', 'NeoWow', 'LibTV', '即梦 TV', '小云雀', 'Vibe Coding', '导演工作台', 'AA 结算计算器']:
            expect(body).to_contain_text(text, timeout=1500)
        expect(body).not_to_contain_text('Runway')
        expect(body).not_to_contain_text('Luma')
        link = self.page.locator('#downloadResume')
        expect(link).to_have_attribute('download', '林俊杰_AIGC视觉设计师_个人简历.pdf')
        response = self.page.request.get(BASE + '/' + link.get_attribute('href'))
        self.assertTrue(response.ok)
        pdf = PdfReader(io.BytesIO(response.body()))
        self.assertEqual(len(pdf.pages), 1)
        self.assertIn('MiniMax H3', pdf.pages[0].extract_text())

    def test_bilingual_layout_on_small_and_large_screens(self):
        for width in [320, 390, 768, 1440]:
            self.page.set_viewport_size({'width': width, 'height': 900})
            for language in ['', '?lang=en']:
                with self.subTest(width=width, language=language):
                    self.page.goto(BASE + '/resume.html' + language)
                    self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'), width)
                    photo = self.page.locator('.resume-avatar')
                    expect(photo).to_be_visible()
                    self.assertTrue(photo.evaluate('e=>e.complete && e.naturalWidth === 351'))
                    for card in self.page.locator('.resume-project').all():
                        box = card.bounding_box()
                        self.assertGreaterEqual(box['x'], 0)
                        self.assertLessEqual(box['x'] + box['width'], width + 1)
                    if language:
                        self.assertIn('lang=en', self.page.locator('a[data-projects-link]').first.get_attribute('href'))
                    self.assertTrue(self.page.locator('a[data-projects-link]').nth(1).get_attribute('href').endswith('#directorTitle'))
        self.assertEqual(self.errors, [])

    def test_qr_and_no_script_fallback(self):
        self.page.goto(BASE + '/resume.html')
        self.page.locator('[data-open-qr="site"]').click()
        expect(self.page.locator('#qrDialog')).to_be_visible()
        self.page.locator('#qrDialogClose').click()
        expect(self.page.locator('#qrDialog')).not_to_be_visible()
        context = self.browser.new_context(java_script_enabled=False, viewport={'width': 320, 'height': 844})
        try:
            page = context.new_page()
            page.goto(BASE + '/resume.html')
            expect(page.locator('#downloadResume')).to_be_visible()
            expect(page.locator('#view-resume')).to_contain_text('导演工作台')
            self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'), 320)
        finally:
            context.close()

    def test_browser_print_keeps_contact_and_last_project_on_one_page(self):
        self.page.goto(BASE + '/resume.html')
        pdf = PdfReader(io.BytesIO(self.page.pdf(format='A4', prefer_css_page_size=True)))
        self.assertEqual(len(pdf.pages), 1)
        text = re.sub(r'\s+', '', unicodedata.normalize('NFKC', pdf.pages[0].extract_text()))
        for value in ['18020169750', 'highstrith@gmail.com', 'AA结算计算器', 'MiniMaxH3']:
            self.assertIn(value, text)


if __name__ == '__main__':
    unittest.main()
