"""Tests for the AbiaCS Assistant API endpoints."""

import asyncio
from unittest.mock import Mock

import httpx
import pytest
from fastapi.testclient import TestClient

import main
from main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "documents_loaded" in data


def test_suggested_questions():
    response = client.get("/api/suggested-questions")
    assert response.status_code == 200
    data = response.json()
    assert "questions" in data
    assert len(data["questions"]) > 0


def test_chat_empty_message():
    response = client.post("/api/chat", json={"message": ""})
    assert response.status_code == 400


def test_chat_missing_message():
    response = client.post("/api/chat", json={})
    assert response.status_code == 422


ADMIN_HEADERS = {"Authorization": "Bearer unit-test-token"}
PDF_BYTES = b"%PDF-1.4\nunit test"


@pytest.fixture
def admin_routes(monkeypatch, tmp_path):
    documents = tmp_path / "documents"
    ingest = Mock()
    monkeypatch.setattr(main, "ADMIN_TOKEN", "unit-test-token")
    monkeypatch.setattr(main, "DOCUMENTS_DIR", documents)
    monkeypatch.setattr("ingest.ingest", ingest)
    monkeypatch.setattr(main, "load_vector_store", Mock())
    main.limiter.reset()
    return documents, ingest


@pytest.mark.parametrize("path", ["/api/upload", "/api/ingest"])
@pytest.mark.parametrize("headers", [{}, {"Authorization": "Bearer wrong-token"}])
def test_admin_routes_reject_invalid_credentials(admin_routes, path, headers):
    documents, ingest = admin_routes
    response = client.post(path, headers=headers)
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert not documents.exists()
    ingest.assert_not_called()


def test_upload_authenticates_before_reading_body(admin_routes):
    def body():
        pytest.fail("An unauthenticated upload body was read.")
        yield b""

    response = client.post(
        "/api/upload",
        headers={"Content-Type": "multipart/form-data; boundary=test"},
        content=body(),
    )
    assert response.status_code == 401


@pytest.mark.parametrize("path", ["/api/upload", "/api/ingest"])
def test_admin_routes_disabled_without_configured_token(admin_routes, monkeypatch, path):
    documents, ingest = admin_routes
    monkeypatch.setattr(main, "ADMIN_TOKEN", "")
    response = client.post(path, headers=ADMIN_HEADERS)
    assert response.status_code == 503
    assert not documents.exists()
    ingest.assert_not_called()


def test_admin_can_trigger_ingest(admin_routes):
    _, ingest = admin_routes
    response = client.post("/api/ingest", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    ingest.assert_called_once_with()
    main.load_vector_store.assert_called_once_with()


def upload_pdf(filename, content=PDF_BYTES):
    return client.post(
        "/api/upload",
        headers=ADMIN_HEADERS,
        files={"file": (filename, content, "application/pdf")},
    )


@pytest.mark.parametrize(
    "filename",
    ["notes.txt", ".pdf", "folder/notes.pdf", r"folder\notes.pdf", "NUL.pdf", "a" * 240 + ".pdf"],
)
def test_upload_rejects_invalid_pdf_filenames(admin_routes, filename):
    documents, ingest = admin_routes
    assert upload_pdf(filename).status_code == 400
    assert not documents.exists()
    ingest.assert_not_called()


def test_upload_rejects_multiple_files(admin_routes):
    documents, ingest = admin_routes
    response = client.post(
        "/api/upload",
        headers=ADMIN_HEADERS,
        files=[("file", ("first.pdf", PDF_BYTES)), ("file", ("second.pdf", PDF_BYTES))],
    )
    assert response.status_code == 400
    assert not documents.exists()
    ingest.assert_not_called()


def test_upload_rejects_pdf_over_the_limit(admin_routes, monkeypatch):
    documents, ingest = admin_routes
    monkeypatch.setattr(main, "MAX_UPLOAD_BYTES", len(PDF_BYTES) - 1)
    assert upload_pdf("notes.pdf").status_code == 413
    assert not documents.exists()
    ingest.assert_not_called()


def test_upload_stops_oversized_stream_without_content_length(admin_routes, monkeypatch):
    documents, ingest = admin_routes
    monkeypatch.setattr(main, "MAX_UPLOAD_BYTES", 16)
    monkeypatch.setattr(main, "MULTIPART_OVERHEAD_BYTES", 256)
    multipart = httpx.Request(
        "POST", "http://testserver/api/upload", files={"file": ("notes.pdf", b"x" * 512)}
    )
    payload = multipart.read()

    async def body():
        yield payload[:256]
        yield payload[256:512]
        pytest.fail("The server continued reading after the upload limit.")

    async def post():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://testserver"
        ) as async_client:
            return await async_client.post(
                "/api/upload",
                headers={**ADMIN_HEADERS, "Content-Type": multipart.headers["content-type"]},
                content=body(),
            )

    response = asyncio.run(post())
    assert "content-length" not in response.request.headers
    assert response.status_code == 413
    assert not documents.exists()
    ingest.assert_not_called()


@pytest.mark.parametrize("symlink", [False, True])
def test_upload_does_not_replace_an_existing_entry(admin_routes, symlink):
    documents, ingest = admin_routes
    documents.mkdir()
    destination = documents / "notes.pdf"
    original = documents.parent / "original.pdf" if symlink else destination
    original.write_bytes(b"original content")
    if symlink:
        destination.symlink_to(original)

    assert upload_pdf("notes.pdf").status_code == 409
    assert original.read_bytes() == b"original content"
    assert list(documents.iterdir()) == [destination]
    ingest.assert_not_called()


def test_admin_can_upload_pdf_at_limit(admin_routes, monkeypatch):
    documents, ingest = admin_routes
    monkeypatch.setattr(main, "MAX_UPLOAD_BYTES", len(PDF_BYTES))
    response = upload_pdf("Civil Service Rules.PDF")
    assert response.status_code == 200
    assert response.json()["filename"] == "Civil Service Rules.pdf"
    saved = documents / response.json()["filename"]
    assert saved.read_bytes() == PDF_BYTES
    assert list(documents.iterdir()) == [saved]
    ingest.assert_called_once_with()
    main.load_vector_store.assert_called_once_with()
