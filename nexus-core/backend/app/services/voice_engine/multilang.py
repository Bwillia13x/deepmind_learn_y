"""
Multi-Language Support for NEXUS.

Provides language-specific system prompts and cultural bridge hints
for EAL (English as Additional Language) students.
"""

from dataclasses import dataclass


@dataclass
class LanguageContext:
    """Context for a specific language/culture."""

    language_code: str
    language_name: str
    greeting_native: str  # How to say hello in native language
    encouragement_native: str  # Encouraging phrase
    common_difficulties: list[str]  # Common English learning challenges
    cultural_notes: list[str]  # Cultural context for curriculum bridging
    alphabet_type: str  # "latin", "arabic", "cyrillic", "logographic", etc.


# Language configurations for common EAL languages in Alberta
LANGUAGE_CONTEXTS: dict[str, LanguageContext] = {
    "Arabic": LanguageContext(
        language_code="ar",
        language_name="Arabic",
        greeting_native="مرحبا (Marhaba)",
        encouragement_native="أحسنت! (Ahsant! - Well done!)",
        common_difficulties=[
            "Vowel sounds (English has more vowels)",
            "TH sounds (not in Arabic)",
            "P/B distinction",
            "Articles (a, an, the)",
            "Right-to-left reading transition",
        ],
        cultural_notes=[
            "Family and community are highly valued",
            "Hospitality is a core cultural value",
            "History of great scientists and mathematicians (Al-Khwarizmi, Ibn Sina)",
            "Rich storytelling traditions (One Thousand and One Nights)",
        ],
        alphabet_type="arabic",
    ),
    "Mandarin": LanguageContext(
        language_code="zh",
        language_name="Mandarin Chinese",
        greeting_native="你好 (Nǐ hǎo)",
        encouragement_native="很好! (Hěn hǎo! - Very good!)",
        common_difficulties=[
            "L/R distinction",
            "Plural forms (Chinese has no plurals)",
            "Verb tenses (Chinese uses time words instead)",
            "Articles (not in Chinese)",
            "Word stress and intonation",
        ],
        cultural_notes=[
            "Education is highly valued",
            "Lunar New Year is the most important holiday",
            "Rich history of inventions (paper, compass, printing)",
            "Confucian values emphasize respect and hard work",
        ],
        alphabet_type="logographic",
    ),
    "Punjabi": LanguageContext(
        language_code="pa",
        language_name="Punjabi",
        greeting_native="ਸਤ ਸ੍ਰੀ ਅਕਾਲ (Sat Sri Akal)",
        encouragement_native="ਬਹੁਤ ਵਧੀਆ! (Bahut vadhia! - Very good!)",
        common_difficulties=[
            "W/V distinction",
            "TH sounds",
            "Word endings (consonant clusters)",
            "Past tense irregular verbs",
        ],
        cultural_notes=[
            "Strong agricultural heritage",
            "Vibrant music and dance traditions (Bhangra)",
            "Family bonds are very important",
            "Festival of Vaisakhi celebrates harvest",
        ],
        alphabet_type="gurmukhi",
    ),
    "Tagalog": LanguageContext(
        language_code="tl",
        language_name="Tagalog/Filipino",
        greeting_native="Kamusta (Hello/How are you)",
        encouragement_native="Magaling! (Excellent!)",
        common_difficulties=[
            "TH sounds (not in Tagalog)",
            "F sound (becomes P)",
            "Consonant clusters at word start",
            "Articles usage",
        ],
        cultural_notes=[
            "Strong family ties (extended family)",
            "Hospitality is a core value",
            "Many English words already in Tagalog",
            "Rich tradition of oral storytelling",
        ],
        alphabet_type="latin",
    ),
    "Spanish": LanguageContext(
        language_code="es",
        language_name="Spanish",
        greeting_native="¡Hola!",
        encouragement_native="¡Muy bien! (Very good!)",
        common_difficulties=[
            "Short vowels vs long vowels",
            "Initial consonant clusters (sp-, st-, sk-)",
            "TH sounds",
            "Word stress patterns",
        ],
        cultural_notes=[
            "Many cognates between Spanish and English",
            "Family celebrations are important",
            "Rich literary traditions",
            "Various cultural backgrounds (Latin America)",
        ],
        alphabet_type="latin",
    ),
    "Ukrainian": LanguageContext(
        language_code="uk",
        language_name="Ukrainian",
        greeting_native="Привіт (Pryvit)",
        encouragement_native="Молодець! (Molodets'! - Well done!)",
        common_difficulties=[
            "TH sounds (not in Ukrainian)",
            "W sound (becomes V)",
            "Articles (not in Ukrainian)",
            "Auxiliary verbs (do, does, did)",
        ],
        cultural_notes=[
            "Strong traditions around holidays (Easter, Christmas)",
            "Rich folk music and dance heritage",
            "Agricultural traditions (wheat, sunflowers)",
            "Current events may be sensitive topic",
        ],
        alphabet_type="cyrillic",
    ),
    "Vietnamese": LanguageContext(
        language_code="vi",
        language_name="Vietnamese",
        greeting_native="Xin chào",
        encouragement_native="Giỏi lắm! (Very good!)",
        common_difficulties=[
            "TH sounds (becomes T or D)",
            "Consonant clusters (not in Vietnamese)",
            "Final consonants",
            "Stress patterns (Vietnamese is tonal)",
            "Plural forms",
        ],
        cultural_notes=[
            "Lunar New Year (Tết) is most important holiday",
            "Strong respect for elders and teachers",
            "Rich food culture",
            "Family is central to social life",
        ],
        alphabet_type="latin_diacritics",
    ),
    "Somali": LanguageContext(
        language_code="so",
        language_name="Somali",
        greeting_native="Salaan",
        encouragement_native="Waa fiican tahay! (You're doing great!)",
        common_difficulties=[
            "P sound (becomes B)",
            "Short vowels",
            "TH sounds",
            "Consonant clusters",
        ],
        cultural_notes=[
            "Strong oral poetry tradition",
            "Nomadic heritage",
            "Extended family is very important",
            "Community gatherings are valued",
        ],
        alphabet_type="latin",
    ),
}

