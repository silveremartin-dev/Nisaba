"""
Script to capture fresh high-resolution screenshots of the live Nisaba system
using Playwright and Google Chrome.
"""

import os
import time
from playwright.sync_api import sync_playwright

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
OUTPUT_DIR = "assets/images"

os.makedirs(OUTPUT_DIR, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(
        executable_path=CHROME_PATH,
        headless=True,
    )
    context = browser.new_context(
        viewport={"width": 1440, "height": 900},
        device_scale_factor=2,  # Retina sharp resolution
    )

    # 1. Main Tablet Explorer with P100001 / P100004
    print("Capturing 01_tablet_explorer_showcase.png...")
    page = context.new_page()
    page.goto("http://127.0.0.1:8000/explorer#P100004", wait_until="networkidle")
    time.sleep(1.5)
    page.screenshot(path=os.path.join(OUTPUT_DIR, "01_tablet_explorer_showcase.png"))

    # 2. Transliteration with Unicode typography and Metrology conversion
    print("Capturing 02_tablet_metrology_unicode.png...")
    page.goto("http://127.0.0.1:8000/explorer#P100001", wait_until="networkidle")
    time.sleep(1.0)
    # Click Unicode toggle
    btn_toggle = page.locator("#btnTranslitMode")
    if btn_toggle.is_visible():
        btn_toggle.click()
        time.sleep(0.5)
    page.screenshot(path=os.path.join(OUTPUT_DIR, "02_tablet_metrology_unicode.png"))

    # 3. Prosopography Network Graph with official inspector card
    print("Capturing 03_prosopography_graph.png...")
    page_graph = context.new_page()
    page_graph.goto("http://127.0.0.1:8000/api/graph/view", wait_until="networkidle")
    time.sleep(2.0)
    # Search for ab-ba-sa6-ga in the search input to highlight and inspect
    search_input = page_graph.locator("#searchInput")
    if search_input.is_visible():
        search_input.fill("ab-ba-sa6-ga")
        time.sleep(0.5)
    # Click first rank item to inspect official
    first_rank = page_graph.locator(".rank-item").first
    if first_rank.is_visible():
        first_rank.click()
        time.sleep(0.5)
    page_graph.screenshot(path=os.path.join(OUTPUT_DIR, "03_prosopography_graph.png"))

    # 4. Ur III Economic Ledger Balance Sheet Modal
    print("Capturing 04_ur3_ledger_balance_sheet.png...")
    page_ledger = context.new_page()
    page_ledger.goto("http://127.0.0.1:8000/explorer", wait_until="networkidle")
    time.sleep(1.0)
    btn_ledger = page_ledger.locator("button:has-text('Ur III Ledger')")
    if btn_ledger.is_visible():
        btn_ledger.click()
        time.sleep(1.0)
    page_ledger.screenshot(path=os.path.join(OUTPUT_DIR, "04_ur3_ledger_balance_sheet.png"))

    browser.close()
    print("All screenshots successfully captured!")
