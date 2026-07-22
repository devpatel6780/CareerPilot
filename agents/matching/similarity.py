"""Embedding similarity between a resume and a job, using each side's
already-stored ChromaDB embeddings (mean-pooled into one vector per side,
since both resumes and jobs are embedded as several short documents rather
than a single vector).
"""

import numpy as np

from vector_store import get_client


def _mean_embedding(collection_name: str, where: dict | None = None) -> np.ndarray | None:
    client = get_client()
    try:
        collection = client.get_collection(collection_name)
    except Exception:
        return None

    result = collection.get(where=where, include=["embeddings"])
    embeddings = result.get("embeddings")
    if embeddings is None or len(embeddings) == 0:
        return None
    return np.mean(np.array(embeddings), axis=0)


def resume_job_similarity(resume_id: int, job_id: int) -> float | None:
    """Cosine similarity scaled to 0-100, or None if either side has no
    stored embeddings (e.g. a resume/job with no skills or bullets).
    """
    resume_vec = _mean_embedding(f"resume_{resume_id}")
    job_vec = _mean_embedding("jobs", where={"job_id": job_id})

    if resume_vec is None or job_vec is None:
        return None

    cosine = float(np.dot(resume_vec, job_vec) / (np.linalg.norm(resume_vec) * np.linalg.norm(job_vec)))
    return max(0.0, min(100.0, (cosine + 1) / 2 * 100))
