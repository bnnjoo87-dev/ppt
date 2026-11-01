"""
Nemotron OCR v2 — fallback يدوي فقط (لا يُستدعى تلقائيًا).
يتطلب NVIDIA GPU + تشغيل حاوية NIM محليًا:  ./run_ocr_nim.sh
الحاوية تستمع على المنفذ 8001 على الجهاز المضيف (لتفادي التعارض مع Flask على 8000).
"""

import base64
import os

import requests


# ⚠️ مفتاح NGC: يُستخدم فقط عند docker login nvcr.io وسحب حاوية nemotron-ocr-v2،
# وليس كـ Bearer key أمام نقطة النهاية المحلية /v1/ocr.
DEFAULT_NGC_API_KEY = "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"


class NvidiaOCRError(Exception):
    pass


def ocr_page(image_bytes: bytes, mime_type: str = "image/png") -> dict:
    ocr_url = os.getenv("NVIDIA_OCR_URL") or "http://localhost:8001/v1/ocr"

    image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    payload = {
        "input": [
            {
                "type": "image_url",
                "url": f"data:{mime_type};base64,{image_b64}",
            }
        ]
    }

    try:
        response = requests.post(
            ocr_url,
            json=payload,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            timeout=120,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise NvidiaOCRError(f"Nemotron OCR request failed: {exc}") from exc

    try:
        return response.json()
    except ValueError as exc:
        raise NvidiaOCRError("Nemotron OCR returned invalid JSON.") from exc
