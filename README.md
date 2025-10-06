# ATS-Tailor: Resume Optimization Assistant

**Tailor your resume to any job description in minutes with AI-powered suggestions.**

A privacy-first tool that analyzes your resume against job descriptions and provides actionable edits to maximize ATS compatibility.

---

## ✨ Features

- 📊 **ATS Scoring** - Get a 0-100 score with detailed breakdown
- 🎯 **Gap Detection** - Identifies missing skills and weak evidence
- ✍️ **AI Suggestions** - LLM-powered bullet rewrites (Ollama, OpenAI, Claude, Gemini)
- 🔒 **Privacy-First** - Runs 100% locally by default
- ⚡ **Fast** - Analysis in <10 seconds

---

## 🚀 Quick Start

### 1. Install
```bash
cd ats-tailor
./install.sh
```

### 2. Setup LLM (choose one)

**Option A: Ollama (Free, Local)**
```bash
brew install ollama
ollama pull llama3.1:8b
ollama serve
```

**Option B: OpenAI/Claude/Gemini**
- Get API key from provider
- Enter in UI when prompted

### 3. Run
```bash
streamlit run ui/app.py
```

Open http://localhost:8501

---

## 📖 Documentation

- **[SCORING_EXPLAINED.md](SCORING_EXPLAINED.md)** - How the ATS score is calculated

---

## 🎯 How It Works

1. **Upload** resume (PDF/DOCX) + paste job description
2. **Analyze** - Matches requirements to your experience
3. **Review** suggestions with exact locations
4. **Apply** edits to improve your score

---

## 🤖 Supported LLM Models

### Free & Local (Ollama)
- llama3.2:3b, llama3.1:8b, llama3.1:70b
- mistral, qwen2.5:7b, or any Ollama model

### Cloud-based (API key required)
- **OpenAI**: GPT-4o, GPT-4o-mini, o1-preview (~$0.002-0.02/resume)
- **Anthropic**: Claude 3.5 Sonnet, Claude 3 Opus, Claude 3 Haiku (~$0.001-0.075/resume)
- **Google**: Gemini 2.0 Flash, Gemini 1.5 Pro, Gemini 1.5 Flash (~$0.0005-0.01/resume)

**Switch models anytime in the UI sidebar** - no code changes needed!

### 🔧 Adding Custom Models

**For Ollama**: Pull any model and it will appear in the dropdown
```bash
ollama pull mistral
ollama pull codellama
ollama pull your-custom-model
```

**For Cloud Providers**: Edit `ui/app.py` to add new model names to the dropdown list
```python
# Example: Add a new OpenAI model
openai_model = st.selectbox(
    "OpenAI Model",
    ["gpt-4o", "gpt-4o-mini", "your-new-model"],  # Add here
    ...
)
```

**Different use cases**:
- **Speed**: llama3.2:3b, Gemini Flash (fastest)
- **Quality**: Claude 3.5 Sonnet, GPT-4o (best suggestions)
- **Cost**: Gemini Flash, GPT-4o-mini (cheapest cloud)
- **Privacy**: Any Ollama model (100% local)
- **Reasoning**: Claude Opus, o1-preview (complex analysis)

---

## 📊 Example Output

```
ATS Score: 78/100

Coverage: 82% - Most requirements covered
Explicitness: 65% - Need to name skills more explicitly

Top Suggestions:
#1 - Experience > bullet 2 (+6 points)
    Current: Built dashboards to track performance
    Suggested: Designed A/B tests analyzing conversion lift with 
                statsmodels, improving campaign ROI by 15%
```

---

## ⚙️ Configuration

Edit `config.yaml`:
```yaml
models:
  llm_backend: "ollama"  # or "openai", "anthropic", "gemini"
  llm_model: "llama3.1:8b"

matching:
  tau_high: 0.75  # Similarity threshold
  tau_low: 0.50

scoring:
  coverage_weight: 0.35
  explicitness_weight: 0.25
```

---

## 🛠️ Tech Stack

- **Parsing**: PyMuPDF, python-docx
- **NLP**: spaCy, sentence-transformers (BGE-large-en-v1.5)
- **Vector Search**: FAISS
- **LLM**: Ollama, OpenAI, Anthropic, Google AI
- **Backend**: FastAPI
- **UI**: Streamlit

---

## 📁 Project Structure

```
ats-tailor/
├── src/
│   ├── parsers/          # PDF/DOCX extraction
│   ├── extractors/       # Resume & JD structure
│   ├── matching/         # Skills matching & evidence retrieval
│   ├── generation/       # LLM suggestions
│   ├── scoring/          # ATS scoring
│   └── api/              # FastAPI endpoints
├── ui/app.py             # Streamlit interface
├── data/
│   ├── skills_taxonomy.json  # 150+ skills
│   └── action_verbs.json
└── config.yaml
```

---

## 🎓 How Scoring Works

See **[SCORING_EXPLAINED.md](SCORING_EXPLAINED.md)** for detailed explanation.

**TL;DR**: Score = weighted sum of:
- Coverage (35%) - Required skills present
- Explicitness (25%) - Skills named explicitly
- Role Alignment (15%) - Title match
- Keywords (15%) - Technical terms
- Writing Quality (10%) - Bullet structure

---

## 🔒 Privacy

- ✅ All processing happens locally by default
- ✅ No data sent to external APIs (unless you choose cloud LLMs)
- ✅ No telemetry or tracking
- ✅ Open source - audit the code

---

## 📝 License

MIT

---

## 🙏 Credits

Built with:
- BGE Embeddings (BAAI)
- Llama 3.1 (Meta)
- Ollama
- Streamlit
- FastAPI
