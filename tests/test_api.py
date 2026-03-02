import io
from pathlib import Path

import app as lexiscan_app


def test_health_endpoint():
    client = lexiscan_app.app.test_client()
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_upload_happy_path(monkeypatch, tmp_path):
    upload_dir = tmp_path / "uploads"
    output_dir = tmp_path / "outputs"
    upload_dir.mkdir()
    output_dir.mkdir()

    monkeypatch.setattr(lexiscan_app, "UPLOAD_FOLDER", str(upload_dir))
    monkeypatch.setattr(lexiscan_app, "OUTPUT_FOLDER", str(output_dir))
    monkeypatch.setattr(lexiscan_app, "extract_text", lambda _path: "Agreement dated 2026-03-02 for USD 5000.")
    monkeypatch.setattr(
        lexiscan_app,
        "extract_entities",
        lambda _text: {
            "dates": ["2026-03-02"],
            "party_names": ["Alpha Corp"],
            "amounts": ["USD 5000"],
            "termination_clauses": ["Termination allowed after notice period."],
        },
    )
    monkeypatch.setattr(lexiscan_app, "validate_entities", lambda entities: entities)

    client = lexiscan_app.app.test_client()
    response = client.post(
        "/upload?save_output=true",
        data={"file": (io.BytesIO(b"dummy"), "contract.txt")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "success"
    assert payload["entities"]["amounts"] == ["USD 5000"]
    assert Path(payload["output_json_path"]).exists()


def test_upload_rejects_unsupported_file_type():
    client = lexiscan_app.app.test_client()
    response = client.post(
        "/upload",
        data={"file": (io.BytesIO(b"dummy"), "contract.exe")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 400
