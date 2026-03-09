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

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
ALLOWED_EXTENSIONS = {"pdf", "txt"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024  # 20MB


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def error_response(message, status_code):
    return jsonify({"status": "error", "message": message}), status_code


def save_output_json(payload, source_filename):
    stem = Path(source_filename).stem
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    output_name = f"{stem}_{timestamp}.json"
    output_path = Path(OUTPUT_FOLDER) / output_name

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    return str(output_path)


@app.route("/")
def home():
    return """
    <html>
    <head>
        <title>LexiScan Auto</title>
        <style>
        body{
            font-family: Arial;
            background:#f4f6f8;
            text-align:center;
        }
        .box{
            background:white;
            width:500px;
            margin:auto;
            margin-top:100px;
            padding:40px;
            border-radius:10px;
            box-shadow:0 5px 15px rgba(0,0,0,0.1);
        }
        button{
            padding:10px 20px;
            background:#2ecc71;
            border:none;
            color:white;
            border-radius:5px;
        }
        </style>
    </head>

    <body>

    <div class="box">
        <h2>LexiScan Auto</h2>
        <p>Upload a Legal Contract (.pdf or .txt)</p>

        <form action="/upload" method="post" enctype="multipart/form-data">
            <input type="file" name="file" accept=".pdf,.txt" required>
            <br><br>
            <button type="submit">Process Document</button>
        </form>

        <p style="margin-top:20px;">
        Add <b>?save_output=true</b> to save JSON output
        </p>
    </div>

    </body>
    </html>
    """


@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "time_utc": datetime.now(timezone.utc).isoformat()
    })


@app.route("/upload", methods=["POST"])
def upload_file():

    if "file" not in request.files:
        return error_response("No file part in request", 400)

    file = request.files["file"]

    if file.filename == "":
        return error_response("No file selected", 400)

    if not allowed_file(file.filename):
        return error_response("Only PDF and TXT files are supported", 400)

    filename = secure_filename(file.filename)

    input_path = Path(UPLOAD_FOLDER) / filename
    file.save(input_path)

    # Extract text
    text = extract_text(str(input_path))

    if not text.strip():
        return error_response("Could not extract text from file", 422)

    # NER extraction
    raw_entities = extract_entities(text)

    # Validation layer
    validated_entities = validate_entities(raw_entities)

    response = {
        "status": "success",
        "file_name": filename,
        "char_count": len(text),
        "entities": validated_entities,
        "meta": {
            "app": APP_NAME,
            "version": APP_VERSION,
            "processed_at_utc": datetime.now(timezone.utc).isoformat()
        }
    }

    save_output = request.args.get("save_output", "true").lower() == "true"

    if save_output:
        output_path = save_output_json(response, filename)
        response["output_json_path"] = output_path

    return jsonify(response)


@app.errorhandler(413)
def file_too_large(e):
    return error_response("File too large. Max size is 20MB.", 413)


@app.errorhandler(500)
def server_error(e):
    return error_response("Internal server error", 500)


if __name__ == "__main__":
    app.run(debug=True)