import asyncio
from playwright.async_api import async_playwright

async def test_pagination():
    """Test pagination button functionality"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Set to False to see what's happening
        page = await browser.new_page()
        
        try:
            # Go to the StartX community page
            url = "https://web.startx.com/community"
            await page.goto(url, wait_until='networkidle', timeout=30000)
            await page.wait_for_timeout(1000)
            
            print("Testing pagination buttons...")
            
            # Test pages 2-10 to see which buttons work
            for page_number in range(2, 11):
                print(f"\n--- Testing Page {page_number} ---")
                
                # Get initial content
                initial_content = await page.content()
                
                # Try different button selectors
                selectors = [
                    f'button:has-text("{page_number}")',
                    f'a:has-text("{page_number}")', 
                    f'[data-page="{page_number}"]',
                    f'[aria-label*="{page_number}"]',
                    f'button[onclick*="{page_number}"]',
                    f'.pagination button:has-text("{page_number}")',
                    f'.pagination a:has-text("{page_number}")'
                ]
                
                button_found = False
                for selector in selectors:
                    try:
                        page_button = page.locator(selector).first
                        if await page_button.is_visible():
                            print(f"✅ Found button for page {page_number} with selector: {selector}")
                            await page_button.click()
                            await page.wait_for_timeout(1000)
                            button_found = True
                            break
                        else:
                            print(f"❌ Button for page {page_number} with selector '{selector}' is not visible")
                    except Exception as e:
                        print(f"❌ Failed with selector '{selector}': {e}")
                        continue
                
                if not button_found:
                    print(f"❌ No working button found for page {page_number}")
                
                # Check if page content changed
                final_content = await page.content()
                if initial_content == final_content:
                    print(f"⚠️  Page {page_number} content is identical - pagination failed")
                else:
                    print(f"✅ Page {page_number} content changed - pagination worked!")
                
                # Small delay between tests
                await asyncio.sleep(0.5)
            
            await browser.close()
            
        except Exception as e:
            print(f"Error: {e}")
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_pagination()) 