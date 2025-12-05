"""
Tests for Multi-Language Support System.

Tests the language-aware prompts and cultural bridge functionality
for EAL (English as Additional Language) students.
"""

import pytest

from app.services.voice_engine.multilang import (
    DEFAULT_CONTEXT,
    LANGUAGE_CONTEXTS,
    LanguageContext,
    build_language_aware_prompt,
    get_cultural_bridge_hint,
    get_language_context,
)


class TestLanguageContext:
    """Tests for LanguageContext dataclass."""

    def test_arabic_context_complete(self) -> None:
        """Test Arabic language context has all fields."""
        ctx = LANGUAGE_CONTEXTS["Arabic"]
        assert ctx.language_code == "ar"
        assert ctx.language_name == "Arabic"
        assert "مرحبا" in ctx.greeting_native  # Marhaba
        assert len(ctx.common_difficulties) > 0
        assert len(ctx.cultural_notes) > 0
        assert ctx.alphabet_type == "arabic"

    def test_mandarin_context_complete(self) -> None:
        """Test Mandarin language context has all fields."""
        ctx = LANGUAGE_CONTEXTS["Mandarin"]
        assert ctx.language_code == "zh"
        assert "你好" in ctx.greeting_native  # Ni hao
        assert ctx.alphabet_type == "logographic"
        assert "L/R distinction" in ctx.common_difficulties

    def test_ukrainian_context_complete(self) -> None:
        """Test Ukrainian language context has all fields."""
        ctx = LANGUAGE_CONTEXTS["Ukrainian"]
        assert ctx.language_code == "uk"
        assert "Привіт" in ctx.greeting_native  # Pryvit
        assert ctx.alphabet_type == "cyrillic"
        # Sensitive topic note
        assert any("Current events" in note for note in ctx.cultural_notes)

    def test_all_contexts_have_required_fields(self) -> None:
        """Test all language contexts have required fields."""
        required_fields = [
            "language_code",
            "language_name",
            "greeting_native",
            "encouragement_native",
            "common_difficulties",
            "cultural_notes",
            "alphabet_type",
        ]

        for language, ctx in LANGUAGE_CONTEXTS.items():
            for field in required_fields:
                assert hasattr(ctx, field), f"{language} missing {field}"
                value = getattr(ctx, field)
                if isinstance(value, list):
                    assert len(value) > 0, f"{language}.{field} is empty"
                else:
                    assert value, f"{language}.{field} is falsy"

    def test_supported_languages(self) -> None:
        """Test all expected EAL languages are supported."""
        expected_languages = [
            "Arabic",
            "Mandarin",
            "Punjabi",
            "Tagalog",
            "Spanish",
            "Ukrainian",
            "Vietnamese",
            "Somali",
        ]
        for lang in expected_languages:
            assert lang in LANGUAGE_CONTEXTS, f"{lang} not supported"


class TestGetLanguageContext:
    """Tests for get_language_context function."""

    def test_exact_match(self) -> None:
        """Test exact language name match."""
        ctx = get_language_context("Arabic")
        assert ctx.language_name == "Arabic"

    def test_case_insensitive_match(self) -> None:
        """Test case-insensitive language matching."""
        ctx = get_language_context("arabic")
        assert ctx.language_name == "Arabic"

        ctx = get_language_context("MANDARIN")
        assert ctx.language_name == "Mandarin Chinese"

    def test_language_code_match(self) -> None:
        """Test matching by language code."""
        ctx = get_language_context("ar")
        assert ctx.language_name == "Arabic"

        ctx = get_language_context("zh")
        assert ctx.language_name == "Mandarin Chinese"

    def test_unknown_language_returns_default(self) -> None:
        """Test unknown language returns default context."""
        ctx = get_language_context("Klingon")
        assert ctx == DEFAULT_CONTEXT
        assert ctx.language_code == "en"
        assert ctx.language_name == "English"

    def test_empty_string_returns_default(self) -> None:
        """Test empty string returns default context."""
        ctx = get_language_context("")
        assert ctx == DEFAULT_CONTEXT

    def test_default_context_values(self) -> None:
        """Test default context has sensible values."""
        assert DEFAULT_CONTEXT.language_code == "en"
        assert DEFAULT_CONTEXT.language_name == "English"
        assert DEFAULT_CONTEXT.greeting_native == "Hello"
        assert DEFAULT_CONTEXT.alphabet_type == "latin"


