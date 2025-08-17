"""
Companies Input Pipeline
Process companies from CSV file row by row:
1. Upload each company to Supabase
2. Process each company to Pinecone (chunk + embed)
"""

import csv
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from dotenv import load_dotenv

from database import get_db, ArticleDatabase
from embedding import get_embedder, ArticleEmbedder

# Load environment variables
load_dotenv()

class CompaniesInputPipeline:
    def __init__(self):
        """Initialize the pipeline with database and embedder instances."""
        self.db = get_db()
        self.embedder = get_embedder()
    
    def process_company_row(
        self,
        company_data: Dict[str, Any],
        chunk_size: int = 1000
    ) -> Dict[str, Any]:
        """
        Process a single company row: upload to Supabase, then to Pinecone.
        
        Args:
            company_data: Dictionary containing company information
            chunk_size: Size of text chunks for Pinecone
        
        Returns:
            Dictionary with processing results
        """
        results = {
            'company_name': company_data.get('Company Name', 'Unknown'),
            'supabase_success': False,
            'pinecone_success': False,
            'article_id': None,
            'chunk_count': 0,
            'error': None
        }
        
        try:
            # Extract company information from CSV columns
            company_name = company_data.get('Company Name', 'Unknown Company')
            drawdown_category = company_data.get('Drawdown Category', '')
            website = company_data.get('Website', '')
            num_employees = company_data.get('Number of employees', '')
            num_jobs = company_data.get('Number of active jobs', '')
            description = company_data.get('Description', '')
            
            # Create combined text for processing
            combined_text = f"Company: {company_name}\n"
            if drawdown_category:
                combined_text += f"Drawdown Category: {drawdown_category}\n"
            if num_employees:
                combined_text += f"Number of Employees: {num_employees}\n"
            if num_jobs:
                combined_text += f"Active Jobs: {num_jobs}\n"
            if website:
                combined_text += f"Website: {website}\n"
            if description:
                combined_text += f"Description: {description}\n"
            
            # Create metadata
            metadata = {
                'type': 'company',
                'drawdown_category': drawdown_category,
                'num_employees': num_employees,
                'num_jobs': num_jobs,
                'source': 'csv_import'
            }
            
            print(f"\n🏢 Processing company: {company_name}")
            print("-" * 50)
            
            # Step 1: Upload to Supabase
            print("📤 Uploading to Supabase...")
            article_id = self.db.store_article(
                url=website or f"company://{company_name.lower().replace(' ', '-')}",
                text=combined_text,
                title=company_name,
                authors=[],
                published_at=datetime.now().isoformat(),
                metadata=metadata
            )
            
            results['supabase_success'] = True
            results['article_id'] = article_id
            print(f"✅ Uploaded to Supabase (ID: {article_id})")
            
            # Step 2: Process to Pinecone
            print("🔍 Processing to Pinecone...")
            chunk_ids = self.embedder.store_article_chunks(
                article_id=article_id,
                text=combined_text,
                title=company_name,
                chunk_size=chunk_size
            )
            
            results['pinecone_success'] = True
            results['chunk_count'] = len(chunk_ids)
            print(f"✅ Uploaded {len(chunk_ids)} chunks to Pinecone")
            
        except Exception as e:
            results['error'] = str(e)
            print(f"❌ Error processing company: {e}")
        
        return results
    
    def process_csv_file(
        self,
        csv_file_path: str,
        chunk_size: int = 1000,
        start_row: int = 0,
        max_rows: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Process companies from a CSV file row by row.
        
        Args:
            csv_file_path: Path to the CSV file
            chunk_size: Size of text chunks for Pinecone
            start_row: Row to start processing from (0-indexed)
            max_rows: Maximum number of rows to process (None for all)
        
        Returns:
            Dictionary with processing summary
        """
        print(f"📁 Processing CSV file: {csv_file_path}")
        print("=" * 60)
        
        if not os.path.exists(csv_file_path):
            raise FileNotFoundError(f"CSV file not found: {csv_file_path}")
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'csv_file': csv_file_path,
            'total_rows': 0,
            'processed_rows': 0,
            'successful_uploads': 0,
            'successful_pinecone': 0,
            'failed_rows': 0,
        }
        
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                rows = list(reader)
                
                summary['total_rows'] = len(rows)
                print(f"📊 Found {len(rows)} rows in CSV file")
                
                # Determine processing range
                end_row = len(rows) if max_rows is None else min(start_row + max_rows, len(rows))
                rows_to_process = rows[start_row:end_row]
                
                print(f"🔄 Processing rows {start_row} to {end_row-1} ({len(rows_to_process)} rows)")
                print("=" * 60)
                
                for i, row in enumerate(rows_to_process, start_row + 1):
                    print(f"\n📝 Row {i}/{end_row}")
                    
                    # Process the company row
                    result = self.process_company_row(row, chunk_size)
                    summary['processed_rows'] += 1
                    
                    if result['supabase_success']:
                        summary['successful_uploads'] += 1
                    
                    if result['pinecone_success']:
                        summary['successful_pinecone'] += 1
                    
                    if result['error']:
                        summary['failed_rows'] += 1
                    
                    # Print progress
                    print(f"   📈 Progress: {summary['processed_rows']}/{len(rows_to_process)}")
                    print(f"   ✅ Supabase: {summary['successful_uploads']}")
                    print(f"   🔍 Pinecone: {summary['successful_pinecone']}")
                    print(f"   ❌ Failed: {summary['failed_rows']}")
        
        except Exception as e:
            print(f"❌ Error processing CSV file: {e}")
            summary['error'] = str(e)
        
        # Print final summary
        print("\n🎉 CSV Processing Complete!")
        print("=" * 60)
        print(f"📊 Final Summary:")
        print(f"   📁 File: {csv_file_path}")
        print(f"   📄 Total rows: {summary['total_rows']}")
        print(f"   🔄 Processed rows: {summary['processed_rows']}")
        print(f"   ✅ Successful Supabase uploads: {summary['successful_uploads']}")
        print(f"   🔍 Successful Pinecone uploads: {summary['successful_pinecone']}")
        print(f"   ❌ Failed rows: {summary['failed_rows']}")
        
        return summary

def demo_companies_processing():
    """Run a demonstration of the companies processing pipeline."""
    
    # Initialize pipeline
    pipeline = CompaniesInputPipeline()
    
    # Process the CSV file
    summary = pipeline.process_csv_file(
        csv_file_path="Climate Map Companies.csv",
        chunk_size=1000,
        start_row=0,
        max_rows=None  # Process all rows
    )
    
    return summary

if __name__ == "__main__":
    demo_companies_processing()
