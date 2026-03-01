import re

def validate_entities(entities):
    validated = entities.copy()

    # Validate date format
    date_pattern = r"\d{4}-\d{2}-\d{2}"

    validated["dates"] = [
        d for d in entities["dates"]
        if re.match(date_pattern, d)
    ]

    # Validate amounts contain currency symbol
    validated["amounts"] = [
        a for a in entities["amounts"]
        if "$" in a or "USD" in a
    ]

    return validated