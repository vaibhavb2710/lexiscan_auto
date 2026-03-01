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

    # Pre-trained detection
    for ent in doc.ents:
        if ent.label_ == "DATE":
            entities["dates"].append(ent.text)
        if ent.label_ == "ORG":
            entities["party_names"].append(ent.text)
        if ent.label_ == "MONEY":
            entities["amounts"].append(ent.text)

    # Rule-based termination clause detection
    termination_pattern = r"(termination.*?\.)"
    matches = re.findall(termination_pattern, text, re.IGNORECASE)

    entities["termination_clauses"] = matches

    return entities