from __future__ import annotations
from pathlib import Path
from typing import Tuple, Optional
from pydub import AudioSegment
from pypdf import PdfReader
from .gemini_client import gen_text, upload_file
from .gemini_client import types  # re-exported
from utils.fs import DATA_PROC, ts
from utils.text import strip_fillers, squeeze_spaces



SYS_PROMPT = """You are a Transcript Cleaner Agent.
Goals:
- Improve punctuation & casing.
- Remove filler words conservatively (do not change meaning).
- Preserve speaker labels if present.
- If timestamps exist (e.g., [mm:ss]), keep them; if not, insert one every ~60 seconds ONLY for audio/video inputs.
Output ONLY the cleaned transcript text.
"""

def _read_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    pages = [p.extract_text() or "" for p in reader.pages]
    return "\n\n".join(pages)

def _load_text_like(path: Path) -> str:
    if path.suffix.lower() in {".txt", ".md"}:
        return Path(path).read_text(encoding="utf-8", errors="ignore")
    if path.suffix.lower() in {".pdf"}:
        return _read_pdf(path)
    raise ValueError("Unsupported text file: " + str(path))

def transcribe_and_clean(input_path: str) -> Tuple[str, Path]:
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(path)

    if path.suffix.lower() in {".txt", ".md", ".pdf"}:
        raw = _load_text_like(path)
        # light local cleanup before LLM pass
        rough = squeeze_spaces(strip_fillers(raw))
        resp = gen_text(rough, system_instruction=SYS_PROMPT, temperature=0.1)
        cleaned = resp.text.strip()
    else:
        # audio/video branch – upload and ask Gemini to transcribe + clean
        file_part = upload_file(str(path))
        prompt = (
            "Transcribe this audio/video. Use readable punctuation, minimal fillers.\n"
            "Insert a [mm:ss] timestamp about every 60 seconds.\n"
            "If speakers are discernible, label them Speaker 1, Speaker 2, ...\n"
            "Return ONLY the cleaned transcript text."
        )
        resp = gen_text(prompt, system_instruction=SYS_PROMPT, attachments=[file_part])
        cleaned = resp.text.strip()

    out_path = DATA_PROC / f"cleaned_{ts()}.txt"
    out_path.write_text(cleaned, encoding="utf-8")
    return cleaned, out_path
