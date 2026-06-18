import json
import os
import requests
import streamlit as st

API_URL = os.getenv(
    "API_URL",
    "https://panskuy-skillbridge-api.hf.space"
)


# ==========================================================
# RECOMMENDATION
# ==========================================================
def get_recommendations(user_text: str):

    try:

        response = requests.post(
            f"{API_URL}/recommend",
            json={
                "skills": user_text,
                "top_k": 5
            },
            timeout=60
        )

        response.raise_for_status()

        raw = response.json()

        recs = []

        for r in raw.get("recommendations", []):

            score = r.get("score", 0)

            recs.append({
                "title": r.get("career", ""),
                "description": r.get("description", ""),
                "suitability": r.get("suitability", ""),
                "experience_level": "Entry Level",
                "match_score": round(score / 100, 4),
                "matched_skills": [],
                "missing_skills": []
            })

        return {
            "success": True,
            "recommendations": recs,
            "message": raw.get("message", "")
        }

    except Exception as e:

        return {
            "success": False,
            "recommendations": [],
            "message": str(e)
        }


# ==========================================================
# SKILL GAP ANALYSIS
# ==========================================================
def get_analysis(user_text: str, target_title: str):

    try:

        response = requests.post(
            f"{API_URL}/match-score",
            json={
                "skills": user_text,
                "target_career": target_title
            },
            timeout=60
        )

        response.raise_for_status()

        score_raw = response.json()

        readiness_str = score_raw.get(
            "readiness_score",
            "0.00%"
        )

        try:
            readiness = int(
                float(
                    readiness_str.replace("%", "")
                )
            )
        except:
            readiness = 0

        owned = score_raw.get(
            "matched_skills",
            []
        )

        missing = list(
            set(
                score_raw.get(
                    "missing_skills",
                    []
                )
            )
        )

        missing.sort()

        gap_pct = score_raw.get(
            "gap_percentage",
            "100.00%"
        )

        return {
            "success": True,
            "readiness_score": readiness,
            "owned_skills": owned,
            "missing_skills_priority": [
                {
                    "skill": skill,
                    "priority": i + 1,
                    "reason": ""
                }
                for i, skill in enumerate(missing)
            ],
            "summary":
                f"Kamu memiliki {len(owned)} dari "
                f"{len(owned) + len(missing)} skill "
                f"yang dibutuhkan untuk posisi "
                f"{target_title}.",
            "_gap_percentage": gap_pct,
            "_readiness_str": readiness_str,
            "_missing_raw": missing
        }

    except Exception as e:

        return {
            "success": False,
            "message": str(e),
            "readiness_score": 0,
            "owned_skills": [],
            "missing_skills_priority": [],
            "_gap_percentage": "100.00%",
            "_readiness_str": "0.00%",
            "_missing_raw": []
        }


# ==========================================================
# ROADMAP GENERATOR
# ==========================================================
def get_roadmap(target_title: str, missing_skills: list):

    try:

        user_text = st.session_state.get(
            "user_skills_text",
            ""
        )

        analysis = st.session_state.get(
            "analysis",
            {}
        )

        gap_pct = analysis.get(
            "_gap_percentage",
            "100.00%"
        )

        ready_str = analysis.get(
            "_readiness_str",
            "0.00%"
        )

        response = requests.post(
            f"{API_URL}/roadmap",
            json={
                "skills": user_text,
                "target_career": target_title,
                "missing_skills": missing_skills,
                "gap_percentage": gap_pct,
                "readiness_score": ready_str
            },
            timeout=120
        )

        response.raise_for_status()

        raw = response.json()

        if not raw.get("success", False):

            return {
                "weeks": []
            }

        data = raw.get(
            "data",
            {}
        )

        if isinstance(data, str):

            try:
                data = json.loads(data)

            except:
                return {
                    "weeks": []
                }

        roadmap_data = data.get(
            "roadmap",
            data
        )

        weeks = []

        for w_num in range(1, 5):

            week_key = f"W{w_num}"

            if week_key not in roadmap_data:
                continue

            w_data = roadmap_data[week_key]

            days = []

            for d_num in range(1, 7):

                day_key = f"d{d_num}"

                if day_key not in w_data:
                    continue

                d_data = w_data[day_key]

                resources = d_data.get(
                    "resources",
                    []
                )

                resource_link = "-"

                if (
                    resources
                    and isinstance(resources, list)
                ):

                    first_resource = resources[0]

                    if isinstance(first_resource, dict):

                        resource_link = first_resource.get(
                            "link",
                            "-"
                        )

                days.append({
                    "day": d_num,
                    "topic": d_data.get(
                        "title",
                        ""
                    ),
                    "detail": d_data.get(
                        "desc",
                        ""
                    ),
                    "resource": resource_link
                })

            weeks.append({
                "week": w_num,
                "focus": w_data.get(
                    "tag",
                    f"Minggu {w_num}"
                ),
                "days": days
            })

        return {
            "weeks": weeks
        }

    except Exception as e:

        print("ROADMAP ERROR:", str(e))

        return {
            "weeks": []
        }
