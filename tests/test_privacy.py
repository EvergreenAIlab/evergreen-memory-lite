import pytest

from evergreen_memory_lite.privacy import PrivacyTier, classify_text


@pytest.mark.parametrize("label", ["P0", "P1", "P2", "P3", "P4"])
def test_classifier_handles_all_tier_labels(label: str) -> None:
    assert classify_text(f"Privacy: {label}") is PrivacyTier.from_label(label)


def test_classifier_uses_highest_explicit_label() -> None:
    assert classify_text("P1 reviewed and raised to P3") is PrivacyTier.P3


def test_invalid_label_is_rejected() -> None:
    with pytest.raises(ValueError):
        PrivacyTier.from_label("P5")
