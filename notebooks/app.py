import streamlit as st
import requests
from datetime import datetime

# Set the URL for your FastAPI application
FASTAPI_URL = "http://localhost:8000"


def post_job_description(job_description):
    response = requests.post(
        f"{FASTAPI_URL}/top-matches", json={"job_description": job_description}
    )
    response.raise_for_status()
    return response.json()


def update_availability(email, interested, interview_datetime=None):
    payload = {
        "email": email,
        "interested": interested,
        "interview_time": (
            interview_datetime.isoformat() if interview_datetime else None
        ),
    }
    response = requests.post(f"{FASTAPI_URL}/update-availability", json=payload)
    response.raise_for_status()
    return response.json()


def get_available_candidates():
    response = requests.get(f"{FASTAPI_URL}/available-candidates")
    response.raise_for_status()
    return response.json()


st.title("HR Candidate Management System")

# Step 1: Input Job Description
st.header("Step 1: Input Job Description")
job_description = st.text_area("Job Description", "")
if st.button("Find Top Matches"):
    with st.spinner("Finding top matches..."):
        top_matches = post_job_description(job_description)
        st.session_state["top_matches"] = top_matches["top_matches"]
        st.success("Top matches found!")

# Display Top Matches
if "top_matches" in st.session_state:
    st.header("Top Matches")
    top_matches_df = [
        {
            "Rank": profile["rank"],
            "Name": profile["name"],
            "Email": profile["email"],
            "Skills": profile["skills"],
            "Experience (years)": profile["experience"],
            "Current Organization": profile["current_organization"],
            "Relevance Score": profile["relevance_score"],
        }
        for profile in st.session_state["top_matches"]
    ]
    st.table(top_matches_df)

    # Step 2: Update Availability
    st.header("Step 2: Update Availability")

    availability_updates = []
    for profile in st.session_state["top_matches"]:
        st.write(f"**{profile['name']}** ({profile['email']})")
        interested = st.radio(
            f"Is {profile['name']} interested?",
            ("Not Interested", "Interested"),
            key=profile["email"],
        )
        interview_datetime = None
        if interested == "Interested":
            interview_date = st.date_input(
                f"Interview Date for {profile['name']}", key=f"date_{profile['email']}"
            )
            interview_time = st.time_input(
                f"Interview Time for {profile['name']}", key=f"time_{profile['email']}"
            )
            interview_datetime = datetime.combine(interview_date, interview_time)
        availability_updates.append(
            (profile["email"], interested == "Interested", interview_datetime)
        )

    if st.button("Update Availability"):
        with st.spinner("Updating availability..."):
            for email, interested, interview_datetime in availability_updates:
                update_availability(email, interested, interview_datetime)
            st.success("Availability updated!")

    # Step 3: Display Available Candidates
    st.header("Step 3: Display Available Candidates")
    if st.button("Show Available Candidates"):
        with st.spinner("Retrieving available candidates..."):
            available_candidates = get_available_candidates()
            available_profiles_df = [
                {
                    "Name": profile["name"],
                    "Email": profile["email"],
                    "Skills": profile["skills"],
                    "Experience (years)": profile["experience"],
                    "Current Organization": profile["current_organization"],
                    "Relevance Score": profile["relevance_score"],
                    "Interview Time": profile["interview_time"],
                }
                for profile in available_candidates["interested_profiles"]
            ]
            st.table(available_profiles_df)
