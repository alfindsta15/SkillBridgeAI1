import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import re

data = pd.read_csv("data/processed/career_profiles.csv")
data

def clean_title(title):
    title = title.split("-")[0]

    title = re.sub(
        r"\b(entry level|entry-level|junior|senior|intern|trainee|fresher|experienced)\b",
        "",
        title,
        flags=re.IGNORECASE
    )

    title = re.sub(r"\s+", " ", title).strip()

    return title

data["Title_Clean"] = data["Title"].apply(clean_title)

data['Title_Clean'].unique()

data["job_text"] = (data["Title_Clean"].fillna("") + " " +
    data["Skills"].fillna("") + " " +
    data["Keywords"].fillna("") + " " +
    data["Responsibilities"].fillna(""))

model = SentenceTransformer("all-MiniLM-L6-v2") #SBERT

def analyze_selected_job(user_input_text, selected_job_title, data_df, model_encoder):

    user_input_text = user_input_text.lower()

    user_emb = model_encoder.encode([user_input_text])[0]

    job_row_df = data_df[data_df['Title_Clean'].str.lower() == selected_job_title.lower()]

    if job_row_df.empty:
        return {"error": f"Job '{selected_job_title}' not found in the dataset."}

    job_row = job_row_df.iloc[0]

    job_text = job_row["job_text"]
    job_emb = model_encoder.encode([job_text])[0]

    score = cosine_similarity([user_emb], [job_emb])[0][0]
    score_percent = round(float(score) * 100, 2)

    job_skills = set([
        s.strip().lower()
        for s in str(job_row["Skills"]).replace(";", ",").split(",") if s.strip()
    ])

    user_skills = set([
        s.strip().lower()
        for s in user_input_text.split(",") if s.strip()
    ])

    missing_skills = list(job_skills - user_skills)

    return {
        "job": selected_job_title,
        "match_score": f"{score_percent}%",
        "missing_skills": missing_skills
    }

user_input = "cms basics"

selected_job = "CopyWriter"

result = analyze_selected_job(user_input, selected_job, data, model)

result