from playwright.sync_api import sync_playwright

def capture_all():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={'width': 1440, 'height': 900})
        
        # 1. Genuine Showcase Tablet Dossier (P131610 Louvre Join)
        page.goto('http://127.0.0.1:8000/explorer')
        page.wait_for_timeout(2000)
        page.screenshot(path='assets/images/01_tablet_explorer_showcase.png')
        print('1. Captured genuine 01_tablet_explorer_showcase.png')
        
        # 2. Genuine Metrology & Assyriological Unicode Typography
        page.click('#card-P100004')
        page.wait_for_timeout(1000)
        page.click('#btnTranslitMode')
        page.wait_for_timeout(1000)
        page.screenshot(path='assets/images/02_tablet_metrology_unicode.png')
        print('2. Captured genuine 02_tablet_metrology_unicode.png')
        
        # 3. Genuine Full-Width Prosopography Graph
        page.click('#btnNavGraph')
        page.wait_for_timeout(3500)
        frame = page.frame(name='', url=lambda u: 'graph' in u)
        if frame:
            rank_item = frame.locator('.rank-item').first
            if rank_item.count() > 0:
                rank_item.click()
                page.wait_for_timeout(1000)
        page.screenshot(path='assets/images/03_prosopography_graph.png')
        print('3. Captured genuine 03_prosopography_graph.png')
        
        # 4. Genuine Ur III Ledger Balance Sheet Modal
        page.click('#btnNavDossier')
        page.wait_for_timeout(1000)
        page.evaluate("openLedgerModal()")
        page.wait_for_timeout(2000)
        page.screenshot(path='assets/images/04_ur3_ledger_balance_sheet.png')
        print('4. Captured genuine 04_ur3_ledger_balance_sheet.png')
        
        browser.close()

if __name__ == '__main__':
    capture_all()
