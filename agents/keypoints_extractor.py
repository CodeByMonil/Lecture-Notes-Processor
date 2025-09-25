from __future__ import annotations
from pathlib import Path
from typing import Dict, Any
from pydantic import BaseModel
import json

from .gemini_client import gen_text
from utils.fs import DATA_PROC, ts

# --------------------------
# Data Models
# --------------------------
class Bullet(BaseModel):
    text: str
    timestamp: str | None = None

class Section(BaseModel):
    heading: str
    bullets: list[Bullet]

class Outline(BaseModel):
    title: str
    topics: list[str]
    sections: list[Section]

# --------------------------
# Convert Pydantic to schema
# --------------------------
def pydantic_to_schema(model: type[BaseModel]) -> dict:
    """
    Return Pydantic model schema as dict for Gemini's response_schema.
    """
    return model.model_json_schema()

# --------------------------
# System Instruction
# --------------------------
SYS_PROMPT = """You are a Key Points Extractor Agent.
Given a cleaned lecture transcript, produce a concise outline JSON.

Guidelines:
- Identify 4–8 main sections (logical chunks of the lecture).
- Each section: a short heading + 3–6 bullet points.
- Include timestamps if present in the transcript (copy or approximate).
- Keep bullets short and scannable.
- DO NOT include any text outside the JSON schema.
"""

# --------------------------
# Extract Outline
# --------------------------
def extract_outline(cleaned_transcript: str) -> tuple[Outline, Path]:
    """
    Extracts a structured outline (JSON) from the cleaned transcript.
    Returns the Outline object and the saved JSON path.
    """
    schema = pydantic_to_schema(Outline)

    prompt = (
        "Create an outline from the following transcript:\n\n"
        + cleaned_transcript[:120000]  # clip to avoid token overflow
    )

    resp = gen_text(
        prompt,
        system_instruction=SYS_PROMPT,
        response_schema=schema,
        temperature=0.2,
    )

    # Handle response
    if hasattr(resp, "parsed") and resp.parsed:
        data = resp.parsed
    else:
        try:
            data = json.loads(resp.text)
        except Exception:
            raise ValueError("❌ Could not parse outline JSON from Gemini response")

    outline = Outline.model_validate(data)

    out_path = DATA_PROC / f"outline_{ts()}.json"
    out_path.write_text(outline.model_dump_json(indent=2), encoding="utf-8")

    return outline, out_path
