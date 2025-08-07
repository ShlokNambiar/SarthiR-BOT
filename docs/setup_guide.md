# RAG System Setup Guide

This guide will help you set up and run the RAG (Retrieval-Augmented Generation) system for processing documents and creating a question-answering chatbot.

## Prerequisites

- Python 3.8 or higher
- OpenAI API key
- Pinecone API key
- (Optional) Supabase account for chat memory persistence
- (Optional) Google API key and Custom Search Engine ID for web search

## Installation

1. Clone or download the repository to your local machine

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the root directory with your API keys:
   ```
   # OpenAI API Key
   OPENAI_API_KEY=your_openai_api_key_here

   # Pinecone API Key
   PINECONE_API_KEY=your_pinecone_api_key_here

   # Supabase Configuration (optional, for chat memory)
   SUPABASE_URL=your_supabase_url_here
   SUPABASE_API_KEY=your_supabase_api_key_here

   # Web Search Configuration (optional, for web search fallback)
   ENABLE_WEB_SEARCH=false
   ```

## Running the Pipeline

### Option 1: Using the Batch File

For Windows users, simply run:
```
run_pipeline.bat
```

### Option 2: Using Python

Process a specific PDF file:
```bash
python main.py --pdf "rag context files/UDCPR Updated 30.01.25 with earlier provisions & corrections.pdf"
```

Process additional files:
```bash
python process_new_files.py --files "rag context files/list_documents_ca_services.txt" "rag context files/comprehensive_regulatory_services.txt"
```

## Running Individual Pipeline Steps

If you need to run specific steps of the pipeline:

### 1. Extract Text from PDF

```bash
python pdf_extractor.py "rag context files/UDCPR Updated 30.01.25 with earlier provisions & corrections.pdf" -o output/udcpr_extracted.json
```

### 2. Chunk the Text

```bash
python text_chunker.py output/udcpr_extracted.json -o output/udcpr_chunked.json
```

### 3. Generate Embeddings

```bash
python embeddings_generator.py output/udcpr_chunked.json -o output/udcpr_embeddings.json -c output/embeddings_checkpoint.json
```

### 4. Upload to Pinecone

```bash
python pinecone_uploader.py output/udcpr_embeddings.json -c output/upload_checkpoint.json
```

## Using the Chatbot

### Command Line Interface

Run the interactive chatbot:
```bash
python rag_chatbot.py
```

Or use the batch file:
```
chat.bat
```

Ask a single question:
```bash
python rag_chatbot.py --query "What are the building height regulations?"
```

### Web Interface

Run the Streamlit web app:
```bash
streamlit run udcpr_chatbot_streamlit.py
```

Or use the batch file:
```
run_web_chatbot.bat
```

## Advanced Features

### Chat Memory

The system supports persistent chat memory using Supabase. To enable this:

1. Create a Supabase project
2. Run the SQL schema in `supabase_schema.sql`
3. Add your Supabase credentials to the `.env` file
4. Use the `--session` parameter to continue conversations:
   ```bash
   python rag_chatbot.py --session "your-session-id"
   ```

### Web Search

For questions outside the document's scope, the system can fall back to web search:

1. Set up a Google Custom Search Engine
2. Add your Google API key and CSE ID to the `.env` file
3. Set `ENABLE_WEB_SEARCH=true` in your `.env` file
4. Use the `--web-search` flag:
   ```bash
   python rag_chatbot.py --web-search
   ```

## Troubleshooting

### API Rate Limits

If you encounter rate limit errors with OpenAI:
- Increase the `RATE_LIMIT_DELAY` in `embeddings_generator.py`
- Reduce the `BATCH_SIZE` to process fewer chunks at once

### Memory Issues

For large documents:
- Process files individually rather than all at once
- Reduce the chunk size in `text_chunker.py`
- Use checkpointing to resume long-running processes

### Pinecone Connection Issues

If you have trouble connecting to Pinecone:
- Check that your API key is correct
- Try a different environment in `pinecone_uploader.py`
- Ensure your Pinecone plan supports the index size you need