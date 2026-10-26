# MatchLens

**They won the ball. What happened next?**

MatchLens helps a sports producer turn synthetic possession recoveries into audience-specific stories with inspectable evidence. One recovery reaches a saved shot in eight seconds; another possession ends without a shot. The story changes only as the relevant events are revealed.

Built by **Deepali Attavar**, with AI-assisted development. Python, pandas and Streamlit power the application. **Microsoft Foundry Local / Phi-4-mini** supports optional local wording preparation. No paid API, Azure deployment or Ollama is required.

## Run the judge demo — no model download

Python **3.12**. Extract/download the project and open a terminal in the folder containing `app.py`.

Windows Command Prompt or PowerShell:

```text
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m streamlit run app.py
```

macOS/Linux:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run app.py
```

Open the local address printed by Streamlit, normally http://localhost:8501. Dependency installation needs internet access. Default replay uses bundled files and starts no model. There are no credentials, account requirements or paid endpoints. Intended platform: desktop browser with a local Python application; native optional AI has only a user-reported Windows run.

## A two-minute walkthrough

1. Select **Riverside**, **Casual Fan**, **English**. Keep local generation off.
2. Click **Explore the two-recovery example**. Compare an eight-second recovery-to-shot sequence with a nine-second recovery-to-possession-change sequence. These are different endpoints, not a speed ranking.
3. Expand **Jump to a key moment**. At checkpoint 1 the outcome is developing. At checkpoint 2 a shot is observed; evidence is 3, 5, 7. Checkpoint 3 follows a different developing recovery. Checkpoint 4 closes that recovery without a shot, evidence 10, 12, 15.
4. Switch to **Analyst** for the detailed sequence, or **Español** for authored Spanish explanations. The recorded outcome stays the same. English prepared AI-assisted templates and Spanish rule-based text are labelled accordingly.
5. Inspect evidence, confirm the review checkbox, and download a producer package. Open its `card.html`; source events, context, provenance and review metadata accompany the card. Changing the selected story or audience resets review.
6. **Match overview** holds the recap and statistics. **Wording studio** holds preparation. **Methods & checks** explains scope and evaluation.

For richer context, choose **Context storyline**, reveal all events, and inspect the first Riverside shot-producing recovery: it follows three earlier recoveries closed without a shot. Baselines use only earlier revealed evidence. The 24-case **Scenario laboratory** exposes additional authored edge cases.

## What AI does—and what it does not

The model drafts wording in advance. Python calculates the outcome, interval, context and evidence. Humans review wording before reuse. During replay, approved templates fill current team names and shot intervals; event IDs always come from current analysis. This separates slow preparation from responsive replay.

Included wording:
- One original user-imported pending template, preserved with its unverified model attribution.
- One human-corrected shot template reconstructed from the exact wording the user displayed in their working app. Its original exported approval timestamp was not supplied, so it is null and its provenance explicitly identifies the reconstruction.

A user-reported Phi-4-mini Quick draft run took **74.8 seconds generation + 21.2 seconds setup**. It produced fenced JSON and misstated the pressure interval. The user corrected and reviewed the wording. This is evidence of a local drafting attempt, not autonomous factual accuracy or a controlled speed benchmark.

Current checks accept a single JSON code fence without editing its contents; reject some unsupported values and pressure timings; and preserve uncertainty. They are incomplete. They do not certify football meaning or translation quality. See [AI reliability](docs/AI_RELIABILITY.md).

Optional generation uses `foundry-local-sdk==2.2.1` in `requirements-local.txt`. Install it only if testing generation; see [local AI setup](docs/LOCAL_AI_SETUP.md). Models may require substantial RAM, downloads and setup time. The observed selected variant was CPU-based. No GPU/NPU acceleration or performance guarantee is claimed. The six-asset preparation workflow is implemented and control-flow tested with mocks; six successful real reviewed outputs are not bundled. A proposed AI story-selection-only redesign has not been implemented.

## Pipeline and implementation

| Stage | Implementation |
| --- | --- |
| Ingest | Replay revealed prefixes of validated synthetic event sequences |
| Interpret | Track recoveries within contiguous possessions, first shots, boundaries and pressure associations |
| Explain | Add prior-outcome context; select reviewed wording or authored fallback |
| Render | Story cards, comparison panels, static HTML and event-timed JSON |
| Personalize | Team selection, fan/analyst detail, English/Spanish |

Main modules: `analytics.py` (facts/context), `narration.py` and `draft_checks.py` (wording/checks), `preparation.py` (snapshot assets/review), `local_ai.py` (isolated local process), `presentation.py` and `design.py` (UI), `producer.py` (reviewed export), `scenarios.py` (authored data).

## Tests

```text
.venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe evaluate.py
```

Use `.venv/bin/python` on macOS/Linux. Tests cover event boundaries, future-event isolation, first-shot timing, context, wording provenance, review invalidation, exports and UI checkpoints. Cancellation tests use a fake subprocess worker. They do not benchmark a native model. See [validation](docs/VALIDATION.md) and `data/evaluation_report.json`. GitHub Actions is configured for Windows and Linux; a remote passing run is not claimed until the repository is published and CI finishes.

## Scope, data and rights

All football events and players are synthetic. No real Premier League match data, match footage, photographs, logos or music are bundled. Northbridge and Riverside are fictional teams used throughout the project. The sample has 21 events, not a complete match. Generated sequences are authored demonstrations, not calibrated research data.

Pressure within five seconds is an association, not a cause. A shot is not chance quality. Pending recoveries are not failures. Replay is not a live feed. HTML exports are static; no broadcast-renderer transport or video synchronization is implemented. No xG, computer vision, speed tracking, multi-agent orchestration or cloud deployment is claimed. Producer time savings and professional user validation remain unmeasured.

See [architecture](docs/ARCHITECTURE.md) and [third-party notices](docs/THIRD_PARTY_NOTICES.md). No open-source license for the author's code is automatically granted by this README; the owner should choose a license deliberately if desired.

## Submission and upgrade

Start at **[START_HERE_SUBMISSION.md](START_HERE_SUBMISSION.md)** for final Windows checks, repository publication, recording and upload. This repository/package is a runnable test build, not a hosted service; localhost is not accessible to judges. Public code/video URLs and final submission remain the entrant's tasks.

When upgrading, keep the old folder as backup. Preserve your own `data/wording_library.json` and `data/preparations/` if they contain later approvals. Never overwrite your only copy. The included shot wording is already reconstructed from the reviewed conversation example.
