from nlp.ner_model import extract_entities



def test_extract_entities_rule_based_fields_present():
    text = (
        "This agreement is made between Alpha Technologies and Beta Holdings. "
        "The fee is USD 12000. Termination may occur upon breach."
    )

    entities = extract_entities(text)

    assert "termination_clauses" in entities
    assert len(entities["termination_clauses"]) >= 1
