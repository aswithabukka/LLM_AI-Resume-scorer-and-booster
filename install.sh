#!/bin/bash
# ATS-Tailor Installation Script

set -e

echo "🚀 Installing ATS-Tailor..."
echo ""

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1

# Install dependencies
echo "📥 Installing dependencies (this may take a few minutes)..."
pip install -r requirements.txt

# Download spaCy model
echo "📚 Downloading spaCy language model..."
python -m spacy download en_core_web_lg

echo ""
echo "✅ Installation complete!"
echo ""
echo "Next steps:"
echo "1. Install Ollama from https://ollama.ai"
echo "2. Run: ollama pull llama3.1:8b"
echo "3. Start the app: streamlit run ui/app.py"
echo ""
echo "Or run the example: python examples/example_usage.py"
echo ""
