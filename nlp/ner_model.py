import os
import re

import spacy


def _load_nlp():
    model_path = os.getenv("LEXISCAN_NER_MODEL_PATH")
    if model_path:
        try:
            return spacy.load(model_path)
        except Exception:
            pass

    try:
        return spacy.load("en_core_web_sm")
    except Exception:
        # Keep service alive even when model is not installed.
        return spacy.blank("en")


nlp = _load_nlp()


def _unique(items):
    seen = set()
    output = []
    for item in items:
        cleaned = item.strip()
        if cleaned and cleaned.lower() not in seen:
            seen.add(cleaned.lower())
            output.append(cleaned)
    return output


def extract_entities(text):
    doc = nlp(text)

    entities = {
        "dates": [],
        "party_names": [],
        "amounts": [],
        "termination_clauses": [],
    }

    for ent in doc.ents:
        if ent.label_ in {"DATE"}:
            entities["dates"].append(ent.text)
        elif ent.label_ in {"ORG", "PERSON", "PARTY"}:
            entities["party_names"].append(ent.text)
        elif ent.label_ in {"MONEY", "AMOUNT"}:
            entities["amounts"].append(ent.text)

    # Contract-specific rule hints to improve party-name extraction.
    party_pattern = re.compile(
        r"(?:between|by and between)\s+([A-Z][A-Za-z0-9&.,\-\s]{2,80})\s+and\s+([A-Z][A-Za-z0-9&.,\-\s]{2,80})",
        re.IGNORECASE,
    )
    for match in party_pattern.finditer(text):
        entities["party_names"].extend([match.group(1), match.group(2)])

    # Backfill dates and amounts using regex if model misses them.
    entities["dates"].extend(
        re.findall(
            r"\b(?:\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},\s+\d{4})\b",
            text,
            re.IGNORECASE,
        )
    )
    entities["amounts"].extend(
        re.findall(r"\b(?:USD|INR|EUR|GBP|Rs\.?)?\s?\$?\s?\d[\d,]*(?:\.\d{1,2})?\b", text, re.IGNORECASE)
    )

    # Pull full sentences with termination/expiry language.
    sentence_pattern = re.compile(
        r"[^.]*\b(termination|terminate|terminated|expiry|expiration|end of term)\b[^.]*\.",
        re.IGNORECASE,
    )
    entities["termination_clauses"] = [m.group(0).strip() for m in sentence_pattern.finditer(text)]

    for key in entities:
        entities[key] = _unique(entities[key])

    return entities
