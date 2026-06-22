"""Explicit privacy-tier labels for the synthetic demonstration."""

from __future__ import annotations

import re
from enum import IntEnum


class PrivacyTier(IntEnum):
    """Privacy tiers ordered from public to most sensitive."""

    P0 = 0
    P1 = 1
    P2 = 2
    P3 = 3
    P4 = 4

    @classmethod
    def from_label(cls, label: str) -> "PrivacyTier":
        """Parse an exact P0-P4 label, ignoring case and surrounding space."""

        normalized = label.strip().upper()
        try:
            return cls[normalized]
        except KeyError as exc:
            raise ValueError(f"Unsupported privacy tier: {label!r}") from exc


_LABEL_PATTERN = re.compile(r"(?<![A-Z0-9])P([0-4])(?![A-Z0-9])", re.IGNORECASE)


def classify_text(text: str, *, default: PrivacyTier = PrivacyTier.P0) -> PrivacyTier:
    """Return the highest explicit tier label found in *text*.

    This function recognizes labels only. It does not infer sensitivity from the
    meaning of the content and is not a privacy or redaction system.
    """

    matches = _LABEL_PATTERN.findall(text)
    if not matches:
        return default
    return PrivacyTier(max(int(value) for value in matches))
