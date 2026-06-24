import pdfplumber
import re


def extract_text_from_pdf(file_path: str):

    text = ""

    with pdfplumber.open(file_path) as pdf:

        for page in pdf.pages:

            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"

    return text


import re

def extract_links(text: str):

    linkedin = ""
    github = ""
    portfolio = ""

    linkedin_match = re.search(
        r"(?:https?://)?(?:www\.)?linkedin\.com/in/[^\s]+",
        text,
        re.IGNORECASE
    )

    github_match = re.search(
        r"(?:https?://)?(?:www\.)?github\.com/[^\s]+",
        text,
        re.IGNORECASE
    )

    portfolio_match = re.search(
        r"[a-zA-Z0-9\-]+\.vercel\.app",
        text,
        re.IGNORECASE
    )

    if linkedin_match:
        linkedin = linkedin_match.group()

    if github_match:
        github = github_match.group()

    if portfolio_match:
        portfolio = portfolio_match.group()

    return {
        "linkedin": linkedin,
        "github": github,
        "portfolio": portfolio
    }