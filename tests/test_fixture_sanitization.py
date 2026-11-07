from __future__ import annotations

import json
import re
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"

# Regex matching any real email address (allowing only @example.com test domain)
NON_TEST_EMAIL_REGEX = re.compile(
    r"\b[A-Za-z0-9._%+-]+@(?!example\.com\b)[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
    re.IGNORECASE,
)

# Regex matching JWT token signatures (Header.Payload.Signature starting with eyJ)
JWT_REGEX = re.compile(r"eyJ[A-Za-z0-9_\-]{20,}\.eyJ[A-Za-z0-9_\-]{20,}")

# Prohibited sensitive keywords that must never appear in checked-in test fixtures
FORBIDDEN_PATTERNS = [
    re.compile(r"Canada Olympic", re.IGNORECASE),
    re.compile(r"Kelwood Place", re.IGNORECASE),
    re.compile(r"chiang", re.IGNORECASE),
    re.compile(r"cognito-idp\.[a-z0-9-]+\.amazonaws\.com", re.IGNORECASE),
    re.compile(r"us-east-2_[a-zA-Z0-9]{9}", re.IGNORECASE),  # Cognito user pool ID
    re.compile(r"authtoken:\s*[a-zA-Z0-9_\-]{40,}", re.IGNORECASE),
    re.compile(r"Bearer\s+eyJ", re.IGNORECASE),
]


def test_fixtures_directory_exists() -> None:
    """Verify fixture directory exists and contains expected files."""
    assert FIXTURES_DIR.is_dir()
    fixture_files = list(FIXTURES_DIR.glob("*.json"))
    assert len(fixture_files) >= 5
    file_names = {f.name for f in fixture_files}
    assert "devices_v1.json" in file_names
    assert "channels_v1.json" in file_names
    assert "sites_v1.json" in file_names
    assert "devices_legacy.json" in file_names
    assert "usages_v1.json" in file_names


def test_fixtures_valid_json() -> None:
    """Ensure all fixture files parse cleanly as valid JSON."""
    for fixture_path in FIXTURES_DIR.glob("*.json"):
        with open(fixture_path, encoding="utf-8") as f:
            data = json.load(f)
            assert isinstance(data, (dict, list)), (
                f"{fixture_path.name} root must be dict or list"
            )


def test_fixtures_zero_unscrubbed_emails() -> None:
    """Ensure no real/production personal email addresses are present in any fixture."""
    for fixture_path in FIXTURES_DIR.glob("*.json"):
        content = fixture_path.read_text(encoding="utf-8")
        matches = NON_TEST_EMAIL_REGEX.findall(content)
        assert not matches, (
            f"Found forbidden non-test email(s) in {fixture_path.name}: {matches}"
        )


def test_fixtures_zero_jwt_tokens() -> None:
    """Ensure zero JWT tokens are present in any fixture."""
    for fixture_path in FIXTURES_DIR.glob("*.json"):
        content = fixture_path.read_text(encoding="utf-8")
        matches = JWT_REGEX.findall(content)
        assert not matches, (
            f"Found forbidden JWT token(s) in {fixture_path.name}: {matches}"
        )


def test_fixtures_zero_forbidden_patterns() -> None:
    """Ensure zero forbidden PII / AWS infrastructure patterns are in any fixture."""
    for fixture_path in FIXTURES_DIR.glob("*.json"):
        content = fixture_path.read_text(encoding="utf-8")
        for pattern in FORBIDDEN_PATTERNS:
            match = pattern.search(content)
            assert not match, (
                f"Forbidden pattern '{pattern.pattern}' found in "
                f"{fixture_path.name}: {match.group(0) if match else ''}"
            )
