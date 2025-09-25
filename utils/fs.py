from __future__ import annotations
import os
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
DATA_IN = ROOT / "data" / "input"
DATA_PROC = ROOT / "data" / "processed"
SLIDES_OUT = ROOT / "outputs" / "slides"
RUNS = ROOT / "runs"

for p in [DATA_IN, DATA_PROC, SLIDES_OUT, RUNS]:
    p.mkdir(parents=True, exist_ok=True)

def ts() -> str:
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

def ensure_dir(path: Path) -> Path:
    Path(path).mkdir(parents=True, exist_ok=True)
    return Path(path)

def unique_path(base: Path, suffix: str) -> Path:
    base = base if base.suffix == "" else base.with_suffix("")
    candidate = base.with_suffix(suffix)
    i = 2
    while candidate.exists():
        candidate = base.with_name(base.name + f"_{i}").with_suffix(suffix)
        i += 1
    return candidate
