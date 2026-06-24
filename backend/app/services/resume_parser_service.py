import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


async def parse_resume_with_ai(resume_text: str):

    prompt = f"""
Extract information from the resume.

Return ONLY valid JSON.

Schema:

{{
    "personal_details": {{
        "full_name": "",
        "email": "",
        "phone": "",
        "location": ""
    }},
    "social_profiles": {{
        "linkedin": "",
        "github": "",
        "portfolio": ""
    }},
    "education": [],
    "skills": [],
    "projects": [],
    "experience": [],
    "certifications": [],
    "achievements": []
}}

Resume:

{resume_text}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0
    )

    content = response.choices[0].message.content

    content = content.replace("```json", "")
    content = content.replace("```", "")

    return json.loads(content)