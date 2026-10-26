# AI reliability update

This update addresses the observed Phi-4-mini draft from event 7. It does not claim to fix the model itself.

## Changes

- Accept either plain JSON or one enclosing JSON code fence. Never extract an object from surrounding prose, repair fields, or silently rewrite facts. Duplicate JSON keys are rejected. Raw model output is retained.
- Compare supported explicit pressure timing phrases with the pressure and recovery events. In this snapshot the actual gap is two seconds; five seconds is the eligibility window, not the measured gap. The observed erroneous draft is rejected even after its formatting is accepted.
- Prompts explicitly distinguish the five-second window from an exact interval.
- Narrowly recognize “does not prove it caused” and “does not establish that it caused” as uncertainty phrases. Independent positive “caused” claims remain rejected. This is not general negation understanding.
- Reusable pressure templates must use the documented five-second window wording. An exact pressure gap belongs only to its snapshot and cannot safely travel to other recoveries.
- Locally approved wording provenance stores the actual generation prompt and raw model output when available instead of reconstructing a possibly different prompt.

## Upgrade

Stop Streamlit. Back up your project. Extract the new package into a separate folder. Copy your saved data/wording_library.json into the new project so the human-corrected shot wording is retained. Keep the new synthetic event CSV. Restart using the same setup instructions.

No new generation is necessary to retain your corrected wording. New drafts will use the stricter checks. If the original erroneous draft is pasted again, the relevant rejection should identify pressure timing rather than merely the code fence.

## Limits

Regex guards cover specific English/Spanish timing constructions, not every paraphrase. They can reject valid prose and miss unsupported claims. Six-asset recap checks remain limited. Translation quality is not certified. A successful parse or green check never substitutes for reviewing the evidence. This change does not accelerate native model inference or establish autonomous factual accuracy.

Regression cases include: accepting a correctly fenced draft without changing its content; rejecting the actual numeric and word-form five-second error; accepting the correct two-second gap only for its snapshot; preventing exact gaps from becoming reusable templates; allowing the specific uncertainty wording while rejecting a separate causal assertion.
