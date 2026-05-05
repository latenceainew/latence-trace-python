# PyPI Publishing

PyPI project: `latence`

Trusted Publisher settings:

- Publisher: GitHub
- Owner: `latenceainew`
- Repository: `latence-trace-python`
- Workflow filename: `publish.yml`
- Environment name: `pypi`

No PyPI API token is required when Trusted Publishing is enabled.

Release flow:

1. Confirm the version in `pyproject.toml` has not been uploaded before.
2. Run `python -m pytest`, `python -m ruff check .`, `python -m build`, and `python -m twine check dist/*`.
3. Create and push a release tag, for example `v0.1.4`.
4. Publish through the protected `pypi` GitHub environment.
