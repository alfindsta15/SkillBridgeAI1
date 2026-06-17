from typing import List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core_logic import (
    analyze_user,
    get_recommendations,
    get_skill_gap,
    get_roadmap
)

app = FastAPI(
    title="SkillBridgeAI API",
    description="Career Recommendation, Skill Gap Analysis, Match Scoring, and Learning Roadmap",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    skills: str
    selected_career: Optional[str] = None
    top_k: int = 5


class RecommendationRequest(BaseModel):
    skills: str
    top_k: int = 5


class SkillGapRequest(BaseModel):
    skills: str
    target_career: str


class RoadmapRequest(BaseModel):
    skills: str
    target_career: str
    missing_skills: List[str]


@app.get("/")
def root():
    return {
        "success": True,
        "message": "SkillBridgeAI API Running",
        "version": "1.0.0"
    }


@app.get("/health")
def health():
    return {
        "success": True,
        "status": "healthy"
    }


@app.post("/analyze")
def analyze(req: AnalyzeRequest):

    return analyze_user(
        user_skill_text=req.skills,
        selected_career=req.selected_career,
        top_k=req.top_k
    )


@app.post("/recommend")
def recommend(req: RecommendationRequest):

    return get_recommendations(
        user_skill_text=req.skills,
        top_k=req.top_k
    )


@app.post("/skill-gap")
def skill_gap(req: SkillGapRequest):

    return get_skill_gap(
        user_skill_text=req.skills,
        target_career=req.target_career
    )


@app.post("/roadmap")
def roadmap(req: RoadmapRequest):

    return get_roadmap(
        user_skill_text=req.skills,
        target_career=req.target_career,
        missing_skills=req.missing_skills
    )
