# Consolidated release review — October 26, 2026 (America/Chicago)

Scope: the complete local package containing the saved-wording display guard, compared against GitHub main `1d67e5d471ebad9de8a28cf8b9e10eec4e45836e`. The GitHub commit passed its 37-test Windows/Linux run. The updated package has 38 tests; its remote run must pass after upload.

## Results

- 38 automated tests passed, including actual Streamlit UI fallback and export review with deliberately damaged saved entries.
- Dependency consistency check passed (`pip check`).
- 24 authored scenarios passed: 84 replay snapshots and 156 checks.
- 252 sample UI combinations passed: all 21 event positions, three team selections, two audiences and two languages.
- All four sources and all 24 laboratory cases rendered without exceptions in the tested flows.
- Saved wording was created, reused and removed through the real Streamlit form in an isolated copy. The release's saved wording was not modified.
- 384 producer export combinations passed integrity, source-prefix, evidence and context checks across scenario prefixes, recoveries, audiences and languages.
- Pinned recovery and selection-change approval behavior were checked during the review series.
- Archive integrity passed. No virtual environment, bytecode cache or secrets file is bundled.
- Relative documentation links were checked; two moved links in development history were corrected.

## Boundaries

AI approval tests use simulated responses; native Phi-4-mini inference, model factuality, translation quality and hardware speed were not re-measured. Streamlit AppTest verifies application state and output, not pixel-level browser layout or every accessibility behavior. This is a local demonstration release, not a certified production broadcast system. These checks do not guarantee absence of all bugs.

## Release gate

Upload this consolidated package's changes, let Windows/Linux CI pass, then perform one short manual replay/export check on the recording laptop. Remaining submission work: a functioning demo video, screenshot, public video link, and portal submission. No further features are proposed for this release.
