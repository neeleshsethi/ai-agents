import streamlit as st
import os
import sys
from pathlib import Path
import requests

# Add the parent directory to the Python path to enable imports
src_dir = Path(__file__).parent.parent
sys.path.insert(0, str(src_dir))

from openai import OpenAI
from google import genai
from google.genai import types

from groq import Groq
from core.config import config

# Set environment variables to prevent permission errors
os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
os.environ['STREAMLIT_SERVER_FILE_WATCHER_TYPE'] = 'none'

# FastAPI backend URL - configure this based on your setup
FASTAPI_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")

def run_rag_pipeline(prompt):
    """Call FastAPI RAG endpoint"""
    try:
        response = requests.post(
            f"{FASTAPI_URL}/rag/",
            json={"question": prompt, "top_k": 5},
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.ConnectionError:
        return {"answer": "Error: Cannot connect to FastAPI backend. Make sure it's running.", "retrieved_images": []}
    except requests.exceptions.Timeout:
        return {"answer": "Error: Request timed out. Please try again.", "retrieved_images": []}
    except Exception as e:
        return {"answer": f"Error: {str(e)}", "retrieved_images": []}

# Initialize session state variables
if 'messages' not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hi! How can I assist you?"}]

if 'retrieved_items' not in st.session_state:
    st.session_state.retrieved_items = []

# Page configuration
st.set_page_config(page_title="Product Assistant", layout="wide")
st.title("🛍️ Product Assistant Chatbot")

# Sidebar for product suggestions
with st.sidebar:
    st.markdown("### 📦 Product Suggestions")
    st.markdown("---")

    if st.session_state.retrieved_items:
        for idx, item in enumerate(st.session_state.retrieved_items):
            # Create a card-like display for each product
            with st.container():
                st.markdown(f"#### Product {idx + 1}")

                # Display product image
                if 'image_url' in item and item['image_url']:
                    st.image(item['image_url'], use_container_width=True)
                else:
                    st.info("🖼️ No image available")

                # Display product description
                description = item.get("description", "No description available")
                st.markdown(f"**Description:**")
                st.write(description)

                # Display product price
                price = item.get("price", "N/A")
                st.markdown(f"**💰 Price:** `${price} USD`")

                # Add a divider between products
                if idx < len(st.session_state.retrieved_items) - 1:
                    st.markdown("---")
    else:
        st.info("💡 Ask about products to see suggestions here!")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message['role']):
        st.markdown(message['content'])

# Chat input
if prompt := st.chat_input("Ask about products..."):
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get assistant response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = run_rag_pipeline(prompt)

            # Get response content
            response_content = response.get("answer", "Sorry, I couldn't process your request.")
            st.markdown(response_content)

            # Add assistant message to chat history
            st.session_state.messages.append({
                'role': 'assistant',
                "content": response_content
            })

            # Extract retrieved items for sidebar and trigger rerun to update sidebar
            st.session_state.retrieved_items = response.get("retrieved_images", [])

    # Force rerun to update sidebar with new retrieved items
    st.rerun()

# Optional: Add a button to clear chat history
with st.sidebar:
    st.markdown("---")
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = [{"role": "assistant", "content": "Hi! How can I assist you?"}]
        st.session_state.retrieved_items = []
        st.rerun()