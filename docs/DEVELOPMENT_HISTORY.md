# Development and validation notes

Historical implementation notes; see the main README for the current workflow.

## What AI does—and what it does not

The model drafts wording in advance. Python calculates the outcome, interval, context and evidence. Humans review wording before reuse. During replay, approved templates fill current team names and shot intervals; event IDs always come from current analysis. This separates slow preparation from responsive replay.

Included wording:
- One original user-imported pending template, preserved with its unverified model attribution.
- One human-corrected shot template reconstructed from the exact wording the user displayed in their working app. Its original exported approval timestamp was not supplied, so it is null and its provenance explicitly identifies the reconstruction.

A user-reported Phi-4-mini Quick draft run took **74.8 seconds generation + 21.2 seconds setup**. It produced fenced JSON and misstated the pressure interval. The user corrected and reviewed the wording. This is evidence of a local drafting attempt, not autonomous factual accuracy or a controlled speed benchmark.

Current checks accept a single JSON code fence without editing its contents; reject some unsupported values and pressure timings; and preserve uncertainty. They are incomplete. They do not certify football meaning or translation quality. See [AI reliability](AI_RELIABILITY.md).

Optional generation uses `foundry-local-sdk==2.2.1` in `requirements-local.txt`. Install it only if testing generation; see [local AI setup](LOCAL_AI_SETUP.md). Models may require substantial RAM, downloads and setup time. The observed selected variant was CPU-based. No GPU/NPU acceleration or performance guarantee is claimed. The six-asset preparation workflow is implemented and control-flow tested with mocks; six successful real reviewed outputs are not bundled. A proposed AI story-selection-only redesign has not been implemented.

