from playwright.sync_api import sync_playwright


with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 1000})
    not_found = []
    page.on("response", lambda response: not_found.append(response.url) if response.status == 404 else None)
    page.goto("http://127.0.0.1:3000/", wait_until="networkidle")

    assert page.locator(".hero-avatar").get_attribute("src") == "assets/hero-digital-human.jpg"
    assert page.locator(".hero-avatar").evaluate("image => image.naturalWidth") == 1792
    assert page.locator(".work-card").count() == 7
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(500)
    titles = [title.strip() for title in page.locator(".work-info h3").all_text_contents()]
    subtitles = [subtitle.strip() for subtitle in page.locator(".work-meta > p:first-child").all_text_contents()]
    catalog = page.request.get("http://127.0.0.1:3000/data/works.json").json()
    assert titles == [work["cnTitle"] for work in catalog]
    assert subtitles == [work["cnSub"] for work in catalog]
    missing_upload_posters = {
        "http://127.0.0.1:3000/assets/uploads/posters/poster-1783864071336.webp",
        "http://127.0.0.1:3000/assets/uploads/posters/poster-1783246320293.webp",
    }
    assert not (set(not_found) & missing_upload_posters), not_found
    assert page.locator(".work-card").nth(0).locator(".work-poster").evaluate("image => image.naturalWidth") > 0
    assert page.locator(".work-card").nth(1).locator(".work-poster").evaluate("image => image.naturalWidth") > 0
    page.locator("#works").scroll_into_view_if_needed()
    page.wait_for_timeout(1200)
    for index, source_path in enumerate([
        "assets/uploads/work-1783863596658-desktop.mp4",
        "assets/uploads/desktop/work-1783436201027-desktop.mp4",
    ]):
        uploaded_video = page.locator(".work-card").nth(index).locator(".work-video")
        assert uploaded_video.locator("source").get_attribute("src") == source_path
        assert uploaded_video.evaluate("video => !video.paused")
    featured_video = page.locator(".work-card").nth(2).locator(".work-video")
    assert featured_video.locator("source").get_attribute("src") == "assets/works/prove-it.mp4"
    assert featured_video.evaluate("video => !video.paused")
    page.locator("#contact").scroll_into_view_if_needed()
    assert page.locator("#contact .contact-unified").count() == 1
    assert page.locator("#contact .contact-column").count() == 2
    assert page.locator("#contact .contact-social-row").count() == 1
    assert page.locator("#contact .contact-social-row [data-social-platform]").count() == 4
    assert page.locator("#contact .contact-sub-kicker").count() == 0
    social_row = page.locator("#contact .contact-social-row")
    social_hub = social_row.locator(".social-hub")
    assert abs((social_hub.bounding_box()["x"] + social_hub.bounding_box()["width"] / 2) - (social_row.bounding_box()["x"] + social_row.bounding_box()["width"] / 2)) < 2
    assert page.locator("#about .contact-card").count() == 0
    assert page.locator("nav a[href='#process']").count() == 0
    assert page.locator("#process").get_attribute("hidden") is not None
    social_links = page.locator("[data-social-platform]")
    assert social_links.count() == 4
    assert social_links.filter(has_text="哔哩哔哩").get_attribute("href") == "https://b23.tv/VFqS3Tj"
    wechat = social_links.filter(has_text="微信")
    wechat.hover()
    qr_preview = page.locator("#social-qr-preview")
    assert qr_preview.is_visible()
    assert qr_preview.locator("img").evaluate("image => image.naturalWidth") > 0
    preview_bounds = qr_preview.bounding_box()
    assert preview_bounds["x"] >= 0 and preview_bounds["y"] >= 0
    assert preview_bounds["x"] + preview_bounds["width"] <= page.viewport_size["width"]
    assert preview_bounds["y"] + preview_bounds["height"] <= page.viewport_size["height"]
    page.locator("#contact .contact-column").first.hover()
    assert not qr_preview.is_visible()
    social_links.filter(has_text="微信").click()
    qr_dialog = page.locator("#social-qr-dialog")
    assert qr_dialog.evaluate("dialog => dialog.open")
    assert qr_dialog.locator("img").evaluate("image => image.naturalWidth") > 0
    mobile = browser.new_page(viewport={"width": 390, "height": 844})
    mobile.goto("http://127.0.0.1:3000/#contact", wait_until="networkidle")
    assert not mobile.evaluate("document.documentElement.scrollWidth > innerWidth")
    assert mobile.locator("#contact .contact-social-row [data-social-platform]").count() == 4
    mobile.close()
    admin = browser.new_page(viewport={"width": 1440, "height": 1000})
    admin.goto("http://127.0.0.1:3000/admin.html", wait_until="networkidle")
    assert admin.locator(".manage-card").count() == 7
    assert admin.locator("#uploadCnDescInput").count() == 1
    assert admin.locator("#uploadEnDescInput").count() == 1
    admin.close()
    browser.close()
