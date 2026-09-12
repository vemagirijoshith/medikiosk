import base64
import os
from pathlib import Path
from typing import Any

import httpx
import pypdfium2 as pdfium
from dotenv import load_dotenv

from app.services.ai_service import (
    AIAuthenticationError,
    AIConnectionError,
    AIRateLimitError,
    AITimeoutError,
    AIUpstreamError,
)

load_dotenv()

OCR_BASE_URL = "https://ai.api.nvidia.com/v1/cv/nvidia/nemotron-ocr-v2"


def _image_data_url(content: bytes, content_type: str) -> str:
    encoded = base64.b64encode(content).decode("ascii")
    return f"data:{content_type};base64,{encoded}"


def _render_pdf_pages(path: Path) -> list[tuple[bytes, str]]:
    try:
        pdf = pdfium.PdfDocument(str(path))
        pages = []
        for index in range(len(pdf)):
            page = pdf[index]
            bitmap = page.render(scale=2)
            pil_image = bitmap.to_pil()
            from io import BytesIO

            output = BytesIO()
            pil_image.save(output, format="PNG")
            pages.append((output.getvalue(), "image/png"))
        return pages
    except Exception as exc:
        raise AIUpstreamError("Document could not be rendered for OCR") from exc


def _normalize_response(payload: dict[str, Any], page_index: int) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise AIUpstreamError("OCR provider returned an invalid response")
    page_payload = payload.get("data", payload.get("pages", [payload]))
    if not isinstance(page_payload, list):
        page_payload = [page_payload]
    page = page_payload[0] if page_payload else {}
    if not isinstance(page, dict):
        raise AIUpstreamError("OCR provider returned an invalid page")
    detections = page.get("text_detections", [])
    if not isinstance(detections, list):
        raise AIUpstreamError("OCR provider returned invalid text detections")
    text_parts = [
        detection.get("text", "")
        for detection in detections
        if isinstance(detection, dict) and isinstance(detection.get("text", ""), str)
    ]
    text = page.get("text", page.get("markdown", page.get("content", "")))
    if not text and text_parts:
        text = "\n".join(text_parts)
    return {
        "page": page_index,
        "text": text if isinstance(text, str) else "",
        "elements": detections or page.get("elements", []),
        "tables": page.get("tables", []),
        "confidence": page.get("confidence"),
        "raw_response": payload,
    }


async def extract_document_text(path: Path, content_type: str) -> dict[str, Any]:
    api_key = os.getenv("NVIDIA_API_KEY")
    base_url = os.getenv("NVIDIA_OCR_BASE_URL", OCR_BASE_URL).rstrip("/")
    if not api_key:
        raise AIAuthenticationError("OCR provider credentials are not configured")
    if not path.is_file():
        raise FileNotFoundError("Stored document file does not exist")

    if content_type == "application/pdf":
        pages = _render_pdf_pages(path)
    elif content_type in {"image/jpeg", "image/png"}:
        pages = [(path.read_bytes(), content_type)]
    else:
        raise AIUpstreamError("Unsupported OCR document type")

    normalized_pages = []
    async with httpx.AsyncClient(timeout=60.0) as client:
        for page_index, (content, page_type) in enumerate(pages):
            payload = {
                "input": [{"type": "image_url", "url": _image_data_url(content, page_type)}],
            }
            try:
                response = await client.post(
                    base_url,
                    headers={"Authorization": f"Bearer {api_key}"},
                    json=payload,
                )
            except httpx.TimeoutException as exc:
                raise AITimeoutError("OCR provider request timed out") from exc
            except httpx.RequestError as exc:
                raise AIConnectionError("OCR provider could not be reached") from exc
            if response.status_code in (401, 403):
                raise AIAuthenticationError("OCR provider authentication failed")
            if response.status_code == 429:
                raise AIRateLimitError("OCR provider is temporarily rate-limited")
            if response.status_code >= 400:
                raise AIUpstreamError("OCR provider returned an error")
            try:
                normalized_pages.append(_normalize_response(response.json(), page_index))
            except (ValueError, TypeError) as exc:
                raise AIUpstreamError("OCR provider returned malformed data") from exc

    text = "\n\n".join(page["text"] for page in normalized_pages if page["text"])
    return {
        "text": text,
        "pages": normalized_pages,
        "elements": [item for page in normalized_pages for item in page["elements"]],
        "tables": [item for page in normalized_pages for item in page["tables"]],
        "confidence": None,
        "raw_response": [page["raw_response"] for page in normalized_pages],
    }