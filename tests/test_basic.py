"""Basic tests for ATS-Tailor components"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.parsers import DocumentParser
from src.extractors import ResumeSectionizer, JDExtractor
from src.matching import SkillsMatcher


def test_document_parser_text():
    """Test parsing raw text"""
    parser = DocumentParser()
    
    text = "This is a test resume\nWith multiple lines"
    doc = parser.parse_text(text, "test.txt")
    
    assert doc.text == "This is a test resume\nWith multiple lines"
    assert doc.filename == "test.txt"
    assert doc.file_type == "text"


def test_resume_sectionizer():
    """Test resume sectionization"""
    sectionizer = ResumeSectionizer()
    
    resume_text = """
    John Doe
    john@email.com
    
    EXPERIENCE
    Software Engineer - Company A
    • Built features
    • Improved performance
    
    SKILLS
    Python, SQL, AWS
    
    EDUCATION
    BS Computer Science
    """
    
    sections = sectionizer.sectionize(resume_text)
    
    # Should have at least header, experience, skills, education
    assert len(sections) >= 4
    
    # Check section types
    section_types = [s.section_type.value for s in sections]
    assert 'experience' in section_types
    assert 'skills' in section_types
    assert 'education' in section_types


def test_jd_extractor():
    """Test JD requirement extraction"""
    jd_text = """
    Data Scientist Position
    
    Requirements:
    - 3+ years of Python experience
    - Strong SQL skills
    - Experience with machine learning
    
    Preferred:
    - AWS experience
    - PhD in related field
    """
    
    extractor = JDExtractor()
    requirements = extractor.extract_requirements(jd_text)
    
    # Should extract some requirements
    assert len(requirements) > 0
    
    # Check for must-have vs preferred
    must_haves = [r for r in requirements if r.requirement_type.value == 'must_have']
    preferred = [r for r in requirements if r.requirement_type.value == 'preferred']
    
    assert len(must_haves) > 0


def test_skills_matcher():
    """Test skills matching"""
    matcher = SkillsMatcher()
    
    # Test exact match
    match = matcher.match_skill("Python")
    assert match is not None
    assert match.canonical_skill == "Python"
    
    # Test alias match
    match = matcher.match_skill("pytorch")
    assert match is not None
    assert match.canonical_skill == "PyTorch"
    
    # Test extraction from text
    text = "I have experience with Python, SQL, and AWS"
    matches = matcher.extract_skills_from_text(text)
    
    skill_names = [m.canonical_skill for m in matches]
    assert "Python" in skill_names
    assert "SQL" in skill_names
    assert "AWS" in skill_names


def test_skills_taxonomy_loaded():
    """Test that skills taxonomy loads correctly"""
    matcher = SkillsMatcher()
    
    # Check taxonomy has expected categories
    categories = matcher.get_all_categories()
    
    assert 'programming_languages' in categories
    assert 'ml_frameworks' in categories
    assert 'cloud_platforms' in categories
    
    # Check some skills exist
    python_skills = matcher.get_category_skills('programming_languages')
    assert 'Python' in python_skills
    assert 'SQL' in python_skills


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
