import pytest

from tier3.prospeo import client as prospeo_module


class _FakeResponse:
    status_code = 200

    def json(self):
        return {
            "error": False,
            "results": [
                {
                    "person": {
                        "first_name": "Ada",
                        "last_name": "Lovelace",
                        "current_job_title": "Chief Executive Officer",
                        "linkedin_url": "https://www.linkedin.com/in/ada-lovelace",
                        "email": {
                            "status": "VERIFIED",
                            "revealed": False,
                            "email": "a**@example.com",
                        },
                    },
                    "company": {"name": "Example", "domain": "example.com"},
                },
            ],
        }


class _FakeAsyncClient:
    request_json = None

    def __init__(self, **_kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return None

    async def post(self, _url, *, json, **_kwargs):
        self.__class__.request_json = json
        return _FakeResponse()


@pytest.mark.asyncio
async def test_domain_search_uses_current_prospeo_schema(monkeypatch):
    monkeypatch.setenv("PROSPEO_API_KEY", "test-key")
    monkeypatch.setattr(prospeo_module.httpx, "AsyncClient", _FakeAsyncClient)

    results = await prospeo_module.ProspeoClient().domain_search("example.com", limit=10)

    assert _FakeAsyncClient.request_json == {
        "filters": {
            "company": {
                "websites": {
                    "include": ["example.com"],
                },
            },
        },
        "page": 1,
    }
    assert len(results) == 1
    assert results[0].first_name == "Ada"
    assert results[0].title == "Chief Executive Officer"
    assert results[0].email == ""
    assert results[0].verified is False
