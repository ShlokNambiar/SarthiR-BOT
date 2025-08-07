"""
Chat Handler Module

This module provides the chat input functionality for the UDCPR RAG Chatbot.
It is imported by streamlit_app.py to handle chat interactions.
"""

import streamlit as st
import time
import openai
import os
from datetime import datetime

# Try to import necessary modules
try:
    from rag_chatbot import (
        generate_response, create_chat_prompt, format_context_from_results,
        MODEL, MAX_HISTORY_MESSAGES, TOP_K_RESULTS, WEB_SEARCH_ENABLED, WEB_SEARCH_AVAILABLE
    )
    from query_interface import search_pinecone
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

# Chat input function
def handle_chat_input():
    # Chat input
    if prompt := st.chat_input("Ask a question about UDCPR..."):
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
                    # Check if we should use web search
                    use_web_search = st.session_state.use_web_search and WEB_SEARCH_AVAILABLE

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
                                                 "modified", "revision", "current", "2023", "2024", "added", "removed",
                                                 "most", "latest", "changes", "amendments", "notifications"]

                        # Explicit phrases that should always trigger web search
                        force_web_search_phrases = [
                            "most recent", "latest update", "new rules", "recent changes",
                            "latest amendment", "current version", "updated regulation",
                            "what are the most recent", "what are the latest", "recent notification"
                        ]

                        is_udcpr_related = any(keyword in prompt.lower() for keyword in udcpr_keywords)
                        needs_external_info = any(keyword in prompt.lower() for keyword in external_info_keywords)
                        force_web_search = any(phrase in prompt.lower() for phrase in force_web_search_phrases)

                        # Check if we have any relevant results at all, regardless of score
                        has_any_results = len(results) > 0

                        # ALWAYS use web search for queries that explicitly ask for recent/latest information
                        if force_web_search:
                            has_relevant_results = False
                        # Don't use web search for greetings, very short queries, or standard UDCPR queries
                        elif is_greeting or len(prompt.strip()) < 10 or (is_udcpr_related and not needs_external_info and has_any_results):
                            has_relevant_results = True  # Pretend we have relevant results to skip web search
                        else:
                            # Check if RAG results are relevant enough
                            has_relevant_results = False
                            if results:
                                for result in results:
                                    if result.get("score", 0) > 0.75:  # Using threshold from rag_chatbot.py
                                        has_relevant_results = True
                                        break

                        # If no relevant results and not a basic interaction, use web search
                        if not has_relevant_results:
                            from web_search import perform_web_search, format_search_results_for_context
                            message_placeholder.markdown("Searching the web for information...")
                            web_results = perform_web_search(prompt, num_results=3)
                            if web_results:
                                web_search_context = format_search_results_for_context(web_results)

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
                            st.warning(f"Failed to save to Supabase: {str(e)}")

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

                    # Check if we should use web search
                    use_web_search = st.session_state.use_web_search and WEB_SEARCH_AVAILABLE

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

# Add buttons for conversation management
def add_conversation_buttons():
    col1, col2 = st.columns(2)

    # Clear conversation button
    if col1.button("Clear Conversation"):
        # Reset all conversation state
        st.session_state.chat_history = []
        st.session_state.messages = []

        # Create a new session if using Supabase
        if SUPABASE_AVAILABLE and st.session_state.use_supabase:
            try:
                from supabase_config import create_chat_session
                supabase = initialize_supabase()
                session_id = create_chat_session(supabase)
                st.session_state.session_id = session_id
            except Exception as e:
                st.warning(f"Failed to create new session: {str(e)}")
                st.session_state.use_supabase = False

        st.experimental_rerun()

    # New conversation button (keeps Supabase enabled but starts fresh)
    if SUPABASE_AVAILABLE and st.session_state.use_supabase and col2.button("New Conversation"):
        # Reset conversation but keep Supabase enabled
        st.session_state.chat_history = []
        st.session_state.messages = []

        # Create a new session
        try:
            from supabase_config import create_chat_session
            supabase = initialize_supabase()
            session_id = create_chat_session(supabase)
            st.session_state.session_id = session_id
        except Exception as e:
            st.warning(f"Failed to create new session: {str(e)}")
            st.session_state.use_supabase = False

        st.experimental_rerun()

# Add footer
def add_footer():
    footer_components = ["OpenAI GPT-4o", "Pinecone"]

    if SUPABASE_AVAILABLE and st.session_state.use_supabase:
        footer_components.append("Supabase")

    if WEB_SEARCH_AVAILABLE and st.session_state.use_web_search:
        footer_components.append("Web Search")

    footer_text = ", ".join(footer_components)
    st.markdown(f"""
    ---
    *Powered by {footer_text}*
    """)
