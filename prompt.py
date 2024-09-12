RESUME_EXTRACTION_PROMPT_INPUT = """[INST] You are an information extraction assistant. Your task is to extract the following information in JSON format:
- Name: "name"
- Email: "email"
- Phone Number: "phone_number"
- Current Organization: "current_organization"
- Years of Experience: "years_experience" (round to nearest integer, 0 if not mentioned)
- Skills: "skills"

Ensure the "years_experience" field is an integer. If the resume mentions 2.5+ years of experience, round it up to 3. If the experience is not mentioned, set it to 0.

Use this syntax for your response:
{{
    "filename": {filename},
    "name": "...",
    "email": "...",
    "phone_number": "...",
    "current_organization": "...",
    "years_experience": ...,
    "skills": "..."
}}


Input: {text}

Output:"""


# Email Template
EMAIL_TEMPLATE = """
Hi {name},

You are invited to the first round of interviews for the position you applied for. 
Please find the details below:

Date: {interview_date}
Time: {interview_time}
Location: {location}

Best regards,
[Your Company]
"""
