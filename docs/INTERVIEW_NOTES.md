# Explain your project

## Your opening

“I built MatchLens to answer a narrow football question: after a team wins the ball, what happens next? I structured the work as an event pipeline, linked each conclusion to source events, and separated slow AI preparation from responsive replay.”

Describe AI-assisted coding honestly. Own the decisions you understand and verified; do not claim to have manually written every line.

## The story to lead with

“Two recoveries, two different endings” is the demonstration. Show the visual contrast first, then rewind to explain how the pipeline arrived there. These authored synthetic examples demonstrate the tool; they do not establish findings about real teams. For job applications, connect the same work to the employer’s confirmed tools and decisions, as outlined in PORTFOLIO_STRATEGY.md.

## Decisions to explain

- Why possession IDs? They prevent linking a recovery to an unrelated later shot.
- Why keep pending separate? A sample can stop before the possession finishes. Missing evidence is not a negative outcome.
- Why prepared wording? Local generation was slow and later hit a memory limit. Reusable reviewed wording removes that dependency from replay.
- What does AI contribute? Draft wording during preparation. Python computes facts and selects eligible wording; the selector is not an AI agent.
- Why evidence IDs? Producers can inspect the exact events supporting the explanation.
- What transfers from data engineering? Input validation, explicit state, reproducible scenarios, data lineage, deterministic transformations, and tests at boundary conditions.
- What is not proven? Producer time savings, audience engagement, pressure causality, chance quality, and production scalability.

## Walk through event 15

Riverside recovered at event 12. No same-possession shot followed before event 15 started a different possession. Therefore recovery 12 is closed without a recorded shot. Evidence includes preceding pressure 10, recovery 12, and boundary 15. The earlier recovery at event 5 did reach shot 7. The recap is one shot outcome, one closed outcome, zero pending.

## Next validation

Ask a broadcast producer to trace and write the same synthetic sequences with and without MatchLens. Compare correctness, time to a usable card, and edit effort. Predefine those measures before testing; do not invent results for a résumé.
