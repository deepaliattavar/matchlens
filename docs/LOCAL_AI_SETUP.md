> Submission update: a real user-reported Phi-4-mini run completed (74.8s generation, 21.2s setup), but required factual correction. This does not verify that the context workaround was applied or solved the memory issue. The current SDK is 2.2.1; its Windows wheel includes WinML. Do not install the older separate -winml package into this environment. Use the default no-model replay for judge testing.

# Local AI preparation: controlled next step

The default demo and saved wording work without inference. This document describes an optional local-only attempt to restore generation and produce a six-asset audit. No hosted API or payment account is used. Downloading SDK/runtime components may require internet access. Do not download another model for this workflow.

## Why the previous request failed

The reported failure attempted a KV cache for 131,072 tokens across 32 layers. The existing output limit capped response length, not necessarily the session's cache. The inspected Microsoft runtime source sets a classic generator's maximum length to the full model context when continuous decoding is enabled.

Source inspected October 23, 2026:
- https://github.com/microsoft/Foundry-Local/blob/main/sdk_v2/cpp/src/inferencing/generative/chat/search_options.cc
- https://github.com/microsoft/Foundry-Local/blob/main/sdk_v2/python/src/foundry_local_sdk/session_types.py
- https://github.com/microsoft/Foundry-Local/blob/main/sdk_v2/python/src/foundry_local_sdk/imodel.py

## Reversible workaround — not a confirmed hardware fix

The helper lowers `model.context_length` and `search.max_length` in the single cached Phi-4-mini variant's `genai_config.json` to 4096. It does not change weights or increase any limit. It makes a backup before writing. This is a local configuration workaround, not a promise of upstream support. The model package may be refreshed by a later download/update. It cannot guarantee sufficient free RAM or native runtime compatibility.

Stop Streamlit and close any other local-model applications first. In the extracted project folder, use the virtual environment containing the SDK. If this is a new environment, install the optional dependency:

```powershell
.venv\Scripts\python.exe -m pip install -r requirements-local.txt
```

Inspect without changing anything:

```powershell
.venv\Scripts\python.exe configure_local_model.py
```

The script stops if it cannot identify exactly one cached Phi-4-mini variant. It never downloads weights. If inspection succeeds, apply the backed-up workaround:

```powershell
.venv\Scripts\python.exe configure_local_model.py --apply
```

Restart the app, reveal a recovery, enable optional local generation, and test one draft in Wording studio. If it succeeds, the six-asset preparation workflow is available separately. If it fails, save the error and stop further attempts; the normal replay remains usable.

To undo, stop model applications and run:

```powershell
.venv\Scripts\python.exe configure_local_model.py --restore
```

## Prepare and review six assets

1. Pause at a recovery snapshot.
2. Open **Wording studio → AI preparation — six assets with an audit trail**.
3. Click **Prepare six local AI drafts**. Generation is sequential, in the background, and may take several minutes. One inference failure stops the batch.
4. Review each result against the source facts, including its language quality. Basic checks do not establish semantic truth.
5. Approve individual passing assets. The corresponding fan/analyst card or recap is used only at the exact original snapshot. A changed event prefix invalidates reuse.
6. Download the full audit. Reports also persist under `data/preparations/`.

Every report stores the snapshot hash, model alias, actual model identifier when generation succeeds, SDK version, prompts, raw outputs, timing, source evidence, checks, and approval. There are no fabricated successful reports in the package. Tests use mocks solely to verify orchestration, failure behavior and approval boundaries.

This is an AI-assisted preparation workflow, not autonomous or multi-agent reasoning.
