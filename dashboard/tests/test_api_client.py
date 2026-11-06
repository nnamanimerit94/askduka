from unittest.mock import Mock, patch

import api_client


@patch("api_client.requests.post")
def test_login_success(mock_post):

    response = Mock()

    response.ok = True

    response.json.return_value = {
        "token": "test-token"
    }

    mock_post.return_value = response

    result = api_client.login(
        "owner@example.com",
        "password123",
    )

    assert result["token"] == "test-token"


@patch("api_client.requests.post")
def test_login_failure(mock_post):

    response = Mock()

    response.ok = False
    response.status_code = 401

    mock_post.return_value = response

    try:

        api_client.login(
            "wrong@example.com",
            "wrong-password",
        )

        assert False

    except api_client.APIError as exc:

        assert "401" in str(exc)


@patch("api_client.requests.post")
def test_upload_document(mock_post):

    response = Mock()

    response.ok = True

    response.json.return_value = {
        "document_id": "123",
        "status": "processing",
    }

    mock_post.return_value = response

    file = Mock()

    file.name = "catalog.pdf"
    file.type = "application/pdf"

    result = api_client.upload_document(
        file,
        "test-token",
    )

    assert result["document_id"] == "123"
    assert result["status"] == "processing"


@patch("api_client.requests.get")
def test_get_conversations(mock_get):

    response = Mock()

    response.ok = True

    response.json.return_value = {
        "conversations": []
    }

    mock_get.return_value = response

    result = api_client.get_conversations(
        "test-token"
    )

    assert result["conversations"] == []
