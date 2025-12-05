"""
Tests for Privacy Guard functionality.

Verifies PII scrubbing per .context/02_privacy_charter.md requirements.
"""

import pytest

from app.core.privacy_guard import (
    PIIPlaceholder,
    contains_pii,
    scrub_dict,
    scrub_pii,
)


class TestScrubPii:
    """Tests for the scrub_pii function."""

    def test_scrub_email(self) -> None:
        """Should replace email addresses with placeholder."""
        text = "Contact me at john.doe@example.com for details"
        result = scrub_pii(text)
        assert "<EMAIL>" in result
        assert "john.doe@example.com" not in result

    def test_scrub_phone_formats(self) -> None:
        """Should replace various phone number formats."""
        test_cases = [
            "Call me at 555-0199",
            "Phone: 555-123-4567",
            "Call (555) 123-4567",
            "My number is +1-555-123-4567",
            "Reach me at 555.123.4567",
        ]
        for text in test_cases:
            result = scrub_pii(text)
            assert PIIPlaceholder.PHONE in result, f"Failed for: {text}"

    def test_scrub_names(self) -> None:
        """Should replace name patterns with placeholder."""
        text = "Student John Smith completed the assignment"
        result = scrub_pii(text)
        assert PIIPlaceholder.NAME in result
        assert "John Smith" not in result

    def test_scrub_sin(self) -> None:
        """Should replace Canadian SIN numbers."""
        text = "SIN: 123-456-789"
        result = scrub_pii(text)
        assert PIIPlaceholder.SIN in result
        assert "123-456-789" not in result

    def test_scrub_student_id(self) -> None:
        """Should replace student ID patterns."""
        test_cases = [
            "Student ID: 12345678",
            "student#: 987654321",
            "ID: 1234567890",
        ]
        for text in test_cases:
            result = scrub_pii(text)
            assert PIIPlaceholder.STUDENT_ID in result, f"Failed for: {text}"

    def test_scrub_address(self) -> None:
        """Should replace street addresses."""
        text = "Lives at 123 Main Street"
        result = scrub_pii(text)
        assert PIIPlaceholder.ADDRESS in result
        assert "123 Main Street" not in result

    def test_scrub_multiple_pii(self) -> None:
        """Should handle multiple PII types in one string."""
        text = "John Smith called from 555-123-4567 about student ID: 12345678"
        result = scrub_pii(text)
        assert "John Smith" not in result
        assert "555-123-4567" not in result
        assert "12345678" not in result

    def test_empty_string(self) -> None:
        """Should handle empty string."""
        assert scrub_pii("") == ""

    def test_none_handling(self) -> None:
        """Should handle None gracefully."""
        assert scrub_pii(None) is None  # type: ignore

    def test_no_pii(self) -> None:
        """Should not modify text without PII."""
        text = "The quick brown fox jumps over the lazy dog"
        assert scrub_pii(text) == text


class TestScrubDict:
    """Tests for the scrub_dict function."""

    def test_scrub_simple_dict(self) -> None:
        """Should scrub string values in dictionary."""
        data = {
            "name": "John Smith",
            "email": "john@example.com",
            "message": "Hello world",
        }
        result = scrub_dict(data)
        assert PIIPlaceholder.NAME in result["name"]
        assert PIIPlaceholder.EMAIL in result["email"]
        assert result["message"] == "Hello world"

    def test_scrub_nested_dict(self) -> None:
        """Should recursively scrub nested dictionaries."""
        data = {
            "student": {
                "name": "Jane Doe",
                "contact": {
                    "phone": "555-123-4567",
                },
            },
        }
        result = scrub_dict(data)
        assert PIIPlaceholder.NAME in result["student"]["name"]
        assert PIIPlaceholder.PHONE in result["student"]["contact"]["phone"]

    def test_scrub_list_in_dict(self) -> None:
        """Should scrub strings within lists."""
        data = {
            "names": ["John Smith", "Jane Doe"],
        }
        result = scrub_dict(data)
        assert all(PIIPlaceholder.NAME in n for n in result["names"])

    def test_preserve_non_string_values(self) -> None:
        """Should preserve non-string values."""
        data = {
            "count": 42,
            "active": True,
            "ratio": 3.14,
        }
        result = scrub_dict(data)
        assert result == data


class TestContainsPii:
    """Tests for the contains_pii function."""

    def test_detect_email(self) -> None:
        """Should detect email addresses."""
        assert contains_pii("Contact: test@example.com")

    def test_detect_phone(self) -> None:
        """Should detect phone numbers."""
        assert contains_pii("Call 555-123-4567")

    def test_detect_name(self) -> None:
        """Should detect name patterns."""
        assert contains_pii("Student: John Smith")

    def test_no_pii_detection(self) -> None:
        """Should not flag clean text."""
        assert not contains_pii("This is clean text without PII")

    def test_empty_string(self) -> None:
        """Should handle empty string."""
        assert not contains_pii("")


class TestRealWorldScenarios:
    """Test real-world scenarios from the NEXUS context."""

    def test_scout_report_scrubbing(self) -> None:
        """Should scrub PII from Scout Report content."""
        report = """
        Student Johnny Martinez showed high engagement today.
        Parent contact: maria.martinez@email.com, 555-234-5678
        Home address: 456 Oak Avenue
        """
        result = scrub_pii(report)

        # Verify all PII is scrubbed
        assert "Johnny Martinez" not in result
        assert "maria.martinez@email.com" not in result
        assert "555-234-5678" not in result
        assert "456 Oak Avenue" not in result

        # Verify report structure is maintained
        assert "showed high engagement today" in result
        assert "Parent contact:" in result

    def test_transcript_scrubbing(self) -> None:
        """Should scrub PII from session transcripts."""
        transcript = """
        NEXUS: Hello! How are you today?
        Student: My name is Sarah Johnson. My phone is 555-0199.
        NEXUS: Nice to meet you! Let's talk about wetlands.
        """
        result = scrub_pii(transcript)

        assert "Sarah Johnson" not in result
        assert "555-0199" not in result
        assert "Let's talk about wetlands" in result

    def test_preserve_curriculum_terms(self) -> None:
        """Should not affect curriculum-specific terms."""
        text = "Outcome SS-5-1-2: Students will examine historical events in Canada"
        result = scrub_pii(text)

        # Should remain unchanged (no PII)
        assert "SS-5-1-2" in result
        assert "Students will examine" in result
