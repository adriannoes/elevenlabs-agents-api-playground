"""Unit tests for knowledge-base helpers."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from elevenlabs.types import RagDocumentIndexResponseModel

from eleven_demo.agents import kb


def test_upload_kb_text_returns_document() -> None:
    added = MagicMock()
    added.id = "doc-1"
    added.name = "seed"

    mock_client = MagicMock()
    mock_client.conversational_ai.knowledge_base.documents.create_from_text.return_value = added

    doc = kb.upload_kb_text("seed", "hello world", client=mock_client)

    assert doc.id == "doc-1"
    assert doc.name == "seed"


def test_compute_rag_empty_ids() -> None:
    out = kb.compute_rag([], client=MagicMock())
    assert out.summaries == ()


def test_compute_rag_maps_success() -> None:
    index = MagicMock(spec=RagDocumentIndexResponseModel)
    success = MagicMock()
    success.status = "success"
    success.data = index

    kb_client = MagicMock()
    kb_client.get_or_create_rag_indexes.return_value = {"d1": success}

    mock_client = MagicMock()
    mock_client.conversational_ai.knowledge_base = kb_client

    out = kb.compute_rag(["d1"], client=mock_client)

    assert len(out.summaries) == 1
    assert out.summaries[0].document_id == "d1"
    assert out.summaries[0].index is index


def test_ensure_kb_file_uploaded_reuses_matching_name() -> None:
    existing = MagicMock()
    existing.type = "file"
    existing.id = "existing-doc"
    existing.name = "01-symptom-fever.md"

    page = MagicMock()
    page.documents = [existing]
    page.has_more = False
    page.next_cursor = None

    kb_client = MagicMock()
    kb_client.list.return_value = page

    mock_client = MagicMock()
    mock_client.conversational_ai.knowledge_base = kb_client

    doc = kb.ensure_kb_file_uploaded(
        Path("/tmp/unused-path-should-not-read-file"),
        name="01-symptom-fever.md",
        client=mock_client,
    )

    assert doc.id == "existing-doc"
    assert doc.name == "01-symptom-fever.md"
    kb_client.documents.create_from_file.assert_not_called()


def test_list_kb_documents_skips_folders() -> None:
    folder = MagicMock()
    folder.type = "folder"
    folder.id = "f1"
    folder.name = "fold"

    fil = MagicMock()
    fil.type = "file"
    fil.id = "d1"
    fil.name = "a.md"

    page = MagicMock()
    page.documents = [folder, fil]
    page.has_more = False
    page.next_cursor = None

    kb_client = MagicMock()
    kb_client.list.return_value = page

    mock_client = MagicMock()
    mock_client.conversational_ai.knowledge_base = kb_client

    docs = kb.list_kb_documents(client=mock_client)

    assert len(docs) == 1
    assert docs[0].id == "d1"
