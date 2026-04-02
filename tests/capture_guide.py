"""
Capture User Guide Screenshots

Launches a headless browser, logs in, navigates every module,
and saves screenshots to static/guide/.

Usage:
    # App must be running first: python app.py
    python tests/capture_guide.py

    # Or start app automatically:
    python tests/capture_guide.py --start-app
"""

import asyncio
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
GUIDE_DIR = ROOT / "static" / "guide"
BASE_URL = "http://localhost:5011"
EMAIL = "demo@ashlandhill.com"
PASSWORD = "demo1234"


PAGES = [
    ("00_login.png",           None,                       "Login page"),
    ("01_welcome.png",         "__after_login__",           "Welcome screen"),
    ("02_productions.png",     "/module/productions",       "Productions"),
    ("03_production_new.png",  "/module/production/new",    "New Production form"),
    ("04_stakeholders.png",    "/module/stakeholders",      "Stakeholders"),
    ("05_accounts.png",        "/module/accounts",          "Collection Accounts"),
    ("06_waterfall.png",       "/module/waterfall",         "Waterfall Engine"),
    ("07_transactions.png",    "/module/transactions",      "Transactions"),
    ("08_disbursements.png",   "/module/disbursements",     "Disbursements"),
    ("09_contracts.png",       "/module/contracts",         "Contract Parser"),
    ("10_reports.png",         "/module/reports",           "Reports"),
    ("11_forecasting.png",     "/module/forecasting",       "Revenue Forecasting"),
    ("12_anomaly.png",         "/module/anomaly",           "Anomaly Detection"),
]


async def run():
    from playwright.async_api import async_playwright

    GUIDE_DIR.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1280, "height": 900})

        # --- Login page screenshot ---
        await page.goto(f"{BASE_URL}/login")
        await page.wait_for_load_state("networkidle")
        await page.screenshot(path=str(GUIDE_DIR / "00_login.png"))
        print("  captured  00_login.png")

        # --- Login ---
        await page.fill('input[name="email"]', EMAIL)
        await page.fill('input[name="password"]', PASSWORD)
        await page.click('button[type="submit"]')
        await page.wait_for_url(f"{BASE_URL}/")
        await asyncio.sleep(2)

        # --- Welcome screen ---
        await page.screenshot(path=str(GUIDE_DIR / "01_welcome.png"))
        print("  captured  01_welcome.png")

        # --- Module pages ---
        for filename, path, label in PAGES:
            if path is None or path == "__after_login__":
                continue

            # Navigate via HTMX swap
            await page.evaluate(f"""
                () => {{
                    var c = document.getElementById('center-content');
                    var ch = document.getElementById('center-chat');
                    if (c && ch) {{ ch.style.display = 'none'; c.style.display = 'block'; }}
                    htmx.ajax('GET', '{path}', {{target: '#center-content', swap: 'innerHTML'}});
                    var h = document.getElementById('center-title');
                    if (h) h.textContent = '{label}';
                }}
            """)
            await asyncio.sleep(1.5)
            await page.screenshot(path=str(GUIDE_DIR / filename))
            print(f"  captured  {filename} — {label}")

        await browser.close()

    print(f"\n  All screenshots saved to {GUIDE_DIR}/")


def main():
    app_proc = None
    if "--start-app" in sys.argv:
        print("  Starting app...")
        app_proc = subprocess.Popen(
            [sys.executable, str(ROOT / "app.py")],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        time.sleep(5)

    print(f"\n{'='*50}")
    print(f"  AHCAM User Guide — Screenshot Capture")
    print(f"{'='*50}\n")

    asyncio.run(run())

    if app_proc:
        app_proc.terminate()
        app_proc.wait()

    print("\n  Done!")


if __name__ == "__main__":
    main()
