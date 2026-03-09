import spacy
import re

nlp = spacy.load("en_core_web_sm")

def extract_entities(text):

    doc = nlp(text)

    entities = {
        "dates": [],
        "party_names": [],
        "amounts": [],
        "termination_clauses": []
    }

    # -------- DATES ----------
    for ent in doc.ents:
        if ent.label_ == "DATE":
            entities["dates"].append(ent.text)

    # -------- MONEY ----------
    money_pattern = r"\$\d+(?:,\d{3})*(?:\.\d+)?"
    entities["amounts"] = re.findall(money_pattern, text)

    # -------- PARTY NAMES ----------
    for ent in doc.ents:
        if ent.label_ in ["ORG", "PERSON"]:
            entities["party_names"].append(ent.text)

    # remove duplicates
    entities["party_names"] = list(set(entities["party_names"]))

    # -------- TERMINATION CLAUSE ----------
    termination_pattern = r"(TERMINATION:.*?termination\.)"
    match = re.search(termination_pattern, text, re.IGNORECASE | re.DOTALL)

    if match:
        entities["termination_clauses"].append(match.group())

    return entities