"""
Nemotron 3.5 Parse — المحرك الأساسي لاستخراج النص + الجداول + الـ layout.
Cloud API: https://ai.api.nvidia.com/v1/retrieval/nvidia/nemotron-3.5-parse/parse

ملاحظة أمنية: المفتاح مضمّن هنا كقيمة افتراضية بطلب صريح من مالك المشروع،
ويمكن تجاوزه دون تعديل الكود عبر متغير البيئة NVIDIA_PARSE_API_KEY (ملف .env).
⚠️ قبل جعل المستودع عامًا على GitHub: اعكس المفتاح (revoke) وأنشئ مفتاحًا جديدًا.
"""

import json
import os

import requests


DEFAULT_NVIDIA_PARSE_API_KEY = "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"

NVIDIA_PARSE_URL = (
    "https://ai.api.nvidia.com/"
    "v1/retrieval/nvidia/nemotron-3.5-parse/parse"
)


class NvidiaParseError(Exception):
    pass


def parse_page(image_bytes: bytes, filename: str = "page.jpg") -> dict:
    api_key = os.getenv("NVIDIA_PARSE_API_KEY") or DEFAULT_NVIDIA_PARSE_API_KEY

    if not api_key:
        raise NvidiaParseError("NVIDIA_PARSE_API_KEY is not configured.")

    content_type = "image/png" if filename.lower().endswith(".png") else "image/jpeg"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    }

    files = {
        "document": (
            filename,
            image_bytes,
            content_type,
        ),
        "options": (
            None,
            json.dumps(
                {
                    "decoding": {
                        "max_output_tokens": 4096,
                    }
                }
            ),
            "application/json",
        ),
    }

    try:
        response = requests.post(
            NVIDIA_PARSE_URL,
            headers=headers,
            files=files,
            timeout=120,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise NvidiaParseError(f"Nemotron Parse request failed: {exc}") from exc

    try:
        result = response.json()
    except ValueError as exc:
        raise NvidiaParseError("NVIDIA returned invalid JSON.") from exc

    if "content" not in result:
        raise NvidiaParseError(f"NVIDIA Parse response has no 'content': {result}")

    return {
        "engine": "nemotron-3.5-parse",
        "content": result["content"],
        "raw": result,
    }
