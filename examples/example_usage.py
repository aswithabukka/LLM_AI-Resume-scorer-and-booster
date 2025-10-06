"""Example usage of ATS-Tailor"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core import ATSTailor
import json


def example_basic_usage():
    """Basic usage example"""
    
    # Sample JD text
    jd_text = """
    Data Scientist - Machine Learning
    
    We're looking for a Data Scientist to join our ML team.
    
    Requirements:
    - 3+ years of experience with Python and SQL
    - Strong experience with machine learning frameworks (scikit-learn, PyTorch, TensorFlow)
    - Experience with A/B testing and statistical analysis
    - Proficiency with cloud platforms (AWS, GCP)
    - Experience with data pipelines and ETL (Airflow, Spark)
    
    Preferred:
    - Experience with LLMs and NLP
    - Knowledge of MLOps tools (MLflow, Docker, Kubernetes)
    - Experience with vector databases (Pinecone, Weaviate)
    
    Responsibilities:
    - Build and deploy ML models for production
    - Design and run A/B tests
    - Collaborate with product and engineering teams
    """
    
    # Sample resume text
    resume_text = """
    John Doe
    Data Scientist
    john.doe@email.com | linkedin.com/in/johndoe
    
    SUMMARY
    Data professional with 4 years of experience in analytics and modeling.
    
    EXPERIENCE
    
    Data Analyst - Tech Company
    Jan 2020 - Present
    • Built dashboards to track KPIs using Tableau
    • Analyzed user behavior data with SQL and Python
    • Created predictive models for customer churn
    • Worked with marketing team on campaign optimization
    
    Junior Analyst - Startup Inc
    Jun 2018 - Dec 2019
    • Performed data cleaning and preprocessing
    • Generated weekly reports for stakeholders
    • Assisted with database management
    
    SKILLS
    Python, SQL, Pandas, NumPy, Scikit-learn, Tableau, Excel
    
    EDUCATION
    BS in Statistics - University of XYZ, 2018
    """
    
    # Initialize ATS-Tailor
    print("Initializing ATS-Tailor...")
    tailor = ATSTailor()
    
    # Analyze
    print("Analyzing resume against JD...")
    result = tailor.analyze(
        resume_text=resume_text,
        jd_text=jd_text
    )
    
    # Print results
    print("\n" + "="*60)
    print(f"ATS SCORE: {result.overall_score}/100")
    print("="*60)
    
    print(f"\n{result.explanation}\n")
    
    print("SCORE BREAKDOWN:")
    for key, value in result.breakdown.items():
        print(f"  {key.replace('_', ' ').title()}: {value:.1%}")
    
    print("\n" + "="*60)
    print("TOP SUGGESTIONS:")
    print("="*60)
    
    for i, edit in enumerate(result.top_edits[:3], 1):
        print(f"\n#{i} - {edit['target']} (+{edit['est_score_gain']} points)")
        print(f"Reason: {edit['reason']}")
        print(f"\nCurrent:\n  {edit['current']}")
        print(f"\nSuggested:\n  {edit['suggested']}")
        print("-" * 60)
    
    if result.skills_insertions:
        print("\n" + "="*60)
        print("SKILLS TO ADD:")
        print("="*60)
        print(", ".join(result.skills_insertions[:10]))
    
    # Export to JSON
    output_path = Path(__file__).parent / "example_output.json"
    with open(output_path, 'w') as f:
        json.dump(result.__dict__, f, indent=2, default=str)
    
    print(f"\n✅ Full results saved to: {output_path}")


def example_file_upload():
    """Example with file upload"""
    
    # This would work with actual resume files
    resume_path = "path/to/your/resume.pdf"
    jd_path = "path/to/job_description.txt"
    
    tailor = ATSTailor()
    
    # Read JD from file
    with open(jd_path, 'r') as f:
        jd_text = f.read()
    
    result = tailor.analyze(
        resume_path=resume_path,
        jd_text=jd_text
    )
    
    print(f"Score: {result.overall_score}/100")


if __name__ == "__main__":
    print("Running ATS-Tailor Example...\n")
    example_basic_usage()
