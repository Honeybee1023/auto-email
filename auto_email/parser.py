import re
from typing import List, Optional, Tuple

from auto_email.models import Profile

SECTION_HEADERS = ["Work Information", "Personal Information", "MIT Information"]


def _section_bounds(text: str, header: str) -> Optional[tuple[int, int]]:
    start = text.find(header)
    if start == -1:
        return None
    start_end = start + len(header)
    next_positions = [text.find(h, start_end) for h in SECTION_HEADERS if h != header]
    next_positions = [p for p in next_positions if p != -1]
    end = min(next_positions) if next_positions else len(text)
    return start_end, end


def _extract_section(text: str, header: str) -> str:
    bounds = _section_bounds(text, header)
    if not bounds:
        return ""
    start, end = bounds
    return text[start:end].strip()


def _find_value_after_label(section_text: str, label: str) -> str:
    lines = [l.strip() for l in section_text.splitlines()]
    for i, line in enumerate(lines):
        if line == label and i + 1 < len(lines):
            return lines[i + 1].strip()
    return ""


def _infer_full_name(text: str) -> str:
    work_idx = text.find("Work Information")
    pre = text[:work_idx] if work_idx != -1 else text
    lines = [l.strip() for l in pre.splitlines() if l.strip()]
    junk = {
        "Alumni Directory",
        "My Account",
        "Name",
        "Search",
        "Back to Search Results",
        "Load More",
        "Work Information",
        "Home Information",
        "Personal Information",
        "MIT Information",
    }
    lines = [l for l in lines if l not in junk]
    if not lines:
        return ""
    candidates = [
        l
        for l in lines
        if re.search(r"'\d{2}", l) or re.search(r"\bPhD\b|\bMNG\b|\bMEng\b|\bSM\b|\bSB\b", l)
    ]
    if candidates:
        return candidates[-1]
    titled = [l for l in lines if re.match(r"^(Mr\.|Ms\.|Mrs\.|Dr\.)\s+", l)]
    return titled[-1] if titled else lines[-1]


def _strip_degrees(name_line: str) -> str:
    return re.split(
        r"\s+(?:'\d{2}|MNG|MEng|SM|SB|PhD|MBA|PD)\b", name_line
    )[0].strip()


def _first_name(full_name: str) -> str:
    name = _strip_degrees(full_name)
    name = re.sub(r"^(Dr\.|Mr\.|Ms\.|Mrs\.)\s+", "", name).strip()
    parts = [p for p in name.split() if p]
    return parts[0] if parts else ""


def parse_profile(text: str, name_line: Optional[str] = None) -> Optional[Profile]:
    if "Work Information" not in text and not name_line:
        return None

    full_name = _strip_degrees(name_line) if name_line else _infer_full_name(text)
    first_name = _first_name(full_name)

    work = _extract_section(text, "Work Information")
    personal = _extract_section(text, "Personal Information")
    mit = _extract_section(text, "MIT Information")

    email = _find_value_after_label(personal, "Email")
    company = _find_value_after_label(work, "Company")
    job_title = (
        _find_value_after_label(work, "Job Title")
        or _find_value_after_label(work, "Occupation")
        or _find_value_after_label(work, "Title")
    )

    return Profile(
        first_name=first_name,
        full_name=full_name,
        email=email,
        company=company,
        job_title=job_title,
        mit_details=mit.strip(),
    )


def parse_profiles(raw_text: str) -> List[Profile]:
    if not raw_text.strip():
        return []

    lines = raw_text.splitlines()
    name_pattern = re.compile(
        r"^(Mr\.|Ms\.|Mrs\.|Dr\.)?\s*[A-Z][A-Za-z\.\-']+(?:\s+[A-Z][A-Za-z\.\-']+)*\s+"
        r"(?:'\d{2}|MNG|MEng|SM|SB|PhD|MBA|PD)\b"
    )

    name_indices: List[Tuple[int, str]] = []
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        if name_pattern.search(line):
            name_indices.append((i, line))

    if not name_indices:
        profile = parse_profile(raw_text)
        return [profile] if profile else []

    profiles: List[Profile] = []
    for idx, (start_i, name_line) in enumerate(name_indices):
        end_i = name_indices[idx + 1][0] if idx + 1 < len(name_indices) else len(lines)
        block = "\n".join(lines[start_i:end_i]).strip()
        profile = parse_profile(block, name_line=name_line)
        if profile:
            profiles.append(profile)
    return profiles
