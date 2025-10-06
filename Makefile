.PHONY: install run-ui run-api run-example test clean help

help:
	@echo "ATS-Tailor - Makefile Commands"
	@echo ""
	@echo "  make install      - Install dependencies"
	@echo "  make run-ui       - Start Streamlit UI"
	@echo "  make run-api      - Start FastAPI server"
	@echo "  make run-example  - Run example script"
	@echo "  make test         - Run tests"
	@echo "  make clean        - Clean temporary files"
	@echo ""

install:
	@echo "Installing ATS-Tailor..."
	chmod +x install.sh
	./install.sh

run-ui:
	@echo "Starting Streamlit UI..."
	streamlit run ui/app.py

run-api:
	@echo "Starting FastAPI server..."
	uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

run-example:
	@echo "Running example..."
	python examples/example_usage.py

test:
	@echo "Running tests..."
	pytest tests/ -v

clean:
	@echo "Cleaning temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache
	rm -rf dist build
	@echo "✓ Clean complete"

format:
	@echo "Formatting code..."
	black src/ ui/ examples/
	@echo "✓ Format complete"

lint:
	@echo "Linting code..."
	flake8 src/ ui/ examples/ --max-line-length=120
	@echo "✓ Lint complete"
