import json
import os

import requests


NVIDIA_PARSE_URL = (
    "https://ai.api.nvidia.com/"
    "v1/retrieval/nvidia/nemotron-3.5-parse/parse"
)


class NvidiaParseError(Exception):
    pass


def parse_page(image_bytes: bytes, filename: str = "page.jpg") -> dict:
    api_key = os.getenv("NVIDIA_PARSE_API_KEY")

    if not api_key:
        raise NvidiaParseError(
            "NVIDIA_PARSE_API_KEY is not configured."
        )

    filename_lower = filename.lower()

    if filename_lower.endswith(".png"):
        content_type = "image/png"
    elif filename_lower.endswith((".jpg", ".jpeg")):
        content_type = "image/jpeg"
    else:
        raise NvidiaParseError(
            "Nemotron Parse requires PNG or JPEG page images."
        )

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
                        "max_output_tokens": 1024
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
            timeout=180,
        )
    except requests.RequestException as exc:
        raise NvidiaParseError(
            f"Nemotron Parse request failed: {exc}"
        ) from exc

    if not response.ok:
        try:
            error_data = response.json()
        except ValueError:
            error_data = response.text[:4000]

        raise NvidiaParseError(
            f"NVIDIA HTTP {response.status_code}: "
            f"{error_data}"
        )

    try:
        result = response.json()
    except ValueError as exc:
        raise NvidiaParseError(
            "NVIDIA returned invalid JSON."
        ) from exc

    if "content" not in result:
        raise NvidiaParseError(
            f"NVIDIA Parse response has no content: {result}"
        )

    return {
        "engine": "nemotron-3.5-parse",
        "content": result["content"],
        "raw": result,
    }
