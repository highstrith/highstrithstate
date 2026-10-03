"""Exercise the public Pages file set without serve.js or the works API."""
import functools
import http.server
import json
import shutil
import tempfile
import threading
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
CATALOG = json.loads((ROOT / "data/works.json").read_text())


class QuietStaticHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def copyfile(self, source, outputfile):
        try:
            super().copyfile(source, outputfile)
        except (BrokenPipeError, ConnectionResetError):
            # A browser legitimately cancels a preview when the modal opens.
            pass


with tempfile.TemporaryDirectory(prefix="portfolio-static-") as directory:
    public = Path(directory)
    shutil.copy(ROOT / "index.html", public / "index.html")
    shutil.copy(ROOT / "desktop-experience.css", public / "desktop-experience.css")
    shutil.copytree(ROOT / "data", public / "data")
    (public / "assets").symlink_to(ROOT / "assets", target_is_directory=True)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(QuietStaticHandler, directory=directory))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    address = f"http://127.0.0.1:{server.server_port}"
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="chrome", headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 1100})
            media = []
            missing = []
            page.on("request", lambda request: media.append(request.url) if ".mp4" in request.url else None)
            page.on("response", lambda response: missing.append(response.url) if response.status == 404 and "/assets/" in response.url else None)
            page.goto(address + "/#works", wait_until="domcontentloaded")
            page.wait_for_function("document.querySelector('.stage-card .work-video')?.currentTime > 0")
            assert page.locator(".stage-card").count() == 5
            assert page.locator(".catalogue-card").count() == 14
            assert media and all(url.endswith("-preview.mp4") for url in media)
            page.locator(".stage-card").first.click()
            page.wait_for_function("document.querySelector('#workPlayerVideo').currentTime > 0")
            assert page.locator("#workPlayerVideo").get_attribute("src") == CATALOG[0]["webVideo"]
            page.keyboard.press("Escape")
            page.locator("#langSwitch").click()
            assert "narrative shorts" in page.locator("#featuredWorks").inner_text()
            page.close()
            for motion in ("no-preference", "reduce"):
                mobile = browser.new_page(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, reduced_motion=motion)
                requests = []
                mobile.on("request", lambda request: requests.append(request.url) if ".mp4" in request.url else None)
                mobile.goto(address + "/#works", wait_until="domcontentloaded")
                mobile.locator(".work-card").first.wait_for()
                assert not requests
                mobile.locator(".work-card").first.click()
                mobile.wait_for_function("document.querySelector('#workPlayerVideo').currentTime > 0")
                assert mobile.locator("#workPlayerVideo").get_attribute("src") == CATALOG[0]["mobileVideo"]
                mobile.close()
            nojs = browser.new_page(viewport={"width": 390, "height": 844}, java_script_enabled=False)
            nojs.goto(address, wait_until="domcontentloaded")
            assert nojs.locator(".no-js-work").count() == 14
            for index, work in enumerate(CATALOG):
                assert nojs.locator(".no-js-work").nth(index).get_attribute("href") == (work["webVideo"] or work["video"])
            assert not missing, missing
            nojs.close()
            browser.close()
        print("Static Pages files: desktop preview/full, mobile and reduced-motion playback, language, no-JS links PASS")
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
