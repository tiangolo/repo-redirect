# GitHub Repo Redirect

Use this service from GitHub-rendered links, such as `contact_links` in `.github/ISSUE_TEMPLATE/config.yml`, to redirect to a path in the same repository.

When users click it, the browser includes a `Referer` header used to determine the GitHub repository.

Set a query parameter `path` with the desired path in the repository.

```text
https://repo-redirect.fastapicloud.dev/github?path=/discussions/categories/questions
```

Example `.github/ISSUE_TEMPLATE/config.yml`:

```yaml
blank_issues_enabled: false
contact_links:
  - name: Ask a question
    url: https://repo-redirect.fastapicloud.dev/github?path=/discussions/categories/questions
    about: Ask questions in GitHub Discussions.
```

Example destination when opened from `https://github.com/fastapi/fastapi/issues`:

```text
https://github.com/fastapi/fastapi/discussions/categories/questions
```

## License

This project is licensed under the terms of the MIT license.
