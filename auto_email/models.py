from dataclasses import dataclass


@dataclass
class Profile:
    first_name: str
    full_name: str
    email: str
    company: str
    job_title: str
    mit_details: str
    personalized_sentence: str = ""
