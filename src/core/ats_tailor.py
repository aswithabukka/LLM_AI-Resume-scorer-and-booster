"""Main ATS-Tailor orchestrator"""

from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
from pathlib import Path

from ..parsers import DocumentParser, ParsedDocument
from ..extractors import ResumeSectionizer, JDExtractor, JobRequirement, SectionType
from ..matching import SkillsMatcher, EvidenceRetriever, Evidence, MatchStatus
from ..generation import SuggestionGenerator, Suggestion, SuggestionType
from ..scoring import ATSScorer, ATSScore


@dataclass
class RequirementMatch:
    """Match result for a single requirement"""
    requirement: str
    requirement_type: str
    skills: List[str]
    status: str
    evidence: Optional[str]
    confidence: float
    suggested_edit_target: Optional[str] = None


@dataclass
class TailorResult:
    """Complete result from ATS-Tailor analysis"""
    overall_score: int
    breakdown: Dict[str, float]
    must_haves: List[RequirementMatch]
    top_edits: List[Dict]
    skills_insertions: List[str]
    summary_suggestion: Optional[str]
    explanation: str


class ATSTailor:
    """Main orchestrator for resume tailoring"""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize ATS-Tailor
        
        Args:
            config: Configuration dictionary (optional)
        """
        config = config or {}
        
        # Initialize components
        self.parser = DocumentParser()
        self.sectionizer = ResumeSectionizer()
        self.skills_matcher = SkillsMatcher()
        self.jd_extractor = JDExtractor(skills_taxonomy=self.skills_matcher.taxonomy)
        
        # Evidence retriever (embeddings)
        self.evidence_retriever = EvidenceRetriever(
            model_name=config.get('embedding_model', 'BAAI/bge-large-en-v1.5'),
            tau_high=config.get('tau_high', 0.75),
            tau_low=config.get('tau_low', 0.50),
            top_k=config.get('top_k', 5)
        )
        
        # Suggestion generator (LLM)
        self.suggestion_generator = SuggestionGenerator(
            llm_backend=config.get('llm_backend', 'ollama'),
            model_name=config.get('llm_model', 'llama3.1:8b'),
            temperature=config.get('temperature', 0.3)
        )
        
        # ATS scorer
        self.scorer = ATSScorer(
            coverage_weight=config.get('coverage_weight', 0.35),
            explicitness_weight=config.get('explicitness_weight', 0.25),
            role_alignment_weight=config.get('role_alignment_weight', 0.15),
            keywords_weight=config.get('keywords_weight', 0.15),
            writing_quality_weight=config.get('writing_quality_weight', 0.10)
        )
    
    def analyze(
        self,
        resume_path: Optional[str] = None,
        resume_text: Optional[str] = None,
        jd_text: str = None,
        jd_path: Optional[str] = None
    ) -> TailorResult:
        """
        Analyze resume against job description
        
        Args:
            resume_path: Path to resume file (PDF/DOCX)
            resume_text: Raw resume text (alternative to file)
            jd_text: Job description text
            jd_path: Path to JD file (alternative to text)
            
        Returns:
            TailorResult with analysis and suggestions
        """
        # Step 1: Parse documents
        if resume_path:
            resume_doc = self.parser.parse(resume_path)
        elif resume_text:
            resume_doc = self.parser.parse_text(resume_text, "resume")
        else:
            raise ValueError("Must provide either resume_path or resume_text")
        
        if jd_path:
            jd_doc = self.parser.parse(jd_path)
            jd_text = jd_doc.text
        elif not jd_text:
            raise ValueError("Must provide either jd_path or jd_text")
        
        # Step 2: Extract structure
        resume_sections = self.sectionizer.sectionize(resume_doc.text)
        jd_requirements = self.jd_extractor.extract_requirements(jd_text)
        
        # Step 3: Extract skills
        resume_skills = set()
        for section in resume_sections:
            skill_matches = self.skills_matcher.extract_skills_from_text(section.content)
            resume_skills.update([m.canonical_skill for m in skill_matches])
        
        must_have_skills = self.jd_extractor.get_must_have_skills(jd_requirements)
        preferred_skills = self.jd_extractor.get_preferred_skills(jd_requirements)
        
        # Step 4: Index resume for evidence retrieval
        resume_bullets = self._extract_all_bullets(resume_sections)
        indexed_sections = self._prepare_resume_for_indexing(resume_sections)
        self.evidence_retriever.index_resume(indexed_sections)
        
        # Step 5: Match requirements to evidence
        evidence_list = []
        requirement_matches = []
        
        for req in jd_requirements:
            if req.requirement_type.value == 'must_have':
                evidence = self.evidence_retriever.retrieve_evidence(
                    requirement=req.text,
                    requirement_skills=req.skills
                )
                evidence_list.append(evidence)
                
                requirement_matches.append(RequirementMatch(
                    requirement=req.text,
                    requirement_type=req.requirement_type.value,
                    skills=req.skills,
                    status=evidence.match_status.value,
                    evidence=evidence.resume_text if evidence.match_status != MatchStatus.MISSING else None,
                    confidence=evidence.similarity_score,
                    suggested_edit_target=f"{evidence.section} > bullet {evidence.bullet_index}" if evidence.bullet_index else evidence.section
                ))
        
        # Step 6: Calculate ATS score
        jd_title = self.jd_extractor.extract_job_title(jd_text) or "Target Role"
        resume_title = self._extract_resume_title(resume_sections)
        jd_keywords = must_have_skills | preferred_skills
        
        ats_score = self.scorer.calculate_score(
            must_have_skills=must_have_skills,
            preferred_skills=preferred_skills,
            evidence_list=evidence_list,
            resume_skills=resume_skills,
            resume_bullets=resume_bullets,
            jd_title=jd_title,
            resume_title=resume_title,
            jd_keywords=jd_keywords
        )
        
        # Step 7: Generate suggestions
        suggestions = self._generate_suggestions(
            requirement_matches=requirement_matches,
            resume_sections=resume_sections,
            must_have_skills=must_have_skills,
            resume_skills=resume_skills,
            ats_score=ats_score
        )
        
        # Step 8: Compile results
        result = self._compile_result(
            ats_score=ats_score,
            requirement_matches=requirement_matches,
            suggestions=suggestions,
            must_have_skills=must_have_skills,
            resume_skills=resume_skills,
            jd_title=jd_title,
            resume_sections=resume_sections
        )
        
        return result
    
    def _extract_all_bullets(self, sections: List) -> List[str]:
        """Extract all bullets from resume sections"""
        bullets = []
        for section in sections:
            bullets.extend(section.bullets)
        return bullets
    
    def _prepare_resume_for_indexing(self, sections: List) -> List[Dict]:
        """Prepare resume sections for embedding indexing"""
        indexed = []
        
        for section in sections:
            # Index each bullet separately
            for i, bullet in enumerate(section.bullets):
                indexed.append({
                    'text': bullet,
                    'section': section.title,
                    'bullet_index': i
                })
            
            # Also index section content as a whole
            if section.content and not section.bullets:
                indexed.append({
                    'text': section.content,
                    'section': section.title,
                    'bullet_index': None
                })
        
        return indexed
    
    def _extract_resume_title(self, sections: List) -> str:
        """Extract current job title from resume"""
        for section in sections:
            if section.section_type == SectionType.EXPERIENCE:
                # Extract from first experience entry
                lines = section.content.split('\n')
                for line in lines[:5]:
                    if line.strip() and len(line.strip()) > 5:
                        return line.strip()
        
        return "Professional"
    
    def _generate_suggestions(
        self,
        requirement_matches: List[RequirementMatch],
        resume_sections: List,
        must_have_skills: set,
        resume_skills: set,
        ats_score: ATSScore
    ) -> List[Suggestion]:
        """Generate actionable suggestions"""
        suggestions = []
        
        # Generate bullet rewrites for weak/missing requirements
        for match in requirement_matches:
            if match.status in ['weak', 'missing']:
                # Higher score gain for missing, lower for weak
                score_gain = self.scorer.estimate_score_gain(ats_score, 'coverage' if match.status == 'missing' else 'explicitness')
                
                # Generate rewrite suggestion
                suggestion = self.suggestion_generator.create_suggestion(
                    suggestion_type=SuggestionType.BULLET_REWRITE,
                    target_section=match.suggested_edit_target.split('>')[0].strip() if match.suggested_edit_target else "Experience",
                    target_location=match.suggested_edit_target or "Experience > bullet",
                    current_text=match.evidence or "Add new bullet point",
                    suggested_text=self.suggestion_generator.generate_bullet_rewrite(
                        current_bullet=match.evidence or "Worked on relevant projects",
                        jd_requirement=match.requirement,
                        requirement_skills=match.skills
                    ),
                    reason=f"JD requires: {match.requirement}",
                    jd_requirement=match.requirement,
                    estimated_score_gain=score_gain
                )
                suggestions.append(suggestion)
        
        # Generate skill insertions for missing skills
        missing_skills = must_have_skills - resume_skills
        if missing_skills:
            skills_section = next((s for s in resume_sections if s.section_type == SectionType.SKILLS), None)
            if skills_section:
                suggestion = self.suggestion_generator.create_suggestion(
                    suggestion_type=SuggestionType.SKILL_INSERTION,
                    target_section="Skills",
                    target_location="Skills section",
                    current_text=skills_section.content,
                    suggested_text=self.suggestion_generator.generate_skill_insertions(
                        missing_skills=list(missing_skills),
                        current_skills_section=skills_section.content
                    ),
                    reason="Add missing must-have skills",
                    jd_requirement="Multiple requirements",
                    estimated_score_gain=self.scorer.estimate_score_gain(ats_score, 'coverage')
                )
                suggestions.append(suggestion)
        
        # Sort by estimated score gain
        suggestions.sort(key=lambda s: s.estimated_score_gain, reverse=True)
        
        return suggestions[:20]  # Top 20 (increased from 10)
    
    def _compile_result(
        self,
        ats_score: ATSScore,
        requirement_matches: List[RequirementMatch],
        suggestions: List[Suggestion],
        must_have_skills: set,
        resume_skills: set,
        jd_title: str,
        resume_sections: List
    ) -> TailorResult:
        """Compile final result"""
        
        # Convert suggestions to dict format
        top_edits = []
        for sugg in suggestions:
            top_edits.append({
                'target': sugg.target_location,
                'current': sugg.current_text,
                'suggested': sugg.suggested_text,
                'reason': sugg.reason,
                'est_score_gain': sugg.estimated_score_gain
            })
        
        # Skills to insert
        missing_skills = list(must_have_skills - resume_skills)
        
        # Generate summary suggestion
        summary_section = next((s for s in resume_sections if s.section_type == SectionType.SUMMARY), None)
        summary_suggestion = None
        if summary_section:
            summary_suggestion = self.suggestion_generator.generate_summary_update(
                current_summary=summary_section.content,
                job_title=jd_title,
                key_skills=list(must_have_skills)[:5]
            )
        
        return TailorResult(
            overall_score=ats_score.overall_score,
            breakdown={
                'coverage': ats_score.breakdown.coverage,
                'explicitness': ats_score.breakdown.explicitness,
                'role_alignment': ats_score.breakdown.role_alignment,
                'keywords': ats_score.breakdown.keywords,
                'writing': ats_score.breakdown.writing_quality
            },
            must_haves=[asdict(m) for m in requirement_matches],
            top_edits=top_edits,
            skills_insertions=missing_skills[:10],
            summary_suggestion=summary_suggestion,
            explanation=ats_score.explanation
        )