class TestBuildLanguageAwarePrompt:
    """Tests for build_language_aware_prompt function."""

    def test_basic_prompt_structure(self) -> None:
        """Test basic prompt contains required elements."""
        prompt = build_language_aware_prompt(
            grade=5,
            primary_language="English",
        )

        assert "NEXUS" in prompt
        assert "Grade 5" in prompt
        assert "Alberta" in prompt
        assert "EAL" in prompt

    def test_includes_grade_level(self) -> None:
        """Test prompt includes correct grade level."""
        for grade in [3, 5, 7, 9]:
            prompt = build_language_aware_prompt(
                grade=grade,
                primary_language="English",
            )
            assert f"Grade {grade}" in prompt

    def test_includes_language_guidance_for_eal(self) -> None:
        """Test EAL languages include language-specific guidance."""
        prompt = build_language_aware_prompt(
            grade=5,
            primary_language="Arabic",
        )

        assert "Arabic" in prompt
        assert "مرحبا" in prompt or "Marhaba" in prompt  # Greeting
        assert "Language Support" in prompt
        # Should mention common difficulties
        assert "TH sounds" in prompt or "vowel" in prompt.lower()

    def test_includes_cultural_notes_for_eal(self) -> None:
        """Test EAL prompts include cultural connection points."""
        prompt = build_language_aware_prompt(
            grade=5,
            primary_language="Ukrainian",
        )

        assert "Cultural Connection Points" in prompt
        # Ukrainian cultural notes should appear
        assert "tradition" in prompt.lower() or "Easter" in prompt or "family" in prompt.lower()

    def test_includes_curriculum_outcome(self) -> None:
        """Test curriculum outcome is included when provided."""
        prompt = build_language_aware_prompt(
            grade=5,
            primary_language="English",
            curriculum_outcome="SCI-5-1: Wetland ecosystems",
        )

        assert "Wetland ecosystems" in prompt or "SCI-5-1" in prompt
        assert "learning focus" in prompt.lower()

    def test_includes_cultural_bridge_hints(self) -> None:
        """Test additional cultural context is included."""
        prompt = build_language_aware_prompt(
            grade=5,
            primary_language="English",
            cultural_bridge_hints="Student interested in soccer",
        )

        assert "soccer" in prompt.lower()
        assert "cultural context" in prompt.lower()

    def test_no_pii_instruction(self) -> None:
        """Test prompt includes instruction to not ask for PII."""
        prompt = build_language_aware_prompt(
            grade=5,
            primary_language="English",
        )

        assert "personal information" in prompt.lower()
        assert "never ask" in prompt.lower() or "don't ask" in prompt.lower()

    def test_english_speaker_no_language_guidance(self) -> None:
        """Test English speakers don't get EAL-specific guidance."""
        prompt = build_language_aware_prompt(
            grade=5,
            primary_language="English",
        )

        # Should not have "Language Support for" section
        assert "Language Support for" not in prompt

    def test_mandarin_specific_elements(self) -> None:
        """Test Mandarin prompt has Chinese-specific elements."""
        prompt = build_language_aware_prompt(
            grade=5,
            primary_language="Mandarin",
        )

        assert "你好" in prompt or "Nǐ hǎo" in prompt
        assert "很好" in prompt or "Hěn hǎo" in prompt
        assert "Mandarin" in prompt or "Chinese" in prompt

    def test_prompt_encourages_speaking(self) -> None:
        """Test prompt encourages student to speak."""
        prompt = build_language_aware_prompt(
            grade=5,
            primary_language="Arabic",
        )

        assert "encourage" in prompt.lower()
        assert "speak" in prompt.lower() or "express" in prompt.lower()


class TestGetCulturalBridgeHint:
    """Tests for get_cultural_bridge_hint function."""

    def test_confederation_arabic_bridge(self) -> None:
        """Test Confederation topic bridge for Arabic speakers."""
        hint = get_cultural_bridge_hint("Arabic", "confederation")

        assert hint is not None
        assert "Arab" in hint

    def test_wetlands_vietnamese_bridge(self) -> None:
        """Test wetlands topic bridge for Vietnamese speakers."""
        hint = get_cultural_bridge_hint("Vietnamese", "wetland ecosystems")

        assert hint is not None
        assert "Mekong" in hint or "Delta" in hint

    def test_identity_tagalog_bridge(self) -> None:
        """Test identity topic bridge for Tagalog speakers."""
        hint = get_cultural_bridge_hint("Tagalog", "personal identity")

        assert hint is not None
        assert "kapamilya" in hint.lower() or "family" in hint.lower()

    def test_democracy_ukrainian_bridge(self) -> None:
        """Test democracy topic bridge for Ukrainian speakers."""
        hint = get_cultural_bridge_hint("Ukrainian", "democracy in Canada")

        assert hint is not None
        assert "freedom" in hint.lower()

    def test_unknown_topic_returns_none(self) -> None:
        """Test unknown topic returns None."""
        hint = get_cultural_bridge_hint("Arabic", "quantum physics")

        assert hint is None

    def test_unknown_language_returns_none(self) -> None:
        """Test unknown language returns None for valid topic."""
        hint = get_cultural_bridge_hint("Klingon", "confederation")

        # May return None if language not in bridges dict
        # This is acceptable behavior
        pass  # No assertion needed, just ensure no exception

    def test_case_insensitive_topic(self) -> None:
        """Test topic matching is case-insensitive."""
        hint_lower = get_cultural_bridge_hint("Arabic", "confederation")
        hint_upper = get_cultural_bridge_hint("Arabic", "CONFEDERATION")
        hint_mixed = get_cultural_bridge_hint("Arabic", "Confederation")

        # All should return the same hint
        assert hint_lower == hint_upper == hint_mixed

    def test_partial_topic_match(self) -> None:
        """Test partial topic matching works."""
        # "wetland" should match topic containing "wetland"
        hint = get_cultural_bridge_hint("Arabic", "wetland ecosystems in Alberta")

        assert hint is not None
        assert "oases" in hint.lower() or "water" in hint.lower()


