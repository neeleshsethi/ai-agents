import streamlit as st
import os
from openai import OpenAI
from google import genai
from google.genai import types

from groq import Groq
from core.config import config
from qdrant_client import QdrantClient
from retrieval import rag_pipeline

# Set environment variables to prevent permission errors
os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
os.environ['STREAMLIT_SERVER_FILE_WATCHER_TYPE'] = 'none'

qdrant_client = QdrantClient(
    url=config.QDRANT_URL, 
    api_key=config.QDRANT_API_KEY,
    check_compatibility=False
)

# Debug: List available collections
try:
    collections = qdrant_client.get_collections()
    print(f"Available collections: {[c.name for c in collections.collections]}")
    print(f"Configured collection name: {config.QDRANT_COLLECTION_NAME}")
except Exception as e:
    print(f"Error listing collections: {e}")




## Lets create sidebar
with st.sidebar:
    st.title("Settings")
    
    provider = st.selectbox("Provider", ['OpenAI', 'Groq', "Google"])
    if provider == "OpenAI":
        model_name = st.selectbox("Model", ["gpt-4o-mini", "gpt-4o"])
    elif provider == "Groq":
        model_name = st.selectbox("Model", ["llama-3.3-70b-versatile"])
    else:
        model_name = st.selectbox("Model", ["gemini-2.0-flash"])

    # Temperature configuration
    st.subheader("Response Configuration")
    temperature = st.slider(
        "Temperature", 
        min_value=0.0, 
        max_value=2.0, 
        value=0.7, 
        step=0.1,
        help="Controls randomness in responses. Lower values are more deterministic, higher values are more creative."
    )
    
    # Max tokens configuration
    max_tokens = st.slider(
        "Max Tokens", 
        min_value=100, 
        max_value=4000, 
        value=500, 
        step=100,
        help="Maximum number of tokens in the response. Higher values allow longer responses."
    )

    st.session_state.provider = provider
    st.session_state.model_name = model_name
    st.session_state.temperature = temperature
    st.session_state.max_tokens = max_tokens

# Check if API keys are configured
def check_api_key(provider):
    if provider == "OpenAI" and not config.OPENAI_API_KEY:
        return False, "OpenAI API key not configured. Please set OPENAI_API_KEY in your .env file."
    elif provider == "Groq" and not config.GROQ_API_KEY:
        return False, "Groq API key not configured. Please set GROQ_API_KEY in your .env file."
    elif provider == "Google" and not config.GOOGLE_API_KEY:
        return False, "Google API key not configured. Please set GOOGLE_API_KEY in your .env file."
    return True, ""

# Initialize clients based on provider
client = None
api_key_valid, error_message = check_api_key(st.session_state.provider)

if api_key_valid:
    try:
        if st.session_state.provider == "OpenAI":
            client = OpenAI(api_key=config.OPENAI_API_KEY)
        elif st.session_state.provider == "Groq":
            client = Groq(api_key=config.GROQ_API_KEY)
        else:
            # Initialize Google AI
            client = genai.Client(api_key=config.GOOGLE_API_KEY)
            
    except Exception as e:
        st.error(f"Failed to initialize {st.session_state.provider} client: {str(e)}")
        client = None
else:
    st.error(error_message)

def run_rag_pipeline(prompt, qdrant_client):
    output = rag_pipeline(prompt, qdrant_client)
    return output['answer']


def run_llm(client, messages, temperature=0.7, max_tokens=500):
    if not client:
        return "Client not initialized. Please check your API key configuration."
    
    if st.session_state.provider == "Google":
        # Convert messages to the format expected by Google GenAI
        # Google GenAI expects a single string or a list of strings
        conversation = ""
        for message in messages:
            if message['role'] == 'user':
                conversation += f"User: {message['content']}\n"
            elif message['role'] == 'assistant':
                conversation += f"Assistant: {message['content']}\n"
        
        response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[conversation],
                config=types.GenerateContentConfig(
                max_output_tokens=max_tokens,
                temperature=temperature,
            ),
        )

        return response.text
    else:
        return client.chat.completions.create(
            model = st.session_state.model_name,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        ).choices[0].message.content
    
    


if 'messages' not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hi How can i assist you ?" }]

for message in st.session_state.messages:
    with st.chat_message(message['role']):
        st.markdown(message['content'])

if prompt := st.chat_input("Hello how can i assist you today"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response = None
        try:
        
            response = run_rag_pipeline(prompt, qdrant_client)
            st.write(response)
            print(response)
        except Exception as ex:
            error_message = f"Error occurred: {str(ex)}"
            st.error(error_message)
            response = error_message

    # Ensure response is always defined before appending to session state
    if response is not None:
        st.session_state.messages.append({'role': 'assistant', "content": response})


