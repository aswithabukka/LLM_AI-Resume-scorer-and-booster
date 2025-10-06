"""Evidence retrieval using embeddings and semantic search"""

import numpy as np
from dataclasses import dataclass
from typing import List, Optional, Tuple
from enum import Enum

from sentence_transformers import SentenceTransformer
import faiss


class MatchStatus(Enum):
    """Status of requirement match"""
    PRESENT = "present"
    WEAK = "weak"
    MISSING = "missing"


@dataclass
class Evidence:
    """Evidence for a requirement from resume"""
    requirement_text: str
    resume_text: str
    similarity_score: float
    match_status: MatchStatus
    section: str
    bullet_index: Optional[int] = None


class EvidenceRetriever:
    """Retrieve evidence from resume using semantic similarity"""
    
    def __init__(
        self,
        model_name: str = "BAAI/bge-large-en-v1.5",
        tau_high: float = 0.75,
        tau_low: float = 0.50,
        top_k: int = 5
    ):
        """
        Initialize evidence retriever
        
        Args:
            model_name: Sentence transformer model name
            tau_high: Threshold for PRESENT status
            tau_low: Threshold for WEAK status
            top_k: Number of top candidates to retrieve
        """
        self.model = SentenceTransformer(model_name)
        self.tau_high = tau_high
        self.tau_low = tau_low
        self.top_k = top_k
        
        self.resume_embeddings = None
        self.resume_texts = []
        self.resume_metadata = []
        self.index = None
    
    def index_resume(self, sections: List[dict]):
        """
        Create embeddings index for resume sections
        
        Args:
            sections: List of dicts with 'text', 'section', 'bullet_index'
        """
        self.resume_texts = [s['text'] for s in sections]
        self.resume_metadata = [
            {'section': s['section'], 'bullet_index': s.get('bullet_index')}
            for s in sections
        ]
        
        # Generate embeddings
        self.resume_embeddings = self.model.encode(
            self.resume_texts,
            normalize_embeddings=True,
            show_progress_bar=False
        )
        
        # Build FAISS index
        dimension = self.resume_embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)  # Inner product (cosine similarity)
        self.index.add(self.resume_embeddings.astype('float32'))
    
    def retrieve_evidence(
        self,
        requirement: str,
        requirement_skills: List[str] = None
    ) -> Evidence:
        """
        Retrieve best evidence for a requirement
        
        Args:
            requirement: Requirement text to match
            requirement_skills: List of skills mentioned in requirement
            
        Returns:
            Evidence object with best match
        """
        if self.index is None:
            raise ValueError("Resume not indexed. Call index_resume() first.")
        
        # Encode requirement
        req_embedding = self.model.encode(
            [requirement],
            normalize_embeddings=True,
            show_progress_bar=False
        )
        
        # Search for top-k matches
        scores, indices = self.index.search(
            req_embedding.astype('float32'),
            min(self.top_k, len(self.resume_texts))
        )
        
        # Get best match
        best_idx = indices[0][0]
        best_score = float(scores[0][0])
        
        # Determine match status
        if best_score >= self.tau_high:
            status = MatchStatus.PRESENT
        elif best_score >= self.tau_low:
            status = MatchStatus.WEAK
        else:
            status = MatchStatus.MISSING
        
        # Boost score if skills match
        if requirement_skills:
            resume_text_lower = self.resume_texts[best_idx].lower()
            skill_matches = sum(1 for skill in requirement_skills if skill.lower() in resume_text_lower)
            if skill_matches > 0:
                # Boost score slightly
                best_score = min(1.0, best_score + 0.05 * skill_matches)
                
                # Re-evaluate status with boosted score
                if best_score >= self.tau_high:
                    status = MatchStatus.PRESENT
                elif best_score >= self.tau_low:
                    status = MatchStatus.WEAK
        
        metadata = self.resume_metadata[best_idx]
        
        return Evidence(
            requirement_text=requirement,
            resume_text=self.resume_texts[best_idx],
            similarity_score=best_score,
            match_status=status,
            section=metadata['section'],
            bullet_index=metadata['bullet_index']
        )
    
    def retrieve_top_k_evidence(
        self,
        requirement: str,
        k: Optional[int] = None
    ) -> List[Tuple[str, float, dict]]:
        """
        Retrieve top-k evidence candidates
        
        Args:
            requirement: Requirement text
            k: Number of results (default: self.top_k)
            
        Returns:
            List of (text, score, metadata) tuples
        """
        if self.index is None:
            raise ValueError("Resume not indexed. Call index_resume() first.")
        
        k = k or self.top_k
        
        # Encode requirement
        req_embedding = self.model.encode(
            [requirement],
            normalize_embeddings=True,
            show_progress_bar=False
        )
        
        # Search
        scores, indices = self.index.search(
            req_embedding.astype('float32'),
            min(k, len(self.resume_texts))
        )
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            results.append((
                self.resume_texts[idx],
                float(score),
                self.resume_metadata[idx]
            ))
        
        return results
    
    def batch_retrieve_evidence(
        self,
        requirements: List[dict]
    ) -> List[Evidence]:
        """
        Retrieve evidence for multiple requirements
        
        Args:
            requirements: List of dicts with 'text' and optional 'skills'
            
        Returns:
            List of Evidence objects
        """
        evidence_list = []
        
        for req in requirements:
            evidence = self.retrieve_evidence(
                requirement=req['text'],
                requirement_skills=req.get('skills', [])
            )
            evidence_list.append(evidence)
        
        return evidence_list
    
    def compute_similarity(self, text1: str, text2: str) -> float:
        """
        Compute cosine similarity between two texts
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score (0-1)
        """
        embeddings = self.model.encode(
            [text1, text2],
            normalize_embeddings=True,
            show_progress_bar=False
        )
        
        # Cosine similarity (dot product of normalized vectors)
        similarity = float(np.dot(embeddings[0], embeddings[1]))
        
        return similarity
