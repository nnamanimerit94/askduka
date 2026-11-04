from fastapi.testclient import TestClient
from backend.app.preview import app, find_answer

client = TestClient(app)


def test_health():
    assert client.get("/health").json()["status"] == "ok"


def test_home_renders():
    response = client.get("/")
    assert response.status_code == 200
    assert "AskDuka" in response.text


def test_demo_matches_catalog_line():
    result = client.post("/demo/ask", json={
        "catalog": "We sell bone straight wigs.\nWe deliver in Lagos.",
        "question": "Do you have bone straight wigs?"
    })
    assert result.status_code == 200
    assert result.json()["answer"] == "We sell bone straight wigs."
    assert result.json()["matched"] is True


def test_demo_unknown_question_falls_back():
    result = find_answer("We sell wigs.", "Do you repair laptops?")
    assert result["matched"] is False


def test_demo_rejects_blank_catalog():
    response = client.post("/demo/ask", json={"catalog": "", "question": "Wigs?"})
    assert response.status_code == 422


def test_preview_not_ready_for_customers():
    assert client.get("/readiness").json()["ready_for_customers"] is False
