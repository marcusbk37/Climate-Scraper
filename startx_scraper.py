import requests
from bs4 import BeautifulSoup
import json
import time
from typing import List, Dict, Optional
import re

class StartXScraper:
    def __init__(self):
        self.base_url = "https://web.startx.com/community"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def get_page_content(self, url: str) -> Optional[str]:
        """Fetch page content using requests"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    def extract_companies_from_html(self, html_content: str) -> List[Dict]:
        """Extract company information from HTML content"""
        soup = BeautifulSoup(html_content, 'html.parser')
        companies = []
        
        # Look for company cards/entries
        # Based on the website structure, companies might be in cards or list items
        company_elements = soup.find_all(['div', 'article', 'li'], class_=re.compile(r'company|startup|card|item'))
        
        if not company_elements:
            # Try alternative selectors
            company_elements = soup.find_all(['div', 'article'], class_=re.compile(r'grid|flex|container'))
        
        for element in company_elements:
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
            print(f"Error extracting company info: {e}")
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
    
    def scrape_climate_companies(self) -> List[Dict]:
        """Main method to scrape climate-related companies"""
        print("Fetching StartX community page...")
        html_content = self.get_page_content(self.base_url)
        
        if not html_content:
            print("Failed to fetch page content")
            return []
        
        print("Extracting companies from HTML...")
        all_companies = self.extract_companies_from_html(html_content)
        
        print(f"Found {len(all_companies)} total companies")
        
        # Filter for climate-related companies
        climate_companies = [company for company in all_companies if self.is_climate_related(company)]
        
        print(f"Found {len(climate_companies)} climate-related companies")
        
        return climate_companies
    
    def save_results(self, companies: List[Dict], filename: str = "climate_companies.json"):
        """Save results to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(companies, f, indent=2, ensure_ascii=False)
        print(f"Results saved to {filename}")

def main():
    scraper = StartXScraper()
    climate_companies = scraper.scrape_climate_companies()
    
    if climate_companies:
        print("\nClimate-related companies found:")
        for i, company in enumerate(climate_companies, 1):
            print(f"\n{i}. {company['name']}")
            if company['description']:
                print(f"   Description: {company['description']}")
            if company['industries']:
                print(f"   Industries: {', '.join(company['industries'])}")
            if company['session']:
                print(f"   Session: {company['session']}")
        
        scraper.save_results(climate_companies)
    else:
        print("No climate-related companies found. The page might require JavaScript rendering.")

if __name__ == "__main__":
    main() 