# Final package validation — October 26, 2026

## Automated evidence

- **37 tests passed** against the final package, including the fictional recording view and reviewed shot template.
- **24/24 authored synthetic scenarios passed**, across **84 revealed prefixes** and **156 checks**; zero failures.
- Latest analytics-plus-wording timing: median **3.40 ms**, p95 **4.88 ms** in the build environment. This excludes UI rendering, context-panel computation, native inference, network and production ingestion. See data/evaluation_report.json for exact values.
- Rule fallback was used for **60/84 prefixes** with the two included prepared templates. This is coverage of authored test cases, not real-world factuality.
- A fresh Linux virtual environment installed only requirements.txt. Tests were run on a clean copied source tree without the Foundry SDK. This verifies the no-model judge path in that environment, not arbitrary Windows hardware.

Coverage: possession boundaries, future-event isolation, shot timing, historical baseline, pending outcomes, template eligibility, current evidence, HTML escaping, producer ZIP contents, review invalidation, UI checkpoints, audience/language selection and fictional-name recording.

AI control-flow tests use mocked outputs and a fake sleeping subprocess. They verify completion refresh, cancellation, timeout and review gates. The observed incorrect pressure draft is a regression fixture; passing its test is not a general factuality score.

## User-reported Windows evidence

Deepali displayed a working replay, both recovery outcomes, audience views, revised design and exported cards. A Phi-4-mini Quick draft run reported 74.8 seconds generation and 21.2 seconds setup; it contained a timing error and fenced JSON. The wording was corrected and displayed in the app. Reported installed SDK: 2.2.1. Reported selected variant: Phi-4-mini-instruct-generic-cpu:5. These observations were supplied through the conversation, not independently measured on the user's machine by this build environment.

The corrected shot wording is reconstructed from the exact conversation example. Original pending-template provenance is preserved. The reconstruction does not invent an original exported approval timestamp or claim a successful six-asset batch.

## Published repository and prior CI

The public repository is https://github.com/deepaliattavar/matchlens. Windows and Linux jobs passed for commit `47cb71a9dc16e1ef4dfce85f373a816db1179ecc` with 32 tests: https://github.com/deepaliattavar/matchlens/actions/runs/40422305029.

The newer input-validation fixes pass 37 tests locally. Their remote CI result is pending upload; the earlier green run does not cover these changes. Added regression tests cover invalid IDs, missing approval metadata, malformed timestamps, and preservation of documented null historical timestamps.

## Still required before submission

- Final clean Windows run of this package and manual checklist.
- Re-run GitHub Actions after uploading the latest validation fixes (37 tests).
- Recorded functioning video under two minutes, public playback checked signed out.
- Final portal submission and confirmation.

Not claimed: native model accuracy certification, successful GPU/NPU acceleration, speed improvement from a controlled A/B benchmark, professional usability study, full browser screenshot review, production graphics integration, or cross-platform native AI compatibility. No model downloads or paid APIs were used for the clean judge test.

Current package: all 37 tests and 24 scenarios pass with the input-validation fixes. Fictional teams remain Northbridge and Riverside.
