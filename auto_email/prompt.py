from typing import List

from auto_email.models import Profile


PROMPT_HEADER = """For each person below, write a SHORT phrase (max 1-2 sentences) that I can insert into an outreach email after the sentence \"I'm also serving as [your role] this year.\"

Rules:
- The phrase should feel natural and warm, like something a real person would say
- It could be a very light personal connection IF one exists naturally (e.g., same field of study, same living group at MIT)
- If there's no natural connection, just write a warm generic sentence (e.g., \"and I've been particularly inspired by the innovative work happening in [their industry]\")
- Do NOT force connections. Do NOT reference obscure activities or hobbies from their profile — that comes across as stalkerish
- Do NOT make it sound like a college admissions essay trying to force a quote into an argument
- Keep it brief and understated. Less is more.
- Start each phrase with a lowercase word (it follows a comma after \"...this year, \" )
- Return ONLY a numbered list matching the order below. No extra commentary.
"""


def generate_prompt(profiles: List[Profile]) -> str:
    lines = [PROMPT_HEADER.strip(), ""]
    for i, p in enumerate(profiles, start=1):
        name = p.full_name or f"{p.first_name}".strip()
        company = p.company or ""
        title = p.job_title or ""
        details = p.mit_details or ""
        lines.append(f"{i}. {name} — {company}, {title}. MIT details: {details}")
    return "\n".join(lines).strip()