# Default context for unknown languages
DEFAULT_CONTEXT = LanguageContext(
    language_code="en",
    language_name="English",
    greeting_native="Hello",
    encouragement_native="Great job!",
    common_difficulties=[],
    cultural_notes=[],
    alphabet_type="latin",
)


def get_language_context(language: str) -> LanguageContext:
    """
    Get context for a specific language.

    Args:
        language: Language name (e.g., "Arabic", "Mandarin")

    Returns:
        LanguageContext with language-specific information
    """
    # Try exact match first
    if language in LANGUAGE_CONTEXTS:
        return LANGUAGE_CONTEXTS[language]

    # Try case-insensitive match
    for key, context in LANGUAGE_CONTEXTS.items():
        if key.lower() == language.lower():
            return context
        if context.language_code.lower() == language.lower():
            return context

    return DEFAULT_CONTEXT


def build_language_aware_prompt(
    grade: int,
    primary_language: str,
    curriculum_outcome: str | None = None,
    cultural_bridge_hints: str | None = None,
) -> str:
    """
    Build a system prompt with language-specific adaptations.

    Args:
        grade: Student's grade level
        primary_language: Student's home language
        curriculum_outcome: Optional current learning focus
        cultural_bridge_hints: Optional additional cultural context

    Returns:
        Complete system prompt with language awareness
    """
    lang_ctx = get_language_context(primary_language)

    curriculum_context = ""
    if curriculum_outcome:
        curriculum_context = f"- Current learning focus: {curriculum_outcome}"

    cultural_section = ""
    if cultural_bridge_hints:
        cultural_section = f"\nAdditional cultural context:\n{cultural_bridge_hints}"

    # Build language-specific guidance
    language_guidance = ""
    if lang_ctx.language_code != "en":
        difficulties = "\n  ".join(f"- {d}" for d in lang_ctx.common_difficulties[:3])
        cultural_notes = "\n  ".join(f"- {n}" for n in lang_ctx.cultural_notes[:2])

        language_guidance = f"""
Language Support for {lang_ctx.language_name} speakers:
- You may occasionally use the greeting "{lang_ctx.greeting_native}" to build rapport
- Use "{lang_ctx.encouragement_native}" when praising effort
- Be especially patient with:
  {difficulties}

Cultural Connection Points:
  {cultural_notes}
"""

    return f"""You are NEXUS, a supportive and patient AI tutor for Grade {grade} EAL (English as Additional Language) students in Alberta, Canada.

Your role:
- Practice conversational English through friendly dialogue
- Speak simply and clearly, adjusting to the student's level
- Encourage the student to speak and express themselves
- Gently correct pronunciation and grammar when appropriate
- Connect topics to Alberta curriculum when relevant
- Be culturally sensitive and welcoming

Student context:
- Grade level: {grade}
- Primary language: {lang_ctx.language_name}
{curriculum_context}
{language_guidance}
Guidelines:
- Use short, clear sentences
- Ask open-ended questions to encourage speaking
- Praise effort and progress
- If the student struggles, offer to explain in simpler terms
- Never ask for personal information (names, addresses, phone numbers)
- Keep conversations educational but fun
{cultural_section}

Start by greeting the student warmly and asking about their day or interests."""


def get_cultural_bridge_hint(
    language: str,
    topic: str,
) -> str | None:
    """
    Get a cultural bridge hint for a specific topic and language.

    Helps connect Alberta curriculum concepts to student's cultural background.

    Args:
        language: Student's home language
        topic: The curriculum topic being discussed

    Returns:
        Cultural bridge hint or None if not applicable
    """
    lang_ctx = get_language_context(language)

    # Topic-specific bridges
    topic_lower = topic.lower()

    bridges = {
        "confederation": {
            "Arabic": "Like how different Arab nations came together in the Arab League",
            "Mandarin": "Similar to how China unified different kingdoms",
            "Ukrainian": "Like how Ukraine became independent from the Soviet Union",
            "Vietnamese": "Similar to Vietnam's reunification history",
        },
        "wetland": {
            "Arabic": "Like oases in the desert, wetlands are special water places",
            "Mandarin": "Similar to rice paddies that need lots of water",
            "Vietnamese": "Like the Mekong Delta where rivers meet the sea",
            "Punjabi": "Like the riverlands where the Indus flows",
        },
        "identity": {
            "Arabic": "Thinking about your family name and where they come from",
            "Mandarin": "Your family history and ancestors",
            "Ukrainian": "Your traditions and what makes your family special",
            "Tagalog": "Your kapamilya (family) and heritage",
        },
        "democracy": {
            "Arabic": "Shura - the Islamic tradition of consultation",
            "Mandarin": "Different from Chinese government, Canadians vote for leaders",
            "Ukrainian": "Fighting for freedom to choose your own leaders",
        },
    }

    # Find matching bridge
    for key, language_bridges in bridges.items():
        if key in topic_lower:
            return language_bridges.get(language) or language_bridges.get(
                lang_ctx.language_name
            )

    return None
