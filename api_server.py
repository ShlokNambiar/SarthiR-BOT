"""
FastAPI Server for UDCPR RAG Chatbot

This server provides REST API endpoints for the UDCPR chatbot
that can be integrated into any website as a floating chatbot.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
import openai
import pinecone
from dotenv import load_dotenv
import traceback
import uuid
from datetime import datetime

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="UDCPR RAG Chatbot API",
    description="API for UDCPR (Unified Development Control and Promotion Regulations) chatbot",
    version="1.0.0"
)

# Add CORS middleware to allow requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your website domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
INDEX_NAME = "udcpr-rag-index"
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1024
MODEL = "gpt-4o"
MAX_HISTORY_MESSAGES = 10
TOP_K_RESULTS = 5

# Global variables for initialized services
pc = None
index = None
openai_client = None

# Pydantic models for request/response
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    chat_history: Optional[List[ChatMessage]] = []

class ChatResponse(BaseModel):
    response: str
    session_id: str
    sources: Optional[List[dict]] = []

class HealthResponse(BaseModel):
    status: str
    message: str

# In-memory session storage (in production, use Redis or database)
sessions = {}

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global pc, index, openai_client
    
    try:
        # Check for required environment variables
        openai_api_key = os.getenv("OPENAI_API_KEY")
        pinecone_api_key = os.getenv("PINECONE_API_KEY")
        
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        if not pinecone_api_key:
            raise ValueError("PINECONE_API_KEY environment variable is required")
        
        # Initialize OpenAI
        openai_client = openai.OpenAI(api_key=openai_api_key)
        
        # Initialize Pinecone
        pc = pinecone.Pinecone(api_key=pinecone_api_key)
        
        # Check if index exists
        index_list = [idx.name for idx in pc.list_indexes()]
        if INDEX_NAME not in index_list:
            raise ValueError(f"Pinecone index '{INDEX_NAME}' does not exist")
        
        # Connect to index
        index = pc.Index(INDEX_NAME)
        
        print("✅ Services initialized successfully")
        
    except Exception as e:
        print(f"❌ Failed to initialize services: {str(e)}")
        raise

def get_query_embedding(query: str):
    """Get embedding for a query string."""
    response = openai_client.embeddings.create(
        input=[query],
        model=EMBEDDING_MODEL,
        dimensions=EMBEDDING_DIMENSIONS
    )
    return response.data[0].embedding

def search_pinecone(query: str, top_k: int = 5):
    """Search Pinecone index with a query string."""
    query_embedding = get_query_embedding(query)
    
    search_response = index.query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True
    )
    
    return search_response["matches"]

def format_context_from_results(results):
    """Format search results into a context string for the LLM."""
    if not results:
        return "No relevant information found in the UDCPR document."
    
    context_parts = []
    sources = []
    
    for i, result in enumerate(results):
        score = result.get("score", 0)
        text = result.get("metadata", {}).get("text", "")
        source = result.get("metadata", {}).get("source", "Unknown")
        page = result.get("metadata", {}).get("page_num", "Unknown")
        
        if text and score > 0.3:  # Include more relevant results (lowered threshold)
            context_parts.append(f"[Source: {source}, Page: {page}]\n{text}\n")
            sources.append({
                "source": source,
                "page": page,
                "score": score
            })
    
    if not context_parts:
        return "No sufficiently relevant information found in the UDCPR document.", []
    
    return "\n".join(context_parts), sources

def create_chat_prompt(query: str, context: str, chat_history: List[ChatMessage] = None):
    """Create a chat prompt for the LLM."""
    messages = []
    
    # System message
    system_message = """You are UDCPR Saathi, an expert assistant for the Unified Development Control and Promotion Regulations (UDCPR) for Maharashtra State, India. You are knowledgeable, helpful, and confident in providing information about building regulations, zoning, FSI, and development control rules.

IMPORTANT GUIDELINES:
1. **Be Confident**: When the context contains relevant information, provide detailed answers confidently. Don't say "the document doesn't provide information" if there's relevant content.

2. **Use Available Information**: Extract and synthesize information from the provided context. Even if it's not perfectly complete, provide what you know and build upon it with standard urban planning knowledge.

3. **Structure Your Answers**: 
   - Start with a direct answer
   - Provide specific details from UDCPR
   - Use bullet points or numbered lists for clarity
   - Include relevant regulations, measurements, and requirements

4. **For Common Terms**: 
   - Green Zone: Areas for environmental conservation, parks, open spaces with restricted development
   - Building Height: Provide specific UDCPR height limits based on road width, zoning, and area type
   - FSI/FAR: Floor Space Index regulations as per UDCPR zones

5. **Be Helpful**: If the exact information isn't in the context but you can infer from related UDCPR content, provide a helpful response and suggest consulting local authorities for specific cases.

6. **Tone**: Professional, knowledgeable, and helpful. You're here to make UDCPR regulations accessible and understandable.

Remember: You're an expert who knows UDCPR well. Be confident in your responses when you have relevant information."""
    
    messages.append({"role": "system", "content": system_message})
    
    # Add chat history if available
    if chat_history:
        recent_history = chat_history[-MAX_HISTORY_MESSAGES:]
        for msg in recent_history:
            messages.append({"role": msg.role, "content": msg.content})
    
    # Add current query with context
    user_message = f"Question: {query}\n\nRelevant sections from the UDCPR document:\n{context}"
    messages.append({"role": "user", "content": user_message})
    
    return messages

@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint"""
    return HealthResponse(
        status="success",
        message="UDCPR RAG Chatbot API is running"
    )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        # Test OpenAI connection
        openai_client.models.list()
        
        # Test Pinecone connection
        index.describe_index_stats()
        
        return HealthResponse(
            status="healthy",
            message="All services are operational"
        )
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Service unhealthy: {str(e)}"
        )

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint"""
    try:
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Get or create session
        if session_id not in sessions:
            sessions[session_id] = {
                "history": [],
                "created_at": datetime.now()
            }
        
        # Search for relevant context
        results = search_pinecone(request.message, top_k=TOP_K_RESULTS)
        context, sources = format_context_from_results(results)
        
        # Create chat prompt
        chat_history = request.chat_history or sessions[session_id]["history"]
        messages = create_chat_prompt(request.message, context, chat_history)
        
        # Generate response
        response = openai_client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.5,
            max_tokens=800
        )
        
        assistant_response = response.choices[0].message.content
        
        # Update session history
        sessions[session_id]["history"].extend([
            ChatMessage(role="user", content=request.message),
            ChatMessage(role="assistant", content=assistant_response)
        ])
        
        # Limit history size
        if len(sessions[session_id]["history"]) > MAX_HISTORY_MESSAGES:
            sessions[session_id]["history"] = sessions[session_id]["history"][-MAX_HISTORY_MESSAGES:]
        
        return ChatResponse(
            response=assistant_response,
            session_id=session_id,
            sources=sources
        )
        
    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@app.delete("/chat/{session_id}")
async def clear_session(session_id: str):
    """Clear a chat session"""
    if session_id in sessions:
        del sessions[session_id]
        return {"message": f"Session {session_id} cleared"}
    else:
        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )

@app.get("/sessions")
async def list_sessions():
    """List all active sessions (for debugging)"""
    return {
        "sessions": list(sessions.keys()),
        "total": len(sessions)
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)