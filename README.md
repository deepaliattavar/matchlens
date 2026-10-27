# MatchLens

**They won the ball. What happened next?**

MatchLens helps sports producers turn possession recoveries into clear stories backed by event evidence. Compare a recovery that reaches a saved shot in eight seconds with one that ends without a shot, then tailor and export the story for your audience.

Built by **Deepali Attavar**, with AI-assisted development. Uses **Python, pandas, Streamlit, and optional Microsoft Foundry Local / Phi-4-mini**.

All teams, players and match events are synthetic. The app runs locally; no Azure subscription, API key or paid inference is required.

## Try it

Use Python **3.12**. Download this repository and open a terminal in the folder containing `app.py`.

**Windows**

```text
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m streamlit run app.py
```

**macOS / Linux**

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run app.py
```

Open the local address printed by Streamlit. Installing dependencies needs internet access; replay needs no model download. Optional native AI setup is documented separately.

## Explore a story

1. Choose **Riverside**, **Casual Fan**, and **English**. Leave local generation off.
2. Select **Explore the two-recovery example** to compare two observed outcomes.
3. Use **Jump to a key moment** to watch a pending recovery become a shot or close without a shot.
4. Switch to **Analyst** to inspect the sequence and evidence, or **Español** for Spanish explanations.
5. Review the selected story, then select **Download story package**. It contains an HTML card, structured story data, evidence, revealed events and a review record.

The 8-second and 9-second examples end at different outcomes; they are not a speed ranking. For a richer baseline, choose **Context storyline** and reveal all events: Riverside's first shot-producing recovery follows three earlier recoveries without shots.

| Workspace | Purpose |
| --- | --- |
| Story desk | Compare recoveries, select a story, inspect evidence and export |
| Match overview | Review statistics and recovery recaps |
| Wording studio | Prepare, approve and save audience-specific wording |
| Methods & checks | Understand the calculations and evaluation results |

## How the pipeline works

**Ingest → Interpret → Explain → Render → Personalize**

Validated synthetic events are revealed in sequence. Python tracks contiguous possessions, recovery outcomes, timing and pressure associations. The story uses earlier observed outcomes for context. Cards and exports adapt to the selected team, audience and language.

AI drafts wording; it does not calculate match facts. A human reviews drafts before they appear on the card. Reviewed templates can be reused with current facts during replay, avoiding a model request for every event. When a reviewed template is unavailable, authored wording supplies the explanation.

To prepare a new local draft, follow [Local AI setup](docs/LOCAL_AI_SETUP.md). After approval, the draft appears on the story card. Select **Load approved draft into editor** to copy it into the reusable-wording form, review it, and save. Export review is tied to the exact story and revealed source data.

## Validation

```text
.venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe evaluate.py
```

On macOS/Linux, use `.venv/bin/python` instead. The suite contains **37 tests**, including simulated AI approval, editor loading, review invalidation and export consistency. The authored analytics evaluation covers **24 scenarios, 84 replay snapshots and 156 checks**. These are synthetic regression checks, not measurements of real-match accuracy or model factuality.

[GitHub Actions](https://github.com/deepaliattavar/matchlens/actions) runs tests on Windows and Linux. Check the latest run for the status of the current commit.

## Scope

This is a replay studio and runnable local test build. HTML cards are static exports; a production video-feed connection is not implemented. Pressure before recovery is an association, not proof of causation. A shot does not measure chance quality, and an unresolved recovery is not counted as a failure.

Local AI can be slow or fail on limited hardware. Model outputs require review; the default demo uses bundled wording. Spanish fallback stories are authored templates, not claimed as generated outputs. Professional producer time savings have not yet been measured.

## Technical documentation

- [Architecture](docs/ARCHITECTURE.md)
- [AI reliability](docs/AI_RELIABILITY.md) and [local setup](docs/LOCAL_AI_SETUP.md)
- [Validation details](docs/VALIDATION.md)
- [Development history and AI provenance](docs/DEVELOPMENT_HISTORY.md)
- [Third-party notices](docs/THIRD_PARTY_NOTICES.md)
- [Submission checklist](START_HERE_SUBMISSION.md)

No real Premier League data, club logos, footage or music is included. No open-source license is granted by this README; a license can be chosen separately by the owner.
