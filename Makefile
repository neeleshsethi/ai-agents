run-streamlit:
	streamlit run src/chatbot-ui/streamlit_app.py

build-docker-streamlit:
	docker build -t streamlit-app:latest .

run-docker-streamlit:
	@echo "Checking if port 8501 is in use..."
	@lsof -ti:8501 | xargs kill -9 2>/dev/null || true
	@echo "Starting docker container on port 8501..."
	docker run -v ${PWD}/.env:/app/.env -p 8501:8501 streamlit-app:latest

test-docker-env:
	@echo "Testing Docker environment with .env file..."
	docker run --rm -v ${PWD}/.env:/app/.env streamlit-app:latest python src/chatbot-ui/test_env.py

test-build-env:
	@echo "Testing Docker build environment (without .env file)..."
	docker run --rm streamlit-app:latest python src/chatbot-ui/test_env.py

clean-docker:
	@echo "Cleaning up Docker containers and images..."
	docker stop $$(docker ps -q --filter ancestor=streamlit-app:latest) 2>/dev/null || true
	docker rm $$(docker ps -aq --filter ancestor=streamlit-app:latest) 2>/dev/null || true
	docker rmi streamlit-app:latest 2>/dev/null || true

debug-docker:
	@echo "Running Docker container in debug mode..."
	docker run -it --rm -v ${PWD}/.env:/app/.env -p 8501:8501 streamlit-app:latest /bin/bash

clean-test-files:
	@echo "Cleaning up test files..."
	rm -f src/chatbot-ui/test_env.py

run-docker-compose:
	docker compose up --build


	
