import json
import os
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, request
from werkzeug.utils import secure_filename

from nlp.ner_model import extract_entities
from ocr.ocr_engine import extract_text
from utils.validator import validate_entities

APP_NAME = "LexiScan Auto"
APP_VERSION = "1.0.0"
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
OUTPUT_FOLDER = os.getenv("OUTPUT_FOLDER", "outputs")
ALLOWED_EXTENSIONS = {"pdf", "txt"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = int(os.getenv("MAX_CONTENT_LENGTH", 20 * 1024 * 1024))


def _allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _error(message, status_code):
    return jsonify({"status": "error", "message": message}), status_code


def _save_output_json(payload, source_filename):
    stem = Path(source_filename).stem
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_name = f"{stem}_{timestamp}.json"
    output_path = Path(OUTPUT_FOLDER) / output_name
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return str(output_path)


@app.route("/", methods=["GET"])
def home():
    return jsonify({"name": APP_NAME, "version": APP_VERSION, "status": "running"})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "time_utc": datetime.now(timezone.utc).isoformat()})


@app.route("/upload", methods=["GET", "POST"])
def upload_file():
    if request.method == "GET":
        return """
<!doctype html>
<html>
  <head><title>LexiScan Upload</title></head>
  <body style="font-family: Arial, sans-serif; max-width: 720px; margin: 40px auto;">
    <h2>LexiScan Auto - Upload</h2>
    <p>Upload a <code>.pdf</code> or <code>.txt</code> file using this form (POST /upload).</p>
    <form method="post" enctype="multipart/form-data">
      <input type="file" name="file" accept=".pdf,.txt" required />
      <button type="submit">Process</button>
    </form>
    <p style="margin-top: 18px;">
      Optional query: <code>?save_output=true</code> to save JSON in the outputs folder.
    </p>
  </body>
</html>
"""

    if "file" not in request.files:
        return _error("No file part in request", 400)

    file = request.files["file"]
    if not file or not file.filename:
        return _error("No file selected", 400)

    if not _allowed_file(file.filename):
        return _error("Only .pdf and .txt files are supported", 400)

    filename = secure_filename(file.filename)
    input_path = Path(UPLOAD_FOLDER) / filename
    file.save(input_path)

    text = extract_text(str(input_path))
    if not text.strip():
        return _error("Could not extract text from the uploaded file", 422)

    raw_entities = extract_entities(text)
    validated_entities = validate_entities(raw_entities)

    response = {
        "status": "success",
        "file_name": filename,
        "char_count": len(text),
        "entities": validated_entities,
        "meta": {
            "app_version": APP_VERSION,
            "processed_at_utc": datetime.now(timezone.utc).isoformat(),
        },
    }

    save_output = request.args.get("save_output", "true").lower() == "true"
    if save_output:
        response["output_json_path"] = _save_output_json(response, filename)

    return jsonify(response), 200


@app.errorhandler(413)
def file_too_large(_error_obj):
    return _error("File too large. Max file size is 20MB by default.", 413)


@app.errorhandler(500)
def internal_error(_error_obj):
    return _error("Internal server error", 500)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=os.getenv("DEBUG", "false").lower() == "true")
