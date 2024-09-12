from fastapi import FastAPI, HTTPException, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from typing import List
from datetime import datetime
from matcher import match_profiles_with_job_description
from utils import (
    get_available_profiles,
    process_multiple_pdfs,
    save_profiles_to_db,
    update_profile_availability,
)
from prompt import RESUME_EXTRACTION_PROMPT_INPUT, EMAIL_TEMPLATE
from response_models import (
    AvailabilityRequest,
    AvailabilityResponse,
    JobDescriptionRequest,
    ListOfInterestedProfiles,
    ListOfProfile,
    ProfileResponse,
    ResumeExtractionResponse,
    UploadFilesResponse,
)
from typing import List, Optional

load_dotenv()

app = FastAPI()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = os.getenv("DB_PATH")
MODEL_ID = os.getenv("MODEL_ID")


# Endpoints


@app.post("/upload", response_model=UploadFilesResponse)
async def upload_files(files: List[UploadFile] = File(...)):
    pdf_bytes_list = [await file.read() for file in files]
    model_id = MODEL_ID
    results = process_multiple_pdfs(
        pdf_bytes_list, model_id, RESUME_EXTRACTION_PROMPT_INPUT, DB_PATH
    )
    response = UploadFilesResponse(
        results=[ResumeExtractionResponse(**result) for result in results]
    )
    return response


@app.post("/top-matches", response_model=ListOfProfile)
async def find_top_matches(job_description_request: JobDescriptionRequest):
    job_description = job_description_request.job_description

    if not job_description:
        raise HTTPException(status_code=400, detail="Job description cannot be empty")

    try:
        top_profiles = match_profiles_with_job_description(job_description)
    except Exception as e:
        print(f"Error in match_profiles_with_job_description: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    formatted_profiles = [
        {
            "rank": i + 1,
            "name": profile[0],
            "email": profile[1],
            "phone_number": profile[2],
            "current_organization": profile[3],
            "years_experience": profile[4],
            "skills": profile[5],
            "relevance_score": relevance_score,
            "interested": False,
            "interview_time": None,
        }
        for i, (profile, relevance_score) in enumerate(top_profiles)
    ]

    save_profiles_to_db(formatted_profiles)

    return ListOfProfile(
        top_matches=[ProfileResponse(**profile) for profile in formatted_profiles]
    )


@app.post("/update-availability")
async def update_availability(availability_request: AvailabilityRequest):
    update_profile_availability(
        availability_request.email,
        availability_request.interested,
        availability_request.interview_time,
    )
    return AvailabilityResponse(message="Availability status updated successfully")


@app.get("/available-candidates", response_model=ListOfInterestedProfiles)
async def get_available_candidates():
    available_profiles = get_available_profiles()
    return ListOfInterestedProfiles(interested_profiles=available_profiles)

from pydantic import BaseModel
class sendMail(BaseModel):
    to_email_c :str
    email_subject :str
    body :str
class ListOfEmails(BaseModel):
    ListOfEmails : List[sendMail]


def send_email(to_email_c, email_subject, body, to_email_r="recruiter@example.com"):
    """
    To-Do(Magesh)
    1. Create a gmail flow for sending emails. 
        1-A. Add the required emails contents as (input)
        1-B. Add gmail skill for sending email
        1-C. Catch the response sent to each candidate (output)
    2. Complete the send email functionality and make necessary changes for catching the response
    """
    return sendMail(to_email_c=to_email_c, email_subject=email_subject, body=body)


@app.get("/send-interview-invitations",response_model=ListOfEmails)
async def send_interview_invitations():
    subject = "Technical Interview"
    available_profiles = get_available_profiles()
    email_responses = []

    for profile in available_profiles:
        name = profile.name
        email = profile.email
        interview_datetime = (
            profile.interview_time
        )  # Assuming this field is already a datetime object
        location = "Your Company Office"  # Example location

        # Extract date and time from interview_datetime
        interview_date = interview_datetime.strftime("%Y-%m-%d")
        interview_time = interview_datetime.strftime("%H:%M:%S")

        # Format the email content
        email_content = EMAIL_TEMPLATE.format(
            name=name,
            interview_date=interview_date,
            interview_time=interview_time,
            location=location,
        )

        # In a real application, you would send this email using a library like smtplib or an API like SendGrid
        try:
            response = send_email(to_email_c=email, email_subject=subject, body=email_content)
            email_responses.append(response)
        except Exception as e:
            return "Exception occurred while sending email to {}: {}".format(email, str(e))
        # For demonstration, printing the email content
        # print(email_content)
    print("The endpoint was sucessfully executed")   
    return ListOfEmails(ListOfEmails=email_responses)


# Run the FastAPI application using Uvicorn server
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
