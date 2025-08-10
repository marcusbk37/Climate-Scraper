import json

def export_companies_to_txt():
    """Read all_companies.json and export company names to a text file"""
    try:
        with open('all_companies.json', 'r', encoding='utf-8') as f:
            companies = json.load(f)
        
        # Extract just the company names
        company_names = [company.get('name', 'Unknown') for company in companies]
        
        # Write to text file
        with open('company_names.txt', 'w', encoding='utf-8') as f:
            f.write('\n'.join(company_names))
        
        print(f"Successfully exported {len(company_names)} company names to company_names.txt")
        
        # Also print first few as preview
        print("\nFirst 10 companies:")
        for i, name in enumerate(company_names[:10], 1):
            print(f"{i}. {name}")
        
        if len(company_names) > 10:
            print(f"... and {len(company_names) - 10} more")
        
    except FileNotFoundError:
        print("Error: all_companies.json not found")
    except json.JSONDecodeError:
        print("Error: Invalid JSON in all_companies.json")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    export_companies_to_txt() 