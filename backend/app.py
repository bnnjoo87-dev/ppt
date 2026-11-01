"""
academic-ppt-ai — Flask API

Endpoints:
  GET  /            → خدمة frontend/index.html (نفس الأصل = لا مشاكل CORS)
  GET  /health      → حالة الخدمة
  POST /api/parse   → Nemotron 3.5 Parse (Cloud API) — المحرك الأساسي
  POST /api/ocr     → Nemotron OCR v2 (NIM محلي) — fallback يدوي فقط

المفاتيح تُقرأ من متغيرات البيئة إن وُجدت، وإلا تُستخدم القيم الافتراضية
المضمّنة داخل nvidia_parse.py / nvidia_ocr.py.
"""

import os

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from nvidia_ocr import NvidiaOCRError, ocr_page
from nvidia_parse import NvidiaParseError, parse_page

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend"))

app = Flask(__name__)
CORS(app)


@app.get("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.get("/health")
def health():
    return jsonify(
        {
            "ok": True,
            "service": "academic-ppt-ai",
            "engines": {
                "parse": True,
                "ocr_fallback": True,
            },
        }
    )


@app.post("/api/parse")
def parse_endpoint():
    if "document" not in request.files:
        return jsonify(
            {
                "ok": False,
                "error": "No document uploaded.",
            }
        ), 400

    document = request.files["document"]
    filename = document.filename or "page.jpg"
    image_bytes = document.read()

    if not image_bytes:
        return jsonify(
            {
                "ok": False,
                "error": "Empty document.",
            }
        ), 400

    try:
        result = parse_page(
            image_bytes=image_bytes,
            filename=filename,
        )
        return jsonify(
            {
                "ok": True,
                "engine": result["engine"],
                "content": result["content"],
            }
        )

    except NvidiaParseError as parse_error:
        # فشل Parse → لا نستدعي OCR تلقائيًا؛
        # الواجهة تعرض زر التجربة اليدوي فقط.
        return jsonify(
            {
                "ok": False,
                "engine": "nemotron-3.5-parse",
                "fallback_available": True,
                "error": str(parse_error),
            }
        ), 502


@app.post("/api/ocr")
def ocr_endpoint():
    if "document" not in request.files:
        return jsonify(
            {
                "ok": False,
                "error": "No document uploaded.",
            }
        ), 400

    document = request.files["document"]
    image_bytes = document.read()

    if not image_bytes:
        return jsonify(
            {
                "ok": False,
                "error": "Empty document.",
            }
        ), 400

    mime_type = document.mimetype or "image/png"

    try:
        result = ocr_page(
            image_bytes=image_bytes,
            mime_type=mime_type,
        )
        return jsonify(
            {
                "ok": True,
                "engine": "nemotron-ocr-v2",
                "result": result,
            }
        )

    except NvidiaOCRError as exc:
        return jsonify(
            {
                "ok": False,
                "engine": "nemotron-ocr-v2",
                "error": str(exc),
            }
        ), 502


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8000,
        debug=False,
    )
