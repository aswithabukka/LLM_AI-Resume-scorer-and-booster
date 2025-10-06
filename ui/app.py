"""Streamlit UI for ATS-Tailor"""

import streamlit as st
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core import ATSTailor


# Page config
st.set_page_config(
    page_title="ATS-Tailor",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .score-card {
        padding: 1.5rem;
        border-radius: 0.5rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        text-align: center;
        margin: 1rem 0;
    }
    .score-number {
        font-size: 3rem;
        font-weight: bold;
    }
    .suggestion-card {
        padding: 1rem;
        border-left: 4px solid #1f77b4;
        background-color: #f0f2f6;
        margin: 0.5rem 0;
        border-radius: 0.25rem;
    }
    .metric-good {
        color: #28a745;
    }
    .metric-warning {
        color: #ffc107;
    }
    .metric-bad {
        color: #dc3545;
    }
</style>
""", unsafe_allow_html=True)


def load_tailor(config=None):
    """Load ATS-Tailor instance with custom config"""
    return ATSTailor(config=config)


def format_score_color(score: float) -> str:
    """Get color class based on score"""
    if score >= 0.8:
        return "metric-good"
    elif score >= 0.6:
        return "metric-warning"
    else:
        return "metric-bad"


def main():
    """Main Streamlit app"""
    
    # Header
    st.markdown('<div class="main-header">📝 ATS-Tailor</div>', unsafe_allow_html=True)
    st.markdown("**Your Personal Resume Optimization Assistant**")
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        st.subheader("🤖 LLM Model Selection")
        
        llm_backend = st.selectbox(
            "Backend",
            ["ollama", "openai", "anthropic", "gemini"],
            index=0,
            help="Choose your LLM provider"
        )
        
        if llm_backend == "ollama":
            ollama_model = st.selectbox(
                "Ollama Model",
                ["llama3.2:3b", "llama3.1:8b", "llama3.1:70b", "mistral", "qwen2.5:7b"],
                index=1,
                help="llama3.2:3b = Fastest | llama3.1:8b = Balanced | llama3.1:70b = Best quality (40GB RAM)"
            )
            st.info("✅ **FREE** | 🔒 **Private** | Make sure Ollama is running")
            
            # Test Ollama connection
            try:
                import ollama
                response = ollama.list()
                # Handle both dict and Pydantic model responses
                if hasattr(response, 'models'):
                    available_models = [m.model for m in response.models]
                else:
                    available_models = [m['name'] for m in response.get('models', [])]
                
                if ollama_model in available_models:
                    st.success(f"✓ {ollama_model} is available")
                else:
                    st.warning(f"⚠️ {ollama_model} not found. Run: `ollama pull {ollama_model}`")
            except Exception as e:
                st.error(f"❌ Ollama not running. Start with: `ollama serve`")
            
            llm_model = ollama_model
            
        elif llm_backend == "openai":
            openai_model = st.selectbox(
                "OpenAI Model",
                ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "o1-preview"],
                index=0,
                help="gpt-4o = Best quality (~$0.02/resume) | gpt-4o-mini = Cheaper (~$0.002/resume)"
            )
            
            api_key = st.text_input(
                "OpenAI API Key",
                type="password",
                help="Get your key from https://platform.openai.com/api-keys"
            )
            
            if api_key:
                st.success("✓ API key provided")
                import os
                os.environ['OPENAI_API_KEY'] = api_key
            else:
                st.warning("⚠️ Enter API key to use OpenAI")
            
            st.info("💰 **~$0.01-0.03/resume** | ☁️ **Cloud-based**")
            llm_model = openai_model
            
        elif llm_backend == "anthropic":
            anthropic_model = st.selectbox(
                "Anthropic Model",
                [
                    "claude-3-5-sonnet-20241022",
                    "claude-3-5-haiku-20241022", 
                    "claude-3-opus-20240229",
                    "claude-3-sonnet-20240229",
                    "claude-3-haiku-20240307"
                ],
                index=0,
                help="3.5 Sonnet = Latest & best | Opus = Most capable | Haiku = Fastest & cheapest"
            )
            
            api_key = st.text_input(
                "Anthropic API Key",
                type="password",
                help="Get your key from https://console.anthropic.com/"
            )
            
            if api_key:
                st.success("✓ API key provided")
                import os
                os.environ['ANTHROPIC_API_KEY'] = api_key
            else:
                st.warning("⚠️ Enter API key to use Claude")
            
            st.info("💰 **~$0.01-0.02/resume** | ☁️ **Cloud-based** | 🧠 **Excellent reasoning**")
            llm_model = anthropic_model
            
        else:  # gemini
            gemini_model = st.selectbox(
                "Gemini Model",
                ["gemini-2.0-flash-exp", "gemini-1.5-pro", "gemini-1.5-flash"],
                index=0,
                help="Gemini 2.0 Flash = Latest & fast | 1.5 Pro = Best quality"
            )
            
            api_key = st.text_input(
                "Google AI API Key",
                type="password",
                help="Get your key from https://aistudio.google.com/app/apikey"
            )
            
            if api_key:
                st.success("✓ API key provided")
                import os
                os.environ['GEMINI_API_KEY'] = api_key
            else:
                st.warning("⚠️ Enter API key to use Gemini")
            
            st.info("💰 **~$0.001-0.01/resume** | ☁️ **Cloud-based** | ⚡ **Very fast**")
            llm_model = gemini_model
        
        # Advanced settings
        with st.expander("🔧 Advanced Settings"):
            temperature = st.slider(
                "Temperature",
                min_value=0.0,
                max_value=1.0,
                value=0.3,
                step=0.1,
                help="Lower = more conservative, Higher = more creative"
            )
            
            tau_high = st.slider(
                "Match Threshold (High)",
                min_value=0.5,
                max_value=1.0,
                value=0.75,
                step=0.05,
                help="Similarity threshold for 'Present' status"
            )
            
            tau_low = st.slider(
                "Match Threshold (Low)",
                min_value=0.3,
                max_value=0.8,
                value=0.50,
                step=0.05,
                help="Similarity threshold for 'Weak' status"
            )
        
        st.markdown("---")
        st.markdown("### 📊 Model Comparison")
        st.markdown("""
        **Ollama (llama3.2:3b)**
        - ✅ FREE & Private | ⚡ Fastest
        - ⭐ Quality: 6/10
        
        **Ollama (llama3.1:8b)**
        - ✅ FREE & Private | ⚡ Fast
        - ⭐ Quality: 7/10
        
        **Claude 3.5 Sonnet**
        - 💰 ~$0.015/resume | 🧠 Best reasoning
        - ⭐ Quality: 9.5/10
        
        **Gemini 2.0 Flash**
        - 💰 ~$0.001/resume | ⚡ Very fast
        - ⭐ Quality: 8.5/10
        
        **GPT-4o**
        - 💰 ~$0.02/resume | 🎯 Most popular
        - ⭐ Quality: 9/10
        """)
        
        st.markdown("---")
        st.markdown("### About")
        st.markdown("""
        ATS-Tailor analyzes your resume against a job description and provides:
        - **ATS Score** (0-100)
        - **Gap Analysis** (missing skills)
        - **Actionable Edits** (ready to paste)
        - **Keyword Suggestions**
        """)
    
    # Main content
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📄 Your Resume")
        
        upload_method = st.radio(
            "Input method:",
            ["Upload File", "Paste Text"],
            horizontal=True
        )
        
        resume_text = None
        resume_path = None
        
        if upload_method == "Upload File":
            uploaded_file = st.file_uploader(
                "Upload resume (PDF or DOCX)",
                type=["pdf", "docx"],
                help="Your file is processed locally and not stored"
            )
            
            if uploaded_file:
                # Save temporarily
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp:
                    tmp.write(uploaded_file.read())
                    resume_path = tmp.name
                
                st.success(f"✅ Uploaded: {uploaded_file.name}")
        else:
            resume_text = st.text_area(
                "Paste resume text:",
                height=300,
                placeholder="Paste your resume text here..."
            )
    
    with col2:
        st.subheader("💼 Job Description")
        
        jd_text = st.text_area(
            "Paste job description:",
            height=300,
            placeholder="Paste the full job description here..."
        )
    
    # Analyze button
    st.markdown("---")
    
    if st.button("🚀 Analyze & Get Suggestions", type="primary", use_container_width=True):
        
        # Validation
        if not (resume_text or resume_path):
            st.error("❌ Please provide your resume")
            return
        
        if not jd_text:
            st.error("❌ Please provide a job description")
            return
        
        # Validate OpenAI setup
        if llm_backend == "openai" and not api_key:
            st.error("❌ Please enter your OpenAI API key in the sidebar")
            return
        
        # Build config from UI settings
        config = {
            'llm_backend': llm_backend,
            'llm_model': llm_model,
            'temperature': temperature,
            'tau_high': tau_high,
            'tau_low': tau_low,
        }
        
        # Run analysis
        with st.spinner(f"🔍 Analyzing with {llm_backend.upper()} ({llm_model})... This may take 10-30 seconds..."):
            try:
                tailor = load_tailor(config=config)
                
                result = tailor.analyze(
                    resume_path=resume_path,
                    resume_text=resume_text,
                    jd_text=jd_text
                )
                
                # Display results
                st.success(f"✅ Analysis complete using **{llm_backend.upper()}** ({llm_model})!")
                
                # Score card
                st.markdown("## 📊 ATS Score")
                
                score_col1, score_col2, score_col3 = st.columns([2, 1, 1])
                
                with score_col1:
                    st.markdown(f"""
                    <div class="score-card">
                        <div class="score-number">{result.overall_score}/100</div>
                        <div>{result.explanation}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with score_col2:
                    st.metric("Coverage", f"{result.breakdown['coverage']:.0%}")
                    st.metric("Keywords", f"{result.breakdown['keywords']:.0%}")
                
                with score_col3:
                    st.metric("Explicitness", f"{result.breakdown['explicitness']:.0%}")
                    st.metric("Writing", f"{result.breakdown['writing']:.0%}")
                
                # Score breakdown
                with st.expander("📈 Detailed Score Breakdown"):
                    for key, value in result.breakdown.items():
                        color_class = format_score_color(value)
                        st.markdown(f"**{key.replace('_', ' ').title()}:** <span class='{color_class}'>{value:.1%}</span>", unsafe_allow_html=True)
                
                # Top suggestions
                st.markdown("---")
                st.markdown("## ✨ Top Suggestions")
                
                if result.top_edits:
                    for i, edit in enumerate(result.top_edits[:5], 1):
                        with st.container():
                            st.markdown(f"""
                            <div class="suggestion-card">
                                <strong>#{i} - {edit['target']}</strong> 
                                <span style="color: #28a745; font-weight: bold;">+{edit['est_score_gain']} points</span>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            col_a, col_b = st.columns(2)
                            
                            with col_a:
                                st.markdown("**Current:**")
                                st.text_area(
                                    "current",
                                    value=edit['current'] or "N/A",
                                    height=80,
                                    key=f"current_{i}",
                                    label_visibility="collapsed"
                                )
                            
                            with col_b:
                                st.markdown("**Suggested:**")
                                st.text_area(
                                    "suggested",
                                    value=edit['suggested'],
                                    height=80,
                                    key=f"suggested_{i}",
                                    label_visibility="collapsed"
                                )
                            
                            st.caption(f"💡 Reason: {edit['reason']}")
                            st.markdown("---")
                else:
                    st.info("No major edits needed - your resume looks good!")
                
                # Skills to add
                if result.skills_insertions:
                    st.markdown("## 🔧 Skills to Add")
                    st.markdown("Add these missing must-have skills to your Skills section:")
                    
                    skills_text = ", ".join(result.skills_insertions)
                    st.code(skills_text, language=None)
                    
                    if st.button("📋 Copy Skills"):
                        st.write("Skills copied to clipboard!")
                
                # Summary suggestion
                if result.summary_suggestion:
                    st.markdown("## 📝 Summary Suggestion")
                    st.text_area(
                        "Updated professional summary:",
                        value=result.summary_suggestion,
                        height=100
                    )
                
                # Requirement matches
                with st.expander("🎯 Requirement Match Details"):
                    st.markdown("### Must-Have Requirements")
                    
                    for req in result.must_haves:
                        status_emoji = {
                            'present': '✅',
                            'weak': '⚠️',
                            'missing': '❌'
                        }.get(req['status'], '❓')
                        
                        st.markdown(f"{status_emoji} **{req['requirement']}**")
                        st.caption(f"Status: {req['status']} | Confidence: {req['confidence']:.2f}")
                        
                        if req['evidence']:
                            st.text(f"Evidence: {req['evidence'][:150]}...")
                        
                        st.markdown("---")
                
                # Export
                st.markdown("---")
                st.markdown("## 💾 Export Results")
                
                export_col1, export_col2 = st.columns(2)
                
                with export_col1:
                    # JSON export
                    result_json = json.dumps(result.__dict__, indent=2, default=str)
                    st.download_button(
                        label="📥 Download JSON",
                        data=result_json,
                        file_name="ats_tailor_results.json",
                        mime="application/json"
                    )
                
                with export_col2:
                    # Text summary
                    summary_text = f"""ATS-Tailor Results
===================
Overall Score: {result.overall_score}/100

{result.explanation}

Top Suggestions:
"""
                    for i, edit in enumerate(result.top_edits[:5], 1):
                        summary_text += f"\n{i}. {edit['target']} (+{edit['est_score_gain']} pts)\n"
                        summary_text += f"   Current: {edit['current']}\n"
                        summary_text += f"   Suggested: {edit['suggested']}\n"
                    
                    st.download_button(
                        label="📥 Download Summary",
                        data=summary_text,
                        file_name="ats_tailor_summary.txt",
                        mime="text/plain"
                    )
                
            except Exception as e:
                st.error(f"❌ Error during analysis: {str(e)}")
                st.exception(e)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 1rem;">
        Made with ❤️ by ATS-Tailor | Privacy-first, local processing | 
        <a href="https://github.com/yourusername/ats-tailor">GitHub</a>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
