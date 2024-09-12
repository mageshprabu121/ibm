from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from fastapi import UploadFile


# Response Models
class UploadFilesRequest(BaseModel):
    files: List[UploadFile]


class ResumeExtractionResponse(BaseModel):
    name: str
    email: str
    phone_number: str
    current_organization: str
    years_experience: int
    skills: str


class UploadFilesResponse(BaseModel):
    results: List[ResumeExtractionResponse]


class JobDescriptionRequest(BaseModel):
    job_description: str


class ProfileResponse(BaseModel):
    rank: int
    name: str
    email: str
    phone_number: str
    current_organization: str
    years_experience: int
    skills: str
    relevance_score: float


class ListOfProfile(BaseModel):
    top_matches: List[ProfileResponse]


class AvailabilityResponse(BaseModel):
    message: str


class AvailabilityRequest(BaseModel):
    email: str
    interested: bool
    interview_time: Optional[datetime]


class InterestedProfileResponse(BaseModel):
    name: str
    email: str
    phone_number: str
    current_organization: str
    years_experience: int
    skills: str
    relevance_score: float
    interview_time: Optional[datetime]


class ListOfInterestedProfiles(BaseModel):
    interested_profiles: List[InterestedProfileResponse]
