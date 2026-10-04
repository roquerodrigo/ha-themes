import pytest

from ha_theme_kit.inventory.classification import Classification, classify_global_token


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("--amber-color", Classification("application", "named-colors")),
        ("--blue-grey-color", Classification("application", "named-colors")),
        ("--dark-grey-color", Classification("application", "named-colors")),
        ("--white-color", Classification("application", "named-colors")),
        ("--primary-color", Classification("application", "roles")),
        ("--dark-primary-color", Classification("application", "roles")),
        ("--error-color", Classification("application", "roles")),
        ("--divider-color", Classification("application", "roles")),
        ("--scrollbar-thumb-color", Classification("application", "roles")),
        ("--ha-button-neutral-color", Classification("application", "button")),
        ("--ha-assist-chip-filled-container-color", Classification("application", "chip")),
        ("--dark-secondary-opacity", Classification("application", "text")),
        ("--light-primary-opacity", Classification("application", "text")),
        ("--safe-area-inset-top", Classification("layout", "safe")),
    ],
)
def test_global_token_classification(name: str, expected: Classification) -> None:
    assert classify_global_token(name) == expected
