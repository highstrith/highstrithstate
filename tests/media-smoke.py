"""Media, contact and local management checks for the desktop exhibition."""
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    missing = []
    page.on("response", lambda response: missing.append(response.url) if response.status == 404 and "/assets/" in response.url else None)
    page.goto("http://127.0.0.1:3000/#works", wait_until="domcontentloaded")
    page.locator(".stage-card").first.wait_for()
    page.wait_for_function("document.querySelector('.stage-card .work-poster')?.naturalWidth > 0")
    page.wait_for_function("document.querySelector('.stage-card .work-video')?.currentTime > 0")
    assert page.locator(".stage-card .work-video source[src]").count() == 1
    page.locator("[data-stage-jump='2']").click()
    page.wait_for_function("document.querySelector('.stage-root').dataset.activeIndex === '2'")
    page.wait_for_function("[...document.querySelectorAll('.stage-card .work-video source[src]')].length === 1")
    assert not missing, missing
    page.locator("a[href='#contact']").first.click()
    assert page.locator("#contact .contact-social-row [data-social-platform]").count() == 4
    assert page.locator("[data-social-platform='bilibili']").get_attribute("href") == "https://b23.tv/VFqS3Tj"
    wechat = page.locator("[data-social-platform='wechat']")
    wechat.hover()
    assert page.locator("#social-qr-preview").is_visible()
    wechat.click()
    assert page.locator("#social-qr-dialog").evaluate("e => e.open")
    page.close()

    admin = browser.new_page(viewport={"width": 1440, "height": 900})
    admin.goto("http://127.0.0.1:3000/admin.html", wait_until="domcontentloaded")
    admin.wait_for_function("document.querySelectorAll('.manage-card').length === 14")
    assert admin.locator("#uploadCnDescInput").count() == 1
    assert admin.locator("#uploadEnDescInput").count() == 1
    admin.close()
    browser.close()
