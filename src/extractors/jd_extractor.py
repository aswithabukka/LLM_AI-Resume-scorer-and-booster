"""Job Description requirement extractor"""

import re
from dataclasses import dataclass
from typing import List, Set, Optional
from enum import Enum


class RequirementType(Enum):
    """Type of job requirement"""
    MUST_HAVE = "must_have"
    PREFERRED = "preferred"
    RESPONSIBILITY = "responsibility"
    NICE_TO_HAVE = "nice_to_have"


@dataclass
class JobRequirement:
    """A single job requirement"""
    text: str
    requirement_type: RequirementType
    skills: List[str]
    years_experience: Optional[int] = None
    is_technical: bool = True


class JDExtractor:
    """Extract structured requirements from job descriptions"""
    
    # Section markers for different requirement types
    MUST_HAVE_MARKERS = [
        "required", "requirements", "qualifications", "must have",
        "you have", "you bring", "minimum qualifications"
    ]
    
    PREFERRED_MARKERS = [
        "preferred", "nice to have", "bonus", "plus", "ideal",
        "preferred qualifications", "we'd love if"
    ]
    
    RESPONSIBILITY_MARKERS = [
        "responsibilities", "you will", "what you'll do",
        "day-to-day", "role", "about the role"
    ]
    
    # Patterns for extracting years of experience
    YEARS_PATTERN = re.compile(
        r'(\d+)\+?\s*(?:years?|yrs?)(?:\s+of)?(?:\s+experience)?',
        re.IGNORECASE
    )
    
    # Technical skill indicators
    TECHNICAL_INDICATORS = [
        "python", "sql", "java", "aws", "cloud", "machine learning",
        "data", "api", "framework", "library", "database", "tool",
        "platform", "system", "software", "code", "programming"
    ]
    
    def __init__(self, skills_taxonomy: dict = None):
        """
        Initialize JD extractor
        
        Args:
            skills_taxonomy: Dictionary mapping canonical skills to aliases
        """
        self.skills_taxonomy = skills_taxonomy or {}
    
    def extract_requirements(self, jd_text: str) -> List[JobRequirement]:
        """
        Extract structured requirements from job description
        
        Args:
            jd_text: Raw job description text
            
        Returns:
            List of JobRequirement objects
        """
        # Split into sections
        sections = self._split_into_sections(jd_text)
        
        requirements = []
        
        for section_type, content in sections.items():
            # Extract individual requirement lines
            req_lines = self._extract_requirement_lines(content)
            
            for line in req_lines:
                req = self._parse_requirement(line, section_type)
                if req:
                    requirements.append(req)
        
        return requirements
    
    def _split_into_sections(self, text: str) -> dict:
        """Split JD into requirement sections"""
        sections = {
            RequirementType.MUST_HAVE: [],
            RequirementType.PREFERRED: [],
            RequirementType.RESPONSIBILITY: [],
        }
        
        lines = text.split('\n')
        current_section = None
        
        for line in lines:
            stripped = line.strip().lower()
            
            if not stripped:
                continue
            
            # Check for section headers
            section_type = self._identify_section_type(stripped)
            if section_type:
                current_section = section_type
                continue
            
            # Add to current section
            if current_section:
                sections[current_section].append(line.strip())
        
        # Convert lists to text
        return {k: '\n'.join(v) for k, v in sections.items() if v}
    
    def _identify_section_type(self, line: str) -> Optional[RequirementType]:
        """Identify section type from header line"""
        for marker in self.MUST_HAVE_MARKERS:
            if marker in line:
                return RequirementType.MUST_HAVE
        
        for marker in self.PREFERRED_MARKERS:
            if marker in line:
                return RequirementType.PREFERRED
        
        for marker in self.RESPONSIBILITY_MARKERS:
            if marker in line:
                return RequirementType.RESPONSIBILITY
        
        return None
    
    def _extract_requirement_lines(self, text: str) -> List[str]:
        """Extract individual requirement lines from section text"""
        lines = text.split('\n')
        requirements = []
        
        bullet_pattern = re.compile(r'^[\s•\-\*\+\d\.]+')
        
        for line in lines:
            stripped = line.strip()
            
            # Skip empty or very short lines
            if len(stripped) < 10:
                continue
            
            # Remove bullet markers
            clean_line = bullet_pattern.sub('', stripped).strip()
            
            if clean_line:
                requirements.append(clean_line)
        
        return requirements
    
    def _parse_requirement(self, text: str, req_type: RequirementType) -> Optional[JobRequirement]:
        """Parse a single requirement line"""
        # Extract skills
        skills = self._extract_skills(text)
        
        # Extract years of experience
        years = self._extract_years(text)
        
        # Determine if technical
        is_technical = self._is_technical_requirement(text)
        
        return JobRequirement(
            text=text,
            requirement_type=req_type,
            skills=skills,
            years_experience=years,
            is_technical=is_technical
        )
    
    def _extract_skills(self, text: str) -> List[str]:
        """Extract skill mentions from requirement text"""
        skills = []
        text_lower = text.lower()
        
        # Check against skills taxonomy
        for category, skill_dict in self.skills_taxonomy.items():
            for canonical_skill, aliases in skill_dict.items():
                # Check canonical name
                if canonical_skill.lower() in text_lower:
                    skills.append(canonical_skill)
                    continue
                
                # Check aliases
                for alias in aliases:
                    if alias.lower() in text_lower:
                        skills.append(canonical_skill)
                        break
        
        return list(set(skills))  # Remove duplicates
    
    def _extract_years(self, text: str) -> Optional[int]:
        """Extract years of experience from requirement text"""
        match = self.YEARS_PATTERN.search(text)
        if match:
            return int(match.group(1))
        return None
    
    def _is_technical_requirement(self, text: str) -> bool:
        """Determine if requirement is technical vs soft skill"""
        text_lower = text.lower()
        
        # Check for technical indicators
        for indicator in self.TECHNICAL_INDICATORS:
            if indicator in text_lower:
                return True
        
        # Check for soft skill indicators
        soft_indicators = [
            "communication", "leadership", "teamwork", "collaboration",
            "stakeholder", "presentation", "agile", "scrum"
        ]
        
        for indicator in soft_indicators:
            if indicator in text_lower:
                return False
        
        # Default to technical if uncertain
        return True
    
    def extract_job_title(self, jd_text: str) -> Optional[str]:
        """Extract job title from JD (usually first line or near top)"""
        lines = jd_text.split('\n')
        
        # Look in first 10 lines for title-like patterns
        for line in lines[:10]:
            stripped = line.strip()
            
            # Skip very short lines
            if len(stripped) < 5:
                continue
            
            # Common title patterns
            title_patterns = [
                r'(Senior|Junior|Lead|Staff|Principal)?\s*(Data Scientist|ML Engineer|Software Engineer|Analyst)',
                r'Job Title:\s*(.+)',
                r'Position:\s*(.+)',
            ]
            
            for pattern in title_patterns:
                match = re.search(pattern, stripped, re.IGNORECASE)
                if match:
                    return match.group(0).replace('Job Title:', '').replace('Position:', '').strip()
        
        return None
    
    def get_must_have_skills(self, requirements: List[JobRequirement]) -> Set[str]:
        """Get all must-have skills from requirements"""
        must_have_skills = set()
        
        for req in requirements:
            if req.requirement_type == RequirementType.MUST_HAVE:
                must_have_skills.update(req.skills)
        
        return must_have_skills
    
    def get_preferred_skills(self, requirements: List[JobRequirement]) -> Set[str]:
        """Get all preferred skills from requirements"""
        preferred_skills = set()
        
        for req in requirements:
            if req.requirement_type == RequirementType.PREFERRED:
                preferred_skills.update(req.skills)
        
        return preferred_skills
