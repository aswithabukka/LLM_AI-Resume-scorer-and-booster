"""Setup script for ATS-Tailor"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text() if readme_path.exists() else ""

setup(
    name="ats-tailor",
    version="0.1.0",
    description="Personal resume optimization assistant with ATS scoring",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/ats-tailor",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "fastapi>=0.109.0",
        "uvicorn[standard]>=0.27.0",
        "pydantic>=2.5.3",
        "pymupdf>=1.23.8",
        "python-docx>=1.1.0",
        "docx2txt>=0.8",
        "spacy>=3.7.2",
        "sentence-transformers>=2.3.1",
        "transformers>=4.36.2",
        "torch>=2.1.2",
        "faiss-cpu>=1.7.4",
        "ollama>=0.1.6",
        "numpy>=1.26.3",
        "pandas>=2.1.4",
        "scikit-learn>=1.4.0",
        "streamlit>=1.30.0",
        "plotly>=5.18.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.4",
            "pytest-asyncio>=0.23.3",
            "black>=23.12.1",
            "flake8>=7.0.0",
            "mypy>=1.8.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "ats-tailor=src.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    include_package_data=True,
    package_data={
        "": ["data/*.json", "config.yaml"],
    },
)
