import sqlite3
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
import pandas as pd
from dotenv import load_dotenv
from pdf2image import convert_from_bytes
import pytesseract
from model import initialize_model
from typing import List, Dict, Optional
from fastapi import HTTPException
from response_models import InterestedProfileResponse
from datetime import datetime

# Load environment variables
load_dotenv()

# Global variables
DB_PATH = os.getenv("DB_PATH")


# Function to check if email exists in SQLite database
def check_email_exists(conn, email):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM resumes WHERE email=?", (email,))
        result = cursor.fetchone()
        return result[0] > 0
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return False


# Function to create resumes table if not exists
def create_resumes_table(conn):
    try:
        cursor = conn.cursor()
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS resumes
                 (Name TEXT, Email TEXT PRIMARY KEY, Phone_Number TEXT,
                  Current_Organization TEXT, Years_Experience INTEGER, Skills TEXT)"""
        )
        conn.commit()
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")


def get_available_profiles():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM top_match_user_profiles WHERE interested = ?", (True,)
    )
    rows = cursor.fetchall()

    columns = [desc[0] for desc in cursor.description]
    profiles_db = [dict(zip(columns, row)) for row in rows]

    conn.close()

    available_profiles = [
        InterestedProfileResponse(
            name=profile["name"],
            email=profile["email"],
            phone_number=profile["phone_number"],
            current_organization=profile["current_organization"],
            years_experience=profile["years_experience"],
            skills=profile["skills"],
            relevance_score=profile["relevance_score"],
            interview_time=profile["interview_time"],
        )
        for profile in profiles_db
        if profile["interested"]
    ]

    return available_profiles


# Function to fetch profiles from database
def get_profiles():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT Name, Email, Phone_Number, Current_Organization, Years_Experience, Skills FROM resumes"
        )
        profiles = cursor.fetchall()
        return profiles
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return []


# Function to extract text from PDF
def parse_pdf_with_tesseract(pdf_bytes, page_number=0) -> str:
    try:
        images = convert_from_bytes(
            pdf_bytes, first_page=page_number + 1, last_page=page_number + 1
        )
        if not images:
            return "Failed to convert PDF to image"
        page_image = images[0]
        extracted_text = pytesseract.image_to_string(page_image)
        return extracted_text
    except Exception as e:
        print(f"Error parsing PDF: {e}")
        return "Failed to extract text"


# Function to process multiple PDFs in parallel
def process_multiple_pdfs(pdf_bytes_list, model_id, prompt, db_path):
    results = []
    with ThreadPoolExecutor(max_workers=None) as executor:
        futures = [
            executor.submit(
                process_resume_from_pdf, pdf_bytes, model_id, prompt, db_path
            )
            for pdf_bytes in pdf_bytes_list
        ]
        for future in as_completed(futures):
            results.append(future.result())
    return results


# Function to insert or update resume information in SQLite
def process_resume_from_pdf(pdf_bytes, model_id, prompt, db_path):
    try:
        # Extract text from PDF
        extracted_text = parse_pdf_with_tesseract(pdf_bytes, 0)

        parsed_pdf_file = "uploaded_file.pdf"  # Placeholder for filename
        text = extracted_text + "\n" + f"File Name: {parsed_pdf_file}\n"
        prompt = prompt.format(filename=parsed_pdf_file, text=text)

        # Initialize model
        model = initialize_model(model_id)

        # Generate response
        resp = model.generate(prompt=prompt)["results"][0]["generated_text"]

        # Extract JSON from response
        first, last = resp.find("{"), resp.rfind("}")
        resp_json = json.loads(resp[first : last + 1], strict=False)

        # Extract information from JSON
        name = resp_json.get("name", "")
        email = resp_json.get("email", "")
        phone_number = resp_json.get("phone_number", "")
        current_organization = resp_json.get("current_organization", "")
        years_experience = resp_json.get("years_experience", "")
        skills = resp_json.get("skills", "")

        # Connect to SQLite database
        with sqlite3.connect(db_path) as conn:
            # Ensure resumes table exists
            create_resumes_table(conn)

            # Check if email already exists
            if check_email_exists(conn, email):
                # Perform update if email exists
                cursor = conn.cursor()
                cursor.execute(
                    """UPDATE resumes 
                             SET name=?, phone_number=?, current_organization=?, 
                                 years_experience=?, skills=?
                             WHERE email=?""",
                    (
                        name,
                        phone_number,
                        current_organization,
                        years_experience,
                        skills,
                        email,
                    ),
                )
            else:
                # Perform insert if email does not exist
                cursor = conn.cursor()
                cursor.execute(
                    """INSERT INTO resumes 
                             (name, email, phone_number, current_organization, years_experience, skills) 
                             VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        name,
                        email,
                        phone_number,
                        current_organization,
                        years_experience,
                        skills,
                    ),
                )
            conn.commit()

            inferred = {
                "name": name,
                "email": email,
                "phone_number": phone_number,
                "current_organization": current_organization,
                "years_experience": years_experience,
                "skills": skills,
            }

            return inferred

    except (json.JSONDecodeError, sqlite3.Error, Exception) as e:
        print(f"Error processing resume: {e}")
        return {}


# Function to save profiles to a database table
def save_profiles_to_db(profiles: List[Dict]):
    try:
        # Create a DataFrame from the list of profiles
        df = pd.DataFrame(profiles)

        # Connect to the SQLite database
        with sqlite3.connect(DB_PATH) as conn:
            # Create the table if it doesn't exist or overwrite it if it does
            cursor = conn.cursor()
            cursor.execute("DROP TABLE IF EXISTS top_match_user_profiles")
            df.to_sql("top_match_user_profiles", conn, if_exists="replace", index=False)

    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
    except Exception as e:
        print(f"Error saving profiles to database: {e}")


def update_profile_availability(
    email: str, interested: bool, interview_time: Optional[datetime]
):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM top_match_user_profiles WHERE email = ?", (email,))
    profile = cursor.fetchone()

    if not profile:
        conn.close()
        raise HTTPException(status_code=404, detail="Profile not found")

    if interested:
        if not interview_time:
            raise HTTPException(
                status_code=400,
                detail="Interview time is required when interested is true",
            )
        cursor.execute(
            "UPDATE top_match_user_profiles SET interested = ?, interview_time = ? WHERE email = ?",
            (interested, interview_time, email),
        )
    else:
        cursor.execute(
            "UPDATE top_match_user_profiles SET interested = ?, interview_time = NULL WHERE email = ?",
            (interested, email),
        )

    conn.commit()
    conn.close()
