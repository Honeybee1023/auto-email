import re
from typing import List, Optional


def parse_numbered_list(text: str, expected_count: int) -> Optional[List[str]]:
    lines = [l.strip() for l in text.splitlines()]
    numbered = []
    for i, line in enumerate(lines):
        m = re.match(r"^(\d+)[\.)]\s*(.*)$", line)
        if m:
            numbered.append((i, m.group(1), m.group(2).strip()))

    if not numbered:
        return None

    items: List[str] = []
    for idx, (line_idx, _num, first_text) in enumerate(numbered):
        next_idx = numbered[idx + 1][0] if idx + 1 < len(numbered) else len(lines)
        if first_text:
            items.append(first_text)
            continue
        # If the numbered line is empty, take following non-empty lines until next number
        buffer: List[str] = []
        for j in range(line_idx + 1, next_idx):
            if lines[j]:
                buffer.append(lines[j])
        items.append(" ".join(buffer).strip())

    if len(items) != expected_count:
        return None
    return items
