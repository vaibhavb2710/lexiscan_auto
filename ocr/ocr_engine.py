import os
from pathlib import Path

import pdfplumber
import pytesseract
from PIL import ImageOps


TESSERACT_CMD = os.getenv("TESSERACT_CMD")
if TESSERACT_CMD:
    pytesseract.pytesseract.tesseract_cmd = str(Path(TESSERACT_CMD))


def _ocr_page(page):
    # Convert PDF page to an image and pre-process for OCR stability.
    page_image = page.to_image(resolution=300).original
    gray = ImageOps.grayscale(page_image)
    contrasted = ImageOps.autocontrast(gray)
    return pytesseract.image_to_string(contrasted, config="--oem 3 --psm 6")


def extract_text_from_pdf(file_path):
    text_chunks = []

    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = (page.extract_text() or "").strip()
            if page_text:
                text_chunks.append(page_text)
            else:
                try:
                    text_chunks.append(_ocr_page(page).strip())
                except Exception:
                    # Skip OCR-failed pages but continue the rest of the document.
                    text_chunks.append("")

    return "\n".join(chunk for chunk in text_chunks if chunk)


def extract_text(file_path):
    suffix = Path(file_path).suffix.lower()
    if suffix == ".pdf":
        return extract_text_from_pdf(file_path)
    if suffix == ".txt":
        with open(file_path, "r", encoding="utf-8", errors="ignore") as handle:
            return handle.read()
    return ""
