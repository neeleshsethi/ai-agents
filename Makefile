run-fastapi:
	uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

run-streamlit:
	streamlit run src/chatbot-ui/streamlit_app.py

run-all:
	@echo "Starting FastAPI backend and Streamlit frontend..."
	@echo "Note: You may want to run these in separate terminals instead."
	@make run-fastapi & make run-streamlit

build-docker-streamlit:
	docker build -f Dockerfile.streamlit -t streamlit-app:latest .

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
	@echo "Ensuring Colima is running..."
	@colima status >/dev/null 2>&1 || (colima start && sleep 10)
	@echo "Waiting for Docker daemon to be ready..."
	@until docker ps >/dev/null 2>&1; do echo "Waiting for Docker..."; sleep 2; done
	@echo "Stopping any existing containers on ports 8000 and 8501..."
	@lsof -ti:8000 | xargs kill -9 2>/dev/null || true
	@lsof -ti:8501 | xargs kill -9 2>/dev/null || true
	@docker compose down 2>/dev/null || true
	@echo "Starting Docker Compose services..."
	docker compose up --build


	
