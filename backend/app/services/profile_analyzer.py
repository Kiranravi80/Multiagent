import os
import json
from groq import Groq

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


async def analyze_profile(user_data):

    prompt = f"""
Return technical skills only.

Do not return soft skills.

missing_skills should contain
industry-relevant skills needed
for recommended roles.

Schema:


{
    {
        "experience_level": "",
        "total_experience_years": 0,
        "primary_domain": "",
        "secondary_domains": [],
        "recommended_roles": [],
        "core_skills": [],
        "missing_skills": [],
        "career_stage": ""
    }
}

Profile:

{json.dumps(user_data, indent=2)}
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

    content = content.replace(
        "```json",
        ""
    )

    content = content.replace(
        "```",
        ""
    )

    return json.loads(content)