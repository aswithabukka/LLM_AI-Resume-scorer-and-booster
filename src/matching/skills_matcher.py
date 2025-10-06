"""Skills taxonomy matcher"""

import json
from pathlib import Path
from dataclasses import dataclass
from typing import List, Set, Dict, Optional


@dataclass
class SkillMatch:
    """Result of matching a skill"""
    canonical_skill: str
    matched_alias: Optional[str]
    category: str
    confidence: float = 1.0


class SkillsMatcher:
    """Match skills using taxonomy and fuzzy matching"""
    
    def __init__(self, taxonomy_path: Optional[str] = None):
        """
        Initialize skills matcher
        
        Args:
            taxonomy_path: Path to skills taxonomy JSON file
        """
        if taxonomy_path is None:
            # Default path
            taxonomy_path = Path(__file__).parent.parent.parent / "data" / "skills_taxonomy.json"
        
        self.taxonomy = self._load_taxonomy(taxonomy_path)
        self.skill_to_category = self._build_skill_index()
    
    def _load_taxonomy(self, path: Path) -> Dict:
        """Load skills taxonomy from JSON"""
        with open(path, 'r') as f:
            return json.load(f)
    
    def _build_skill_index(self) -> Dict[str, str]:
        """Build reverse index: skill -> category"""
        index = {}
        
        for category, skills_dict in self.taxonomy.items():
            for canonical_skill, aliases in skills_dict.items():
                # Add canonical skill
                index[canonical_skill.lower()] = category
                
                # Add all aliases
                for alias in aliases:
                    index[alias.lower()] = category
        
        return index
    
    def match_skill(self, skill_text: str) -> Optional[SkillMatch]:
        """
        Match a skill text to canonical skill
        
        Args:
            skill_text: Skill text to match
            
        Returns:
            SkillMatch if found, None otherwise
        """
        skill_lower = skill_text.lower().strip()
        
        # Direct match
        if skill_lower in self.skill_to_category:
            category = self.skill_to_category[skill_lower]
            canonical = self._find_canonical(skill_lower, category)
            
            return SkillMatch(
                canonical_skill=canonical,
                matched_alias=skill_text if skill_text != canonical else None,
                category=category,
                confidence=1.0
            )
        
        # Fuzzy match (substring)
        for canonical_skill, aliases in self._get_all_skills():
            # Check if skill_text is substring of canonical or vice versa
            if skill_lower in canonical_skill.lower() or canonical_skill.lower() in skill_lower:
                category = self.skill_to_category[canonical_skill.lower()]
                return SkillMatch(
                    canonical_skill=canonical_skill,
                    matched_alias=skill_text,
                    category=category,
                    confidence=0.8
                )
            
            # Check aliases
            for alias in aliases:
                if skill_lower in alias.lower() or alias.lower() in skill_lower:
                    category = self.skill_to_category[alias.lower()]
                    canonical = self._find_canonical(alias.lower(), category)
                    return SkillMatch(
                        canonical_skill=canonical,
                        matched_alias=skill_text,
                        category=category,
                        confidence=0.7
                    )
        
        return None
    
    def _find_canonical(self, skill_lower: str, category: str) -> str:
        """Find canonical skill name for a matched skill"""
        skills_dict = self.taxonomy.get(category, {})
        
        for canonical, aliases in skills_dict.items():
            if canonical.lower() == skill_lower:
                return canonical
            if skill_lower in [a.lower() for a in aliases]:
                return canonical
        
        return skill_lower.title()
    
    def _get_all_skills(self):
        """Generator for all canonical skills and their aliases"""
        for category, skills_dict in self.taxonomy.items():
            for canonical, aliases in skills_dict.items():
                yield canonical, aliases
    
    def extract_skills_from_text(self, text: str) -> List[SkillMatch]:
        """
        Extract all skills mentioned in text
        
        Args:
            text: Text to extract skills from
            
        Returns:
            List of SkillMatch objects
        """
        text_lower = text.lower()
        matches = []
        seen_skills = set()
        
        # Check all skills in taxonomy
        for category, skills_dict in self.taxonomy.items():
            for canonical_skill, aliases in skills_dict.items():
                # Check canonical
                if canonical_skill.lower() in text_lower and canonical_skill not in seen_skills:
                    matches.append(SkillMatch(
                        canonical_skill=canonical_skill,
                        matched_alias=None,
                        category=category,
                        confidence=1.0
                    ))
                    seen_skills.add(canonical_skill)
                    continue
                
                # Check aliases
                for alias in aliases:
                    if alias.lower() in text_lower and canonical_skill not in seen_skills:
                        matches.append(SkillMatch(
                            canonical_skill=canonical_skill,
                            matched_alias=alias,
                            category=category,
                            confidence=0.9
                        ))
                        seen_skills.add(canonical_skill)
                        break
        
        return matches
    
    def get_category_skills(self, category: str) -> List[str]:
        """Get all canonical skills in a category"""
        return list(self.taxonomy.get(category, {}).keys())
    
    def get_all_categories(self) -> List[str]:
        """Get all skill categories"""
        return list(self.taxonomy.keys())
    
    def normalize_skill(self, skill: str) -> str:
        """Normalize a skill to its canonical form"""
        match = self.match_skill(skill)
        return match.canonical_skill if match else skill
