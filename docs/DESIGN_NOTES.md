# MatchLens interface decisions

Designed for a producer moving from sequence to explanation to export.

## Visual hierarchy

A restrained masthead identifies the product and synthetic-data status. A question-led headline sets the task. Three compact metrics separate replay time, observed coverage and playback state. A comparison establishes the story before detailed analytics. The selected recovery card uses a dark forest surface as the visual focal point. Context uses a pale inset; evidence and review follow it.

## Colour and typography

Page #F7F8F3, primary text #182F2B, action green #17624B, muted text #53665F. White panels and fine borders establish grouping. Amber distinguishes a closed-no-shot comparison from the green shot outcome; text labels always accompany colour. Segoe UI on Windows, Arial/system fallbacks elsewhere; no paid fonts or external requests. Body copy around 16px, compact uppercase labels, tabular numeric metrics, responsive display sizes. Visible keyboard focus is retained and strengthened. Reduced-motion preferences are respected.

## Progressive disclosure

Four workspaces separate storytelling, match statistics, wording preparation and technical details. All tab contents are evaluated by Streamlit, so generation actions still need explicit button presses and enabled local inference. The default state starts no model. Replay controls remain available in the sidebar. The welcome action opens the authored comparison without manual event scrubbing. Advanced model options and guided checkpoints are collapsible.

## Honest clocks and decisions

A pinned story shows both the replay's As of time and its recovery time. Pending outcomes are not treated as failures. Two comparison times terminate at different kinds of event; no speed-ranking claim. Exact-snapshot approval is unchanged. HTML exports retain evidence and method labels. Responsive iframe content heights avoid a fixed card viewport cutting off longer translations.

## Verification boundary

Automated interaction checks cover the welcome action, tab structure, audience switching, story lifecycle and review invalidation. Browser installation was unavailable in this environment, so screenshot-based visual inspection was not completed. Verify the final layout on the target Windows browser, especially at narrow widths and increased zoom. This is a deliberate design implementation, not a claim that outside users or a professional UX reviewer have evaluated it.
