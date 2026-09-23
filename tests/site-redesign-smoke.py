from pathlib import Path

from playwright.sync_api import sync_playwright


with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    page.goto("http://127.0.0.1:3000/", wait_until="domcontentloaded")
    page.locator(".work-card").first.wait_for()
    assert page.locator(".work-card").count() == 8
    assert page.locator(".work-card").last.locator("h3").inner_text() == "动作预演"
    assert page.locator(".work-description").count() == 0
    assert page.locator("#works .tag-row").count() == 0
    assert page.locator("#works .section-note").count() == 0
    assert page.locator(".hero-visual .hero-avatar").get_attribute("src") == "assets/hero-digital-human-full.jpg"
    assert page.locator("#bgMusic").evaluate("audio => audio.paused")
    assert page.locator(".works-grid").evaluate("grid => getComputedStyle(grid).gridTemplateColumns.split(' ').length") == 4
    assert page.locator("#contact .contact-actions .btn").count() == 1

    card = page.locator(".work-card").first
    card.hover()
    page.wait_for_timeout(2800)
    assert page.locator("#workPlayer").get_attribute("aria-hidden") == "true"
    card.focus()
    page.keyboard.press("Enter")
    assert page.locator("#workPlayer").get_attribute("aria-hidden") == "false"
    assert page.locator(".shell").evaluate("element => element.inert")
    for key in ("Tab", "Tab", "Tab", "Shift+Tab", "Shift+Tab", "Shift+Tab"):
        page.keyboard.press(key)
        assert page.evaluate("document.activeElement.closest('#workPlayer') !== null")
    page.keyboard.press("Escape")
    assert page.locator("#workPlayer").get_attribute("aria-hidden") == "true"
    assert not page.locator(".shell").evaluate("element => element.inert")
    assert card.evaluate("element => document.activeElement === element")

    page.locator(".works-page-button[data-page='2']").first.click()
    assert page.locator(".work-card").count() == 5
    assert page.locator(".work-card").first.locator("h3").inner_text() == "产品视觉实验"
    page.locator("#langSwitch").click()
    assert page.locator(".work-card").first.locator("h3").inner_text() == "Product Visual Study"

    tablet = browser.new_page(viewport={"width": 820, "height": 950})
    tablet.goto("http://127.0.0.1:3000/", wait_until="domcontentloaded")
    brand = tablet.locator(".brand").bounding_box()
    nav = tablet.locator(".nav").bounding_box()
    actions = tablet.locator(".actions").bounding_box()
    assert brand["x"] + brand["width"] < nav["x"] < actions["x"]
    assert tablet.locator(".works-grid").evaluate("grid => getComputedStyle(grid).gridTemplateColumns.split(' ').length") == 2
    tablet.close()

    mobile = browser.new_page(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
    mobile.goto("http://127.0.0.1:3000/", wait_until="domcontentloaded")
    mobile.locator(".work-card").first.wait_for()
    assert mobile.locator(".topbar").bounding_box()["height"] < 185
    assert mobile.locator(".hero .btn.primary").bounding_box()["y"] < 844
    assert not mobile.evaluate("document.documentElement.scrollWidth > innerWidth")
    mobile.locator(".work-card").first.click()
    assert mobile.locator("#workPlayer").get_attribute("aria-hidden") == "false"
    mobile.locator("#workPlayerClose").click()
    assert mobile.locator("#workPlayer").get_attribute("aria-hidden") == "true"
    mobile.close()

    narrow = browser.new_page(viewport={"width": 320, "height": 760}, is_mobile=True, has_touch=True)
    narrow.goto("http://127.0.0.1:3000/", wait_until="domcontentloaded")
    narrow.locator("#langSwitch").click()
    brand_label = narrow.locator(".brand-copy").bounding_box()
    actions = narrow.locator(".actions").bounding_box()
    assert brand_label is None or brand_label["x"] + brand_label["width"] <= actions["x"]
    narrow.close()

    static = browser.new_page(viewport={"width": 1280, "height": 800})
    static.route("**/api/works", lambda route: route.fulfill(status=404, body="not found"))
    asset_failures = []
    static.on("response", lambda response: asset_failures.append(response.url) if response.status == 404 and "/assets/" in response.url else None)
    static.goto("http://127.0.0.1:3000/", wait_until="domcontentloaded")
    static.locator(".work-card").first.wait_for()
    assert static.locator(".work-card").count() == 8
    assert static.locator(".work-card").last.locator("h3").inner_text() == "动作预演"
    assert static.locator(".hero-avatar").evaluate("image => image.naturalWidth") == 1792
    assert asset_failures == []
    static.close()

    public = browser.new_page(viewport={"width": 1280, "height": 800})
    public.route("https://portfolio.example/**", lambda route: route.fulfill(response=route.fetch(url=route.request.url.replace("https://portfolio.example", "http://127.0.0.1:3000"))))
    public.goto("https://portfolio.example/", wait_until="domcontentloaded")
    public.locator(".work-card").first.wait_for()
    assert public.locator("#adminEntryLink").is_hidden()
    assert public.locator(".work-card").count() == 8
    public.close()

    file_page = browser.new_page(viewport={"width": 1280, "height": 800})
    file_page.goto((Path(__file__).resolve().parents[1] / "index.html").as_uri(), wait_until="domcontentloaded")
    file_page.locator(".work-card").first.wait_for()
    catalog = page.request.get("http://127.0.0.1:3000/data/works.json").json()
    assert file_page.locator(".work-card").count() == 8
    assert file_page.locator(".work-card h3").all_text_contents() == [work["cnTitle"] for work in catalog[:8]]
    assert file_page.locator(".works-page-button[aria-label='第 2 页']").count() == 1
    file_page.locator(".works-page-button[aria-label='第 2 页']").click()
    assert file_page.locator(".work-card h3").all_text_contents() == [work["cnTitle"] for work in catalog[8:]]
    file_page.close()
    page.close()
    browser.close()
