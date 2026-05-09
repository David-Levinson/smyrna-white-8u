import os
import json
import time
from playwright.sync_api import sync_playwright

GC_EMAIL    = os.environ["GC_EMAIL"]
GC_PASSWORD = os.environ["GC_PASSWORD"]
TEAM_ID     = "vLOFzQgEgjIp"
TEAM_URL    = f"https://web.gc.com/teams/{TEAM_ID}/2026-summer-smyrna-white-8u---2026"
OUTPUT_FILE = "scraper/gc_data.json"

def scrape():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
        )
        page = context.new_page()

        print("Navigating to GameChanger login...")
        page.goto("https://web.gc.com/login", wait_until="networkidle", timeout=30000)
        time.sleep(3)

        print("Page title:", page.title())
        print("Page URL:", page.url)

        # Click the email field and type slowly like a real user
        print("Filling email...")
        email_field = page.wait_for_selector('input[name="email"]', timeout=10000)
        email_field.click()
        time.sleep(0.5)
        page.keyboard.type(GC_EMAIL, delay=50)
        time.sleep(1)

        # Click Continue
        print("Clicking Continue...")
        page.click('button:has-text("Continue")')
        time.sleep(4)
        page.screenshot(path="scraper/debug_login2.png")

        # Now wait for password field
        print("Waiting for password field...")
        page.wait_for_selector('input[type="password"]', timeout=15000)
        page.click('input[type="password"]')
        time.sleep(0.5)
        page.keyboard.type(GC_PASSWORD, delay=50)
        time.sleep(1)

        # Submit
        print("Submitting...")
        page.click('button[type="submit"], button:has-text("Sign in"), button:has-text("Log in"), button:has-text("Continue")')
        page.wait_for_load_state("networkidle", timeout=20000)
        time.sleep(4)

        print("Post-login URL:", page.url)
        page.screenshot(path="scraper/debug_postlogin.png")

        print("Navigating to team page...")
        page.goto(TEAM_URL, wait_until="networkidle", timeout=30000)
        time.sleep(4)
        page.screenshot(path="scraper/debug_team.png")

        data = {
            "roster":   scrape_roster(page),
            "schedule": scrape_schedule(page),
            "results":  scrape_results(page),
            "stats":    scrape_stats(page),
        }

        browser.close()
        return data

def scrape_roster(page):
    print("Scraping roster...")
    try:
        page.goto(f"https://web.gc.com/teams/{TEAM_ID}/2026-summer-smyrna-white-8u---2026/roster",
                  wait_until="networkidle", timeout=20000)
        time.sleep(3)
        players = []
        rows = page.query_selector_all('[class*="player"], [class*="roster"] [class*="row"], [class*="PlayerCard"], li[class*="player"]')
        print(f"Found {len(rows)} player elements")
        for row in rows:
            text = row.inner_text().strip()
            if text:
                players.append({"raw": text})
        if not players:
            body = page.query_selector('[class*="roster"], main, [class*="content"]')
            if body:
                players = [{"raw": body.inner_text().strip()}]
        return players
    except Exception as e:
        print(f"Roster error: {e}")
        return []

def scrape_schedule(page):
    print("Scraping schedule...")
    try:
        page.goto(f"https://web.gc.com/teams/{TEAM_ID}/2026-summer-smyrna-white-8u---2026/schedule",
                  wait_until="networkidle", timeout=20000)
        time.sleep(3)
        games = []
        rows = page.query_selector_all('[class*="game"], [class*="event"], [class*="Game"], [class*="schedule"] li')
        print(f"Found {len(rows)} schedule elements")
        for row in rows:
            text = row.inner_text().strip()
            if text:
                games.append({"raw": text})
        if not games:
            body = page.query_selector('main, [class*="schedule"], [class*="content"]')
            if body:
                games = [{"raw": body.inner_text().strip()}]
        return games
    except Exception as e:
        print(f"Schedule error: {e}")
        return []

def scrape_results(page):
    print("Scraping results...")
    try:
        rows = page.query_selector_all('[class*="completed"], [class*="result"], [class*="final"]')
        results = []
        for row in rows:
            text = row.inner_text().strip()
            if text:
                results.append({"raw": text})
        return results
    except Exception as e:
        print(f"Results error: {e}")
        return []

def scrape_stats(page):
    print("Scraping stats...")
    try:
        page.goto(f"https://web.gc.com/teams/{TEAM_ID}/2026-summer-smyrna-white-8u---2026/stats",
                  wait_until="networkidle", timeout=20000)
        time.sleep(3)
        rows = page.query_selector_all('table tr, [class*="stat"], [class*="player-stat"]')
        stats = []
        for row in rows:
            text = row.inner_text().strip()
            if text:
                stats.append({"raw": text})
        if not stats:
            body = page.query_selector('table, [class*="stats"], main')
            if body:
                stats = [{"raw": body.inner_text().strip()}]
        return stats
    except Exception as e:
        print(f"Stats error: {e}")
        return []

if __name__ == "__main__":
    print("Starting GameChanger scraper...")
    data = scrape()
    print(f"Scraped: {len(data['roster'])} roster, {len(data['schedule'])} schedule, {len(data['stats'])} stats items")
    os.makedirs("scraper", exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Data saved to {OUTPUT_FILE}")
    print(json.dumps(data, indent=2)[:2000])
