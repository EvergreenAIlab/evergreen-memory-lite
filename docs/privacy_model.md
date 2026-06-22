# Privacy model

Privacy labels describe the expected impact of disclosure. A label is a handling aid, not an automatic guarantee.

| Tier | Meaning | Example handling |
| --- | --- | --- |
| P0 | Public or deliberately synthetic | Suitable for this public demo and its tests. |
| P1 | Low-sensitivity operational information | Keep local and share only with intended collaborators. |
| P2 | Personal but low-risk information | Require a clear purpose, limited access, and review before sharing. |
| P3 | Sensitive private information | Use strict access controls, encryption, and explicit retention rules. |
| P4 | Highly sensitive identity, medical, financial, or legal information | Keep out of this project; use purpose-built controls and professional review. |

## Repository rule

This repository ships and accepts P0 synthetic data only. The included classifier reads an explicit label; it does not inspect meaning reliably and must not be used to declare real material safe.

If there is uncertainty, stop. Do not copy the material into the repository, an issue, a pull request, a screenshot, or a log. Create a new synthetic reproduction instead.
