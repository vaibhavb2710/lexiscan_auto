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
<!DOCTYPE html>
<html>
<head>
<title>LexiScan Auto - AI Legal Analyzer</title>

<style>

*{
margin:0;
padding:0;
box-sizing:border-box;
font-family: 'Segoe UI', sans-serif;
}

body{
height:100vh;
background: linear-gradient(135deg,#0f2027,#203a43,#2c5364);
display:flex;
justify-content:center;
align-items:center;
color:white;
}

.container{
width:700px;
background: rgba(255,255,255,0.08);
backdrop-filter: blur(15px);
padding:40px;
border-radius:16px;
box-shadow:0 20px 40px rgba(0,0,0,0.4);
text-align:center;
}

h1{
font-size:36px;
margin-bottom:10px;
}

.subtitle{
opacity:0.8;
margin-bottom:30px;
}

.upload-box{
border:2px dashed rgba(255,255,255,0.4);
padding:40px;
border-radius:12px;
cursor:pointer;
transition:0.3s;
}

.upload-box:hover{
background:rgba(255,255,255,0.1);
}

button{
margin-top:20px;
padding:12px 30px;
border:none;
border-radius:30px;
background:linear-gradient(45deg,#00c6ff,#0072ff);
color:white;
font-size:16px;
cursor:pointer;
transition:0.3s;
}

button:hover{
transform:scale(1.05);
}

#loader{
display:none;
margin-top:20px;
}

.result{
margin-top:30px;
text-align:left;
background:rgba(0,0,0,0.3);
padding:20px;
border-radius:10px;
max-height:300px;
overflow:auto;
}

pre{
white-space:pre-wrap;
word-wrap:break-word;
}

</style>

</head>

<body>

<div class="container">

<h1>LexiScan Auto</h1>
<div class="subtitle">AI Powered Legal Contract Analyzer</div>

<form id="uploadForm">

<div class="upload-box">
<input type="file" id="fileInput" name="file" accept=".pdf,.txt" required>
<p>Drag & Drop or Select a Contract</p>
</div>

<button type="submit">Analyze Document</button>

</form>

<div id="loader">
⏳ AI is analyzing your contract...
</div>

<div class="result" id="resultBox" style="display:none;">
<h3>Extracted Entities</h3>
<pre id="jsonOutput"></pre>
</div>

</div>

<script>

const form = document.getElementById("uploadForm")
const loader = document.getElementById("loader")
const resultBox = document.getElementById("resultBox")
const jsonOutput = document.getElementById("jsonOutput")

form.addEventListener("submit", async function(e){

e.preventDefault()

loader.style.display = "block"
resultBox.style.display = "none"

const fileInput = document.getElementById("fileInput")
const formData = new FormData()

formData.append("file", fileInput.files[0])

const response = await fetch("/upload",{
method:"POST",
body:formData
})

const data = await response.json()

loader.style.display = "none"
resultBox.style.display = "block"

jsonOutput.textContent = JSON.stringify(data,null,2)

})

</script>

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