# NEXUS Privacy Charter

## Guiding Principle

NEXUS is designed for Alberta K-12 schools and must comply with FOIP (Freedom of Information
and Protection of Privacy Act). Privacy is not a feature—it is the foundation.

## Hard Rules

### Rule 1: Audio is Transient

- Audio streams are processed in real-time and NEVER persisted to disk
- Only text transcripts (after PII scrubbing) may be stored
- Audio buffers are cleared immediately after TTS/STT processing

### Rule 2: No PII in LLM Prompts

All data sent to external LLM providers must be scrubbed of:

- Student names → Replace with `<STUDENT>`
- Teacher names → Replace with `<TEACHER>`
- Phone numbers → Replace with `<PHONE>`
- Email addresses → Replace with `<EMAIL>`
- Physical addresses → Replace with `<ADDRESS>`
- Any identifying numbers (student IDs) → Replace with `<ID>`

### Rule 3: No Biometric Collection

- NO video capture
- NO facial recognition
- NO voice biometrics or voiceprints
- Voice is used ONLY for real-time STT; no voice signatures stored

### Rule 4: Student Anonymization

- Database stores `student_code` (hashed identifier), NEVER actual names
- Mapping of `student_code` to real identity is maintained ONLY in school's
  existing Student Information System (SIS), not in NEXUS
- All Scout Reports reference `student_code` only

### Rule 5: Data Residency

- All data stored in Alberta-domiciled, encrypted databases
- School Board retains data governance authority
- No data transfer to non-Canadian jurisdictions without explicit approval

## Privacy Guard Implementation

The `PrivacyGuard` middleware must:

1. Intercept ALL incoming requests
2. Apply PII regex patterns to request bodies
3. Log only sanitized content
4. Reject requests containing un-scrubbable PII patterns

```python
# Required PII Patterns
PATTERNS = {
    "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    "phone": r"(\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}",
    "name": r"\b[A-Z][a-z]+\s[A-Z][a-z]+\b",  # Basic name pattern
}
```

## Consent Requirements

### Student Interaction (Phase 1-2)

- Parental consent required for student participation
- Opt-out available at any time
- No penalty for non-participation

### Affective Detection (Phase 3 - Future)

- Requires independent Ethics Review Board (ERB) approval
- Explicit, informed parental consent (separate from general consent)
- Must demonstrate educational necessity
- Federated processing only (no raw affect data leaves device)

## Data Retention

| Data Type | Retention Period | Notes |
|-----------|------------------|-------|
| Oracy Session Transcripts | 1 school year | Anonymized |
| Scout Reports | 2 school years | Teacher access only |
| Audio Streams | 0 (never stored) | Real-time only |
| System Logs | 90 days | PII-scrubbed |

## Audit Trail

All data access must be logged with:

- Timestamp
- Accessor role (teacher/admin)
- Data type accessed
- Purpose code
