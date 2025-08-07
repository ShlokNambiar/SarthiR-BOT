# UDCPR RAG API Deployment Guide

This guide will help you deploy the UDCPR RAG chatbot API to Render.

## Prerequisites

1. **API Keys Required:**
   - OpenAI API Key (from https://platform.openai.com/api-keys)
   - Pinecone API Key (from https://app.pinecone.io/)

2. **Pinecone Index Setup:**
   - You need a Pinecone index named `udcpr-rag-index`
   - The index should already be populated with UDCPR document embeddings
   - If not populated, run the pipeline first: `python main.py --pdf "rag context files/UDCPR Updated 30.01.25 with earlier provisions & corrections.pdf"`

## Deployment Steps

### 1. Prepare Your Repository

Make sure your repository contains:
- `api_server.py` (FastAPI server)
- `requirements.txt` (with FastAPI dependencies)
- `render.yaml` (deployment configuration)
- All the RAG pipeline files

### 2. Deploy to Render

1. **Create Render Account:**
   - Go to https://render.com and sign up
   - Connect your GitHub account

2. **Create New Web Service:**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Choose the repository containing this code

3. **Configure Deployment:**
   - **Name:** `udcpr-rag-api` (or your preferred name)
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python api_server.py`

4. **Set Environment Variables:**
   In the Render dashboard, add these environment variables:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   PINECONE_API_KEY=your_pinecone_api_key_here
   ```

5. **Deploy:**
   - Click "Create Web Service"
   - Wait for deployment to complete (usually 5-10 minutes)

### 3. Test Your Deployment

1. **Get Your API URL:**
   - After deployment, you'll get a URL like: `https://your-app-name.onrender.com`

2. **Test Health Endpoint:**
   ```bash
   curl https://your-app-name.onrender.com/health
   ```

3. **Test Chat Endpoint:**
   ```bash
   curl -X POST https://your-app-name.onrender.com/chat \
     -H "Content-Type: application/json" \
     -d '{"message": "What are the building height regulations?"}'
   ```

## API Endpoints

### Health Check
```
GET /health
```
Returns the health status of the API.

### Chat
```
POST /chat
```
**Request Body:**
```json
{
  "message": "Your question about UDCPR",
  "session_id": "optional-session-id",
  "chat_history": []
}
```

**Response:**
```json
{
  "response": "AI response",
  "session_id": "session-id",
  "sources": [
    {
      "source": "document-name",
      "page": "page-number",
      "score": 0.85
    }
  ]
}
```

### Clear Session
```
DELETE /chat/{session_id}
```
Clears a specific chat session.

### List Sessions
```
GET /sessions
```
Lists all active sessions (for debugging).

## Integration with Your Website

1. **Update the HTML Example:**
   - Open `chatbot_integration_example.html`
   - Replace `API_BASE_URL` with your deployed Render URL
   - Customize the styling to match your website

2. **Add to Your Website:**
   - Copy the chatbot HTML/CSS/JavaScript code
   - Integrate it into your website's template
   - Make sure to update the API URL

## Example Integration Code

```javascript
const API_BASE_URL = 'https://your-app-name.onrender.com';

async function sendMessage(message) {
    const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            message: message,
            session_id: sessionId
        })
    });
    
    const data = await response.json();
    return data.response;
}
```

## Troubleshooting

### Common Issues:

1. **API Keys Not Working:**
   - Verify your OpenAI and Pinecone API keys are correct
   - Check that environment variables are set in Render dashboard

2. **Pinecone Index Not Found:**
   - Make sure your Pinecone index is named `udcpr-rag-index`
   - Verify the index contains embeddings data

3. **Deployment Fails:**
   - Check the build logs in Render dashboard
   - Ensure all dependencies are in requirements.txt

4. **CORS Issues:**
   - The API is configured to allow all origins
   - If you need to restrict origins, update the CORS middleware in `api_server.py`

### Performance Optimization:

1. **Cold Starts:**
   - Render free tier has cold starts
   - Consider upgrading to paid tier for better performance

2. **Response Time:**
   - First request may be slower due to model loading
   - Subsequent requests should be faster

## Security Considerations

1. **API Keys:**
   - Never commit API keys to your repository
   - Use Render's environment variables feature

2. **Rate Limiting:**
   - Consider adding rate limiting for production use
   - Monitor your OpenAI API usage

3. **CORS:**
   - In production, restrict CORS to your specific domain
   - Update the `allow_origins` in `api_server.py`

## Monitoring

1. **Render Dashboard:**
   - Monitor deployment status
   - Check logs for errors
   - View metrics and usage

2. **API Monitoring:**
   - Use the `/health` endpoint for health checks
   - Monitor response times and error rates

## Support

If you encounter issues:
1. Check the Render deployment logs
2. Test the API endpoints manually
3. Verify your environment variables are set correctly
4. Ensure your Pinecone index is properly configured