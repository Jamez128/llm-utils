import pytest
from unittest.mock import patch, MagicMock
from decorators import retry_with_backoff

# Test 1: Success on first try
def test_returns_response_on_success():
    @retry_with_backoff(max_retries=3)
    def mock_function():
        return "success"

    result = mock_function()
    assert result == "success"

# Test 2: Fails, retries, then succeeds
def test_retries_then_succeeds():
    mock_func = MagicMock(side_effect = [Exception("fail"), Exception("fail"), "success"])

    @retry_with_backoff(max_retries=3, base_delay=0.01)
    def decorated_func():
        return mock_func()

    result = decorated_func()
    assert result == "success"
    assert mock_func.call_count == 3 # check it was called 3 times

# Test 3: Raises after max retries exhausted
def test_raises_after_max_retries():
    mock_func = MagicMock(side_effect=Exception("persistent error"))

    @retry_with_backoff(max_retries=3, base_delay=0.01)
    def decorated_func():
        return mock_func()

    with pytest.raises(Exception, match="persistent error"):
        decorated_func()
