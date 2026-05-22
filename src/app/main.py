from typing import Annotated
from urllib.parse import unquote, urlparse, urlunparse

from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse

app = FastAPI()


def get_github_repo_url(referer: str) -> str:
    parsed = urlparse(referer)
    if parsed.scheme != "https" or parsed.netloc.lower() != "github.com":
        raise HTTPException(
            status_code=400,
            detail="Referer must be a GitHub URL",
        )

    path_parts = [part for part in parsed.path.split("/") if part]
    if len(path_parts) < 2:
        raise HTTPException(
            status_code=400,
            detail="Referer must include a GitHub owner and repo",
        )

    owner, repo = path_parts[:2]
    return urlunparse((parsed.scheme, parsed.netloc, f"/{owner}/{repo}", "", "", ""))


def decode_path(path: str) -> str:
    decoded_path = path
    for _ in range(3):
        next_decoded_path = unquote(decoded_path)
        if next_decoded_path == decoded_path:
            break
        decoded_path = next_decoded_path
    return decoded_path


def validate_redirect_path(path: str) -> str:
    decoded_path = decode_path(path)

    if not decoded_path.startswith("/"):
        raise HTTPException(
            status_code=400,
            detail="Redirect path must be absolute",
        )

    if any(ord(character) < 32 or ord(character) == 127 for character in decoded_path):
        raise HTTPException(
            status_code=400,
            detail="Redirect path must not contain control characters",
        )

    if "\\" in decoded_path:
        raise HTTPException(
            status_code=400,
            detail="Redirect path must not contain backslashes",
        )

    if "?" in decoded_path or "#" in decoded_path:
        raise HTTPException(
            status_code=400,
            detail="Redirect path must not contain query strings or fragments",
        )

    if "//" in decoded_path:
        raise HTTPException(
            status_code=400,
            detail="Redirect path must not contain empty path segments",
        )

    if ".." in decoded_path.split("/"):
        raise HTTPException(
            status_code=400,
            detail="Redirect path must not contain '..' path segments",
        )

    return path


@app.get("/", response_class=HTMLResponse)
async def read_root() -> str:
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>GitHub Repo Redirect</title>
  <style>
    body {
      color: #24292f;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.5;
      margin: 0;
      padding: 2rem;
    }
    main {
      max-width: 42rem;
    }
    code, pre {
      background: #f6f8fa;
      border-radius: 6px;
      font-family: ui-monospace, SFMono-Regular, Consolas, "Liberation Mono", monospace;
    }
    code {
      padding: 0.15rem 0.3rem;
    }
    pre {
      overflow-x: auto;
      padding: 1rem;
    }
    a {
      color: #0969da;
    }
  </style>
</head>
<body>
  <main>
    <h1>GitHub Repo Redirect</h1>
    <p>
      Use this service from GitHub-rendered links, such as <code>contact_links</code> in
      <code>.github/ISSUE_TEMPLATE/config.yml</code>,
      to redirect to a path in the same repository.
    </p>
    <p>
      It is especially useful for, and made for,
      <a href="https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/creating-a-default-community-health-file">GitHub default community health files</a>,
      where the same config can be shared across repositories in an organization.
    </p>
    <p>
      When users click it, the browser includes a <code>Referer</code> header used to determine the GitHub repository.
    </p>
    <p>Set a query parameter <code>path</code> with the desired path in the repository.
    </p>
    <pre>https://repo-redirect.fastapicloud.dev/github?path=/discussions/categories/questions</pre>
    <p>Example <code>.github/ISSUE_TEMPLATE/config.yml</code>:</p>
    <pre>blank_issues_enabled: false
contact_links:
  - name: Ask a question
    url: https://repo-redirect.fastapicloud.dev/github?path=/discussions/categories/questions
    about: Ask questions in GitHub Discussions.</pre>
    <p>
      Example destination when opened from
      <code>https://github.com/fastapi/fastapi/issues</code>:
    </p>
    <pre>https://github.com/fastapi/fastapi/discussions/categories/questions</pre>
  </main>
</body>
</html>"""


@app.get("/github")
async def redirect_to_github_repo_path(
    path: Annotated[
        str,
        Query(
            description="Absolute path to append to the GitHub owner/repo URL.",
        ),
    ],
    referer: Annotated[str | None, Header()] = None,
) -> RedirectResponse:
    if referer is None:
        raise HTTPException(status_code=400, detail="Referer header is required")

    repo_url = get_github_repo_url(referer)
    redirect_path = validate_redirect_path(path)
    return RedirectResponse(
        f"{repo_url}{redirect_path}",
        headers={"Cache-Control": "no-store", "Vary": "Referer"},
    )
