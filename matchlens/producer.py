"""Review identity and self-contained producer handoff; no network access."""
import hashlib
import io
import json
import zipfile
from datetime import datetime, timezone
from presentation import broadcast_card_html


def audience_story(story):
    """Short authored fan fallback; approved AI wording is never edited silently."""
    result = dict(story)
    if story['viewing_mode'] != 'Casual Fan' or story['generation_method'] != 'rule_based':
        return result
    es = story['language'] == 'Español'
    team = story.get('recovery_team', story['favorite_team'])
    state = story.get('lifecycle_state')
    if state == 'shot':
        n = story['seconds_to_shot']
        result['explanation'] = (f'{team} convirtió una recuperación en un remate en {n} segundos, dentro de la misma posesión.' if es else
                                 f'{team} turned a recovery into a shot in {n} seconds, within the same possession.')
    elif state == 'closed':
        result['explanation'] = (f'{team} recuperó el balón, pero la posesión terminó sin un remate registrado.' if es else
                                 f'{team} won the ball back, but the possession ended without a recorded shot.')
    elif state == 'developing':
        result['explanation'] = (f'{team} recuperó el balón; aún no se ha observado un remate ni un cambio de posesión.' if es else
                                 f'{team} won the ball back; no shot or possession change has been observed yet.')
    return result


def review_key(story, events):
    """Bind review to wording, audience, context and all revealed source data."""
    content = json.dumps(story, sort_keys=True, ensure_ascii=False) + events.to_json(orient='records')
    return hashlib.sha256(content.encode()).hexdigest()


def producer_bundle(story, events, approved_key):
    identity = review_key(story, events)
    if approved_key != identity:
        raise ValueError('Review the current story before exporting its producer package.')
    if not story.get('recovery_event_id'):
        raise ValueError('Select an observed recovery first.')
    ids = set(story['evidence_event_ids']) | set(story.get('context', {}).get('baseline_evidence_event_ids', []))
    if not ids.issubset(set(events.event_id)):
        raise ValueError('Story evidence is not present in the revealed source.')
    manifest = {'schema_version': 1, 'reviewed_snapshot_sha256': identity,
                'reviewed_utc': datetime.now(timezone.utc).isoformat(),
                'review_type': 'User affirmed facts, audience and language in the local UI',
                'synthetic': True, 'generation_method': story['generation_method'],
                'scope': 'Static preview and event-timed JSON; no production feed synchronization.'}
    packet = {**story, 'schema_version': 3, 'display_duration_seconds': 8,
              'replace_on_evidence_change': True, 'review': manifest}
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('card.html', broadcast_card_html(story))
        archive.writestr('story.json', json.dumps(packet, indent=2, ensure_ascii=False))
        archive.writestr('evidence.csv', events[events.event_id.isin(ids)].to_csv(index=False))
        archive.writestr('revealed_events.csv', events.to_csv(index=False))
        archive.writestr('review.json', json.dumps(manifest, indent=2))
        archive.writestr('README.txt', 'MatchLens — reviewed synthetic story\nOpen card.html for the preview. story.json includes context and wording provenance.\nEvidence and the revealed source are included for inspection. Human review is an affirmation, not a correctness guarantee.\nA shot does not measure chance quality. Pressure association does not establish causation.\nThis is a synthetic partial sequence, not a real match report.\n')
    return buffer.getvalue()
