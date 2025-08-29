# Gmail Processor

This module integrates Gmail reading with Supabase and Pinecone databases to store and search through emails.

## Features

- **Gmail Integration**: Reads emails using Composio Gmail API
- **Supabase Storage**: Stores full email content and metadata in Supabase
- **Pinecone Embeddings**: Creates searchable embeddings of email content
- **Search Functionality**: Search through processed emails using semantic search
- **Email Content Extraction**: Handles multipart emails and extracts text content

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment Variables**:
   Make sure you have the following environment variables set in your `.env` file:
   ```
   # Gmail/Composio
   COMPOSIO_API_KEY=your_composio_api_key
   
   # Supabase
   SUPABASE_URL=your_supabase_url
   SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
   
   # Pinecone
   PINECONE_API_KEY=your_pinecone_api_key
   PINECONE_ENVIRONMENT=your_pinecone_environment
   PINECONE_INDEX_NAME=your_pinecone_index_name
   ```

3. **Gmail Authentication**:
   - Run `python gmail_login.py` to set up Gmail authentication
   - Follow the OAuth flow in your browser
   - The connection will be saved for future use

## Usage

### Command Line Interface

The easiest way to use this module is through the command line interface:

```bash
# Process 10 emails (default)
python process_gmail.py

# Process a specific number of emails
python process_gmail.py --max-emails 50

# Process emails with custom chunk size
python process_gmail.py --max-emails 20 --chunk-size 500

# Search through processed emails
python process_gmail.py --search "investment opportunity"

# Search with custom result limit
python process_gmail.py --search "startup funding" --top-k 20
```

### Programmatic Usage

You can also use the `GmailProcessor` class directly in your code:

```python
from gmail_processor import GmailProcessor

# Initialize the processor
processor = GmailProcessor()

# Process emails
processed_ids = processor.process_emails(max_results=10, chunk_size=1000)

# Search through processed emails
results = processor.search_emails("your search query", top_k=10)

# Access the results
for email in results['emails']:
    print(f"Title: {email['title']}")
    print(f"From: {email['metadata']['from_email']}")
    print(f"Content: {email['text'][:200]}...")
```

## File Structure

- `gmail_login.py`: Gmail authentication setup
- `gmail_read.py`: Basic Gmail reading functionality
- `gmail_processor.py`: Main processor class that integrates everything
- `process_gmail.py`: Command line interface
- `requirements.txt`: Python dependencies

## How It Works

1. **Email Reading**: Uses Composio Gmail API to fetch emails
2. **Content Extraction**: Extracts text content from multipart emails
3. **Supabase Storage**: Stores full email data with metadata
4. **Chunking**: Splits email content into searchable chunks
5. **Pinecone Storage**: Stores embeddings of chunks for semantic search
6. **Search**: Provides semantic search through processed emails

## Email Metadata

Each processed email includes the following metadata:
- `email_id`: Gmail message ID
- `thread_id`: Gmail thread ID
- `from_email`: Sender email address
- `to_email`: Recipient email address
- `date`: Email date
- `source`: Set to 'gmail'
- `processed_at`: Timestamp when processed

## Error Handling

The processor includes comprehensive error handling:
- Skips emails with no content
- Continues processing if individual emails fail
- Provides detailed logging of successes and failures
- Handles Gmail API errors gracefully

## Notes

- Emails are stored with a URL format of `gmail://{email_id}` for consistency
- The processor prefers plain text over HTML content when available
- Chunks are created with sentence boundaries to maintain context
- Duplicate emails (same URL) are handled gracefully

