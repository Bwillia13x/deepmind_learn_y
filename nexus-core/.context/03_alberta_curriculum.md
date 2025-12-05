# Alberta Curriculum Reference

## Program of Studies Format

Curriculum outcomes follow the format:
`{Subject} - Grade {N} - {Strand} - {Specific Outcome}`

Example: "Social Studies - Grade 5 - Stories of Canada - 5.1.2"

## Sample Outcomes for RAG System

### Social Studies Grade 5

- **5.1.1**: Students will appreciate the complexity of identity in the Canadian context
- **5.1.2**: Students will examine historical events in the Canadian context
- **5.2.1**: Students will examine the histories and stories of First Nations peoples
- **5.2.2**: Students will assess the impact of Confederation on Canada

### Language Arts Grade 5

- **LA.5.1.1**: Students will listen, speak, read, and write to explore thoughts and ideas
- **LA.5.1.2**: Students will comprehend and respond personally to oral, print, and media texts
- **LA.5.2.1**: Students will use strategies to generate ideas for oral and written texts
- **LA.5.2.2**: Students will organize ideas using appropriate text structures

### Science Grade 5

- **SCI.5.1**: Students will describe the properties of wetland ecosystems
- **SCI.5.2**: Students will investigate weather and climate patterns
- **SCI.5.3**: Students will demonstrate understanding of electricity and magnetism

## Cultural Bridge Guidelines

When explaining Alberta curriculum to EAL students:

1. **Identify Home Context**: Determine student's country/region of origin
2. **Find Analogies**: Map Canadian concepts to familiar concepts from their background
3. **Use Concrete Examples**: Abstract concepts should be grounded in tangible scenarios
4. **Validate Prior Knowledge**: Acknowledge what students already know from their culture

### Example Cultural Bridges

| Alberta Concept | Ukrainian Context | Syrian Context | Filipino Context |
|----------------|-------------------|----------------|------------------|
| Confederation | Union of Soviet republics → independence | Ottoman Empire regions | Spanish/American colonial unification |
| Wetlands | Pripyat marshes | Euphrates delta | Rice paddies, mangroves |
| Democratic government | Post-Soviet elections | -- (use different frame) | Barangay system |

## Outcome Embedding Format

For the vector store, each outcome should be embedded with:

```json
{
  "outcome_id": "SS-5-1-2",
  "subject": "Social Studies",
  "grade": 5,
  "strand": "Stories of Canada",
  "outcome_text": "Students will examine historical events...",
  "keywords": ["history", "Canada", "events", "Confederation"],
  "cultural_bridge_hints": ["national formation", "unification", "colonial history"]
}
```

## Grade Level Language Guidance

| Grade | Reading Level | Vocabulary | Sentence Complexity |
|-------|--------------|------------|---------------------|
| K-2 | Beginning | Concrete, simple | Short, declarative |
| 3-4 | Developing | Some abstract | Compound sentences |
| 5-6 | Intermediate | Grade-level abstract | Complex sentences |
| 7-9 | Advanced | Domain-specific | Varied structures |
