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

    file.name = "catalog.txt"
    file.type = "text/plain"

    result = api_client.upload_document(
        file,
        "test-token",
        "business-123",
    )

    assert mock_post.call_args.args[0].endswith("/api/businesses/business-123/documents")
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


@patch("api_client.requests.get")
def test_list_businesses_uses_owner_token(mock_get):
    response = Mock(ok=True)
    response.json.return_value = {"businesses": [{"business_id": "business-123"}]}
    mock_get.return_value = response
    assert api_client.list_businesses("test-token")["businesses"][0]["business_id"] == "business-123"
    assert mock_get.call_args.kwargs["headers"]["Authorization"] == "Bearer test-token"


@patch("api_client.requests.get")
def test_list_documents_scopes_to_business(mock_get):
    response = Mock(ok=True)
    response.json.return_value = {"documents": []}
    mock_get.return_value = response
    assert api_client.list_documents("test-token", "business-123") == {"documents": []}
    assert mock_get.call_args.args[0].endswith("/api/businesses/business-123/documents")


@patch("api_client.requests.post")
def test_register_business_sends_new_business_details(mock_post):
    response = Mock(ok=True)
    response.json.return_value = {"owner_id": "owner-123", "business_id": "business-123"}
    mock_post.return_value = response
    result = api_client.register_business("owner@example.com", "secure password 1234", "My Shop")
    assert result["business_id"] == "business-123"
    assert mock_post.call_args.args[0].endswith("/api/auth/register-business")
    assert mock_post.call_args.kwargs["json"]["business_name"] == "My Shop"


@patch("api_client.requests.post")
def test_register_business_disabled_backend_error(mock_post):
    mock_post.return_value = Mock(ok=False, status_code=404)
    try:
        api_client.register_business("owner@example.com", "secure password 1234", "My Shop")
        assert False, "Expected APIError"
    except api_client.APIError as exc:
        assert "404" in str(exc)
