# MatchLens — finish your submission

Prepared for Deepali Attavar. This package is prepared, not submitted or published.

## 1. Test this final folder on Windows (about 10–15 minutes)

Keep the working older project as a backup. Extract the final ZIP into a NEW folder. Open Command Prompt in the inner `matchlens` folder containing `app.py`.

```text
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe -m streamlit run app.py
```

Expected automated result: **30 tests pass**. This test does not require Foundry, model downloads or paid services. If a command fails, retain the exact error; do not mark the test complete.

In the app:
- [ ] Select **Riverside**, Casual Fan, English. Leave local AI OFF.
- [ ] Click Explore the two-recovery example: comparison shows eight seconds to a shot and nine seconds to a possession change, with different endpoints explained.
- [ ] Checkpoint 1: developing, evidence 3,5. Checkpoint 2: shot in eight seconds, evidence 3,5,7. Checkpoint 3: developing, evidence 10,12. Checkpoint 4: closed without a shot, evidence 10,12,15.
- [ ] At checkpoint 2, the prepared wording appears. In Wording studio verify the saved shot template exists. It is reconstructed from your corrected chat example; if you have your original exported wording file, preserve it as stronger provenance.
- [ ] Analyst and Español change the experience without changing the outcome. Spanish wording is authored fallback unless you have separately generated and reviewed a Spanish asset.
- [ ] Review and export at checkpoint 2. Extract the producer ZIP and open card.html. It should say Riverside and eight seconds. Confirm evidence CSV and story JSON are present.
- [ ] Change audience: the review checkbox resets.
- [ ] Open Match overview at checkpoint 4: Riverside has one shot-producing recovery, one closed without a shot, none pending.

No additional model run is required for these checks. Do not install optional AI dependencies merely to record the replay. Local AI previously produced a draft that required correction; this is honestly documented.

## 2. Publish the source on GitHub

Use the clean extracted source files, not a folder containing your environment or downloaded model weights.

1. Sign in to GitHub, create a repository named `matchlens`, and make it Public. A public repository is a submission requirement.
2. Upload the project CONTENTS so `app.py` and `README.md` appear at the repository root, not inside another `matchlens` folder.
3. Include all `.py` files, requirements files, README, this guide, `.gitignore`, `.streamlit`, `.github`, `data`, `docs`, and `tests`.
4. Do NOT upload `.venv`, `__pycache__`, model weights, `.env`, secrets, downloads, private feedback, or unrelated personal files. The supplied clean ZIP excludes these. Do not just upload the ZIP as the entire repository.
5. Save/commit the upload. Verify README renders and data/sample_events.csv is accessible.
6. Check the Actions tab. If CI runs, wait for both Windows and Linux results; do not claim remote CI passed until it actually does. If it fails, inspect the log before proceeding.
7. Open the repository in a signed-out/private browser window. Confirm source is public. Save its URL.

Use docs/PROJECT_PITCH.md for the project description. Do not add an open-source license without deciding its terms deliberately.

## 3. Record your actual app (target 105–110 seconds)

Use docs/DEMO_GUIDE.txt. Capture the running app, not a slide-only pitch. No match footage, logos, music or third-party images are needed. Close unrelated personal browser tabs and notifications before recording.

Keep generation OFF while recording replay. Demonstrate prepared wording and disclose that local AI drafting is reviewed before reuse. Do not imply the instant replay card is a new live model response. Show the actual UI for evidence inspection and export. You can describe the observed drafting error and correction without replaying a 96-second generation.

Upload to an allowed public video service (for example YouTube), obtain its public watch URL, and test access signed out. Confirm runtime is strictly less than two minutes. Do not rely on a private video link that judges cannot view.

## 4. Complete the Innovation Studio project entry

- Title: MatchLens.
- Tagline and description: docs/PROJECT_PITCH.md.
- Technology: Microsoft Foundry Local / Phi-4-mini, Python, pandas, Streamlit. Do not claim Azure-hosted inference or multi-agent orchestration.
- Code: public GitHub repository URL.
- Demo: public video URL.
- Testing access: repository README with the no-model local setup; the repository is the runnable test build. Do not enter localhost as a hosted website.
- Complete every mandatory portal field; check any category-specific requirement against the actual implementation.
- Submit using the portal's final submission action and retain its confirmation. Merely saving a draft may not finish the entry.

## 5. Deadline and final checks

Official rules checked October 26, 2026: submission closes **October 27, 2026 at 11:59 pm Pacific**, equivalent to **October 28 at 1:59 am America/Chicago**. Aim to finish on October 26 or well before the deadline on October 27. Confirm the portal has no official updated notice before submitting.

The rules require a public repository, functioning video under two minutes, English submission materials, synthetic football data and free judge access to a working site/demo/test build. Keep the public repository and accessible video available through the judging period ending November 10, 2026 Pacific. Eligibility, ownership and necessary permissions remain your confirmations; this checklist is not a legal certification.

Official source: https://github.com/microsoft/insidethegamehackathon/blob/main/OFFICIAL%20RULES.md (Sections 1, 4.3–4.11).

## Completion record — fill this yourself

- Windows test date/result:
- Manual checks complete:
- Public repository URL:
- Remote CI result:
- Public demo URL and exact duration:
- Signed-out access checked:
- Final submission confirmation:

Do not replace these fields with invented evidence. No producer user study or measured commercial savings is claimed.
