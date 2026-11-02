import os
import json
import base64
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
# السماح بجميع المصادر بما فيها فتح الملف محلياً على الهاتف (Origin: null)
CORS(app, resources={r"/*": {"origins": "*"}})

# مفاتيح الـ API الخاصة بك
PARSE_API_KEY = os.getenv(
    "PARSE_API_KEY",
    "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"
)
OCR_API_KEY = os.getenv(
    "OCR_API_KEY",
    "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"
)

PARSE_URL = "https://ai.api.nvidia.com/v1/retrieval/nvidia/nemotron-3.5-parse/parse"
OCR_URL = "https://ai.api.nvidia.com/v1/cv/nvidia/nemotron-ocr-v2"


@app.route("/", methods=["GET"])
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok", "message": "Backend is running"}), 200


def call_nemotron_parse(image_bytes, filename, mime_type):
    """النموذج الأول: Nemotron 3.5 Parse"""
    headers = {
        "Authorization": f"Bearer {PARSE_API_KEY}",
        "Accept": "application/json"
    }
    files = {
        "document": (filename, image_bytes, mime_type),
        "options": (None, json.dumps({"decoding": {"max_output_tokens": 1024}}), "application/json")
    }
    response = requests.post(PARSE_URL, headers=headers, files=files, timeout=60)
    response.raise_for_status()
    data = response.json()
    return data.get("content", "")


def call_nemotron_ocr(image_bytes, mime_type):
    """النموذج الثاني: Nemotron OCR v2 عبر السحابة"""
    b64_image = base64.b64encode(image_bytes).decode("utf-8")
    headers = {
        "Authorization": f"Bearer {OCR_API_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    payload = {
        "input": [
            {
                "type": "image_url",
                "url": f"data:{mime_type};base64,{b64_image}"
            }
        ]
    }
    response = requests.post(OCR_URL, headers=headers, json=payload, timeout=60)
    response.raise_for_status()
    data = response.json()
    return data


@app.route("/parse", methods=["POST"])
@app.route("/ocr", methods=["POST"])
def process_image():
    if "file" not in request.files and "document" not in request.files:
        return jsonify({"error": "لم يتم إرفاق صورة"}), 400

    file = request.files.get("file") or request.files.get("document")
    image_bytes = file.read()
    filename = file.filename or "image.jpg"
    mime_type = file.mimetype or "image/jpeg"

    # المحاولة بالنموذج الأول (Parse) ثم التبديل للنموذج الثاني (OCR) عند الحاجة
    try:
        text = call_nemotron_parse(image_bytes, filename, mime_type)
        return jsonify({"status": "success", "model": "nemotron-3.5-parse", "text": text, "content": text})
    except Exception as parse_err:
        try:
            ocr_result = call_nemotron_ocr(image_bytes, mime_type)
            return jsonify({"status": "success", "model": "nemotron-ocr-v2", "result": ocr_result, "content": str(ocr_result)})
        except Exception as ocr_err:
            return jsonify({
                "error": "فشل استخراج النص في كلا النموذجين",
                "parse_error": str(parse_err),
                "ocr_error": str(ocr_err)
            }), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
