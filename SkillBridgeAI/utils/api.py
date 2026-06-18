import json, os, requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8501")


def get_recommendations(user_text: str):
    raw = requests.post(f"{API_URL}/recommend", json={"skills": user_text, "top_k": 5}).json()
    recs = []
    for r in raw.get("recommendations", []):
        score = r.get("score", 0)
        recs.append({
            "title":            r.get("career", ""),
            "experience_level": "Entry Level",
            "match_score":      round(score / 100, 4),
            "matched_skills":   [],
            "missing_skills":   []
        })
    return {"recommendations": recs}


def get_analysis(user_text: str, target_title: str):
    score_raw = requests.post(f"{API_URL}/match-score", json={"skills": user_text, "target_career": target_title}).json()

    readiness_str = score_raw.get("readiness_score", "0.00%")
    try:
        readiness = int(float(readiness_str.replace("%", "")))
    except:
        readiness = 0

    owned   = score_raw.get("matched_skills", [])
    missing = score_raw.get("missing_skills", [])
    gap_pct = score_raw.get("gap_percentage", "100.00%")

    return {
        "readiness_score": readiness,
        "owned_skills": owned,
        "missing_skills_priority": [{"skill": s, "priority": i+1, "reason": ""} for i, s in enumerate(missing)],
        "summary": f"Kamu memiliki {len(owned)} dari {len(owned)+len(missing)} skill yang dibutuhkan untuk posisi {target_title}.",
        "_gap_percentage": gap_pct,
        "_readiness_str": readiness_str,
        "_missing_raw": missing
    }


def get_roadmap(target_title: str, missing_skills: list):
    user_text = st.session_state.get("user_skills_text", "")
    analysis  = st.session_state.get("analysis", {})
    gap_pct   = analysis.get("_gap_percentage", "100.00%")
    ready_str = analysis.get("_readiness_str", "0.00%")

    raw = requests.post(f"{API_URL}/roadmap", json={
        "skills":          user_text,
        "target_career":   target_title,
        "missing_skills":  missing_skills,
        "gap_percentage":  gap_pct,
        "readiness_score": ready_str
    }).json()

    if not raw.get("success"):
        return {"weeks": []}

    data = raw.get("data", {})
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except:
            return {"weeks": []}

    roadmap_data = data.get("roadmap", data)
    weeks = []
    for w_num in range(1, 5):
        w_data = roadmap_data.get(f"W{w_num}")
        if not w_data:
            continue
        days = []
        for d_num in range(1, 7):
            d_data = w_data.get(f"d{d_num}")
            if not d_data:
                continue
            resources    = d_data.get("resources", [])
            resource_str = resources[0]["link"] if resources else "-"
            days.append({
                "day":      d_num,
                "topic":    d_data.get("title", ""),
                "detail":   d_data.get("desc", ""),
                "resource": resource_str
            })
        weeks.append({
            "week":  w_num,
            "focus": w_data.get("tag", f"Minggu {w_num}"),
            "days":  days
        })

    return {"weeks": weeks}
