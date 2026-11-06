from unittest.mock import Mock, patch

import api_client


@patch("api_client.requests.get")
def test_current_owner_sends_bearer_token(mock_get):
    response = Mock(ok=True)
    response.json.return_value = {"owner_id": "owner-123"}
    mock_get.return_value = response
    assert api_client.current_owner("secret") == {"owner_id": "owner-123"}
    assert mock_get.call_args.kwargs["headers"]["Authorization"] == "Bearer secret"


@patch("api_client.requests.post")
def test_logout_revokes_token(mock_post):
    mock_post.return_value = Mock(ok=True)
    api_client.revoke_session("secret")
    assert mock_post.call_args.kwargs["headers"]["Authorization"] == "Bearer secret"


@patch("api_client.requests.post")
def test_logout_failure_is_not_silenced(mock_post):
    mock_post.return_value = Mock(ok=False, status_code=503)
    try:
        api_client.revoke_session("secret")
        assert False, "Expected APIError"
    except api_client.APIError:
        pass
