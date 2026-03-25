import re
from datetime import datetime



DATE_FORMATS = (
    "%Y-%m-%d",
    "%d-%m-%Y",
    "%d/%m/%Y",
    "%m/%d/%Y",
    "%B %d, %Y",
    "%b %d, %Y",
)


def _normalize_date(raw_date):
    value = raw_date.strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def _normalize_amount(raw_amount):
    value = raw_amount.strip()
    if re.search(r"(\$|USD|INR|EUR|GBP|Rs\.?)", value, re.IGNORECASE) and re.search(
        r"\d", value
    ):
        return value
    return None


def validate_entities(entities):
    validated = {
        "dates": [],
        "party_names": [],
        "amounts": [],
        "termination_clauses": [],
    }

    for date in entities.get("dates", []):
        normalized = _normalize_date(date)
        if normalized:
            validated["dates"].append(normalized)

    for amount in entities.get("amounts", []):
        normalized = _normalize_amount(amount)
        if normalized:
            validated["amounts"].append(normalized)

    for party in entities.get("party_names", []):
        cleaned = party.strip()
        if len(cleaned) > 2:
            validated["party_names"].append(cleaned)

    for clause in entities.get("termination_clauses", []):
        cleaned = clause.strip()
        if len(cleaned) > 20:
            validated["termination_clauses"].append(cleaned)

    for key in validated:
        deduped = []
        seen = set()
        for value in validated[key]:
            marker = value.lower()
            if marker not in seen:
                seen.add(marker)
                deduped.append(value)
        validated[key] = deduped

    return validated
