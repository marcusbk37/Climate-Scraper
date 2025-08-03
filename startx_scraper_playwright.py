import asyncio
from playwright.async_api import async_playwright
import json
from typing import List, Dict, Optional
import re

# i probs have to use genAI to filter the companies to be climate (rather than doing algorithmically)
# what is js rendering vs. non-js rendering?

class StartXScraperPlaywright:
    def __init__(self):
        self.base_url = "https://web.startx.com/community"
        
    async def get_page_content(self, page, url: str, page_number: int = 1) -> Optional[str]:
        """Fetch page content using Playwright with JavaScript rendering"""
        try:
            if page_number == 1:
                # Only navigate to the URL for the first page
                await page.goto(url, wait_until='networkidle', timeout=30000)
                await page.wait_for_timeout(2000)  # Wait 2 seconds to ensure buttons are loaded
            
            # If we need to navigate to a specific page, try clicking pagination
            if page_number > 1:
                print(f"\n--- Testing Page {page_number} ---")
                
                # Get initial content to compare later
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
                            # print(f"✅ Found button for page {page_number} with selector: {selector}")
                            await page_button.click()
                            await page.wait_for_timeout(1000)
                            button_found = True
                            break
                        else:
                            # print(f"❌ Button for page {page_number} with selector '{selector}' is not visible")
                            pass
                    except Exception as e:
                        # print(f"❌ Failed with selector '{selector}': {e}")
                        pass
                        continue
                
                if not button_found:
                    # print(f"❌ No working button found for page {page_number}")
                    pass
                    # Fall back to URL parameter
                    if '?' in url:
                        url += f"&page={page_number}"
                    else:
                        url += f"?page={page_number}"
                    await page.goto(url, wait_until='networkidle', timeout=30000)
                    await page.wait_for_timeout(1000)
                
                # Check if page content changed
                final_content = await page.content()
                if initial_content == final_content:
                    # print(f"⚠️  Page {page_number} content is identical - pagination failed")
                    return None  # Return None to indicate no change
                else:
                    # print(f"✅ Page {page_number} content changed - pagination worked!")
                    pass
            
            # Try to click "Load More" buttons if they exist
            load_more_selectors = [
                'button:has-text("Load More")',
                'button:has-text("Show More")',
                '[data-testid="load-more"]',
                '.load-more',
                '.show-more'
            ]
            
            for selector in load_more_selectors:
                try:
                    load_more_button = page.locator(selector).first
                    if await load_more_button.is_visible():
                        # print(f"Found load more button: {selector}")
                        pass
                        await load_more_button.click()
                        await page.wait_for_timeout(1000)
                except:
                    pass
                    continue
            
            # Get the final HTML content
            html_content = await page.content()
            return html_content
            
        except Exception as e:
            # print(f"Error fetching {url}: {e}")
            pass
            return None
    
    def extract_companies_from_html(self, html_content: str) -> List[Dict]:
        """Extract company information from HTML content"""
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(html_content, 'html.parser')
        companies = []
        
        # Look for company cards/entries with more specific selectors
        company_elements = soup.find_all(['div', 'article', 'li'], class_=re.compile(r'company|startup|card|item|grid-item'))
        
        if not company_elements:
            # Try alternative selectors
            company_elements = soup.find_all(['div', 'article'], class_=re.compile(r'grid|flex|container'))
        
        # If still no elements, try to find any divs that might contain company info
        if not company_elements:
            company_elements = soup.find_all('div', class_=True)
        
        # print(f"Found {len(company_elements)} potential company elements")
        
        for i, element in enumerate(company_elements):
            company_info = self.extract_company_info(element)
            if company_info:
                companies.append(company_info)
        
        return companies
    
    def extract_company_info(self, element) -> Optional[Dict]:
        """Extract individual company information from an element"""
        try:
            # Look for company name
            name_element = element.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'div'], 
                                     class_=re.compile(r'title|name|company-name'))
            if not name_element:
                name_element = element.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            
            if not name_element:
                return None
                
            company_name = name_element.get_text(strip=True)
            if not company_name:
                return None
            
            # Look for description
            description_element = element.find(['p', 'div', 'span'], 
                                            class_=re.compile(r'description|summary|tagline'))
            description = description_element.get_text(strip=True) if description_element else ""
            
            # Look for industries/tags
            industry_elements = element.find_all(['span', 'div'], 
                                              class_=re.compile(r'tag|industry|category'))
            industries = [tag.get_text(strip=True) for tag in industry_elements if tag.get_text(strip=True)]
            
            # Look for session/year
            session_element = element.find(['span', 'div'], 
                                        class_=re.compile(r'session|year|cohort'))
            session = session_element.get_text(strip=True) if session_element else ""
            
            return {
                'name': company_name,
                'description': description,
                'industries': industries,
                'session': session
            }
            
        except Exception as e:
            # print(f"Error extracting company info: {e}")
            return None
    
    def is_climate_related(self, company_info: Dict) -> bool:
        """Check if a company is climate-related based on its industries and description"""
        climate_keywords = [
            'climate', 'cleantech', 'clean tech', 'sustainability', 'renewable', 
            'solar', 'wind', 'energy', 'carbon', 'emissions', 'green', 'environmental',
            'conservation', 'recycling', 'waste', 'water', 'agriculture', 'food tech',
            'transportation', 'electric vehicle', 'ev', 'battery', 'storage'
        ]
        
        # Check industries
        industries_text = ' '.join(company_info.get('industries', [])).lower()
        for keyword in climate_keywords:
            if keyword in industries_text:
                return True
        
        # Check description
        description = company_info.get('description', '').lower()
        for keyword in climate_keywords:
            if keyword in description:
                return True
        
        return False
    
    async def scrape_climate_companies(self) -> List[Dict]:
        """Main method to scrape climate-related companies from all pages"""
        # print("Fetching StartX community pages with Playwright...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)  # Set to False to match test file
            page = await browser.new_page()
            
            try:
                all_companies = []
                page_number = 1
                max_pages = 50  # Set a reasonable limit
                
                while page_number <= max_pages:
                    # print(f"\n--- Processing Page {page_number} ---")
                    
                    html_content = await self.get_page_content(page, self.base_url, page_number)
                    
                    if not html_content:
                        # print(f"Failed to fetch page {page_number}, skipping to next page...")
                        page_number += 1
                        continue
                    
                    # Extract companies from this page
                    page_companies = self.extract_companies_from_html(html_content)
                    
                    if not page_companies:
                        print(f"No companies found on page {page_number}, skipping to next page...")
                        page_number += 1
                        continue
                    
                    all_companies.extend(page_companies)
                    print(f"Found {len(page_companies)} companies on page {page_number}")
                    
                    # Check if there's a next page by looking for pagination
                    if page_number == 1:
                        # On first page, try to determine total pages
                        from bs4 import BeautifulSoup
                        soup = BeautifulSoup(html_content, 'html.parser')
                        pagination_elements = soup.find_all(['button', 'a'], string=re.compile(r'\d+'))
                        page_numbers = []
                        for elem in pagination_elements:
                            text = elem.get_text(strip=True)
                            if text.isdigit() and 1 <= int(text) <= 100:
                                page_numbers.append(int(text))
                        
                        if page_numbers:
                            max_pages = max(page_numbers)
                            # print(f"Detected {max_pages} total pages")
                    
                    page_number += 1
                    
                    # Add a small delay between pages to be respectful
                    await asyncio.sleep(0.5)
                
                print(f"\nFound {len(all_companies)} total companies across all pages")
                
                # Save all companies to JSON file
                self.save_results(all_companies, "all_companies.json")
                
                # Filter for climate-related companies
                climate_companies = [company for company in all_companies if self.is_climate_related(company)]
                
                await browser.close()
                print(f"Found {len(climate_companies)} climate-related companies")
                return climate_companies
                
            except Exception as e:
                print(f"Error during scraping: {e}")
                await browser.close()
                return []
    
    def save_results(self, companies: List[Dict], filename: str = "climate_companies_playwright.json"):
        """Save results to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(companies, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(companies)} companies to {filename}")

async def main():
    scraper = StartXScraperPlaywright()
    climate_companies = await scraper.scrape_climate_companies()
    
    if climate_companies:
        # print("\nClimate-related companies found:")
        for i, company in enumerate(climate_companies, 1):
            # print(f"\n{i}. {company['name']}")
            # if company['description']:
            #     print(f"   Description: {company['description']}")
            # if company['industries']:
            #     print(f"   Industries: {', '.join(company['industries'])}")
            # if company['session']:
            #     print(f"   Session: {company['session']}")
            pass
        
        scraper.save_results(climate_companies)
    else:
        # print("No climate-related companies found.")
        pass

if __name__ == "__main__":
    asyncio.run(main()) 