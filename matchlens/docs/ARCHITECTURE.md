# How MatchLens works

## Event contract

Each row has event_id, time (minutes:seconds), team, player, event_type, outcome, and possession_id. Validation rejects missing values, duplicate IDs, malformed or decreasing timestamps, and possession IDs that reappear after their contiguous segment ends. elapsed_seconds is derived from time. Row order resolves equal timestamps. The supported demo contract uses numeric event and possession IDs.

## Recovery state

For each recovery with outcome controlled, scan later revealed events in the same possession. The first same-team shot produces the shot state and a time difference. If possession changes before a shot, the recovery is closed without a shot. Otherwise it remains developing. A shot state persists even if a later possession boundary is observed. This represents the first shooting outcome, not every possible outcome of the attack.

## Evidence and wording

A story cites the recovery, an eligible preceding pressure event, and either a shot or the first possession-boundary event as appropriate. Templates never provide event IDs. A template key consists of outcome, pressure association, viewing mode and language. Reuse substitutes verified values and applies basic checks again. Unsupported or corrupted wording falls back to authored text.

The working dataset is sliced before analytics, wording selection and recap calls. The original full dataset exists only to support replay navigation; insight functions receive the revealed prefix. Scrubbing backward recomputes the state, rather than treating a future outcome as already known.

## Preparation versus replay

The optional Foundry Local worker creates drafts for a frozen evidence packet. Review and save happen in the preparation UI. The resulting JSON library persists beside the sample dataset. During replay, loading and formatting reviewed wording does not invoke the worker. Imported draft provenance is retained as imported; it is not represented as verified model execution.

## Rendering

The HTML card escapes dynamic text, uses inline CSS, and loads no external assets. The visible method label distinguishes AI-prepared and rule-based wording. HTML export contains one snapshot. JSON export includes the observation time, source event, evidence and suggested duration. A production renderer would need a transport, synchronization, expiry, error handling and integration testing.

## Deliberate tradeoffs

The transparent rules and tiny dataset make the prototype explainable and testable. They do not establish match-level tactical conclusions. A production feed would require event corrections, deduplication, late-arrival handling, persistent state and broader validation. Those are future work, not completed features. There is no autonomous agent claim.

## New context and preparation boundaries

`recovery_context` freezes each baseline at the target recovery's start, including that boundary event to resolve the preceding possession. Earlier unresolved recoveries remain a separate count. The median is displayed only when at least three earlier recoveries reached a shot. A first-shot milestone requires prior no-shot outcomes, no earlier shot outcome, and no unresolved earlier recovery.

`preparation.py` derives six jobs from a revealed snapshot. The worker processes them sequentially and stops on the first inference error. Reports persist after each result. Fan, analyst and recap assets in English and Spanish are individually reviewed; an exact snapshot hash prevents an approved text from following a changed event prefix. This is a controlled workflow, not an autonomous agent.

An editorial recommendation table ranks first-shot milestones, other shot outcomes, closed outcomes, then pending cases. It is explicitly rule-based and separate from model drafting.

The cached-model workaround is deliberately outside automatic application startup. It backs up configuration and can be restored. No model weights are modified or distributed.

## Producer review and handoff

producer.py supplies the short authored fan fallback and a review identity computed from the complete story JSON plus revealed source records. AI-approved wording is never shortened silently. Approval is a Streamlit checkbox keyed by this identity, not a claim of automatic factual verification. The package builder rejects a mismatched review identity or evidence outside the revealed source. The downloaded ZIP includes card.html, story.json with context/provenance, evidence.csv, revealed_events.csv, review.json and README.txt. It makes no publication or external network call. Preview downloads are explicitly unreviewed.
