# Ambiguous Language Guide

Use this guide when the user's wording sounds polished but remains hard to execute. Apply these patterns even when the original request is written in another language.

## What to look for

Watch for words that sound useful but hide missing decisions:

- optimize
- improve
- professional
- clear
- concise
- comprehensive
- strategic
- systematic
- high-quality
- polished
- actionable
- complete
- insightful
- user-friendly

These words are not wrong. They are incomplete until they are tied to observable outcomes, priorities, or constraints.

## Conversion patterns

### Vague verb -> concrete deliverable

Instead of accepting:

- "optimize this"
- "handle this"
- "improve the prompt"

Ask:

- What concrete output should be better?
- Better in what way: faster, more accurate, easier to review, more consistent, or easier to reuse?

### Vague adjective -> observable traits

Instead of accepting:

- "professional"
- "clear"
- "concise"

Ask:

- What would make it look professional in practice?
- What level of detail is right for the audience?
- Should the result read like bullets, a memo, or a client-ready draft?

### Vague standard -> acceptance check

Instead of accepting:

- "high quality"
- "good enough"
- "complete"

Ask:

- How will you judge whether the result is good?
- What must be included?
- What would make you reject the output?

### Vague priority -> forced tradeoff

Instead of accepting:

- "make it fast and thorough"
- "make it detailed but concise"
- "make it strategic and practical"

Ask:

- If the model cannot maximize both, which should it favor?
- What is the first priority and what is the second?

## Common unpacking moves

### 1. Turn abstractions into choices

Replace a broad question with two or three concrete options.

Example:

- Instead of "What style do you want?"
- Ask "Should this be an executive summary, a working memo, or a final external draft?"

### 2. Turn quality words into review checks

Replace a quality adjective with a checkable rule.

Example:

- Instead of "make it comprehensive"
- Ask "Which sections or issues must not be missed?"

### 3. Turn intent words into business purpose

Replace a generic request with the decision it should support.

Example:

- Instead of "help me improve this analysis"
- Ask "What decision should this analysis help someone make?"

### 4. Turn uncertainty into explicit handling rules

Replace hidden assumptions with visible exception behavior.

Example:

- Instead of "do your best with missing info"
- Ask "Should the model stop, flag gaps, or continue with placeholders?"

## Coaching rule

Do not attack vague language as bad writing. Treat it as evidence that a decision has not been made yet. Your job is to surface the missing decision and make it explicit.
