# Harness Principles

Use these principles as the evaluation frame.

## Prompt checks

Review whether the draft clearly states:

- the goal
- the available inputs
- the separation between instructions and source material
- the required output shape
- the process or decomposition for complex work
- the completion standard
- the rule for missing information

## Harness structure

Use five structural blocks when rewriting prompts for non-trivial work:

1. Goal
2. Inputs
3. Process
4. Exceptions
5. Output and acceptance

Interpret them as follows:

- Goal: what must be produced and why it exists
- Inputs: what materials the model may use
- Process: the sequence or method to follow
- Exceptions: what to do when data is missing, conflicting, risky, or out of scope
- Output and acceptance: what the final answer must look like and what counts as done

## Meta-prompt dimensions

Use these six dimensions to decide what to ask next:

1. goal
2. constraints
3. inputs
4. paths
5. human and AI division of labor
6. skill potential

## Common failure patterns

Watch for these problems:

- background is present, but the real task is not explicit
- the prompt asks for "optimize" or "analyze" without a deliverable
- source materials and instructions are mixed together
- there is no rule for missing information, so the model may invent
- the task is multi-step but the prompt assumes the model will infer the workflow
- there is no acceptance standard, so the output cannot be checked
- the user piles on context instead of cleaning the task definition

## Coaching bias

The skill should teach better prompt engineering habits, not just patch the current draft. When possible, help the user see:

- which missing dimension caused the weakness
- which question closed that gap
- why the rewritten prompt is more stable
