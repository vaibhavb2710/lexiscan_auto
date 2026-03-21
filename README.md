

# LexiScan Auto - Legal Contract Entity Extractor

LexiScan Auto is a Flask microservice for extracting legal entities from native/scanned documents.

## Features
- OCR for `.pdf` and `.txt` documents
- Scanned-page OCR fallback with Tesseract
- Named entity extraction for:
  - `dates`
  - `party_names`
  - `amounts`
  - `termination_clauses`
- Rule-based post-processing and validation
- JSON API with output artifact export
- Custom NER training scaffold (spaCy)
- Dockerized deployment
- Pytest test suite

## Project Structure
```text
app.py
ocr/
  ocr_engine.py
nlp/
  ner_model.py
  train_ner.py
  training_data/sample_contracts.json
utils/
  validator.py
tests/
  test_api.py
  test_ner_model.py
  test_validator.py
Dockerfile
docker-compose.yml
requirements.txt
```

## Local Setup
1. Create and activate virtual environment:
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```
2. Install dependencies:
```powershell
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```
3. Install Tesseract OCR:
- Windows: install Tesseract and set `TESSERACT_CMD` if not in PATH.

4. Run API:
```powershell
python app.py
```

## API
### `GET /`
Service metadata.

### `GET /health`
Health check endpoint.

### `POST /upload?save_output=true`
Upload a document as multipart form data using key `file`.

Example:
```powershell
curl -X POST "http://127.0.0.1:5000/upload?save_output=true" `
  -F "file=@sample_contract.pdf"
```

Sample response:
```json
{
  "status": "success",
  "file_name": "sample_contract.pdf",
  "char_count": 2763,
  "entities": {
    "dates": ["2026-03-02"],
    "party_names": ["Alpha Corp", "Beta LLC"],
    "amounts": ["USD 10,000"],
    "termination_clauses": ["Termination may occur upon material breach."]
  },
  "meta": {
    "app_version": "1.0.0",
    "processed_at_utc": "2026-03-02T12:34:56.789+00:00"
  },
  "output_json_path": "outputs/sample_contract_20260302T123456Z.json"
}
```

## Custom NER Training
1. Prepare training data in this format:
```json
[
  {
    "text": "Agreement dated 2026-01-15 between Alpha and Beta for USD 2000.",
    "entities": [[16, 26, "DATE"], [35, 40, "PARTY"], [45, 49, "PARTY"], [54, 62, "AMOUNT"]]
  }
]
```

2. Train:
```powershell
python nlp/train_ner.py
```

3. Use custom model:
```powershell
$env:LEXISCAN_NER_MODEL_PATH="nlp/custom_model"
python app.py
```

## Run Tests
```powershell
pytest -q
```

## Docker
Build and run:
```powershell
docker compose up --build
```

The API will be available at `http://localhost:5000`.
