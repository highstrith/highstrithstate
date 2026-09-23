from playwright.sync_api import sync_playwright


with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    for motion in ("no-preference", "reduce"):
        page = browser.new_page(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, reduced_motion=motion)
        page.goto("http://127.0.0.1:3000/#works", wait_until="domcontentloaded")
        page.locator(".work-card").first.wait_for()
        indexes = range(page.locator(".work-card").count()) if motion == "no-preference" else (0,)
        for index in indexes:
            card = page.locator(".work-card").nth(index)
            card.scroll_into_view_if_needed()
            card.click()
            player = page.locator("#workPlayerVideo")
            page.wait_for_timeout(2000)
            state = player.evaluate("video => ({ src: video.currentSrc, readyState: video.readyState, networkState: video.networkState, paused: video.paused, error: video.error?.message, currentTime: video.currentTime })")
            print(motion, index, state)
            assert page.locator("#workPlayer").get_attribute("aria-hidden") == "false"
            assert state["readyState"] >= 2 and not state["paused"] and state["currentTime"] > 0
            page.locator("#workPlayerClose").click()
        page.close()
    browser.close()
