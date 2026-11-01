#!/usr/bin/env bash
# تشغيل حاوية Nemotron OCR v2 (NIM) — يتطلب NVIDIA GPU + Docker + NVIDIA Container Toolkit.
# المنفذ على الجهاز المضيف: 8001 (لتفادي التعارض مع Flask الذي يعمل على 8000).
set -euo pipefail

# المفتاح مضمّن هنا بطلب صريح من مالك المشروع — يمكن تجاوزه عبر متغير البيئة NGC_API_KEY.
export NGC_API_KEY="${NGC_API_KEY:-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}"
export LOCAL_NIM_CACHE="${LOCAL_NIM_CACHE:-$HOME/.cache/nim}"

mkdir -p "$LOCAL_NIM_CACHE/cache" "$LOCAL_NIM_CACHE/weights"

docker run -it --rm --name="nemotron-ocr-v2" \
  --runtime=nvidia \
  --gpus '"device=0"' \
  --shm-size=16GB \
  -e NGC_API_KEY \
  -e NIM_ENGINE_MODEL_DOWNLOAD_PROVIDER=ngc \
  -v "$LOCAL_NIM_CACHE/cache:/opt/cache" \
  -v "$LOCAL_NIM_CACHE/weights:/model" \
  -u "$(id -u)" \
  -p 8001:8000 \
  nvcr.io/nim/nvidia/nemotron-ocr-v2:latest
