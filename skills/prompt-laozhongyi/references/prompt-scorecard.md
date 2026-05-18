# Task Framing Scorecard

Use this scorecard before asking follow-up questions. The purpose is not only evaluation but training: show the user which parts of task definition are strong, which are weak, and why those weaknesses will create execution risk.

## Scoring scale

Score every dimension from 1 to 5.

- 1: missing or dangerously vague
- 2: present but weak
- 3: usable with noticeable risk
- 4: clear and mostly robust
- 5: strong, explicit, and reusable

Do not inflate scores for polished wording. Score based on whether a model or teammate could execute the task reliably.

## Dimensions

### 1. Problem definition

Ask:

- Is the real problem actually defined?
- Is the task framed as a problem to solve, not just a vague request to "improve" something?
- Is the business purpose visible?

High score signals:

- states the underlying problem clearly
- distinguishes the real task from the current draft prompt
- explains why this output is needed

Low score risks:

- the model solves the wrong problem
- the output sounds useful but misses the real need

### 2. Deliverable clarity

Ask:

- Is the final deliverable explicit?
- Is the result a summary, recommendation, memo, table, draft, checklist, or something else?
- Is the deliverable concrete enough to recognize when it is done?

High score signals:

- names the exact deliverable
- distinguishes analysis from final output
- avoids vague verbs such as "optimize" or "handle" without a concrete result

Low score risks:

- the model returns the wrong kind of answer
- the output cannot be used downstream

### 3. Audience and decision context

Ask:

- Who will read or use the output?
- What decision, action, or handoff should it support?
- How much detail does that audience need?

High score signals:

- names the audience or owner
- ties the output to a decision or use case
- clarifies detail level and tone only when they matter

Low score risks:

- the answer is pitched at the wrong level
- the model over-explains or under-explains

### 4. Input readiness

Ask:

- Are the needed materials available?
- Is the source of truth clear?
- Are missing inputs acknowledged?

High score signals:

- required inputs are listed
- authoritative inputs are distinguishable from optional context
- gaps in inputs are visible rather than hidden

Low score risks:

- the model fills gaps with guesses
- the answer depends on data it never received

### 5. Constraints and boundaries

Ask:

- Are constraints explicit?
- Are there time, format, compliance, confidentiality, or scope boundaries?
- Is there anything the model must not do?

High score signals:

- states the relevant boundaries
- identifies no-go areas
- prevents obvious overreach

Low score risks:

- the model produces something unusable or risky
- the answer drifts beyond the safe scope

### 6. Tradeoff clarity

Ask:

- What matters most if everything cannot be optimized at once?
- Should the model favor speed, completeness, precision, persuasion, or stability?
- Are the priorities ordered?

High score signals:

- names the primary priority
- makes tradeoffs explicit
- avoids "do everything perfectly" framing

Low score risks:

- the model optimizes for the wrong thing
- the user gets a generic answer because priorities were never chosen

### 7. Process design

Ask:

- For complex work, is the workflow broken into stages?
- Is there an order that reduces failure risk?
- Should the model check for gaps before final drafting?

High score signals:

- sequences major steps clearly
- separates analysis from final output when useful
- includes checks before finishing when the task is risky

Low score risks:

- the model commits too early to a flawed path
- important reasoning steps get skipped

### 8. Unknowns and exception handling

Ask:

- What should happen when information is missing, conflicting, or uncertain?
- Should the model ask, flag, stop, continue with placeholders, or make bounded assumptions?
- Are unresolved unknowns visible?

High score signals:

- defines what to do with missing or conflicting information
- surfaces unknowns explicitly
- forbids fabrication where it would be harmful

Low score risks:

- silent assumptions leak into the answer
- hallucinated details appear confident

### 9. Acceptance criteria

Ask:

- What counts as done?
- How would a reviewer judge whether the output succeeded?
- Are the quality checks tied to the real business need?

High score signals:

- names completion criteria
- defines what a successful output looks like
- makes review possible without guesswork

Low score risks:

- no clear way to judge success
- revision loops drift because standards stay implicit

### 10. Skill potential

Ask:

- Is this a repeated workflow?
- Are the inputs, steps, and acceptance rules stable enough to reuse?
- Would hardening this task save time or reduce variance?

High score signals:

- task is frequent
- structure is stable across runs
- reusable inputs and checks can be defined

Low score risks:

- the task is too one-off to justify hardening
- the user tries to optimize wording instead of improving process design

## Output format

Present the scorecard in a compact table or bullet list. For each dimension include:

- dimension name
- score out of 5
- one-line judgment
- one-line main risk

After the scorecard, add:

- strongest dimension
- weakest dimension
- training takeaway: the one or two thinking habits the user should focus on improving

## Coaching guidance

- Be strict but fair. The scorecard should create learning value, not fake precision.
- A polished sentence with a weak problem definition should still score low.
- Avoid false granularity. If two dimensions are weak, explain which one blocks execution more.
- Use the scorecard to choose the next follow-up question.
- When the user improves over multiple rounds, call out what score improved and why.