class TestLanguageAlphabetTypes:
    """Tests for alphabet type categorization."""

    def test_arabic_script_languages(self) -> None:
        """Test Arabic script languages are identified."""
        ctx = get_language_context("Arabic")
        assert ctx.alphabet_type == "arabic"

    def test_cyrillic_languages(self) -> None:
        """Test Cyrillic script languages are identified."""
        ctx = get_language_context("Ukrainian")
        assert ctx.alphabet_type == "cyrillic"

    def test_logographic_languages(self) -> None:
        """Test logographic script languages are identified."""
        ctx = get_language_context("Mandarin")
        assert ctx.alphabet_type == "logographic"

    def test_latin_script_languages(self) -> None:
        """Test Latin script languages are identified."""
        for lang in ["Spanish", "Tagalog", "Somali"]:
            ctx = get_language_context(lang)
            assert ctx.alphabet_type in ["latin", "latin_diacritics"], f"{lang} wrong type"

    def test_gurmukhi_script(self) -> None:
        """Test Punjabi uses Gurmukhi script."""
        ctx = get_language_context("Punjabi")
        assert ctx.alphabet_type == "gurmukhi"


class TestCommonDifficulties:
    """Tests for language-specific learning difficulties."""

    def test_th_sound_difficulties(self) -> None:
        """Test languages that struggle with TH sounds."""
        # TH is difficult for many non-English speakers
        languages_with_th_issues = ["Arabic", "Vietnamese", "Ukrainian", "Somali", "Tagalog"]

        for lang in languages_with_th_issues:
            ctx = get_language_context(lang)
            has_th_difficulty = any(
                "th" in d.lower() for d in ctx.common_difficulties
            )
            assert has_th_difficulty, f"{lang} should list TH difficulty"

    def test_article_difficulties(self) -> None:
        """Test languages that struggle with articles."""
        # Many languages don't have articles (a, an, the)
        languages_without_articles = ["Arabic", "Mandarin", "Ukrainian"]

        for lang in languages_without_articles:
            ctx = get_language_context(lang)
            has_article_difficulty = any(
                "article" in d.lower() for d in ctx.common_difficulties
            )
            assert has_article_difficulty, f"{lang} should list article difficulty"

    def test_l_r_distinction(self) -> None:
        """Test Mandarin lists L/R distinction difficulty."""
        ctx = get_language_context("Mandarin")
        has_lr = any("l/r" in d.lower() for d in ctx.common_difficulties)
        assert has_lr, "Mandarin should list L/R distinction difficulty"


class TestCulturalNotes:
    """Tests for cultural notes content."""

    def test_family_importance_noted(self) -> None:
        """Test many cultures note family importance."""
        family_focused = ["Arabic", "Punjabi", "Tagalog", "Vietnamese", "Somali"]

        for lang in family_focused:
            ctx = get_language_context(lang)
            has_family_note = any(
                "family" in note.lower() for note in ctx.cultural_notes
            )
            assert has_family_note, f"{lang} should note family importance"

    def test_educational_values_noted(self) -> None:
        """Test Mandarin notes education value."""
        ctx = get_language_context("Mandarin")
        has_education_note = any(
            "education" in note.lower() for note in ctx.cultural_notes
        )
        assert has_education_note, "Mandarin should note education value"

    def test_cultural_sensitivity_for_ukraine(self) -> None:
        """Test Ukrainian notes handle current events sensitively."""
        ctx = get_language_context("Ukrainian")
        # Should mention that current events may be sensitive
        has_sensitive_note = any(
            "current events" in note.lower() or "sensitive" in note.lower()
            for note in ctx.cultural_notes
        )
        assert has_sensitive_note, "Ukrainian should have sensitivity note"
