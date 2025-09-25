from __future__ import annotations
import os
from typing import Any, Dict, Optional, List, Union
from google import genai
from google.genai import types
from dotenv import load_dotenv

# --------------------------
# Load environment --
# --------------------------
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError(
        "❌ GEMINI_API_KEY not set. Create a .env file from .env.example and add your key."
    )

MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")  # default model

# --------------------------
# Client
# --------------------------
client = genai.Client(api_key=GEMINI_API_KEY)

# --------------------------
# Text generation
# --------------------------
def gen_text(
    prompt: Union[str, List[Any]],
    system_instruction: Optional[str] = None,
    temperature: float = 0.2,
    response_schema: Optional[Any] = None,
    mime: Optional[str] = None,
    attachments: Optional[list] = None,
) -> types.GenerateContentResponse:
    """
    Generate text/content from Gemini.
    - prompt: str or list of content blocks
    - system_instruction: optional system message
    - temperature: randomness factor
    - response_schema: optional pydantic schema for structured output
    - mime: enforce mime type (e.g. application/json)
    - attachments: list of pre-processed file attachments
    """
    cfg = types.GenerateContentConfig(
        temperature=temperature,
        system_instruction=system_instruction,
        response_mime_type=mime or ("application/json" if response_schema else None),
        response_schema=response_schema,
    )

    contents: List[Any] = []
    if attachments:
        contents.extend(attachments)
    contents.append(prompt)

    res = client.models.generate_content(
        model=MODEL,
        contents=contents,
        config=cfg,
    )
    return res

# --------------------------
# Embedding
# --------------------------
def embed_texts(texts: List[str], model: str = "text-embedding-004") -> List[List[float]]:
    """
    Generate embeddings for a list of texts.
    Returns a list of vectors (list of floats).
    """
    vectors: List[List[float]] = []
    BATCH_SIZE = 32

    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        resp = client.models.embed_content(model=model, contents=batch)
        for emb in resp.embeddings:
            vectors.append(emb.values)

    return vectors

# --------------------------
# File upload
# --------------------------
def upload_file(path: str):
    """
    Upload file to Gemini for multimodal usage.
    """
    return client.files.upload(file=path)

# --------------------------
# Token counting (heuristic)
# --------------------------
def count_tokens(text: str) -> int:
    """
    Approximate token count for budgeting.
    Gemini tokens ≈ 4 characters/token in English.
    """
    return max(1, len(text) // 4)
