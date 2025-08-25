import urllib, urllib.request
# url = 'http://export.arxiv.org/api/query?search_query=all:electron&start=0&max_results=1'
# data = urllib.request.urlopen(url)
# print(data.read().decode('utf-8'))

def search_arxiv(keyword, max_results=5):
    # URL encode the keyword for the query
    encoded_keyword = urllib.parse.quote(keyword)
    
    # Construct the ArXiv API query URL
    query_url = f'http://export.arxiv.org/api/query?search_query=all:{encoded_keyword}&start=0&max_results={max_results}'
    
    try:
        # Make the request
        response = urllib.request.urlopen(query_url)
        data = response.read().decode('utf-8')
        
        # Basic XML parsing to extract titles and abstracts
        # This is a simple approach - could use xml.etree.ElementTree for more robust parsing
        papers = data.split('<entry>')[1:]  # Skip the first split as it's header info
        
        print(f"\nFound {len(papers)} papers related to '{keyword}':\n")
        print("-" * 80)
        
        for i, paper in enumerate(papers, 1):
            # Extract title
            title_start = paper.find('<title>') + 7
            title_end = paper.find('</title>')
            title = paper[title_start:title_end].strip()
            
            # Extract abstract
            abstract_start = paper.find('<summary>') + 9
            abstract_end = paper.find('</summary>')
            abstract = paper[abstract_start:abstract_end].strip()
            # Extract link/URL
            id_start = paper.find('<id>') + 4
            id_end = paper.find('</id>')
            paper_id = paper[id_start:id_end].strip()
            # Convert ArXiv ID to URL format
            url = f"https://arxiv.org/abs/{paper_id.split('/')[-1]}"
            
            print(f"\nPaper {i}:")
            print(f"Title: {title}")
            print(f"Abstract: {abstract}")
            print(f"URL: {url}")
            print("-" * 80)
            
    except Exception as e:
        print(f"Error occurred: {e}")

# Example usage
keyword = "quantum computing"
search_arxiv(keyword)
