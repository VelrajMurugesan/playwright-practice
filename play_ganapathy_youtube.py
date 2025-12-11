"""
play_ganapathy_youtube.py
Searches YouTube for "Tamil devotional songs", finds a Ganapathy/Ganesh video
(if available) in the results, opens it and ensures playback.

Usage:
    python play_ganapathy_youtube.py
"""

import time
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# ---------- CONFIG ----------
QUERY = "Ganapathy Tamil devotional songs"
GANAPATHY_KEYWORDS = ["ganapathy", "ganesh",
                      "ganesha", "ganapathi", "ganapati"]
HEADLESS = False        # set True to run without showing the browser
MAX_SEARCH_WAIT = 150    # seconds to wait for search results to appear
CLICK_WAIT = 8          # seconds to wait after clicking a video for playback
EXTRA_PLAY_WAIT = 45    # additional seconds to wait after attempting to start playback
# ---------- END CONFIG ------


def contains_ganapathy(text: str) -> bool:
    text_lower = (text or "").lower()
    for kw in GANAPATHY_KEYWORDS:
        if kw in text_lower:
            return True
    return False


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS)
        context = browser.new_context()
        page = context.new_page()

        try:
            # 1) Go to YouTube
            page.goto("https://www.youtube.com", timeout=30000)
            # Accept cookie popups if they appear (common in EU); try several selectors
            try:
                # attempt to click "Agree" type buttons quickly if present
                for sel in [
                    'button:has-text("I agree")',
                    'button:has-text("AGREE")',
                    'button:has-text("Accept all")',
                    'button:has-text("Accept")',
                    'button:has-text("I agree")'
                ]:
                    if page.query_selector(sel):
                        page.click(sel)
                        break
            except Exception:
                pass

            # 2) Find the search input and search
            # use provided XPath for the search input; target the input inside yt-searchbox
            search_selector = 'xpath=//*[@id="center"]/yt-searchbox//input'
            page.wait_for_selector(
                search_selector, timeout=MAX_SEARCH_WAIT * 1000)
            page.fill(search_selector, QUERY)
            # press Enter to submit search
            page.keyboard.press("Enter")

            # 3) Wait for results and collect video links
            page.wait_for_selector(
                "ytd-video-renderer,ytd-grid-video-renderer, a#video-title", timeout=MAX_SEARCH_WAIT * 1000)
            time.sleep(1)  # small buffer for dynamic loading

            # Grab visible video title anchors
            video_anchors = page.query_selector_all("a#video-title")
            chosen = None
            chosen_title = None

            for a in video_anchors:
                title = a.get_attribute("title") or a.inner_text() or ""
                href = a.get_attribute("href") or ""
                # ensure it's a regular watch link
                if href and "/watch" in href:
                    if contains_ganapathy(title):
                        chosen = a
                        chosen_title = title.strip()
                        break

            # If not found, fallback to the first watch video
            if not chosen and video_anchors:
                for a in video_anchors:
                    href = a.get_attribute("href") or ""
                    if href and "/watch" in href:
                        chosen = a
                        chosen_title = (a.get_attribute("title")
                                        or a.inner_text() or "").strip()
                        break

            if not chosen:
                print(
                    "No video results found. Try increasing timeouts or check network.")
                return

            print("Selected video:", chosen_title)
            # 4) Click the video (open in same tab)
            # Use scroll into view then click
            chosen.scroll_into_view_if_needed()
            chosen.click()
            # wait for navigation / player to load
            page.wait_for_load_state("networkidle", timeout=195000)

            # 5) Ensure playback: the HTML5 video element can be queried
            # Wait a little for the player controls to show
            time.sleep(2)

            # Attempt to play if paused: use evaluate to check HTMLVideoElement paused property
            try:
                is_paused = page.evaluate(
                    "() => { const v = document.querySelector('video'); return v ? v.paused : null; }")
                if is_paused is None:
                    print("Video element not found immediately; waiting a bit...")
                    time.sleep(2)
                else:
                    if is_paused:
                        print("Video is paused — attempting to play...")
                        # click the big play button area (center) or call play() via JS
                        page.evaluate(
                            "() => { const v = document.querySelector('video'); if (v) { v.play().catch(()=>{}); } }")
                    else:
                        print("Video already playing.")
            except PlaywrightTimeout:
                print("Timed out checking video playback state.")
            except Exception as e:
                print("Playback check/play attempt error:", e)

            # Extra: If playback still not started, try clicking the player center
            time.sleep(1)
            still_paused = page.evaluate(
                "() => { const v = document.querySelector('video'); return v ? v.paused : null; }")
            if still_paused:
                try:
                    # click roughly at center of player element
                    player = page.query_selector("video")
                    if player:
                        box = player.bounding_box()
                        if box:
                            page.mouse.click(
                                box["x"] + box["width"]/2, box["y"] + box["height"]/2)
                            print("Clicked player center to start playback.")
                except Exception:
                    pass

            print("Waiting a bit so you can see/hear the video...")
            # increase the wait after attempting to start playback by EXTRA_PLAY_WAIT seconds
            time.sleep(CLICK_WAIT + EXTRA_PLAY_WAIT)

        finally:
            # keep the browser open if headless=False so user can interact; close only if headless=True
            if HEADLESS:
                context.close()
                browser.close()
            else:
                print(
                    "Script finished. Browser left open (HEADLESS=False). Close it manually when done.")


if __name__ == "__main__":
    run()
