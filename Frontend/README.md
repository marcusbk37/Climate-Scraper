# Article Search Frontend

A simple, user-friendly web interface for searching through articles stored in your Pinecone/Supabase database.

## Features

- 🔍 **Natural Language Search**: Search using everyday language
- 📱 **Responsive Design**: Works on desktop, tablet, and mobile
- ⚡ **Fast Results**: Real-time search with relevance scoring
- 🎨 **Modern UI**: Clean, professional interface
- 📊 **Relevance Scoring**: See how well each article matches your query

## Setup Instructions

### Prerequisites

Make sure you have:
1. Python 3.8+ installed
2. Your `.env` file with Pinecone and Supabase credentials in the `Embedding/` directory
3. Articles already processed and stored in your database

### Installation

1. **Navigate to the Frontend directory:**
   ```bash
   cd Frontend
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the application:**
   ```bash
   python app.py
   ```

4. **Open your browser and go to:**
   ```
   http://localhost:5000
   ```

## Usage

### For Non-Technical Users

1. **Enter your search query** in the search box
   - Use natural language (e.g., "AI in healthcare", "climate change solutions")
   - Be specific for better results
   - Try different keywords if you don't get the results you want

2. **Click "Search Articles"** or press Enter

3. **Review the results:**
   - Articles are sorted by relevance (highest match first)
   - Each article shows a relevance percentage
   - Click on article titles to open the original source
   - View article previews to see if they're relevant

### Example Searches

- "artificial intelligence healthcare"
- "climate change renewable energy"
- "machine learning applications"
- "sustainable technology solutions"
- "AI ethics and privacy"

## Technical Details

### Architecture

- **Frontend**: HTML/CSS/JavaScript with modern, responsive design
- **Backend**: Flask web server
- **Search**: Pinecone vector database for semantic search
- **Storage**: Supabase for article metadata and content

### API Endpoints

- `GET /` - Main search interface
- `POST /search` - Search endpoint (accepts JSON with `query` and optional `top_k`)
- `GET /health` - Health check endpoint

### Environment Variables

The application uses the same environment variables as your Embedding system:
- `PINECONE_API_KEY`
- `PINECONE_ENVIRONMENT`
- `PINECONE_INDEX_NAME`
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`

## Troubleshooting

### Common Issues

1. **"Module not found" errors:**
   - Make sure you're in the `Frontend` directory
   - Ensure the `Embedding` directory is accessible
   - Check that all requirements are installed

2. **"Search failed" errors:**
   - Verify your `.env` file has correct credentials
   - Check that Pinecone and Supabase are accessible
   - Ensure you have articles in your database

3. **No search results:**
   - Try different search terms
   - Check that articles have been processed and stored
   - Verify the search query isn't too specific

### Getting Help

If you encounter issues:
1. Check the terminal output for error messages
2. Verify your environment variables are set correctly
3. Ensure your database has articles to search through

## Customization

### Styling
The interface uses CSS custom properties and can be easily customized by modifying the styles in `templates/index.html`.

### Search Parameters
You can adjust search behavior by modifying the `top_k` parameter in the JavaScript code (currently set to 20 results).

### Adding Features
The Flask app structure makes it easy to add new features like:
- Search filters
- Result pagination
- Export functionality
- User authentication
