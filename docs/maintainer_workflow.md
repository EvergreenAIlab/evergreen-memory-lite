# Maintainer workflow

## Changes

After the one-time empty-repository bootstrap, every change goes through a feature branch and pull request. Keep each pull request focused, require CI to pass, and review both the diff and generated behavior before approval.

All examples and reproductions must be deliberately synthetic P0 material. Real private data must not appear in issues, pull requests, discussions, screenshots, fixtures, terminal output, or logs.

## Review and release preparation

1. Confirm the contribution matches the project scope and privacy model.
2. Run the complete test suite and the repository safety checks.
3. Review dependencies, source-file handling, and security implications.
4. Update documentation and the changelog when behavior changes.
5. Complete [the release checklist](release_checklist.md) before proposing a tag or release.
6. Require maintainer approval before tagging or publishing.

Codex may assist with pull-request review, documentation, focused tests, CI diagnosis, security-oriented diff review, and release preparation. It must not receive or process private data for this project, and a maintainer remains responsible for every approval and release.
