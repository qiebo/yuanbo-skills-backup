# Task Canvas

Use this canvas as the main working artifact. The rewritten prompt should come from the canvas, not the other way around.

## Canvas fields

### 1. Problem to solve

- What is the real problem or need?
- Why does this task exist?

### 2. Deliverable

- What concrete output should be produced?
- What form should it take?

### 3. Audience and decision context

- Who will use or read the output?
- What decision, action, or handoff should it support?

### 4. Inputs and source of truth

- What materials are available?
- Which sources are authoritative?
- What is still missing?

### 5. Constraints and boundaries

- What limits matter: time, scope, compliance, confidentiality, format, tone?
- What must the model not do?

### 6. Tradeoffs and priorities

- If not everything can be optimized, what matters most?
- What should the model favor?

### 7. Process

- What sequence should the work follow?
- Should analysis and drafting be separated?

### 8. Exceptions and unknowns

- What should happen if data is missing, uncertain, or conflicting?
- Which unknowns must stay visible?

### 9. Acceptance criteria

- What counts as done?
- What would make the output clearly useful?

### 10. Reuse or skill potential

- Is this a one-off task or a repeated workflow?
- Is the task stable enough to harden into a skill?

## Working states

For each field, mark the current state as one of:

- confirmed
- working assumption
- missing

The point is not to make the first canvas perfect. The point is to make hidden ambiguity visible.

## Update pattern

After each meaningful answer from the user:

- move newly clear facts into confirmed
- keep unresolved items in still open or missing
- record bounded assumptions explicitly

## Suggested output shape

Use a compact bullet structure such as:

- Problem to solve
  - confirmed:
  - working assumption:
  - missing:

Repeat for the fields that matter most to the current task. Keep the canvas lean, but keep the ambiguity visible.

## Coaching rule

If the prompt sounds polished but the canvas is weak, coach the canvas first. A stronger prompt built on a weak canvas is still weak.
