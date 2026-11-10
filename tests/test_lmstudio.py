import httpx
import pytest
from pydantic import ValidationError

from monitor.config import LMConfig
from monitor.integrations.lmstudio import LMStudioAdapter


def test_disabled_never_calls_http():
    client = httpx.Client(
        transport=httpx.MockTransport(lambda req: pytest.fail("disabled HTTP call"))
    )
    adapter = LMStudioAdapter(LMConfig(), client)
    assert adapter.collect().source.status == "disabled"
    adapter.close()


def test_models_only_and_auth(monkeypatch):
    calls = []
    monkeypatch.setenv("TEST_LM_TOKEN", "local-test-only")

    def handler(request):
        calls.append(request)
        assert request.method == "GET"
        assert request.url.path == "/api/v1/models"
        assert request.headers["Authorization"] == "Bearer local-test-only"
        return httpx.Response(
            200,
            json={
                "models": [
                    {"display_name": "Model A", "loaded_instances": [{"id": "a"}]},
                    {"display_name": "Not loaded", "loaded_instances": []},
                ]
            },
        )

    adapter = LMStudioAdapter(
        LMConfig(enabled=True, token_env="TEST_LM_TOKEN"),
        httpx.Client(transport=httpx.MockTransport(handler)),
    )
    result = adapter.collect(now=10, monotonic=0)
    assert result.loaded_models == ["Model A"]
    assert result.tokens_per_second is None
    adapter.collect(now=11, monotonic=1)
    assert len(calls) == 1
    adapter.close()


@pytest.mark.parametrize("status,body", [(401, b"no"), (200, b"x" * 2048), (200, b'{"wrong":[]}')])
def test_errors_and_size_limit(status, body):
    client = httpx.Client(
        transport=httpx.MockTransport(lambda r: httpx.Response(status, content=body))
    )
    adapter = LMStudioAdapter(LMConfig(enabled=True, max_response_bytes=1024), client)
    result = adapter.collect()
    assert result.source.status == "unavailable"
    assert not result.loaded_models
    adapter.close()


def test_credentials_not_allowed_in_url():
    with pytest.raises(ValidationError):
        LMConfig(base_url="http://user:password@localhost:1234")
