# Release checklist

- [ ] Run the complete test suite.
- [ ] Run secret and private-data scans over tracked files.
- [ ] Verify every file under `data/` is deliberately synthetic P0 material.
- [ ] Run the README PowerShell quick start from a clean environment.
- [ ] Confirm no real personal, company, or investment data appears in code, fixtures, documentation, issues, or release notes.
- [ ] Review the exact Git diff and tracked file list.
- [ ] Confirm generated local databases, logs, caches, and outputs are ignored.
- [ ] Update the changelog and version when appropriate.
- [ ] Tag and publish a release only after maintainer approval.
