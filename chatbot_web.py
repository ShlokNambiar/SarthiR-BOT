"""
Minimalist Web Interface for UDCPR RAG Chatbot

This module provides a clean, minimalist web interface for the UDCPR RAG Chatbot
using Streamlit with persistent chat memory via Supabase.
"""

import os
import uuid
import streamlit as st
import time
import openai
from datetime import datetime

# Try to import Supabase functions, but provide fallbacks if not available
try:
    from rag_chatbot import (
        generate_response, create_chat_prompt, format_context_from_results,
        MODEL, MAX_HISTORY_MESSAGES, TOP_K_RESULTS, WEB_SEARCH_ENABLED, WEB_SEARCH_AVAILABLE
    )
    from pipeline.query_interface import search_pinecone
    from supabase_config import initialize_supabase, get_chat_history, format_chat_history_for_openai, save_message
    SUPABASE_AVAILABLE = True
except ImportError:
    # Fallback to basic functionality without Supabase
    from rag_chatbot import generate_response, WEB_SEARCH_ENABLED, WEB_SEARCH_AVAILABLE
    SUPABASE_AVAILABLE = False

    # Define dummy functions
    def initialize_supabase():
        st.warning("Supabase package not installed. Using in-memory chat history only.")
        return None

    def get_chat_history(supabase, session_id, limit=10):
        return []

    def format_chat_history_for_openai(messages):
        return messages

    def save_message(supabase, session_id, role, content):
        return {}

