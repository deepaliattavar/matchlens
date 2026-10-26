# Local AI speed: what changed and how to verify it

## Findings

A UI completion bug was found: collect_ai_result saved a completed result but never returned True. The polling fragment depended on True to rerun the page. A finished request could therefore leave a stale working message until another interaction refreshed the page. This is fixed and regression-tested; it does not reduce native inference time.

The application already retained model weights between requests. That remains in place. Releasing the model or restarting Streamlit makes the next request cold again. No new acceleration is claimed from this pre-existing behavior.

Microsoft's current Python SDK documents output token limits and model lifecycle reuse. Its Windows integration documentation describes WinML execution providers, but hardware support and the selected model variant matter. This update does NOT install WinML, download a different model, force an NPU/GPU, or modify a cached model configuration. Do not assume an Intel AI Boost device means this particular model is using it.

Sources inspected October 24, 2026:
- https://github.com/microsoft/Foundry-Local/blob/main/sdk_v2/python/README.md
- https://github.com/microsoft/Foundry-Local/blob/main/sdk_v2/INFERENCING.md
- https://learn.microsoft.com/en-us/azure/foundry-local/how-to/how-to-integrate-with-inference-sdks

## Implemented changes

- Quick draft: shorter instruction prompt, maximum 160 output tokens; Full draft retains the old prompt and 256-token ceiling. A lower ceiling can help a verbose response, but will not necessarily speed up a response that already stops early. It can truncate JSON; rejected drafts never bypass checks. Both modes require human review.
- Six-asset preparation retains 256 tokens because recap outputs are longer.
- Visible stages distinguish starting the runtime, checking/downloading, loading weights and generating. Elapsed time includes setup; actual setup and generation timings remain in completed results.
- Cancel local generation asks the worker-owning thread to terminate the subprocess, releasing this app's model. It does not kill other applications. Cancellation may take a few seconds.
- Generation has a 120-second limit after the worker reports generation started. Overall request limit remains 600 seconds to allow initial loading/download. Timeout stops work and keeps the deterministic story; it is not a successful output or a speed improvement.
- Profile-specific result keys prevent accidentally reusing a Full result as a Quick result. Existing same-fact session caching remains.
- Completed drafts now automatically refresh the UI.

## First test on your laptop

1. Stop the current app before updating its files. Preserve your data folder.
2. Open the updated app; choose Riverside, Casual Fan, English, checkpoint 2.
3. Enable local generation. In Wording studio / Prepare or edit reusable wording, select Quick draft.
4. Generate once. Watch the stage; do not click repeatedly. Cancel if you want to stop.
5. Copy the actual result, setup time, generation time and any validation errors. Review the draft against the evidence. No model calls are needed for the default replay.
6. If the 131072-token cache-allocation failure recurs, shorter output alone will not necessarily fix it. The existing backed-up context workaround remains separate and unverified on your hardware.

## Optional measured comparison

Stop Streamlit first to avoid two model processes competing for RAM. From the project folder:

```powershell
.venv\Scripts\python.exe benchmark_local_ai.py
```

This performs one warm-up, then a Quick and a Full request on the same seven-event snapshot with the same model retained in memory. Three actual requests can take minutes. It stops on inference failure and preserves partial results. Press Ctrl+C to stop. No cloud API or payment is involved.

For two rounds with reversed second-round order:

```powershell
.venv\Scripts\python.exe benchmark_local_ai.py --runs 2
```

That is five calls including warm-up. Read data/local_speed_report.json. Compare warm generation times, basic check results and human-reviewed usefulness together. A faster but inaccurate or truncated answer is not a win. A single pair is noisy and order-dependent; it is not a stable performance claim. No local benchmark results are bundled because this environment did not run your native model.

## Test boundary

25 automated tests passed, including a real subprocess transport with an explicitly fake sleeping worker for cancel/timeout checks. Those tests prove control flow, not Phi speed, memory usage, provider selection or factuality. No success or timing has been fabricated. No paid service or Ollama was added.
