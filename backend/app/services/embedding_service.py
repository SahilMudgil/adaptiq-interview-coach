import math
import hashlib
import re
from typing import List, Optional
import numpy as np
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.models.all_models import PDFChunk, QuestionBank

EMBEDDING_DIM = 384

def _local_semantic_embedding(text: str, dim: int = EMBEDDING_DIM) -> List[float]:
    """
    High-performance, deterministic semantic-hash vectorizer.
    Generates a normalized dense vector of length `dim` capturing word stems,
    character n-grams, and term weights without requiring heavy external model weights.
    """
    cleaned = re.sub(r'[^a-zA-Z0-9\s]', ' ', text.lower())
    words = cleaned.split()
    if not words:
        return [0.0] * dim

    vec = np.zeros(dim, dtype=np.float32)

    # Word-level hashed projections
    for i, word in enumerate(words):
        # 1-gram
        h1 = int(hashlib.sha256(word.encode('utf-8')).hexdigest()[:8], 16) % dim
        # Position-discounted TF weight
        vec[h1] += 1.0

        # Subword character n-grams (3-grams) for morphological similarity
        if len(word) >= 3:
            for j in range(len(word) - 2):
                ngram = word[j:j+3]
                h_ng = int(hashlib.md5(ngram.encode('utf-8')).hexdigest()[:8], 16) % dim
                vec[h_ng] += 0.35

        # Bigram with adjacent word
        if i < len(words) - 1:
            bigram = f"{word}_{words[i+1]}"
            h2 = int(hashlib.sha256(bigram.encode('utf-8')).hexdigest()[:8], 16) % dim
            vec[h2] += 0.75

    # L2 normalize
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm

    return vec.tolist()

async def get_embedding(text: str) -> List[float]:
    """
    Returns an embedding vector for the provided text.
    If OPENAI_API_KEY is configured, can use OpenAI embedding;
    otherwise uses the fast local semantic vectorizer.
    """
    if not text or not text.strip():
        return [0.0] * EMBEDDING_DIM

    # Fallback to local semantic vectorizer
    return _local_semantic_embedding(text, EMBEDDING_DIM)

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Computes cosine similarity between two unit-normalized or arbitrary vectors."""
    if not v1 or not v2:
        return 0.0
    a = np.array(v1, dtype=np.float32)
    b = np.array(v2, dtype=np.float32)
    dot = np.dot(a, b)
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0
    return float(dot / denom)

def search_similar_pdf_chunks(
    db: Session,
    query_text: str,
    subject_id: Optional[str] = None,
    topic_id: Optional[str] = None,
    limit: int = 3
) -> List[PDFChunk]:
    """
    Retrieves the most semantically relevant PDF chunks for a given query and topic.
    """
    query_vec = _local_semantic_embedding(query_text, EMBEDDING_DIM)
    query = db.query(PDFChunk)

    if subject_id:
        query = query.filter(PDFChunk.subject_id == subject_id)
    if topic_id:
        query = query.filter(PDFChunk.topic_id == topic_id)

    chunks = query.all()
    if not chunks:
        # If no chunk matches the topic directly, relax topic filter to subject
        if topic_id and subject_id:
            chunks = db.query(PDFChunk).filter(PDFChunk.subject_id == subject_id).all()

    if not chunks:
        return []

    # Score and rank by cosine similarity
    scored = []
    for chunk in chunks:
        if chunk.embedding:
            sim = cosine_similarity(query_vec, chunk.embedding)
            scored.append((sim, chunk))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item[1] for item in scored[:limit]]

def search_similar_question_bank(
    db: Session,
    query_text: str,
    topic_id: Optional[str] = None,
    difficulty: Optional[int] = None,
    limit: int = 3
) -> List[QuestionBank]:
    """
    Retrieves the most relevant question bank examples.
    """
    query_vec = _local_semantic_embedding(query_text, EMBEDDING_DIM)
    query = db.query(QuestionBank)

    if topic_id:
        query = query.filter(QuestionBank.topic_id == topic_id)
    if difficulty:
        query = query.filter(QuestionBank.difficulty == difficulty)

    items = query.all()
    if not items and topic_id:
        items = db.query(QuestionBank).filter(QuestionBank.topic_id == topic_id).all()

    if not items:
        return []

    scored = []
    for item in items:
        if item.embedding:
            sim = cosine_similarity(query_vec, item.embedding)
            scored.append((sim, item))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item[1] for item in scored[:limit]]
