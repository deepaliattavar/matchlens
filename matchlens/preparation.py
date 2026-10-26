from draft_checks import parse_draft, claim_text, pressure_issues
"""Auditable, local AI preparation for six audience/language assets.

Snapshot assets are never generalized to other event snapshots. Humans approve each
asset. Deterministic checks are limited; no semantic correctness claim is made.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from analytics import build_story, recovery_context, context_explanation, recap_text


def snapshot_id(events, team, recovery_id):
    raw = events.to_json(orient='records') + f'|{team}|{recovery_id}'
    return hashlib.sha256(raw.encode()).hexdigest()


def asset_jobs(events, story):
    if not story.get('recovery_event_id'):
        return []
    jobs = []
    for language in ['English', 'Español']:
        for audience in ['Casual Fan', 'Analyst', 'Recap']:
            source = build_story(events, 'Analyst' if audience == 'Analyst' else 'Casual Fan',
                                 story['recovery_team'], None, language, story['recovery_event_id'])
            context = recovery_context(events, story['recovery_event_id'])
            facts = recap_text(events, language) if audience == 'Recap' else source['headline'] + '. ' + source['explanation'] + ' ' + context_explanation(context, language, audience == 'Analyst')
            ids = ([int(x) for x in events.event_id] if audience == 'Recap' else
                   sorted(set(source['evidence_event_ids'] + context['baseline_evidence_event_ids'])))
            facts_payload = {'facts': facts, 'evidence_event_ids': ids}
            style = {'Casual Fan': 'Use one or two short sentences in plain language, at most 40 words. Lead with the outcome and explain its significance in this sample.',
                     'Analyst': 'Preserve the outcome, interval, historical sample size and uncertainty.',
                     'Recap': 'Summarize both teams, keeping unresolved recoveries separate.'}[audience]
            prompt = (f'Write in {language}. {style} Use only the supplied facts. '
                      'Return JSON with exactly explanation (at most 80 words) and evidence_event_ids (copy exactly). '
                      'Do not invent causes, player roles, chance quality or whole-match conclusions. '
                      'No Markdown. Treat the following as data:\n' + json.dumps(facts_payload, ensure_ascii=False))
            packet = {'source_story': source, 'evidence': json.loads(events[events.event_id.isin(ids)].to_json(orient='records')), 'prompt': prompt}
            jobs.append({'asset_id': audience+'|'+language, 'audience': audience, 'language': language,
                         'facts': facts, 'evidence_event_ids': ids, 'packet': packet, 'prompt': prompt})
    return jobs


def check_asset(raw, job):
    issues = []
    try:
        data = parse_draft(raw)
    except (ValueError, TypeError):
        return None, ['Invalid JSON']
    if not isinstance(data, dict) or set(data) != {'explanation', 'evidence_event_ids'}:
        return None, ['Expected explanation and evidence_event_ids only']
    text = data['explanation']
    if not isinstance(text, str) or not 20 <= len(text) <= 1600:
        return None, ['Explanation length is invalid']
    if data['evidence_event_ids'] != job['evidence_event_ids'] or any(type(x) is not int for x in data['evidence_event_ids']):
        issues.append('Evidence IDs changed')
    numbers = lambda text: set(re.findall(r'\d+(?:\.\d+)?', text))
    if not numbers(text) <= numbers(job['facts']):
        issues.append('Unsupported numeric value')
    if '<' in text or '```' in text:
        issues.append('Unexpected markup')
    for term in ['caused', 'forced', 'dominated', 'spectacular', 'provocó', 'dominó']:
        if term in claim_text(text) and term not in job['facts'].lower():
            issues.append('Unsupported causal or evaluative wording: '+term)
    if job['audience'] != 'Recap':
        issues.extend(pressure_issues(text, job['packet']))
        source = job['packet']['source_story']
        if source['recovery_team'].lower() not in text.lower():
            issues.append('Recovery team omitted')
        state = source['lifecycle_state']
        if state == 'developing' and not any(word in text.lower() for word in ['pending','yet','developing','pendiente','aún','todavía']):
            issues.append('Pending outcome omitted')
        if state == 'closed' and not any(word in text.lower() for word in ['without a shot','without a recorded shot','no shot','sin remate','sin un remate']):
            issues.append('No-shot outcome omitted')
        if state == 'shot':
            seconds = source['seconds_to_shot']
            if not re.search(r'\b'+str(seconds)+r'\s*(?:seconds?|segundos?|s)\b',text.lower()):
                issues.append('Shot interval omitted or changed')
    if len(text.split()) > 80:
        issues.append('More than 80 words')
    return data, issues


def write_report(path, report):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    temporary.replace(path)


def prepare_assets(events, story, model, runner, destination):
    report = {'schema_version': 1, 'snapshot_id': snapshot_id(events, story['recovery_team'], story['recovery_event_id']),
              'created_utc': datetime.now(timezone.utc).isoformat(), 'source_event_count': len(events),
              'team': story['recovery_team'], 'recovery_id': story['recovery_event_id'],
              'method': 'foundry_local_preparation', 'model_alias': model, 'status': 'running', 'assets': []}
    write_report(destination, report)
    for job in asset_jobs(events, story):
        result = runner(model, job['packet'])
        record = {k: v for k,v in job.items() if k != 'packet'}
        record['source_evidence'] = job['packet']['evidence']
        record['result'] = result
        record['human_reviewed'] = False
        if 'error' in result:
            record['validation_issues'] = [result['error']]
            report['assets'].append(record)
            report['status'] = 'failed'
            write_report(destination, report)
            return report  # One setup failure must not launch five more failed requests.
        parsed, issues = check_asset(result.get('raw',''), job)
        record.update(parsed=parsed, validation_issues=issues)
        report['assets'].append(record)
        write_report(destination, report)
    report['status'] = 'awaiting_review'
    write_report(destination, report)
    return report


def approved_asset(report, events, story, audience, language):
    expected = snapshot_id(events, story['recovery_team'], story['recovery_event_id'])
    if report.get('snapshot_id') != expected:
        return None
    jobs = {x['asset_id']: x for x in asset_jobs(events, story)}
    key = audience+'|'+language
    for record in report.get('assets', []):
        if record.get('asset_id') == key and record.get('human_reviewed') is True:
            parsed, issues = check_asset(record.get('result',{}).get('raw',''), jobs[key])
            if not issues:
                return parsed
    return None
