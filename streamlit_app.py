"""
Streamlit entry point for UDCPR RAG Chatbot

This file serves as the entry point for Streamlit Cloud deployment.
It simply imports the standalone app to avoid any set_page_config conflicts.
"""

# Import the standalone app
# This will run the entire app defined in udcpr_chatbot_streamlit.py
import udcpr_chatbot_streamlit

# The app will run automatically when imported
