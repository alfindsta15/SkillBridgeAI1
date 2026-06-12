import os
import logging
import warnings
import pandas as pd
import numpy as np
import json
import math
from sklearn.metrics.pairwise import cosine_similarity
from src.skill_extraction.skill_gap import normalize_skill_name

warnings.filterwarnings("ignore")
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN_WARNING"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
try:
    from huggingface_hub.utils import disable_progress_bars
    disable_progress_bars()
except ImportError:
    pass

logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
logging.getLogger("transformers").setLevel(logging.ERROR)

from sentence_transformers import SentenceTransformer


careers = pd.read_csv("data/processed/career_profiles.csv")
embeddings = np.load("data/embeddings/career_embeddings.npy")

with open("data/processed/career_skills.json", "r", encoding="utf-8") as f:
    career_skills_data = json.load(f)

career_skills_dict = {item["career"]: item["skills"] for item in career_skills_data}
valid_careers = {item["career"] for item in career_skills_data if len(item["skills"]) > 0}

mask = careers["career"].isin(valid_careers)
careers = careers[mask].reset_index(drop=True)
embeddings = embeddings[mask]

all_careers_count = len(career_skills_data)
skill_frequencies = {}
for item in career_skills_data:
    normalized_skills = {normalize_skill_name(s) for s in item["skills"]}
    for s in normalized_skills:
        skill_frequencies[s] = skill_frequencies.get(s, 0) + 1

skill_idf = {}
for s, freq in skill_frequencies.items():
    skill_idf[s] = math.log((1 + all_careers_count) / (1 + freq)) + 1.0

default_idf = math.log((1 + all_careers_count) / 1) + 1.0

_model = None

def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def recommend_career(user_skill_text: str, top_k: int = 5):
    user_skills_list = [s.strip() for s in user_skill_text.split(",") if s.strip()]
    normalized_user_skills = {normalize_skill_name(s) for s in user_skills_list}

    aligned_query = "The candidate is proficient and has skills in: " + ", ".join(user_skills_list) + "."
    user_embedding = get_model().encode([aligned_query])

    similarities = cosine_similarity(
        user_embedding,
        embeddings
    )[0]

    hybrid_recommendations = []

    SEMANTIC_WEIGHT = 0.5
    COVERAGE_WEIGHT = 0.5
    OVERLAP_BONUS = 15.0
    MAX_HYBRID_SCORE = 100.0

    for idx, row in careers.iterrows():
        career_name = row["career"]
        semantic_score = float(similarities[idx] * 100)

        career_skills = career_skills_dict.get(career_name, [])
        normalized_career_skills = {normalize_skill_name(s) for s in career_skills}

        matching_skills = normalized_user_skills.intersection(normalized_career_skills)
        overlap_count = len(matching_skills)

        match_idf_sum = sum(skill_idf.get(s, default_idf) for s in matching_skills)
        total_idf_sum = sum(skill_idf.get(s, default_idf) for s in normalized_career_skills)
        
        coverage_score = (match_idf_sum / total_idf_sum * 100.0) if total_idf_sum > 0 else 0.0

        raw_hybrid_score = (
            SEMANTIC_WEIGHT * semantic_score
            + COVERAGE_WEIGHT * coverage_score
            + overlap_count * OVERLAP_BONUS
        )
        hybrid_score = float(min(MAX_HYBRID_SCORE, raw_hybrid_score))

        display_matched = []
        for s in career_skills:
            if normalize_skill_name(s) in matching_skills:
                display_matched.append(s)

        if hybrid_score >= 75.0:
            suitability = "Sangat Cocok (High Suitability)"
        elif hybrid_score >= 50.0:
            suitability = "Cocok (Medium Suitability)"
        else:
            suitability = "Kurang Cocok (Low Suitability)"

        matched_str = ", ".join(display_matched) if display_matched else "tidak ada skill wajib yang cocok secara langsung"
        
        if overlap_count > 0:
            explain_text = (
                f"Direkomendasikan karena kecocokan semantik konteks sebesar {semantic_score:.1f}%, "
                f"serta kecocokan langsung pada {overlap_count} skill wajib: ({matched_str})."
            )
        else:
            explain_text = (
                f"Direkomendasikan murni berdasarkan kesamaan semantik profil latar belakang "
                f"sebesar {semantic_score:.1f}%."
            )

        hybrid_recommendations.append({
            "career": career_name,
            "score": hybrid_score,
            "semantic_score": semantic_score,
            "coverage_score": coverage_score,
            "overlap_count": overlap_count,
            "matched_skills": display_matched,
            "suitability": suitability,
            "explanation": explain_text
        })

    hybrid_recommendations = sorted(hybrid_recommendations, key=lambda x: x["score"], reverse=True)

    recommendations = []
    for item in hybrid_recommendations[:top_k]:
        recommendations.append({
            "career": item["career"],
            "score": float(item["score"]),
            "suitability": item["suitability"],
            "matched_skills": item["matched_skills"],
            "explanation": item["explanation"]
        })

    return {
        "success": True,
        "recommendations": recommendations
    }