"""
Gmail processor that reads emails and stores them in both Supabase and Pinecone databases.
Integrates with the existing embedding.py and database.py files from the Frontend directory.
"""

import os
import sys
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv

# Add the Frontend directory to the path to import the modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Frontend'))

# Import the existing modules
from embedding import ArticleEmbedder
from database import ArticleDatabase
from gmail_read import GmailReader

# Load environment variables
load_dotenv()

class GmailProcessor:
    def __init__(self):
        """Initialize the Gmail processor with all necessary components."""
        self.gmail_reader = GmailReader()
        self.embedder = ArticleEmbedder()
        self.db = ArticleDatabase()
        
    def extract_email_content(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract relevant content from Gmail email data.
        
        Args:
            email_data: Raw email data from Composio Gmail API
            
        Returns:
            Dict containing extracted email content
        """
        try:
            # Extract basic email information from Composio format
            email_id = email_data.get('messageId', '')
            thread_id = email_data.get('threadId', '')
            
            # Extract subject and sender from Composio format
            subject = email_data.get('subject', 'No Subject')
            sender = email_data.get('sender', 'Unknown')
            to_email = email_data.get('to', 'Unknown')
            date = email_data.get('messageTimestamp', '')
            
            # Extract email body from preview
            preview = email_data.get('preview', {})
            body = preview.get('body', '') if preview else ''
            
            # If no body in preview, try messageText
            if not body:
                body = email_data.get('messageText', '')
            
            # Create a URL-like identifier for the email
            email_url = f"gmail://{email_id}"
            
            return {
                'email_id': email_id,
                'thread_id': thread_id,
                'subject': subject,
                'from_email': sender,
                'to_email': to_email,
                'date': date,
                'body': body,
                'url': email_url,
                'raw_data': email_data  # Keep raw data for potential future use
            }
        except Exception as e:
            print(f"❌ Error extracting email content: {e}")
            return None
    

    
    def process_emails(self, max_results: int = 10, chunk_size: int = 1000) -> List[str]:
        """
        Process emails from Gmail and store them in both Supabase and Pinecone.
        
        Args:
            max_results: Maximum number of emails to process
            chunk_size: Size of text chunks for Pinecone storage
            
        Returns:
            List of processed email IDs
        """
        print(f"🚀 Starting email processing for {max_results} emails...")
        
        # Read emails from Gmail
        gmail_result = self.gmail_reader.read_emails(max_results=max_results)
        # print("gmail result:", gmail_result) - getting gmail results properly
        
        if not gmail_result or 'data' not in gmail_result:
            print("❌ No emails retrieved from Gmail")
            return []
        
        emails = gmail_result['data'].get('messages', [])
        if not emails:
            print("❌ No messages found in Gmail response")
            return []
        
        print(f"📧 Found {len(emails)} emails to process")
        
        processed_ids = []
        
        for i, email in enumerate(emails):
            try:
                print(f"\n📝 Processing email {i+1}/{len(emails)}...")
                print("email:", email)
                # Extract email content
                email_content = self.extract_email_content(email)
                if not email_content or not email_content.get('body'):
                    print(f"⚠️  Skipping email {i+1} - no content extracted")
                    continue
                print("email text:", email_content['body'])
                
                # Create a title from subject
                title = email_content['subject'] or f"Email from {email_content['from_email']}"
                
                # Create metadata for the email
                metadata = {
                    "type": "email",
                    'email_id': email_content['email_id'],
                    'thread_id': email_content['thread_id'],
                    'from_email': email_content['from_email'],
                    'to_email': email_content['to_email'],
                    'date': email_content['date'],
                    'source': 'gmail',
                    'processed_at': datetime.utcnow().isoformat()
                }
                
                # Store in Supabase
                print(f"💾 Storing email in Supabase...")
                article_id = self.db.store_article(
                    url=email_content['url'], # want the URL for the email for deduplication... ith... and can choose not to show it
                    text=email_content['body'],
                    title=title,
                    authors=[email_content['from_email']],
                    published_at=email_content['date'],
                    metadata=metadata
                )
                
                if not article_id:
                    print(f"❌ Failed to store email {i+1} in Supabase")
                    continue
                
                # Store chunks in Pinecone
                print(f"🔍 Storing email chunks in Pinecone...")
                chunk_ids = self.embedder.store_article_chunks(
                    article_id=article_id,
                    text=email_content['body'],
                    title=title,
                    chunk_size=chunk_size
                )
                
                if chunk_ids:
                    print(f"✅ Successfully processed email {i+1}: {title}")
                    print(f"   📊 Stored {len(chunk_ids)} chunks in Pinecone")
                    processed_ids.append(article_id)
                else:
                    print(f"⚠️  Email {i+1} stored in Supabase but failed to store chunks in Pinecone")
                
            except Exception as e:
                print(f"❌ Error processing email {i+1}: {e}")
                continue
        
        print(f"\n🎯 Email processing complete!")
        print(f"✅ Successfully processed {len(processed_ids)} out of {len(emails)} emails")
        
        return processed_ids


def main():
    """Main function to test the Gmail processor."""
    processor = GmailProcessor()
    
    # Process a few emails
    print("🚀 Testing Gmail processor...")
    processed_ids = processor.process_emails(max_results=5)
    
    if processed_ids:
        print(f"\n✅ Successfully processed {len(processed_ids)} emails")
        
    else:
        print("❌ No emails were processed successfully")

if __name__ == "__main__":
    main()
