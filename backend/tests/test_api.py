"""Tests for the AbiaCS Assistant API endpoints."""

import pytest
from fastapi.testclient import TestClient

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
