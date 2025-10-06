"""Generate resume suggestions using local LLM"""

import json
from dataclasses import dataclass
from typing import List, Optional, Dict
from enum import Enum
from pathlib import Path

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


class SuggestionType(Enum):
    """Type of suggestion"""
    BULLET_REWRITE = "bullet_rewrite"
    SKILL_INSERTION = "skill_insertion"
    SUMMARY_UPDATE = "summary_update"
    KEYWORD_ADD = "keyword_add"


@dataclass
class Suggestion:
    """A resume improvement suggestion"""
    suggestion_type: SuggestionType
    target_section: str
    target_location: str  # e.g., "Experience > Company X > bullet 2"
    current_text: Optional[str]
    suggested_text: str
    reason: str
    jd_requirement: str
    estimated_score_gain: int


class SuggestionGenerator:
    """Generate actionable resume suggestions using LLM"""
    
    def __init__(
        self,
        llm_backend: str = "ollama",
        model_name: str = "llama3.1:8b",
        temperature: float = 0.3,
        max_tokens: int = 150
    ):
        """
        Initialize suggestion generator
        
        Args:
            llm_backend: LLM backend (ollama, openai, etc.)
            model_name: Model name
            temperature: Generation temperature
            max_tokens: Max tokens to generate
        """
        self.llm_backend = llm_backend
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Load action verbs
        verbs_path = Path(__file__).parent.parent.parent / "data" / "action_verbs.json"
        with open(verbs_path, 'r') as f:
            self.action_verbs = json.load(f)
        
        if llm_backend == "ollama" and not OLLAMA_AVAILABLE:
            raise ImportError("ollama package not installed. Run: pip install ollama")
    
    def generate_bullet_rewrite(
        self,
        current_bullet: str,
        jd_requirement: str,
        requirement_skills: List[str],
        context_facts: List[str] = None
    ) -> str:
        """
        Generate a rewritten bullet that addresses JD requirement
        
        Args:
            current_bullet: Current resume bullet
            jd_requirement: JD requirement to address
            requirement_skills: Skills mentioned in requirement
            context_facts: Additional context facts
            
        Returns:
            Rewritten bullet text
        """
        # Build prompt
        prompt = self._build_bullet_rewrite_prompt(
            current_bullet,
            jd_requirement,
            requirement_skills,
            context_facts or []
        )
        
        # Generate
        response = self._call_llm(prompt)
        
        # Clean up response
        rewritten = self._extract_bullet_from_response(response)
        
        return rewritten
    
    def generate_skill_insertions(
        self,
        missing_skills: List[str],
        current_skills_section: str
    ) -> str:
        """
        Generate updated skills section with missing skills
        
        Args:
            missing_skills: Skills to add
            current_skills_section: Current skills section text
            
        Returns:
            Updated skills section
        """
        # Simple insertion - just add to existing
        skills_to_add = [s for s in missing_skills if s.lower() not in current_skills_section.lower()]
        
        if not skills_to_add:
            return current_skills_section
        
        # Add to end
        updated = current_skills_section.strip()
        if updated and not updated.endswith(','):
            updated += ","
        
        updated += " " + ", ".join(skills_to_add)
        
        return updated
    
    def generate_summary_update(
        self,
        current_summary: str,
        job_title: str,
        key_skills: List[str],
        years_experience: Optional[int] = None
    ) -> str:
        """
        Generate updated summary that aligns with JD
        
        Args:
            current_summary: Current summary text
            job_title: Target job title
            key_skills: Key skills to highlight
            years_experience: Years of experience
            
        Returns:
            Updated summary
        """
        prompt = f"""Rewrite this professional summary to align with a {job_title} role.

Current summary: {current_summary}

Requirements:
- Highlight these key skills: {', '.join(key_skills[:5])}
{f"- Mention {years_experience}+ years of experience" if years_experience else ""}
- Keep it to 2-3 sentences
- Be specific and quantified where possible
- Stay truthful to the original content

Rewritten summary:"""
        
        response = self._call_llm(prompt)
        
        return response.strip()
    
    def _build_bullet_rewrite_prompt(
        self,
        current_bullet: str,
        jd_requirement: str,
        requirement_skills: List[str],
        context_facts: List[str]
    ) -> str:
        """Build prompt for bullet rewriting"""
        
        # Select relevant action verbs
        action_verbs = self._select_action_verbs(jd_requirement)
        
        prompt = f"""You are a resume optimization expert. Rewrite the following resume bullet to better match a job requirement.

JD Requirement: "{jd_requirement}"
Key skills to highlight: {', '.join(requirement_skills)}

Current bullet: "{current_bullet}"

{f"Additional context: {'; '.join(context_facts)}" if context_facts else ""}

Guidelines:
1. Keep it to ONE line (max 28 words)
2. Start with a strong action verb (suggestions: {', '.join(action_verbs[:5])})
3. Include specific skills from the requirement if truthful
4. Add quantified impact if possible (%, $, time saved, etc.)
5. DO NOT invent facts - only enhance what's already there
6. Make the connection to the JD requirement explicit

Rewritten bullet (one line only):"""
        
        return prompt
    
    def _select_action_verbs(self, requirement: str) -> List[str]:
        """Select relevant action verbs based on requirement"""
        req_lower = requirement.lower()
        
        # Map keywords to verb categories
        if any(word in req_lower for word in ['build', 'develop', 'create', 'design']):
            return self.action_verbs['creation']
        elif any(word in req_lower for word in ['lead', 'manage', 'mentor']):
            return self.action_verbs['leadership']
        elif any(word in req_lower for word in ['improve', 'optimize', 'enhance']):
            return self.action_verbs['improvement']
        elif any(word in req_lower for word in ['analyze', 'evaluate', 'research']):
            return self.action_verbs['analysis']
        elif any(word in req_lower for word in ['automate', 'script', 'pipeline']):
            return self.action_verbs['automation']
        elif any(word in req_lower for word in ['model', 'predict', 'train', 'ml', 'machine learning']):
            return self.action_verbs['data_science']
        else:
            return self.action_verbs['creation']
    
    def _call_llm(self, prompt: str) -> str:
        """Call LLM backend"""
        if self.llm_backend == "ollama":
            return self._call_ollama(prompt)
        elif self.llm_backend == "openai":
            return self._call_openai(prompt)
        elif self.llm_backend == "anthropic":
            return self._call_anthropic(prompt)
        elif self.llm_backend == "gemini":
            return self._call_gemini(prompt)
        else:
            raise ValueError(f"Unsupported LLM backend: {self.llm_backend}")
    
    def _call_ollama(self, prompt: str) -> str:
        """Call Ollama API"""
        try:
            response = ollama.generate(
                model=self.model_name,
                prompt=prompt,
                options={
                    'temperature': self.temperature,
                    'num_predict': self.max_tokens,
                }
            )
            return response['response'].strip()
        except Exception as e:
            # Fallback to simple template if LLM fails
            return f"[LLM Error: {e}] Unable to generate suggestion"
    
    def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API"""
        try:
            if not OPENAI_AVAILABLE:
                return "[Error] OpenAI package not installed. Run: pip install openai"
            
            client = openai.OpenAI()  # Reads OPENAI_API_KEY from environment
            response = client.chat.completions.create(
                model=self.model_name,  # e.g., "gpt-4o" or "gpt-4-turbo"
                messages=[
                    {"role": "system", "content": "You are a professional resume writer. Provide only the rewritten bullet point, nothing else."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"[OpenAI Error: {e}] Unable to generate suggestion"
    
    def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic Claude API"""
        try:
            if not ANTHROPIC_AVAILABLE:
                return "[Error] Anthropic package not installed. Run: pip install anthropic"
            
            import os
            if not os.environ.get('ANTHROPIC_API_KEY'):
                return "[Error] ANTHROPIC_API_KEY not set. Please add your API key in the UI sidebar."
            
            client = anthropic.Anthropic()  # Reads ANTHROPIC_API_KEY from environment
            message = client.messages.create(
                model=self.model_name,  # e.g., "claude-3-5-sonnet-20241022"
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system="You are a professional resume writer. Provide only the rewritten bullet point, nothing else.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return message.content[0].text.strip()
        except Exception as e:
            error_msg = str(e)
            if "credit" in error_msg.lower() or "balance" in error_msg.lower():
                return "[Error] Anthropic API has no credits. Please add credits or switch to Ollama (free)."
            return f"[Anthropic Error: {error_msg[:100]}] Switch to Ollama for free local inference."
    
    def _call_gemini(self, prompt: str) -> str:
        """Call Google Gemini API"""
        try:
            if not GEMINI_AVAILABLE:
                return "[Error] Google AI package not installed. Run: pip install google-generativeai"
            
            # Configure with API key from environment
            import os
            genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))
            
            model = genai.GenerativeModel(
                model_name=self.model_name,  # e.g., "gemini-2.0-flash-exp"
                generation_config={
                    "temperature": self.temperature,
                    "max_output_tokens": self.max_tokens,
                }
            )
            
            full_prompt = f"You are a professional resume writer. Provide only the rewritten bullet point, nothing else.\n\n{prompt}"
            response = model.generate_content(full_prompt)
            return response.text.strip()
        except Exception as e:
            return f"[Gemini Error: {e}] Unable to generate suggestion"
    
    def _extract_bullet_from_response(self, response: str) -> str:
        """Extract clean bullet from LLM response"""
        # Remove common prefixes
        response = response.strip()
        
        # Remove meta-text like "Here is a rewritten bullet..."
        meta_phrases = [
            "here is a rewritten bullet",
            "here's a rewritten bullet",
            "rewritten bullet:",
            "here is the rewritten",
            "here's the rewritten",
            "revised bullet:",
            "updated bullet:",
            "that meets the guidelines:",
        ]
        
        response_lower = response.lower()
        for phrase in meta_phrases:
            if phrase in response_lower:
                # Find where the actual content starts
                idx = response_lower.find(phrase)
                # Skip past the phrase and any following punctuation/newlines
                response = response[idx + len(phrase):].strip()
                response = response.lstrip(':•-*+ \n')
                break
        
        # Remove bullet markers
        response = response.lstrip('•-*+ ')
        
        # Take first substantial line if multiple
        lines = [l.strip() for l in response.split('\n') if l.strip()]
        if lines:
            # Skip lines that are just meta-text
            for line in lines:
                if len(line) > 20 and not line.lower().startswith(('here', 'this', 'note')):
                    bullet = line
                    break
            else:
                bullet = lines[0]
        else:
            bullet = response
        
        # Remove quotes if present
        bullet = bullet.strip('"\'')
        
        # If still contains meta-text, return a fallback
        if 'guideline' in bullet.lower() or 'rewritten' in bullet.lower():
            return "[Generated suggestion - please review and customize]"
        
        return bullet
    
    def create_suggestion(
        self,
        suggestion_type: SuggestionType,
        target_section: str,
        target_location: str,
        current_text: Optional[str],
        suggested_text: str,
        reason: str,
        jd_requirement: str,
        estimated_score_gain: int = 5
    ) -> Suggestion:
        """Create a Suggestion object"""
        return Suggestion(
            suggestion_type=suggestion_type,
            target_section=target_section,
            target_location=target_location,
            current_text=current_text,
            suggested_text=suggested_text,
            reason=reason,
            jd_requirement=jd_requirement,
            estimated_score_gain=estimated_score_gain
        )
