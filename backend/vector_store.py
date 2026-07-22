"""ChromaDB wrapper for resume/job embeddings, using all-MiniLM-L6-v2 via
sentence-transformers (consistent across the project, per the build spec).
"""

from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions

PERSIST_DIR = Path(__file__).resolve().parent / "chroma_db"

_embedding_fn = None
_client = None


def get_embedding_fn():
    global _embedding_fn
    if _embedding_fn is None:
        _embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
    return _embedding_fn


def get_client():
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=str(PERSIST_DIR))
    return _client


def embed_resume(resume_id: int, structured: dict) -> None:
    """Embeds a resume's skills + experience bullets into a collection scoped
    to this resume version, tagged with resume_id per the build spec.
    """
    documents = list(structured.get("skills", []))
    for entry in structured.get("experience", []):
        documents.extend(entry.get("bullets", []))

    if not documents:
        return

    collection = get_client().get_or_create_collection(
        name=f"resume_{resume_id}",
        embedding_function=get_embedding_fn(),
    )
    collection.add(
        ids=[f"resume_{resume_id}_{i}" for i in range(len(documents))],
        documents=documents,
        metadatas=[{"resume_id": resume_id} for _ in documents],
    )


def embed_job(job_id: int, structured: dict) -> None:
    """Embeds a job's requirements/skills/responsibilities into the shared
    'jobs' ChromaDB collection (all jobs share one collection, unlike the
    per-resume-version collections), tagged with job_id.
    """
    documents = []
    for field in ("requirements", "required_skills", "nice_to_have_skills", "responsibilities"):
        documents.extend(structured.get(field, []))

    if not documents:
        return

    collection = get_client().get_or_create_collection(
        name="jobs",
        embedding_function=get_embedding_fn(),
    )
    collection.add(
        ids=[f"job_{job_id}_{i}" for i in range(len(documents))],
        documents=documents,
        metadatas=[{"job_id": job_id, "company": structured.get("company", "")} for _ in documents],
    )
