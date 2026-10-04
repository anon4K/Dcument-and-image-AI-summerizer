import json
import time

from django.http import JsonResponse, StreamingHttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .llm import stream_summary, stream_image_analysis, stream_with_retry
from .extract import extract_text
from .models import QueryLog

IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
DOC_EXTENSIONS = (".pdf", ".docx", ".txt")
MAX_SIZE = 10 * 1024 * 1024
MAX_FILES = 5


def sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def upload_page(request):
    return render(request, "qa/upload.html")


async def history(request):
    logs = [log async for log in QueryLog.objects.order_by("-created_at")[:50]]
    return render(request, "qa/history.html", {"logs": logs})


async def process_one(upload):
    """Runs one file through extraction + LLM, returns (kind, text_or_None)."""
    file_bytes = upload.read()
    filename = upload.name
    content_type = upload.content_type

    if content_type in IMAGE_TYPES:
        return "image", stream_with_retry(stream_image_analysis, file_bytes, content_type, retries=2)
    if filename.lower().endswith(DOC_EXTENSIONS):
        text = extract_text(file_bytes, filename)
        if not text.strip():
            return "document", None
        return "document", stream_with_retry(stream_summary, text, retries=2)
    return None, None


@csrf_exempt
@require_POST
async def analyze(request):
    uploads = request.FILES.getlist("file")
    if not uploads:
        return JsonResponse({"error": "Attach at least one file under field name 'file'"}, status=400)
    if len(uploads) > MAX_FILES:
        return JsonResponse({"error": f"Max {MAX_FILES} files at once"}, status=400)
    for f in uploads:
        if f.size > MAX_SIZE:
            return JsonResponse({"error": f"{f.name} is over 10 MB"}, status=400)

        async def event_stream():
            try:
                for upload in uploads:
                    filename = upload.name
                    yield sse("file_start", {"filename": filename})

                    kind, generator = await process_one(upload)

                    if kind is None:
                        yield sse("file_error", {"filename": filename, "message": "Unsupported file type"})
                        continue
                    if generator is None:
                        yield sse("file_error", {"filename": filename, "message": "Couldn't extract any text"})
                        continue

                    log = await QueryLog.objects.acreate(filename=filename, file_kind=kind, question=f"[{kind}] {filename}")
                    start = time.monotonic()
                    parts = []
                    try:
                        async for evt, payload in generator:
                            if evt == "token":
                                parts.append(payload)
                                yield sse("token", {"filename": filename, "text": payload})
                            else:
                                log.input_tokens = payload["input_tokens"]
                                log.output_tokens = payload["output_tokens"]
                    except Exception as e:
                        yield sse("file_error", {"filename": filename, "message": f"{type(e).__name__}: {e}"})
                    finally:
                        log.answer = "".join(parts)
                        log.latency_ms = int((time.monotonic() - start) * 1000)
                        await log.asave()

                    yield sse("file_done", {"filename": filename, "log_id": log.id})
            finally:
                yield sse("all_done", {})

        response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
        response["Cache-Control"] = "no-cache"
        return response