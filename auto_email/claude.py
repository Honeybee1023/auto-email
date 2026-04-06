import re
from typing import List, Optional


def parse_numbered_list(text: str, expected_count: int) -> Optional[List[str]]:
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    items: List[str] = []
    for line in lines:
        m = re.match(r"^(\d+)[\.)]\s+(.*)$", line)
        if m:
            items.append(m.group(2).strip())
    if len(items) != expected_count:
        return None
    return items
