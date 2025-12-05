# NEXUS Domain Glossary

## Core Terminology

### Oracy Session

A voice-interactive tutoring session between NEXUS and an EAL student. Sessions focus on
spoken English practice through multi-turn Socratic dialogue anchored to Alberta curriculum.

### Scout Report

A qualitative insight summary generated for teachers after an Oracy Session. This is NOT a
grade—it is a draft observation to reduce teacher administrative burden.

Components:

- Engagement Level (High/Medium/Low)
- Linguistic Observations (pronunciation, grammar patterns)
- Curriculum Connections (which outcomes were touched)
- Recommended Next Steps

### Student Code

A hashed, non-identifying code used to track student progress. We NEVER store student names
in the database. Format: `STU-{hash}`.

## Alberta Education Terms

### EAL (English as an Additional Language)

Students whose primary language is not English and who require specialized support for
English language acquisition.

### IPP (Individual Program Plan)

A compliance document required for students with identified learning needs. Teachers spend
significant time drafting these. NEXUS provides "Draft 0" insights to reduce this burden.

### PAT (Provincial Achievement Test)

Standardized assessments administered by Alberta Education. Our target metric is improving
EAL student performance on PAT Literacy benchmarks.

### PUF (Program Unit Funding)

Early childhood funding for specialized programming. Context for future expansion.

### Program of Studies

Alberta's official curriculum documents defining learning outcomes by subject and grade.

## Technical Terms

### Curriculum Bridge

The RAG (Retrieval-Augmented Generation) system that links student conversations to relevant
Alberta Program of Studies outcomes, enabling culturally-aware explanations.

### Privacy Guard

Middleware that scrubs PII (Personally Identifiable Information) from all logs and LLM
requests before processing.

### Voice Engine

The real-time audio processing pipeline handling STT (Speech-to-Text), LLM dialogue, and
TTS (Text-to-Speech) for Oracy Sessions.

## Variable Naming Conventions

| Concept | Use This | NOT This |
|---------|----------|----------|
| Student identifier | `student_code` | `user_id`, `student_name` |
| Session record | `oracy_session` | `user_log`, `session` |
| Teacher insight | `scout_report` | `report`, `summary` |
| Curriculum link | `curriculum_outcome` | `topic`, `subject` |
