from __future__ import annotations

import pytest


@pytest.fixture
def mock_openai_client(mocker: pytest.MockFixture) -> object:
    mock = mocker.patch("openai.OpenAI")
    return mock.return_value
