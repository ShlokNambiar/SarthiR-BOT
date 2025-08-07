# UDCPR RAG Chatbot API

A Retrieval-Augmented Generation (RAG) chatbot API for the Unified Development Control and Promotion Regulations (UDCPR) document for Maharashtra State, India. This API provides intelligent responses to queries about building regulations, zoning requirements, and development control rules.

## 🚀 Features

- **FastAPI REST API** - High-performance API server
- **RAG Implementation** - Retrieval-Augmented Generation using OpenAI and Pinecone
- **Session Management** - Maintains conversation context
- **CORS Enabled** - Ready for web integration
- **Source Attribution** - Returns document sources for transparency
- **Floating Chatbot Widget** - Ready-to-use HTML/CSS/JS integration
- **Render Deployment Ready** - One-click deployment configuration

## 🛠️ Tech Stack

- **Backend**: FastAPI, Python 3.8+
- **AI/ML**: OpenAI GPT-4, OpenAI Embeddings
- **Vector Database**: Pinecone
- **Document Processing**: PyMuPDF, LangChain
- **Deployment**: Render (configured)

## 📋 Prerequisites

- Python 3.8 or higher
- OpenAI API key ([Get here](https://platform.openai.com/api-keys))
- Pinecone API key ([Get here](https://app.pinecone.io/))

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/udcpr-rag-chatbot.git
cd udcpr-rag-chatbot
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Up Environment Variables

Create a `.env` file in the root directory:

```env
# Required
OPENAI_API_KEY=your_openai_api_key_here
PINECONE_API_KEY=your_pinecone_api_key_here

# Optional
SUPABASE_URL=your_supabase_url_here
SUPABASE_API_KEY=your_supabase_api_key_here
ENABLE_WEB_SEARCH=false
```

### 4. Process Documents (First Time Setup)

```bash
# Process the UDCPR PDF and upload to Pinecone
python main.py --pdf "rag context files/UDCPR Updated 30.01.25 with earlier provisions & corrections.pdf"
```

### 5. Run the API Server

```bash
python api_server.py
```

The API will be available at `http://localhost:8000`

## 📚 API Documentation

### Endpoints

#### Health Check
```http
GET /health
```

#### Chat
```http
POST /chat
```

**Request Body:**
```json
{
  "message": "What are the building height regulations?",
  "session_id": "optional-session-id",
  "chat_history": []
}
```

**Response:**
```json
{
  "response": "According to UDCPR regulations...",
  "session_id": "session-123",
  "sources": [
    {
      "source": "UDCPR Document",
      "page": "15",
      "score": 0.85
    }
  ]
}
```

#### Clear Session
```http
DELETE /chat/{session_id}
```

#### List Sessions
```http
GET /sessions
```

## 🌐 Web Integration

Use the provided `chatbot_integration_example.html` as a template for integrating the chatbot into your website:

```javascript
const API_BASE_URL = 'https://your-deployed-api.onrender.com';

async function sendMessage(message) {
    const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: message })
    });
    return await response.json();
}
```

## 🚀 Deployment

### Deploy to Render

1. **Fork this repository** to your GitHub account

2. **Create a new Web Service** on [Render](https://render.com)

3. **Connect your GitHub repository**

4. **Configure the service:**
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python api_server.py`

5. **Add environment variables:**
   - `OPENAI_API_KEY`
   - `PINECONE_API_KEY`

6. **Deploy!** 🎉

The `render.yaml` file is included for automatic configuration.

## 🧪 Testing

Test the API locally:

```bash
python test_api.py
```

Test specific endpoints:

```bash
# Health check
curl http://localhost:8000/health

# Chat
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What are the FSI regulations?"}'
```

## 📁 Project Structure

```
udcpr-rag-chatbot/
├── api_server.py              # FastAPI server
├── main.py                    # RAG pipeline orchestrator
├── requirements.txt           # Python dependencies
├── render.yaml               # Render deployment config
├── .env.example              # Environment variables template
├── .gitignore               # Git ignore rules
├── DEPLOYMENT_GUIDE.md      # Detailed deployment guide
├── chatbot_integration_example.html  # Web integration example
├── test_api.py              # API testing script
├── rag context files/       # Source documents
│   ├── UDCPR Updated 30.01.25 with earlier provisions & corrections.pdf
│   └── ...
├── output/                  # Processed data (generated)
└── pipeline modules/        # RAG processing modules
    ├── pdf_extractor.py
    ├── text_chunker.py
    ├── embeddings_generator.py
    ├── pinecone_uploader.py
    └── query_interface.py
```

## 🔧 Configuration

### Pinecone Setup

1. Create a Pinecone index named `udcpr-rag-index`
2. Use dimensions: `1024`
3. Use metric: `cosine`

### OpenAI Models Used

- **Embeddings**: `text-embedding-3-small`
- **Chat**: `gpt-4o`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- 📖 Check the [Deployment Guide](DEPLOYMENT_GUIDE.md) for detailed instructions
- 🐛 Report issues on [GitHub Issues](https://github.com/yourusername/udcpr-rag-chatbot/issues)
- 💬 For questions about UDCPR regulations, use the chatbot!

## 🙏 Acknowledgments

- Maharashtra State Government for UDCPR documentation
- OpenAI for GPT-4 and embedding models
- Pinecone for vector database services
- FastAPI for the excellent web framework

---

**Made with ❤️ for better urban planning and development in Maharashtra**