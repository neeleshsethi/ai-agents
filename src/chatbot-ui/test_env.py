#!/usr/bin/env python3
"""
Test script to verify environment configuration for Streamlit app
"""
import os
import sys

def test_environment():
    """Test that all required environment variables and directories are set up correctly"""
    
    print("Testing environment configuration...")
    
    # Check environment variables
    env_vars = [
        'STREAMLIT_SERVER_HEADLESS',
        'STREAMLIT_SERVER_FILE_WATCHER_TYPE',
        'STREAMLIT_CONFIG_DIR',
        'STREAMLIT_DATA_DIR',
        'STREAMLIT_CACHE_DIR',
        'HOME'
    ]
    
    for var in env_vars:
        value = os.environ.get(var)
        print(f"{var}: {value}")
    
    # Check if directories exist and are writable
    directories = [
        os.environ.get('STREAMLIT_CONFIG_DIR', '/home/app/.streamlit'),
        os.environ.get('STREAMLIT_DATA_DIR', '/home/app/.streamlit/data'),
        os.environ.get('STREAMLIT_CACHE_DIR', '/home/app/.streamlit/cache'),
        os.environ.get('HOME', '/home/app')
    ]
    
    for directory in directories:
        if directory:
            exists = os.path.exists(directory)
            writable = os.access(directory, os.W_OK) if exists else False
            print(f"Directory {directory}: exists={exists}, writable={writable}")
    
    # Test Python path
    print(f"Python path: {sys.path}")
    
    # Test if we can import required modules
    try:
        import streamlit
        print(f"Streamlit version: {streamlit.__version__}")
    except ImportError as e:
        print(f"Failed to import streamlit: {e}")
    
    # Test config import - this may fail during build if .env is not present
    try:
        from core.config import config
        print("Successfully imported config")
        # Check if API keys are present (optional during build)
        api_keys = ['OPENAI_API_KEY', 'GROQ_API_KEY', 'GOOGLE_API_KEY', 'COMET_API_KEY']
        for key in api_keys:
            value = getattr(config, key, None)
            if value:
                print(f"{key}: {'*' * (len(value) - 4) + value[-4:] if len(value) > 4 else '***'}")
            else:
                print(f"{key}: Not set (this is OK during build)")
    except ImportError as e:
        print(f"Failed to import config: {e}")
    except Exception as e:
        print(f"Config import succeeded but validation failed: {e}")
        print("This is expected during build when .env file is not present")
    
    print("Environment test completed.")

if __name__ == "__main__":
    test_environment() 