from __future__ import annotations
from pathlib import Path
import json
import numpy as np
from typing import List, Dict, Tuple, Optional
from .gemini_client import embed_texts  # you already have a client; we'll add embed_texts below

KB_DIR = Path("data/kb")
CHUNKS = KB_DIR / "kb_chunks.jsonl"
EMB_FILE = KB_DIR / "kb_embeddings.npy"
META = KB_DIR / "kb_meta.json"

def _load_kb():
    if not (CHUNKS.exists() and EMB_FILE.exists() and META.exists()):
        return [], None, None
    chunks = [json.loads(x) for x in open(CHUNKS, "r", encoding="utf-8")]
    E = np.load(EMB_FILE).astype("float32")
    with open(META, "r", encoding="utf-8") as f:
        meta = json.load(f)
    # Precompute norms if not normalized
    norms = np.linalg.norm(E, axis=1, keepdims=True)
    norms = np.clip(norms, 1e-12, None)
    return chunks, E, norms

_CHUNKS, _E, _NORMS = _load_kb()

def cosine_topk(query_vec: np.ndarray, k: int = 8) -> List[int]:
    # query_vec: (D,) or (1,D)
    q = query_vec.astype("float32").reshape(1, -1)
    qn = np.linalg.norm(q, axis=1, keepdims=True)
    qn = np.clip(qn, 1e-12, None)
    sims = ( _E @ q.T ) / (_NORMS.squeeze() * qn.squeeze())
    sims = sims.squeeze()
    idx = np.argsort(-sims)[:k]
    return idx.tolist()

def retrieve_context(cleaned_text: str, k: int = 8) -> List[Dict]:
    """Return top-k snippet dicts: {text, parent_id, course, topic_tags, score}"""
    if len(_CHUNKS) == 0:
        return []
    qv = embed_texts([cleaned_text])[0]  # (D,)
    top_idx = cosine_topk(qv, k=k)
    out = []
    for i in top_idx:
        row = _CHUNKS[i].copy()
        # crude score recompute to show
        score = float(np.dot(_E[i], qv) / (np.linalg.norm(_E[i]) * np.linalg.norm(qv)))
        row["score"] = round(score, 4)
        out.append(row)
    return out
