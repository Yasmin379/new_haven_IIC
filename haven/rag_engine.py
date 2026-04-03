"""
HAVEN RAG Engine — Simple Keyword Version
Place this file at: haven/rag_engine.py
"""

import os
import pickle

BASE_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_PATH = os.path.join(BASE_DIR, "haven_dataset.txt")

_knowledge_base = None


def _load_knowledge():
    global _knowledge_base
    if _knowledge_base is None:
        if not os.path.exists(DATASET_PATH):
            _knowledge_base = []
            return _knowledge_base
        with open(DATASET_PATH, "r", encoding="utf-8") as f:
            text = f.read()
        sections = [s.strip() for s in text.split("---") if len(s.strip()) > 50]
        _knowledge_base = sections
        print(f"[HAVEN RAG] Loaded {len(_knowledge_base)} knowledge sections.")
    return _knowledge_base


def retrieve(query, top_k=2):
    """Simple keyword-based retrieval."""
    sections = _load_knowledge()
    if not sections:
        return []

    query_words = set(query.lower().split())
    # Remove common stop words so matching is more meaningful
    stop_words = {'i', 'am', 'is', 'the', 'a', 'an', 'and', 'or', 'but', 'in',
                  'on', 'at', 'to', 'for', 'of', 'with', 'my', 'me', 'it', 'so',
                  'do', 'not', 'feel', 'feeling', 'very', 'really', 'just', 'get'}
    query_words = query_words - stop_words

    scored = []
    for section in sections:
        section_lower = section.lower()
        score = sum(1 for word in query_words if word in section_lower)
        if score > 0:
            scored.append((score, section))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [s[1] for s in scored[:top_k]]


def build_prompt(user_message, retrieved_chunks):
    if retrieved_chunks:
        context = "\n".join([chunk[:200] for chunk in retrieved_chunks[:2]])
        return f"Context: {context}\n\nStudent says: {user_message}"
    return user_message

def build_index():
    """No-op for simple version."""
    sections = _load_knowledge()
    print(f"[HAVEN RAG] Simple mode ready with {len(sections)} sections.")
    return len(sections)
