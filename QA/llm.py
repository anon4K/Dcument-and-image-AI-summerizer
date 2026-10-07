import os
import asyncio
from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
MODEL = "gemini-3.5-flash-lite"


async def _with_retry(stream_fn, *args, retries=2):
    for attempt in range(retries + 1):
        try:
            async for item in stream_fn(*args):
                yield item
            return
        except Exception as e:
            if "UNAVAILABLE" in str(e) and attempt < retries:
                await asyncio.sleep(2 * (attempt + 1))  # 2s, then 4s
                continue
            raise


async def stream_summary(text: str):
    async for item in _with_retry(_raw_stream_summary, text):
        yield item


async def _raw_stream_summary(text: str):
    prompt = f"Summarize the following document in a short paragraph, then list the 3 most important points:\n\n{text}"
    response = await client.aio.models.generate_content_stream(model=MODEL, contents=prompt)
    async for chunk in response:
        if chunk.text:
            yield "token", chunk.text
    yield "usage", {"input_tokens": 0, "output_tokens": 0}


async def stream_image_analysis(image_bytes: bytes, mime_type: str):
    async for item in _with_retry(_raw_stream_image_analysis, image_bytes, mime_type):
        yield item


async def _raw_stream_image_analysis(image_bytes: bytes, mime_type: str):
    image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
    prompt = "Describe what's in this image in detail, and note anything notable."
    response = await client.aio.models.generate_content_stream(model=MODEL, contents=[image_part, prompt])
    async for chunk in response:
        if chunk.text:
            yield "token", chunk.text
    yield "usage", {"input_tokens": 0, "output_tokens": 0}