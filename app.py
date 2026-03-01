from flask import Flask, request, jsonify
import os
from ocr.ocr_engine import extract_text_from_pdf
from nlp.ner_model import extract_entities
from utils.validator import validate_entities

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/upload", methods=["POST"])
def upload_file():
    file = request.files["file"]
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    text = extract_text_from_pdf(file_path)
    entities = extract_entities(text)
    validated = validate_entities(entities)

    return jsonify(validated)

if __name__ == "__main__":
    app.run(debug=True)