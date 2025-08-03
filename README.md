# StartX Climate Companies Scraper

This project scrapes the StartX community page to extract climate-related companies using web scraping techniques.

## Features

- Extracts company information from the StartX community page
- Filters for climate-related companies based on keywords
- Supports both requests+BeautifulSoup and Playwright for JavaScript rendering
- Saves results to JSON files
- Handles dynamic content loading

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Install Playwright browsers (if using the Playwright version):
```bash
playwright install
```

## Usage

### Basic Scraper (Requests + BeautifulSoup)

Run the basic scraper:
```bash
python startx_scraper.py
```

### Playwright Scraper (for JavaScript-heavy pages)

If the basic scraper doesn't work due to JavaScript rendering, use the Playwright version:
```bash
python startx_scraper_playwright.py
```

## Output

The scrapers will:
1. Fetch the StartX community page
2. Extract company information (name, description, industries, session)
3. Filter for climate-related companies
4. Display results in the console
5. Save results to JSON files:
   - `climate_companies.json` (basic scraper)
   - `climate_companies_playwright.json` (Playwright scraper)

## Climate Keywords

The scraper looks for companies with these climate-related keywords:
- climate, cleantech, clean tech, sustainability, renewable
- solar, wind, energy, carbon, emissions, green, environmental
- conservation, recycling, waste, water, agriculture, food tech
- transportation, electric vehicle, ev, battery, storage

## Files

- `startx_scraper.py` - Basic scraper using requests + BeautifulSoup
- `startx_scraper_playwright.py` - Advanced scraper using Playwright
- `requirements.txt` - Python dependencies
- `README.md` - This file

## Notes

- The basic scraper is faster but may not work if the page requires JavaScript
- The Playwright scraper can handle dynamic content and "Load More" buttons
- Both scrapers save results to JSON files for further analysis
- The scrapers include error handling and timeout protection 