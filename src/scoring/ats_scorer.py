"""ATS scoring algorithm"""

import re
from dataclasses import dataclass
from typing import List, Set, Dict
from ..matching.evidence_retriever import Evidence, MatchStatus


@dataclass
class ScoreBreakdown:
    """Breakdown of ATS score components"""
    coverage: float  # 0-1
    explicitness: float  # 0-1
    role_alignment: float  # 0-1
    keywords: float  # 0-1
    writing_quality: float  # 0-1


@dataclass
class ATSScore:
    """Complete ATS score with breakdown"""
    overall_score: int  # 0-100
    breakdown: ScoreBreakdown
    explanation: str


class ATSScorer:
    """Calculate ATS score for resume-JD match"""
    
    def __init__(
        self,
        coverage_weight: float = 0.35,
        explicitness_weight: float = 0.25,
        role_alignment_weight: float = 0.15,
        keywords_weight: float = 0.15,
        writing_quality_weight: float = 0.10
    ):
        """
        Initialize ATS scorer
        
        Args:
            coverage_weight: Weight for must-have skills coverage
            explicitness_weight: Weight for explicit skill mentions
            role_alignment_weight: Weight for role title alignment
            keywords_weight: Weight for keyword matching
            writing_quality_weight: Weight for writing quality
        """
        self.weights = {
            'coverage': coverage_weight,
            'explicitness': explicitness_weight,
            'role_alignment': role_alignment_weight,
            'keywords': keywords_weight,
            'writing_quality': writing_quality_weight
        }
        
        # Validate weights sum to 1.0
        total = sum(self.weights.values())
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0, got {total}")
    
    def calculate_score(
        self,
        must_have_skills: Set[str],
        preferred_skills: Set[str],
        evidence_list: List[Evidence],
        resume_skills: Set[str],
        resume_bullets: List[str],
        jd_title: str,
        resume_title: str,
        jd_keywords: Set[str]
    ) -> ATSScore:
        """
        Calculate comprehensive ATS score
        
        Args:
            must_have_skills: Required skills from JD
            preferred_skills: Preferred skills from JD
            evidence_list: Evidence matches for requirements
            resume_skills: Skills mentioned in resume
            resume_bullets: All resume bullets
            jd_title: Job title from JD
            resume_title: Current/target title from resume
            jd_keywords: Important keywords from JD
            
        Returns:
            ATSScore object
        """
        # Calculate each component
        coverage = self._calculate_coverage(must_have_skills, evidence_list)
        explicitness = self._calculate_explicitness(must_have_skills, resume_skills)
        role_alignment = self._calculate_role_alignment(jd_title, resume_title)
        keywords = self._calculate_keyword_match(jd_keywords, resume_skills, resume_bullets)
        writing_quality = self._calculate_writing_quality(resume_bullets)
        
        # Calculate weighted overall score
        overall = (
            self.weights['coverage'] * coverage +
            self.weights['explicitness'] * explicitness +
            self.weights['role_alignment'] * role_alignment +
            self.weights['keywords'] * keywords +
            self.weights['writing_quality'] * writing_quality
        )
        
        # Scale to 0-100
        overall_score = int(overall * 100)
        
        # Create breakdown
        breakdown = ScoreBreakdown(
            coverage=coverage,
            explicitness=explicitness,
            role_alignment=role_alignment,
            keywords=keywords,
            writing_quality=writing_quality
        )
        
        # Generate explanation
        explanation = self._generate_explanation(breakdown, overall_score)
        
        return ATSScore(
            overall_score=overall_score,
            breakdown=breakdown,
            explanation=explanation
        )
    
    def _calculate_coverage(
        self,
        must_have_skills: Set[str],
        evidence_list: List[Evidence]
    ) -> float:
        """
        Calculate coverage of must-have skills
        
        Returns: 0-1 score
        """
        if not must_have_skills:
            return 1.0
        
        # Count how many must-haves are present or weak
        covered = 0
        for evidence in evidence_list:
            if evidence.match_status in [MatchStatus.PRESENT, MatchStatus.WEAK]:
                covered += 1
        
        # Coverage = (present + weak) / total must-haves
        coverage = covered / len(must_have_skills) if must_have_skills else 1.0
        
        return min(1.0, coverage)
    
    def _calculate_explicitness(
        self,
        must_have_skills: Set[str],
        resume_skills: Set[str]
    ) -> float:
        """
        Calculate how many must-haves are explicitly named
        
        Returns: 0-1 score
        """
        if not must_have_skills:
            return 1.0
        
        # Count exact matches (case-insensitive)
        resume_skills_lower = {s.lower() for s in resume_skills}
        explicit_matches = sum(
            1 for skill in must_have_skills
            if skill.lower() in resume_skills_lower
        )
        
        explicitness = explicit_matches / len(must_have_skills)
        
        return min(1.0, explicitness)
    
    def _calculate_role_alignment(
        self,
        jd_title: str,
        resume_title: str
    ) -> float:
        """
        Calculate alignment between JD title and resume title
        
        Returns: 0-1 score
        """
        if not jd_title or not resume_title:
            return 0.5  # Neutral if missing
        
        jd_lower = jd_title.lower()
        resume_lower = resume_title.lower()
        
        # Exact match
        if jd_lower == resume_lower:
            return 1.0
        
        # Extract key role words
        role_keywords = [
            'data scientist', 'ml engineer', 'machine learning',
            'software engineer', 'analyst', 'engineer', 'scientist',
            'developer', 'architect', 'manager', 'lead', 'senior',
            'junior', 'staff', 'principal'
        ]
        
        # Check for common role keywords
        jd_roles = [kw for kw in role_keywords if kw in jd_lower]
        resume_roles = [kw for kw in role_keywords if kw in resume_lower]
        
        if not jd_roles:
            return 0.5
        
        # Calculate overlap
        overlap = len(set(jd_roles) & set(resume_roles))
        alignment = overlap / len(jd_roles) if jd_roles else 0.5
        
        return min(1.0, alignment)
    
    def _calculate_keyword_match(
        self,
        jd_keywords: Set[str],
        resume_skills: Set[str],
        resume_bullets: List[str]
    ) -> float:
        """
        Calculate keyword matching (tools, platforms, technologies)
        
        Returns: 0-1 score
        """
        if not jd_keywords:
            return 1.0
        
        # Combine resume skills and extract from bullets
        resume_text = ' '.join(resume_bullets).lower()
        resume_skills_lower = {s.lower() for s in resume_skills}
        
        # Count keyword matches
        matches = 0
        for keyword in jd_keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in resume_skills_lower or keyword_lower in resume_text:
                matches += 1
        
        keyword_score = matches / len(jd_keywords) if jd_keywords else 1.0
        
        return min(1.0, keyword_score)
    
    def _calculate_writing_quality(self, resume_bullets: List[str]) -> float:
        """
        Calculate writing quality heuristics
        
        Checks:
        - Bullet length (≤28 words ideal)
        - Starts with action verb
        - Contains numbers/metrics
        
        Returns: 0-1 score
        """
        if not resume_bullets:
            return 0.5
        
        scores = []
        
        action_verbs = {
            'led', 'built', 'developed', 'created', 'designed', 'implemented',
            'improved', 'optimized', 'analyzed', 'managed', 'drove', 'increased',
            'reduced', 'launched', 'established', 'automated', 'trained', 'deployed'
        }
        
        for bullet in resume_bullets:
            bullet_score = 0.0
            
            # Check length (max 28 words)
            word_count = len(bullet.split())
            if word_count <= 28:
                bullet_score += 0.33
            elif word_count <= 35:
                bullet_score += 0.20
            
            # Check for action verb
            first_word = bullet.split()[0].lower() if bullet.split() else ''
            if first_word in action_verbs:
                bullet_score += 0.33
            
            # Check for numbers/metrics
            if re.search(r'\d+', bullet):
                bullet_score += 0.34
            
            scores.append(bullet_score)
        
        # Average across all bullets
        avg_score = sum(scores) / len(scores) if scores else 0.5
        
        return min(1.0, avg_score)
    
    def _generate_explanation(
        self,
        breakdown: ScoreBreakdown,
        overall_score: int
    ) -> str:
        """Generate human-readable explanation of score"""
        
        explanations = []
        
        # Overall assessment
        if overall_score >= 80:
            explanations.append("Strong match for this role.")
        elif overall_score >= 60:
            explanations.append("Good match with room for improvement.")
        else:
            explanations.append("Significant gaps to address.")
        
        # Coverage
        if breakdown.coverage < 0.7:
            explanations.append(f"Coverage: {breakdown.coverage:.0%} - Missing key required skills.")
        elif breakdown.coverage < 0.9:
            explanations.append(f"Coverage: {breakdown.coverage:.0%} - Most requirements covered.")
        else:
            explanations.append(f"Coverage: {breakdown.coverage:.0%} - Excellent coverage.")
        
        # Explicitness
        if breakdown.explicitness < 0.6:
            explanations.append(f"Explicitness: {breakdown.explicitness:.0%} - Need to name skills more explicitly.")
        
        # Role alignment
        if breakdown.role_alignment < 0.5:
            explanations.append(f"Role alignment: {breakdown.role_alignment:.0%} - Title mismatch with target role.")
        
        # Keywords
        if breakdown.keywords < 0.6:
            explanations.append(f"Keywords: {breakdown.keywords:.0%} - Missing important technical keywords.")
        
        # Writing quality
        if breakdown.writing_quality < 0.7:
            explanations.append(f"Writing: {breakdown.writing_quality:.0%} - Improve bullet structure and metrics.")
        
        return " ".join(explanations)
    
    def estimate_score_gain(
        self,
        current_score: ATSScore,
        improvement_type: str
    ) -> int:
        """
        Estimate score gain from a specific improvement
        
        Args:
            current_score: Current ATS score
            improvement_type: Type of improvement (coverage, explicitness, etc.)
            
        Returns:
            Estimated score gain (0-100 scale)
        """
        breakdown = current_score.breakdown
        
        # Calculate potential gain based on current weakness
        if improvement_type == 'coverage':
            gap = 1.0 - breakdown.coverage
            potential_gain = gap * self.weights['coverage'] * 100
        elif improvement_type == 'explicitness':
            gap = 1.0 - breakdown.explicitness
            potential_gain = gap * self.weights['explicitness'] * 100
        elif improvement_type == 'keywords':
            gap = 1.0 - breakdown.keywords
            potential_gain = gap * self.weights['keywords'] * 100
        elif improvement_type == 'writing':
            gap = 1.0 - breakdown.writing_quality
            potential_gain = gap * self.weights['writing_quality'] * 100
        else:
            potential_gain = 5  # Default
        
        # Assume improvement addresses ~20% of the gap
        estimated_gain = int(potential_gain * 0.2)
        
        return max(1, min(15, estimated_gain))  # Cap between 1-15 points
