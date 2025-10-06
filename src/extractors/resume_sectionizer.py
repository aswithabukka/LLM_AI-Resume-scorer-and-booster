"""Resume sectionizer - extracts structured sections from resume text"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum


class SectionType(Enum):
    """Resume section types"""
    HEADER = "header"
    SUMMARY = "summary"
    EXPERIENCE = "experience"
    EDUCATION = "education"
    SKILLS = "skills"
    PROJECTS = "projects"
    CERTIFICATIONS = "certifications"
    PUBLICATIONS = "publications"
    AWARDS = "awards"
    OTHER = "other"


@dataclass
class ResumeSection:
    """A section of a resume"""
    section_type: SectionType
    title: str
    content: str
    bullets: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)


@dataclass
class ExperienceEntry:
    """A single work experience entry"""
    company: str
    title: str
    duration: str
    location: Optional[str]
    bullets: List[str]
    raw_text: str


class ResumeSectionizer:
    """Extract and structure resume sections"""
    
    # Common section headers (case-insensitive patterns)
    SECTION_PATTERNS = {
        SectionType.SUMMARY: [
            r"^(professional\s+)?summary",
            r"^profile",
            r"^objective",
            r"^about(\s+me)?",
        ],
        SectionType.EXPERIENCE: [
            r"^(work\s+)?experience",
            r"^employment(\s+history)?",
            r"^professional\s+experience",
            r"^career\s+history",
        ],
        SectionType.EDUCATION: [
            r"^education",
            r"^academic\s+background",
        ],
        SectionType.SKILLS: [
            r"^(technical\s+)?skills",
            r"^competencies",
            r"^expertise",
            r"^technologies",
        ],
        SectionType.PROJECTS: [
            r"^projects",
            r"^key\s+projects",
            r"^selected\s+projects",
        ],
        SectionType.CERTIFICATIONS: [
            r"^certifications?",
            r"^licenses?",
        ],
        SectionType.PUBLICATIONS: [
            r"^publications?",
            r"^papers?",
        ],
        SectionType.AWARDS: [
            r"^awards?",
            r"^honors?",
            r"^achievements?",
        ],
    }
    
    def __init__(self):
        self.compiled_patterns = self._compile_patterns()
    
    def _compile_patterns(self) -> Dict[SectionType, List[re.Pattern]]:
        """Compile regex patterns for section detection"""
        compiled = {}
        for section_type, patterns in self.SECTION_PATTERNS.items():
            compiled[section_type] = [
                re.compile(pattern, re.IGNORECASE) for pattern in patterns
            ]
        return compiled
    
    def sectionize(self, text: str) -> List[ResumeSection]:
        """
        Split resume text into structured sections
        
        Args:
            text: Raw resume text
            
        Returns:
            List of ResumeSection objects
        """
        lines = text.split('\n')
        sections = []
        current_section = None
        current_content = []
        
        # Extract header (first few lines before any section)
        header_lines = []
        i = 0
        while i < min(10, len(lines)):
            line = lines[i].strip()
            if line and not self._is_section_header(line):
                header_lines.append(line)
                i += 1
            else:
                break
        
        if header_lines:
            sections.append(ResumeSection(
                section_type=SectionType.HEADER,
                title="Header",
                content="\n".join(header_lines),
                metadata=self._extract_contact_info("\n".join(header_lines))
            ))
        
        # Process remaining lines
        for line in lines[i:]:
            stripped = line.strip()
            
            if not stripped:
                continue
            
            # Check if this is a section header
            section_type = self._identify_section(stripped)
            
            if section_type:
                # Save previous section
                if current_section:
                    content_text = "\n".join(current_content)
                    sections.append(ResumeSection(
                        section_type=current_section,
                        title=self._get_section_title(current_section),
                        content=content_text,
                        bullets=self._extract_bullets(content_text)
                    ))
                
                # Start new section
                current_section = section_type
                current_content = []
            else:
                # Add to current section
                if current_section:
                    current_content.append(line)
        
        # Save last section
        if current_section and current_content:
            content_text = "\n".join(current_content)
            sections.append(ResumeSection(
                section_type=current_section,
                title=self._get_section_title(current_section),
                content=content_text,
                bullets=self._extract_bullets(content_text)
            ))
        
        return sections
    
    def _is_section_header(self, line: str) -> bool:
        """Check if a line is a section header"""
        return self._identify_section(line) is not None
    
    def _identify_section(self, line: str) -> Optional[SectionType]:
        """Identify the section type from a header line"""
        line_clean = line.strip().lower()
        
        for section_type, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                if pattern.match(line_clean):
                    return section_type
        
        return None
    
    def _get_section_title(self, section_type: SectionType) -> str:
        """Get display title for section type"""
        return section_type.value.replace('_', ' ').title()
    
    def _extract_bullets(self, text: str) -> List[str]:
        """Extract bullet points from section text"""
        bullets = []
        lines = text.split('\n')
        
        bullet_markers = [r'^\s*[•\-\*\+]', r'^\s*\d+\.', r'^\s*[a-z]\)']
        bullet_pattern = re.compile('|'.join(bullet_markers))
        
        for line in lines:
            stripped = line.strip()
            if bullet_pattern.match(line):
                # Remove bullet marker
                clean_bullet = re.sub(r'^[\s•\-\*\+\d\.a-z\)]+', '', stripped).strip()
                if clean_bullet:
                    bullets.append(clean_bullet)
        
        return bullets
    
    def _extract_contact_info(self, header_text: str) -> Dict:
        """Extract contact information from header"""
        metadata = {}
        
        # Email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_match = re.search(email_pattern, header_text)
        if email_match:
            metadata['email'] = email_match.group(0)
        
        # Phone
        phone_pattern = r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        phone_match = re.search(phone_pattern, header_text)
        if phone_match:
            metadata['phone'] = phone_match.group(0)
        
        # LinkedIn
        linkedin_pattern = r'linkedin\.com/in/[\w\-]+'
        linkedin_match = re.search(linkedin_pattern, header_text, re.IGNORECASE)
        if linkedin_match:
            metadata['linkedin'] = linkedin_match.group(0)
        
        # GitHub
        github_pattern = r'github\.com/[\w\-]+'
        github_match = re.search(github_pattern, header_text, re.IGNORECASE)
        if github_match:
            metadata['github'] = github_match.group(0)
        
        return metadata
    
    def extract_experience_entries(self, experience_section: ResumeSection) -> List[ExperienceEntry]:
        """Parse experience section into structured entries"""
        if experience_section.section_type != SectionType.EXPERIENCE:
            return []
        
        entries = []
        lines = experience_section.content.split('\n')
        
        current_entry = None
        current_bullets = []
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            
            # Check if this looks like a new job entry (company/title line)
            # Heuristic: lines with dates or all-caps company names
            if self._looks_like_job_header(stripped):
                # Save previous entry
                if current_entry:
                    entries.append(ExperienceEntry(
                        company=current_entry.get('company', ''),
                        title=current_entry.get('title', ''),
                        duration=current_entry.get('duration', ''),
                        location=current_entry.get('location'),
                        bullets=current_bullets,
                        raw_text=current_entry.get('raw', '')
                    ))
                
                # Start new entry
                current_entry = self._parse_job_header(stripped)
                current_bullets = []
            elif stripped.startswith(('•', '-', '*', '+')):
                # Bullet point
                clean_bullet = re.sub(r'^[\s•\-\*\+]+', '', stripped).strip()
                current_bullets.append(clean_bullet)
        
        # Save last entry
        if current_entry:
            entries.append(ExperienceEntry(
                company=current_entry.get('company', ''),
                title=current_entry.get('title', ''),
                duration=current_entry.get('duration', ''),
                location=current_entry.get('location'),
                bullets=current_bullets,
                raw_text=current_entry.get('raw', '')
            ))
        
        return entries
    
    def _looks_like_job_header(self, line: str) -> bool:
        """Heuristic to detect job entry headers"""
        # Contains date patterns
        date_patterns = [
            r'\d{4}\s*[-–]\s*\d{4}',
            r'\d{4}\s*[-–]\s*Present',
            r'[A-Z][a-z]+\s+\d{4}',
        ]
        
        for pattern in date_patterns:
            if re.search(pattern, line):
                return True
        
        # All caps (company name)
        if line.isupper() and len(line) > 3:
            return True
        
        return False
    
    def _parse_job_header(self, line: str) -> Dict:
        """Parse job header line into components"""
        # This is a simplified parser - real-world would be more robust
        entry = {'raw': line}
        
        # Extract dates
        date_pattern = r'(\w+\s+\d{4}\s*[-–]\s*(?:\w+\s+\d{4}|Present))'
        date_match = re.search(date_pattern, line, re.IGNORECASE)
        if date_match:
            entry['duration'] = date_match.group(1)
        
        # Extract location
        location_pattern = r',\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,?\s*[A-Z]{2})'
        location_match = re.search(location_pattern, line)
        if location_match:
            entry['location'] = location_match.group(1)
        
        return entry
