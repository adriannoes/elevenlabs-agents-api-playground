"""Knowledge-base upload and RAG indexing helpers."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, cast

from pydantic import BaseModel, ConfigDict

from eleven_demo.client import get_client

if TYPE_CHECKING:
    from elevenlabs import ElevenLabs

from elevenlabs.conversational_ai.knowledge_base.client import KnowledgeBaseClient
from elevenlabs.core import File as UploadFile
from elevenlabs.types import (
    EmbeddingModelEnum,
    GetOrCreateRagIndexRequestModel,
    RagDocumentIndexResponseModel,
)

DEFAULT_EMBEDDING_MODEL: EmbeddingModelEnum = "multilingual_e5_large_instruct"


class KbDocument(BaseModel):
    id: str
    name: str

    model_config = ConfigDict(frozen=True, extra="forbid")


class RagChunkSummary(BaseModel):
    document_id: str
    index: RagDocumentIndexResponseModel | None


class RagIndex(BaseModel):
    embedding_model: EmbeddingModelEnum
    summaries: tuple[RagChunkSummary, ...]


def _kb_client(client: ElevenLabs | None = None) -> KnowledgeBaseClient:
    cli = get_client() if client is None else client
    return cast(KnowledgeBaseClient, cli.conversational_ai.knowledge_base)


def upload_kb_text(
    name: str,
    text: str,
    *,
    client: ElevenLabs | None = None,
) -> KbDocument:
    kb = _kb_client(client)
    added = kb.documents.create_from_text(text=text, name=name)
    return KbDocument(id=added.id, name=added.name)


def upload_kb_file(
    path: Path,
    *,
    name: str | None = None,
    client: ElevenLabs | None = None,
) -> KbDocument:
    resolved = path.expanduser().resolve()
    file_name = name or resolved.name
    kb = _kb_client(client)
    payload = resolved.read_bytes()
    upload: UploadFile = (file_name, payload)
    added = kb.documents.create_from_file(file=upload, name=file_name)
    return KbDocument(id=added.id, name=added.name)


def ensure_kb_file_uploaded(
    path: Path,
    *,
    name: str | None = None,
    client: ElevenLabs | None = None,
) -> KbDocument:
    """Return an existing KB document when ``name`` matches; otherwise upload from disk."""
    resolved = path.expanduser().resolve()
    file_name = name or resolved.name
    for doc in list_kb_documents(client=client):
        if doc.name == file_name:
            return doc
    return upload_kb_file(resolved, name=file_name, client=client)


def list_kb_documents(
    *,
    page_size: int = 100,
    client: ElevenLabs | None = None,
) -> list[KbDocument]:
    """Return file and text KB documents (skips folder rows)."""
    kb = _kb_client(client)
    out: list[KbDocument] = []
    cursor: str | None = None
    while True:
        page = kb.list(page_size=page_size, cursor=cursor)
        for item in page.documents:
            doc_type = getattr(item, "type", None)
            if doc_type == "folder":
                continue
            out.append(KbDocument(id=item.id, name=item.name))
        if not page.has_more or page.next_cursor is None:
            break
        cursor = page.next_cursor
    return out


def compute_rag(
    document_ids: list[str],
    *,
    model: EmbeddingModelEnum = DEFAULT_EMBEDDING_MODEL,
    wait: bool = True,
    client: ElevenLabs | None = None,
) -> RagIndex:
    """Request RAG indexes for the listed documents (``wait`` reserved for future async polling)."""
    _ = wait
    kb = _kb_client(client)
    if not document_ids:
        return RagIndex(
            embedding_model=model,
            summaries=(),
        )
    items = tuple(
        GetOrCreateRagIndexRequestModel(document_id=doc_id, create_if_missing=True, model=model)
        for doc_id in document_ids
    )
    resp = kb.get_or_create_rag_indexes(items=list(items))
    summaries: list[RagChunkSummary] = []
    for doc_id in document_ids:
        payload = resp.get(doc_id)
        if payload is None:
            summaries.append(RagChunkSummary(document_id=doc_id, index=None))
            continue
        if payload.status == "success":
            summaries.append(RagChunkSummary(document_id=doc_id, index=payload.data))
        else:
            summaries.append(RagChunkSummary(document_id=doc_id, index=None))
    return RagIndex(embedding_model=model, summaries=tuple(summaries))
