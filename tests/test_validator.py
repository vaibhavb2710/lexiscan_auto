from utils.validator import validate_entities


def test_validate_entities_normalizes_and_filters():
    raw = {
        "dates": ["2026-03-02", "March 2, 2026", "not-a-date"],
        "party_names": ["Alpha Corp", "A", "Beta LLC"],
        "amounts": ["USD 10,000", "5000", "$250.75"],
        "termination_clauses": ["Short", "Termination is allowed with 30 days notice."],
    }

    validated = validate_entities(raw)

    assert validated["dates"] == ["2026-03-02"]
    assert validated["party_names"] == ["Alpha Corp", "Beta LLC"]
    assert validated["amounts"] == ["USD 10,000", "$250.75"]
    assert validated["termination_clauses"] == ["Termination is allowed with 30 days notice."]


