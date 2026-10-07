"""Responsive public site and local-file catalogue fallback."""
from pathlib import Path
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    for width, height in ((1280, 720), (1440, 900), (1920, 1080)):
        page = browser.new_page(viewport={"width": width, "height": height})
        page.goto("http://127.0.0.1:3000/", wait_until="domcontentloaded")
        page.locator(".stage-card").first.wait_for()
        assert page.locator(".stage-card").count() == 5
        assert page.locator(".catalogue-card").count() == 14
        assert page.locator(".catalogue-card", has_text="巨轮空降").count() == 0
        assert page.locator(".hero-avatar").evaluate("image => image.naturalWidth") == 1792
        assert page.locator(".hero .cta-row").bounding_box()["y"] + page.locator(".hero .cta-row").bounding_box()["height"] < height
        assert not page.evaluate("document.documentElement.scrollWidth > innerWidth")
        page.locator("#langSwitch").click()
        assert page.locator("#catalogueTitle").inner_text() == "All works"
        assert not page.evaluate("document.documentElement.scrollWidth > innerWidth")
        page.close()

    for width, height, columns in ((820, 950, 2), (390, 844, 1), (320, 760, 1)):
        page = browser.new_page(viewport={"width": width, "height": height}, is_mobile=width < 700, has_touch=width < 700)
        page.goto("http://127.0.0.1:3000/", wait_until="domcontentloaded")
        page.locator(".work-card").first.wait_for()
        assert page.locator(".work-card").count() == 8
        assert page.locator(".works-grid").first.evaluate("e => getComputedStyle(e).gridTemplateColumns.split(' ').length") == columns
        assert not page.evaluate("document.documentElement.scrollWidth > innerWidth")
        page.locator("#langSwitch").click()
        assert not page.evaluate("document.documentElement.scrollWidth > innerWidth")
        page.close()

    public = browser.new_page(viewport={"width": 1280, "height": 800})
    public.route("https://portfolio.example/**", lambda route: route.fulfill(response=route.fetch(url=route.request.url.replace("https://portfolio.example", "http://127.0.0.1:3000"))))
    public.goto("https://portfolio.example/", wait_until="domcontentloaded")
    public.locator(".stage-card").first.wait_for()
    assert public.locator("#adminEntryLink").is_hidden()
    public.close()

    file_page = browser.new_page(viewport={"width": 1280, "height": 800})
    file_page.goto((Path(__file__).resolve().parents[1] / "index.html").as_uri(), wait_until="domcontentloaded")
    file_page.locator(".catalogue-card").first.wait_for(state="attached")
    assert file_page.locator(".catalogue-card").count() == 14
    assert file_page.locator(".catalogue-card", has_text="巨轮空降").count() == 0
    file_page.close()
    browser.close()
