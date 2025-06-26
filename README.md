# AI Agents - Multi-Provider Chatbot

A Streamlit-based chatbot application that supports multiple AI providers including OpenAI, Groq, and Google AI.

## Features

- **Multi-Provider Support**: Switch between OpenAI, Groq, and Google AI
- **Configurable Parameters**: Adjust temperature and max tokens for responses
- **Real-time Chat Interface**: Interactive chat experience with message history
- **Docker Support**: Containerized deployment with proper security configurations

## Quick Start

### Prerequisites

- Docker installed on your system
- API keys for your chosen providers (OpenAI, Groq, Google AI)

### Environment Setup

Create a `.env` file in the root directory with your API keys:

```bash
OPENAI_API_KEY=your_openai_api_key_here
GROQ_API_KEY=your_groq_api_key_here
GOOGLE_API_KEY=your_google_api_key_here
COMET_API_KEY=your_comet_api_key_here
```

### Running with Docker

1. **Build the Docker image:**
   ```bash
   make build-docker-streamlit
   ```

2. **Run the application:**
   ```bash
   make run-docker-streamlit
   ```

3. **Access the application:**
   Open your browser and navigate to `http://localhost:8501`

### Running Locally

1. **Install dependencies:**
   ```bash
   uv sync
   ```

2. **Run the application:**
   ```bash
   make run-streamlit
   ```

## Available Models

### OpenAI
- GPT-4o Mini
- GPT-4o

### Groq
- Llama 3.3 70B Versatile

### Google AI
- Gemini 2.0 Flash

## Configuration

### Response Parameters

- **Temperature**: Controls randomness (0.0 = deterministic, 2.0 = very creative)
- **Max Tokens**: Maximum length of responses (100-4000 tokens)

### Docker Configuration

The application is configured to run securely in Docker with:
- Non-root user execution
- Proper directory permissions
- Environment variable isolation
- Optimized Python bytecode compilation

## Troubleshooting

### Permission Errors
If you encounter permission errors, the Docker configuration includes:
- Proper directory creation and permissions
- Environment variable configuration
- Non-root user execution

### API Key Issues
Ensure your `.env` file contains valid API keys for your chosen provider.

### Testing Environment
Run the environment test to verify configuration:
```bash
make test-docker-env
```

## Development

### Project Structure
```
ai-agents/
├── src/chatbot-ui/
│   ├── streamlit_app.py      # Main Streamlit application
│   ├── core/
│   │   └── config.py         # Configuration management
│   └── test_env.py           # Environment testing script
├── .streamlit/
│   └── config.toml           # Streamlit configuration
├── Dockerfile                # Docker configuration
├── Makefile                  # Build and run commands
└── pyproject.toml           # Python dependencies
```

### Recent Fixes

1. **Permission Errors**: Fixed Streamlit trying to write to `/nonexistent` by:
   - Setting proper environment variables for Streamlit directories
   - Creating necessary directories with correct permissions
   - Configuring non-root user execution

2. **NameError**: Fixed undefined `response` variable by:
   - Ensuring proper variable scope in error handling
   - Adding null checks before using the response variable

3. **Google AI Integration**: Fixed Google GenAI client initialization by:
   - Using correct import and client structure
   - Proper message formatting for Google AI API

## Makefile Commands

- `make build-docker-streamlit`: Build Docker image
- `make run-docker-streamlit`: Run the application
- `make test-docker-env`: Test environment configuration
- `make clean-docker`: Clean up Docker containers and images
- `make debug-docker`: Run container in debug mode
- `make clean-test-files`: Remove test files

## License

This project is licensed under the MIT License.