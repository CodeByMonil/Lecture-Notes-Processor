from __future__ import annotations
from pathlib import Path
import json
import numpy as np
from typing import List, Dict, Tuple, Optional
from .gemini_client import embed_texts  # ✅ Correct import

KB_DIR = Path("data/kb")
CHUNKS = KB_DIR / "kb_chunks.jsonl"
EMB_FILE = KB_DIR / "kb_embeddings.npy"
META = KB_DIR / "kb_meta.json"

def _load_kb():
    """Safely load KB data with proper error handling"""
    try:
        if not CHUNKS.exists():
            print("KB chunks file not found")
            return [], np.array([]), np.array([])
        
        if not EMB_FILE.exists():
            print("KB embeddings file not found")
            return [], np.array([]), np.array([])
        
        # Load chunks
        chunks = []
        with open(CHUNKS, "r", encoding="utf-8") as f:
            for line in f:
                chunks.append(json.loads(line.strip()))
        
        # Load embeddings safely
        E = np.load(EMB_FILE)
        print(f"Loaded embeddings shape: {E.shape}, dtype: {E.dtype}")
        
        # Convert to float32 if needed
        if E.dtype != np.float32:
            E = E.astype(np.float32)
        
        # Precompute norms safely
        if len(E) > 0:
            norms = np.linalg.norm(E, axis=1, keepdims=True)
            norms = np.clip(norms, 1e-12, None)
        else:
            norms = np.array([])
            
        print(f"✅ Loaded {len(chunks)} chunks, {len(E)} embeddings")
        return chunks, E, norms
        
    except Exception as e:
        print(f"❌ Error loading KB: {e}")
        return [], np.array([]), np.array([])

_CHUNKS, _E, _NORMS = _load_kb()

def cosine_topk(query_vec: np.ndarray, k: int = 8) -> List[int]:
    """Find top-k most similar chunks using cosine similarity"""
    if len(_E) == 0 or len(_CHUNKS) == 0:
        print("❌ No embeddings or chunks available")
        return []
    
    try:
        # Ensure query_vec is proper format
        if isinstance(query_vec, list):
            query_vec = np.array(query_vec, dtype=np.float32)
        
        q = query_vec.reshape(1, -1)
        qn = np.linalg.norm(q, axis=1, keepdims=True)
        qn = np.clip(qn, 1e-12, None)
        
        # Compute cosine similarities
        if len(_NORMS) > 0:
            sims = (_E @ q.T) / (_NORMS * qn)
        else:
            # Fallback: compute norms on the fly
            E_norms = np.linalg.norm(_E, axis=1, keepdims=True)
            E_norms = np.clip(E_norms, 1e-12, None)
            sims = (_E @ q.T) / (E_norms * qn)
        
        sims = sims.squeeze()
        
        # Get top-k indices
        idx = np.argsort(-sims)[:min(k, len(sims))]
        return idx.tolist()
        
    except Exception as e:
        print(f"❌ Error in cosine_topk: {e}")
        return []

def retrieve_context(cleaned_text: str, k: int = 8) -> str:
    """Return top-k relevant context as a single string"""
    if len(_CHUNKS) == 0:
        return "No knowledge base available."
    
    if len(cleaned_text.strip()) < 10:
        return "Query text too short for retrieval."
    
    try:
        print(f"🔍 Retrieving context for query: {cleaned_text[:100]}...")
        
        # Get query embedding using your Gemini client
        embeddings = embed_texts([cleaned_text])
        if not embeddings or len(embeddings) == 0:
            return "Failed to generate query embedding."
        
        qv = embeddings[0]
        print(f"✅ Generated query embedding of length: {len(qv)}")
        
        # Get top matches
        top_idx = cosine_topk(qv, k=k)
        
        if not top_idx:
            return "No relevant context found in knowledge base."
        
        print(f"✅ Found {len(top_idx)} relevant chunks")
        
        # Combine top matches into a single context string
        context_parts = []
        for i, idx in enumerate(top_idx):
            if idx < len(_CHUNKS):
                chunk = _CHUNKS[idx]
                score = 0.0
                
                # Calculate similarity score
                try:
                    chunk_vec = _E[idx]
                    score = float(np.dot(chunk_vec, qv) / (np.linalg.norm(chunk_vec) * np.linalg.norm(qv)))
                except:
                    pass
                
                context_parts.append(f"### Relevant Content {i+1} (Score: {score:.3f})")
                context_parts.append(f"**Course**: {chunk.get('course', 'Unknown')}")
                context_parts.append(f"**Topics**: {', '.join(chunk.get('topic_tags', []))}")
                context_parts.append(f"**Content**: {chunk.get('text', '')}")
                context_parts.append("")
        
        return "\n".join(context_parts)
        
    except Exception as e:
        print(f"❌ Error in retrieve_context: {e}")
        return f"Knowledge base retrieval error: {str(e)}"

def simple_retrieve_context(cleaned_text: str, k: int = 8) -> str:
    """Simple retriever that doesn't use embeddings"""
    try:
        if not CHUNKS.exists():
            return "Knowledge base not available."
        
        chunks = []
        with open(CHUNKS, "r", encoding="utf-8") as f:
            for line in f:
                chunks.append(json.loads(line.strip()))
        
        if not chunks:
            return "Knowledge base is empty."
        
        # Simple keyword-based matching as fallback
        query_words = set(cleaned_text.lower().split())
        relevant_chunks = []
        
        for chunk in chunks[:k]:
            chunk_text = chunk.get('text', '').lower()
            chunk_course = chunk.get('course', '').lower()
            
            # Simple word matching
            matches = len(query_words.intersection(set(chunk_text.split())))
            if matches > 0:
                relevant_chunks.append(chunk)
        
        if not relevant_chunks:
            relevant_chunks = chunks[:k]  # Fallback to first k chunks
        
        context_parts = []
        for i, chunk in enumerate(relevant_chunks):
            context_parts.append(f"### Content {i+1}")
            context_parts.append(f"**Course**: {chunk.get('course', 'Unknown')}")
            context_parts.append(f"**Content**: {chunk.get('text', '')}")
            context_parts.append("")
        
        return "\n".join(context_parts)
        
    except Exception as e:
        return f"Simple retrieval error: {str(e)}"

# Test function
def test_retrieval():
    """Test the retrieval system"""
    test_text = "machine learning basics"
    print("Testing retrieval with:", test_text)
    
    # Try the main retriever first
    try:
        result = retrieve_context(test_text, k=2)
        print("Main retriever result:")
        print(result[:500] + "..." if len(result) > 500 else result)
    except Exception as e:
        print(f"Main retriever failed: {e}")
        # Fallback to simple retriever
        result = simple_retrieve_context(test_text, k=2)
        print("Simple retriever result:")
        print(result[:500] + "..." if len(result) > 500 else result)
    
    return result

if __name__ == "__main__":
    test_retrieval()