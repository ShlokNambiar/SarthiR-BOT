# GitHub Deployment Instructions

## 🚀 Quick Deploy to GitHub

Your UDCPR RAG Chatbot API is now ready for GitHub! Here's how to deploy it:

### 1. Create GitHub Repository

1. Go to [GitHub](https://github.com) and create a new repository
2. Name it: `udcpr-rag-chatbot` (or your preferred name)
3. Make it public or private as needed
4. **Don't** initialize with README (we already have one)

### 2. Push to GitHub

```bash
# Add your GitHub repository as remote
git remote add origin https://github.com/yourusername/udcpr-rag-chatbot.git

# Push to GitHub
git branch -M main
git push -u origin main
```

### 3. Deploy to Render

1. Go to [Render](https://render.com)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Render will automatically detect the `render.yaml` configuration
5. Add environment variables:
   - `OPENAI_API_KEY`
   - `PINECONE_API_KEY`
6. Deploy!

## 📁 Project Structure

```
udcpr-rag-chatbot/
├── 📄 README.md                 # Main documentation
├── 🚀 api_server.py            # FastAPI server (main entry point)
├── ⚙️ render.yaml              # Render deployment config
├── 📋 requirements.txt         # Python dependencies
├── 🔧 main.py                  # RAG pipeline orchestrator
├── 📚 docs/                    # Documentation
│   ├── DEPLOYMENT_GUIDE.md
│   ├── CHATBOT_README.md
│   └── ...
├── 💡 examples/                # Integration examples
│   ├── chatbot_integration_example.html
│   └── test_api.py
├── 🔧 pipeline/                # RAG processing modules
│   ├── __init__.py
│   ├── pdf_extractor.py
│   ├── text_chunker.py
│   ├── embeddings_generator.py
│   ├── pinecone_uploader.py
│   └── query_interface.py
├── 📁 rag context files/       # Source documents
└── 📁 output/                  # Generated data (gitignored)
```

## 🔑 Key Features

✅ **FastAPI REST API** - Production-ready API server  
✅ **RAG Implementation** - Retrieval-Augmented Generation  
✅ **Vector Database** - Pinecone integration  
✅ **AI Models** - OpenAI GPT-4 and embeddings  
✅ **Session Management** - Conversation context  
✅ **CORS Enabled** - Web integration ready  
✅ **Documentation** - Comprehensive guides  
✅ **Examples** - Ready-to-use integration code  
✅ **Deployment Ready** - Render configuration included  

## 🌐 API Endpoints

- `GET /` - Root endpoint
- `GET /health` - Health check
- `POST /chat` - Main chat endpoint
- `DELETE /chat/{session_id}` - Clear session
- `GET /sessions` - List active sessions

## 🔧 Environment Variables Required

```env
OPENAI_API_KEY=your_openai_api_key_here
PINECONE_API_KEY=your_pinecone_api_key_here
```

## 📱 Integration Example

```javascript
const API_URL = 'https://your-app.onrender.com';

async function sendMessage(message) {
    const response = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message })
    });
    return await response.json();
}
```

## 🎯 Next Steps

1. **Deploy to GitHub** (follow steps above)
2. **Deploy to Render** using the GitHub integration
3. **Test the API** using the provided test script
4. **Integrate into your website** using the HTML example
5. **Customize** the chatbot styling and behavior

## 📞 Support

- 📖 Check the documentation in the `docs/` folder
- 🐛 Report issues on GitHub Issues
- 💬 Use the chatbot for UDCPR-related questions!

---

**Your UDCPR RAG Chatbot API is ready for production! 🎉**