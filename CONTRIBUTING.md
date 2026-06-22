# Contributing

Thank you for helping keep Evergreen Memory Lite small, useful, and safe.

## Issues

Search existing issues before opening one. Describe the expected behavior, actual behavior, Windows and Python versions, and a minimal synthetic reproduction. Security vulnerabilities should follow [SECURITY.md](SECURITY.md), not a public issue.

## Local checks

From PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest
```

Run the dry-run example as an additional behavior check:

```powershell
.\.venv\Scripts\python.exe -m evergreen_memory_lite.runner --input data\synthetic
```

## Safe contributions

- Keep changes focused and use standard-library Python where practical.
- Add tests for changed behavior.
- Use invented P0 fixtures with obvious synthetic markers.
- Review diffs and generated output before committing.
- Never put real private data in issues, pull requests, examples, screenshots, logs, or test fixtures.
- Never submit credentials, access strings, real personal documents, or real organization data.

By contributing, you agree that your contribution is licensed under the MIT License.
