from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app, follow_redirects=False)


def test_root_returns_human_readable_html() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "GitHub Repo Redirect" in response.text
    assert "contact_links" in response.text
    assert (
        "https://github.com/fastapi/fastapi/discussions/categories/questions"
        in response.text
    )


def test_github_redirect_uses_referer_repo_and_path() -> None:
    response = client.get(
        "/github",
        params={"path": "/discussions/categories/questions"},
        headers={"referer": "https://github.com/fastapi/fastapi/issues"},
    )

    assert response.status_code == 307
    assert response.headers["location"] == (
        "https://github.com/fastapi/fastapi/discussions/categories/questions"
    )
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["vary"] == "Referer"


def test_github_redirect_uses_owner_and_repo_from_deeper_referer_path() -> None:
    response = client.get(
        "/github",
        params={"path": "/pulls"},
        headers={"referer": "https://github.com/tiangolo/sandbox/issues/123"},
    )

    assert response.status_code == 307
    assert response.headers["location"] == "https://github.com/tiangolo/sandbox/pulls"


def test_github_redirect_requires_referer() -> None:
    response = client.get("/github", params={"path": "/pulls"})

    assert response.status_code == 400
    assert response.json() == {"detail": "Referer header is required"}


def test_github_redirect_rejects_non_github_referer() -> None:
    response = client.get(
        "/github",
        params={"path": "/pulls"},
        headers={"referer": "https://github.com.example.com/fastapi/fastapi/issues"},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Referer must be a GitHub URL"}


def test_github_redirect_requires_absolute_path() -> None:
    response = client.get(
        "/github",
        params={"path": "pulls"},
        headers={"referer": "https://github.com/fastapi/fastapi/issues"},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Redirect path must be absolute"}


def test_github_redirect_rejects_encoded_parent_path_segment() -> None:
    response = client.get(
        "/github",
        params={"path": "/%252e%252e/settings"},
        headers={"referer": "https://github.com/fastapi/fastapi/issues"},
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Redirect path must not contain '..' path segments"
    }


def test_github_redirect_rejects_query_strings_in_path() -> None:
    response = client.get(
        "/github",
        params={"path": "/issues/1?tab=comments"},
        headers={"referer": "https://github.com/fastapi/fastapi/issues"},
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Redirect path must not contain query strings or fragments"
    }


def test_github_redirect_rejects_encoded_parent_path_with_encoded_separators() -> None:
    response = client.get(
        "/github",
        params={"path": "/%252f..%252fsettings"},
        headers={"referer": "https://github.com/fastapi/fastapi/issues"},
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Redirect path must not contain empty path segments"
    }


def test_github_redirect_rejects_encoded_query_strings_in_path() -> None:
    response = client.get(
        "/github",
        params={"path": "/issues/1%253Ftab=comments"},
        headers={"referer": "https://github.com/fastapi/fastapi/issues"},
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Redirect path must not contain query strings or fragments"
    }


def test_github_redirect_rejects_encoded_fragments_in_path() -> None:
    response = client.get(
        "/github",
        params={"path": "/issues/1%2523comment"},
        headers={"referer": "https://github.com/fastapi/fastapi/issues"},
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Redirect path must not contain query strings or fragments"
    }


def test_github_redirect_rejects_encoded_backslashes() -> None:
    response = client.get(
        "/github",
        params={"path": "/issues%255c1"},
        headers={"referer": "https://github.com/fastapi/fastapi/issues"},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Redirect path must not contain backslashes"}


def test_github_redirect_rejects_encoded_control_characters() -> None:
    response = client.get(
        "/github",
        params={"path": "/%250d%250ax-test:%2520bad"},
        headers={"referer": "https://github.com/fastapi/fastapi/issues"},
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Redirect path must not contain control characters"
    }
