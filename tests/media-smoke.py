from playwright.sync_api import sync_playwright


with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 1000})
    not_found = []
    page.on("response", lambda response: not_found.append(response.url) if response.status == 404 else None)
    page.goto("http://127.0.0.1:3000/", wait_until="networkidle")

    assert page.locator(".hero-poster").get_attribute("src") == "assets/posters/hero-fireflies.jpg"
    assert page.locator(".hero-video source").get_attribute("data-src") == "assets/hero-fireflies.mp4"
    assert page.locator(".hero-video source").get_attribute("src") == "assets/hero-fireflies.mp4"
    assert page.locator(".work-card").count() == 7
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(500)
    titles = [title.strip() for title in page.locator(".work-info h3").all_text_contents()]
    subtitles = [subtitle.strip() for subtitle in page.locator(".work-meta > p:first-child").all_text_contents()]
    assert titles[-5:] == ["Prove It", "搭讪", "巨轮空降", "导出成片", "Timeline 1"]
    assert subtitles[-5:] == ["广告 / 剪辑", "叙事 / 剪辑", "特效 / 合成", "剪辑 / 后期", "竖版 / 节奏"]
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
    assert page.locator("#contact .contact-column").count() == 3
    assert page.locator("#about .contact-card").count() == 0
    assert page.locator("nav a[href='#process']").count() == 0
    assert page.locator("#process").get_attribute("hidden") is not None
    social_links = page.locator("[data-social-platform]")
    assert social_links.count() == 4
    assert social_links.filter(has_text="哔哩哔哩").get_attribute("href") == "https://b23.tv/VFqS3Tj"
    social_links.filter(has_text="微信").click()
    qr_dialog = page.locator("#social-qr-dialog")
    assert qr_dialog.evaluate("dialog => dialog.open")
    assert qr_dialog.locator("img").evaluate("image => image.naturalWidth") > 0
    admin = browser.new_page(viewport={"width": 1440, "height": 1000})
    admin.goto("http://127.0.0.1:3000/admin.html", wait_until="networkidle")
    assert admin.locator(".manage-card").count() == 7
    assert admin.locator("#uploadCnDescInput").count() == 1
    assert admin.locator("#uploadEnDescInput").count() == 1
    admin.close()
    browser.close()