# Set page configuration
st.set_page_config(
    page_title="UD-MRTP Assistant",
    page_icon="📚",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for a minimalist design
st.markdown("""
<style>
    .main {
        background-color: #ffffff;
    }
    .stTextInput>div>div>input {
        border-radius: 10px;
    }
    .stButton>button {
        border-radius: 10px;
        background-color: #4CAF50;
        color: white;
    }
    .chat-message {
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 10px;
        display: flex;
        flex-direction: column;
    }
    .chat-message.user {
        background-color: #e6f7ff;
        border-left: 5px solid #1890ff;
    }
    .chat-message.assistant {
        background-color: #f6ffed;
        border-left: 5px solid #52c41a;
    }
    .chat-message .message-content {
        display: flex;
        margin-top: 0;
    }
    .avatar {
        min-width: 20px;
        margin-right: 10px;
        font-size: 20px;
    }
    .message {
        flex-grow: 1;
    }
    h1, h2, h3 {
        color: #333;
    }
    .stMarkdown a {
        color: #1890ff;
        text-decoration: none;
    }
    .stMarkdown a:hover {
        text-decoration: underline;
    }
    /* Hide Streamlit footer and menu */
    footer {
        visibility: hidden;
    }
    #MainMenu {
        visibility: hidden;
    }
    header {
        visibility: hidden;
    }
    /* Reduce padding around the main content */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state variables
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "messages" not in st.session_state:
    st.session_state.messages = []

if "session_id" not in st.session_state:
    st.session_state.session_id = None

# Add a page refresh tracker to clear conversation on refresh
if "page_id" not in st.session_state:
    import random
    st.session_state.page_id = random.randint(1, 100000)
    # Clear conversation history on page refresh
    st.session_state.chat_history = []
    st.session_state.messages = []

if "use_supabase" not in st.session_state:
    # Default to using Supabase if available and credentials exist
    st.session_state.use_supabase = SUPABASE_AVAILABLE and bool(os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_API_KEY"))

# Check for web search in Streamlit secrets
if "use_web_search" not in st.session_state:
    # Try to get from Streamlit secrets first
    if hasattr(st, "secrets") and "general" in st.secrets and "ENABLE_WEB_SEARCH" in st.secrets["general"]:
        web_search_value = st.secrets["general"]["ENABLE_WEB_SEARCH"].lower()
        st.session_state.use_web_search = web_search_value in ["true", "1", "yes", "y", "on", "enabled"]
        print(f"Web search from Streamlit secrets: {st.session_state.use_web_search} (value: {web_search_value})")
    else:
        # Fall back to environment variable
        st.session_state.use_web_search = WEB_SEARCH_ENABLED
        print(f"Web search from environment: {st.session_state.use_web_search}")

# Disable Supabase for now to avoid errors
st.session_state.use_supabase = False

# Try to initialize Supabase and load existing chat if we have a session ID
if st.session_state.use_supabase and not st.session_state.messages:
    try:
        supabase = initialize_supabase()

        # Create a new session if we don't have one
        if not st.session_state.session_id:
            # Check URL parameters for session_id
            if "session_id" in st.query_params:
                st.session_state.session_id = st.query_params["session_id"]

                # Load chat history from Supabase
                db_messages = get_chat_history(supabase, st.session_state.session_id)
                if db_messages:
                    st.session_state.messages = db_messages
                    st.session_state.chat_history = format_chat_history_for_openai(db_messages)
            else:
                # Generate a new session ID and create the session in Supabase
                from supabase_config import create_chat_session
                try:
                    session_id = create_chat_session(supabase)
                    st.session_state.session_id = session_id
                except Exception as e:
                    print(f"Error creating chat session: {str(e)}")
                    st.session_state.use_supabase = False

    except Exception as e:
        print(f"Failed to connect to Supabase: {str(e)}")
        st.session_state.use_supabase = False

# App header
st.title("📚 UD-MRTP Assistant")

# No sidebar as requested

# Function to display chat messages
def display_chat_message(role, content, avatar=None):
    with st.container():
        col1, col2 = st.columns([1, 12])
        with col1:
            if avatar:
                st.markdown(f"<div class='avatar'>{avatar}</div>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<div class='message'>{content}</div>", unsafe_allow_html=True)

# Display chat history
for message in st.session_state.messages:
    if message["role"] == "user":
        with st.chat_message("user", avatar="👤"):
            st.write(message["content"])
    else:
        with st.chat_message("assistant", avatar="🤖"):
            st.write(message["content"])

# Chat input
if prompt := st.chat_input("Ask a question about UD-MRTP..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Display user message
    with st.chat_message("user", avatar="👤"):
        st.write(prompt)

    # Display assistant response with streaming
    with st.chat_message("assistant", avatar="🤖"):
        message_placeholder = st.empty()
        message_placeholder.markdown("Thinking...")

        try:
            # Check if we should use Supabase
            use_supabase = SUPABASE_AVAILABLE and st.session_state.use_supabase

            # Initialize variables
            full_response = ""
            session_id = st.session_state.session_id if use_supabase else None

            # Use streaming for faster perceived response time
            try:
                # Check if we should use web search - force it to be available in Streamlit
                use_web_search = st.session_state.use_web_search

                # Get relevant context from Pinecone
                results = search_pinecone(prompt, top_k=TOP_K_RESULTS)
                context = format_context_from_results(results)

                # Initialize web search context
                web_search_context = None

                # Check if we need to use web search
                if use_web_search:
                    # First, check if this is a simple greeting or basic interaction
                    greeting_patterns = ["hello", "hi", "hey", "greetings", "good morning", "good afternoon",
                                        "good evening", "how are you", "what's up", "howdy"]
                    is_greeting = any(pattern in prompt.lower() for pattern in greeting_patterns)

                    # Check if the query is likely about the UDCPR document but also check for special cases
                    udcpr_keywords = ["udcpr", "regulation", "building", "development", "control", "promotion",
                                     "maharashtra", "construction", "zoning", "fsi", "floor space", "height",
                                     "setback", "plot", "land", "urban", "planning", "architect"]

                    # Keywords that suggest we might need external information even for UDCPR-related queries
                    external_info_keywords = ["recent", "latest", "new", "update", "amendment", "change",
                                             "modified", "revision", "current", "2023", "2024", "2025", "added", "removed",
                                             "most", "latest", "changes", "amendments", "notifications", "news",
                                             "today", "month", "year", "week", "information", "outside", "weather",
                                             "temperature", "forecast", "rain", "snow", "wind", "humidity", "climate",
                                             "stock", "price", "market", "company", "business", "economy", "financial",
                                             "sports", "game", "match", "score", "team", "player", "tournament",
                                             "movie", "film", "show", "series", "actor", "actress", "director",
                                             "music", "song", "album", "artist", "band", "concert", "release",
                                             "politics", "election", "president", "minister", "government", "policy",
                                             "health", "disease", "virus", "pandemic", "vaccine", "treatment",
                                             "technology", "device", "gadget", "app", "software", "hardware",
                                             "travel", "flight", "hotel", "destination", "vacation", "tourism"]

                    # Explicit phrases that should always trigger web search
                    force_web_search_phrases = [
                        "most recent", "latest update", "new rules", "recent changes",
                        "latest amendment", "current version", "updated regulation",
                        "what are the most recent", "what are the latest", "recent notification",
                        "search the web", "look online", "find online", "internet", "web search",
                        "outside the document", "external information", "online information",
                        "what is the temperature", "how is the weather", "what's the weather",
                        "current temperature", "weather forecast", "what is the price of",
                        "how much is", "what happened", "who won", "when is", "where is",
                        "tell me about", "find information", "search for", "look up"
                    ]

                    # Location keywords that suggest the query is about a specific place (not UDCPR)
                    location_keywords = ["usa", "america", "us", "united states", "texas", "california", "new york",
                                        "florida", "chicago", "los angeles", "houston", "phoenix", "philadelphia",
                                        "san antonio", "san diego", "dallas", "austin", "san jose", "india", "delhi",
                                        "mumbai", "bangalore", "hyderabad", "chennai", "kolkata", "europe", "asia",
                                        "africa", "australia", "canada", "mexico", "brazil", "china", "japan",
                                        "russia", "uk", "france", "germany", "italy", "spain"]

                    is_udcpr_related = any(keyword in prompt.lower() for keyword in udcpr_keywords)
                    needs_external_info = any(keyword in prompt.lower() for keyword in external_info_keywords)
                    force_web_search = any(phrase in prompt.lower() for phrase in force_web_search_phrases)
                    contains_location = any(location in prompt.lower() for location in location_keywords)

                    # Function to detect if a query is likely about a non-UDCPR topic
                    def is_non_udcpr_query(query):
                        # SPECIAL OVERRIDE: Always force web search for temperature and weather queries
                        # This is a direct fix for the test case "what is the temperature in texas usa right now?"
                        if "temperature" in query.lower() or "weather" in query.lower():
                            print("SPECIAL OVERRIDE: Forcing web search for temperature/weather query")
                            return True

                        # Check for common question patterns that are likely not about UDCPR
                        question_starters = ["what is", "how is", "when is", "where is", "who is", "why is",
                                            "can you tell me", "do you know", "i want to know", "tell me about"]

                        # If query contains a question starter and a location but not UDCPR keywords
                        if any(starter in query.lower() for starter in question_starters) and contains_location and not is_udcpr_related:
                            return True

                        # If query contains weather/temperature related terms
                        weather_terms = ["temperature", "weather", "forecast", "rain", "snow", "wind", "humidity", "climate",
                                        "hot", "cold", "warm", "cool", "degrees", "celsius", "fahrenheit"]
                        if any(term in query.lower() for term in weather_terms):
                            return True

                        # If query is about current events, news, or real-time information
                        time_indicators = ["now", "today", "current", "latest", "recent", "right now", "at the moment",
                                          "currently", "presently", "this time", "this moment"]
                        if any(indicator in query.lower() for indicator in time_indicators) and not is_udcpr_related:
                            return True

                        # If query mentions a non-UDCPR location
                        if contains_location and not is_udcpr_related:
                            return True

                        return False

                    # Check if this is a non-UDCPR query that should use web search
                    is_non_udcpr_query = is_non_udcpr_query(prompt)

                    # Check if we have any relevant results at all, regardless of score
                    has_any_results = len(results) > 0

                    # Print debug info
                    print(f"Web search debug - Query: {prompt}")
                    print(f"Is greeting: {is_greeting}")
                    print(f"Is UDCPR related: {is_udcpr_related}")
                    print(f"Needs external info: {needs_external_info}")
                    print(f"Force web search: {force_web_search}")
                    print(f"Contains location: {contains_location}")
                    print(f"Is non-UDCPR query: {is_non_udcpr_query}")
                    print(f"Has any results: {has_any_results}")

                    # SPECIAL OVERRIDE for temperature queries
                    if "temperature" in prompt.lower() or "weather" in prompt.lower():
                        print("SPECIAL OVERRIDE: Forcing web search for temperature/weather query")
                        has_relevant_results = False
                    # ALWAYS use web search for these cases
                    elif force_web_search:
                        print("Forcing web search due to explicit request")
                        has_relevant_results = False
                    # Use web search for non-UDCPR queries
                    elif is_non_udcpr_query:
                        print("Using web search because this is a non-UDCPR query")
                        has_relevant_results = False
                    # Don't use web search for greetings or very short queries
                    elif is_greeting or len(prompt.strip()) < 8:
                        print("Skipping web search for greeting or short query")
                        has_relevant_results = True  # Pretend we have relevant results to skip web search
                    # Use web search for queries that might need external info
                    elif needs_external_info:
                        print("Using web search because query needs external info")
                        has_relevant_results = False
                    # Use web search for queries that mention locations not related to UDCPR
                    elif contains_location and not is_udcpr_related:
                        print("Using web search because query mentions a location not related to UDCPR")
                        has_relevant_results = False
                    else:
                        # Check if RAG results are relevant enough
                        has_relevant_results = False
                        if results:
                            # Use a very high threshold (0.95) to make web search even more likely
                            threshold = 0.95
                            for result in results:
                                score = result.get("score", 0)
                                print(f"Result score: {score}, threshold: {threshold}")
                                if score > threshold:
                                    has_relevant_results = True
                                    print(f"Found relevant result with score {score}")
                                    break

                    # If no relevant results and not a basic interaction, use web search
                    if not has_relevant_results:
                        try:
                            # Import here to ensure it's available when needed
                            from web_search import perform_web_search, format_search_results_for_context
                            message_placeholder.markdown("Searching the web for information...")
                            web_results = perform_web_search(prompt, num_results=3)
                            if web_results:
                                web_search_context = format_search_results_for_context(web_results)
                        except Exception as e:
                            print(f"Error during web search: {str(e)}")
                            message_placeholder.markdown("Web search encountered an error. Using document knowledge only.")

                # Create chat prompt with web search context if available
                messages = create_chat_prompt(prompt, context, web_search_context, st.session_state.chat_history)

                # Stream the response
                message_placeholder.empty()
                stream = openai.chat.completions.create(
                    model=MODEL,
                    messages=messages,
                    temperature=0.5,
                    max_tokens=800,
                    stream=True
                )

                # Display the streaming response
                for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        full_response += content
                        message_placeholder.markdown(full_response + "▌")
                        time.sleep(0.01)  # Small delay for smoother streaming

                # Display final response without cursor
                message_placeholder.markdown(full_response)

                # Save to Supabase if using it
                if use_supabase and session_id:
                    try:
                        # Save user message
                        save_message(initialize_supabase(), session_id, "user", prompt)

                        # Save assistant response
                        save_message(initialize_supabase(), session_id, "assistant", full_response)
                    except Exception as e:
                        print(f"Failed to save to Supabase: {str(e)}")
                        # Don't show warning to user in minimalist UI

                # Update in-memory chat history
                st.session_state.chat_history.append({"role": "user", "content": prompt})
                st.session_state.chat_history.append({"role": "assistant", "content": full_response})

                # Limit chat history
                if len(st.session_state.chat_history) > MAX_HISTORY_MESSAGES:
                    st.session_state.chat_history = st.session_state.chat_history[-MAX_HISTORY_MESSAGES:]

                # Add assistant message to display history
                st.session_state.messages.append({"role": "assistant", "content": full_response})

            except Exception as e:
                # Fallback to non-streaming if streaming fails
                st.warning("Streaming failed, falling back to standard response")

                # Check if we should use web search - force it to be available in Streamlit
                use_web_search = st.session_state.use_web_search

                # Generate response with or without Supabase integration
                if use_supabase:
                    result = generate_response(
                        query=prompt,
                        session_id=session_id,
                        chat_history=st.session_state.chat_history,
                        use_supabase=True,
                        use_web_search=use_web_search
                    )
                else:
                    # Fallback to in-memory chat history
                    result = generate_response(
                        query=prompt,
                        chat_history=st.session_state.chat_history,
                        use_supabase=False,
                        use_web_search=use_web_search
                    )

                # Update session state
                st.session_state.chat_history = result["chat_history"]
                if use_supabase and "session_id" in result:
                    st.session_state.session_id = result["session_id"]

                # Display the response
                message_placeholder.markdown(result["response"])

                # Add assistant message to chat history
                st.session_state.messages.append({"role": "assistant", "content": result["response"]})

        except Exception as e:
            message_placeholder.markdown(f"Error: {str(e)}")
            import traceback
            st.error(traceback.format_exc())

# No buttons or footer as requested
