import base64
import os

import requests


class NvidiaOCRError(Exception):
    pass


def ocr_page(
    image_bytes: bytes,
    mime_type: str = "image/png",
) -> dict:

    ocr_url = os.getenv(
        "NVIDIA_OCR_URL",
        "http://localhost:8000/v1/ocr",
    )

    image_b64 = base64.b64encode(
        image_bytes
    ).decode("utf-8")

    payload = {
        "input": [
            {
                "type": "image_url",
                "url": (
                    f"data:{mime_type};base64,"
                    f"{image_b64}"
                ),
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
            timeout=180,
        )
    except requests.RequestException as exc:
        raise NvidiaOCRError(
            f"Nemotron OCR request failed: {exc}"
        ) from exc

    if not response.ok:
        try:
            error_data = response.json()
        except ValueError:
            error_data = response.text[:4000]

        raise NvidiaOCRError(
            f"OCR HTTP {response.status_code}: "
            f"{error_data}"
        )

    try:
        return response.json()
    except ValueError as exc:
        raise NvidiaOCRError(
            "Nemotron OCR returned invalid JSON."
        ) from exc
