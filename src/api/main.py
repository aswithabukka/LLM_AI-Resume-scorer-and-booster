"""FastAPI backend for ATS-Tailor"""

import tempfile
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ..core import ATSTailor, TailorResult


app = FastAPI(
    title="ATS-Tailor API",
    description="Resume optimization API",
    version="0.1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global tailor instance
tailor = None


@app.on_event("startup")
async def startup_event():
    """Initialize ATS-Tailor on startup"""
    global tailor
    tailor = ATSTailor()


class AnalyzeRequest(BaseModel):
    """Request model for text-based analysis"""
    resume_text: str
    jd_text: str


class AnalyzeResponse(BaseModel):
    """Response model"""
    success: bool
    result: Optional[dict] = None
    error: Optional[str] = None


@app.get("/")
async def root():
    """Health check"""
    return {"status": "ok", "service": "ATS-Tailor API"}


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_text(request: AnalyzeRequest):
    """
    Analyze resume and JD from text input
    
    Args:
        request: AnalyzeRequest with resume_text and jd_text
        
    Returns:
        AnalyzeResponse with results
    """
    try:
        result = tailor.analyze(
            resume_text=request.resume_text,
            jd_text=request.jd_text
        )
        
        return AnalyzeResponse(
            success=True,
            result=result.__dict__
        )
    except Exception as e:
        return AnalyzeResponse(
            success=False,
            error=str(e)
        )


@app.post("/analyze/upload", response_model=AnalyzeResponse)
async def analyze_upload(
    resume_file: UploadFile = File(...),
    jd_text: str = Form(...)
):
    """
    Analyze resume from uploaded file and JD from text
    
    Args:
        resume_file: Uploaded resume file (PDF/DOCX)
        jd_text: Job description text
        
    Returns:
        AnalyzeResponse with results
    """
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(resume_file.filename).suffix) as tmp:
            content = await resume_file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        # Analyze
        result = tailor.analyze(
            resume_path=tmp_path,
            jd_text=jd_text
        )
        
        # Clean up
        Path(tmp_path).unlink()
        
        return AnalyzeResponse(
            success=True,
            result=result.__dict__
        )
    except Exception as e:
        return AnalyzeResponse(
            success=False,
            error=str(e)
        )


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "tailor_initialized": tailor is not None
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
