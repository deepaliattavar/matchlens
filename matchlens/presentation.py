"""Self-contained, escaped HTML presentations."""

def contrast_html(cases, spanish=False):
    from html import escape
    cards = []
    for case in cases:
        shot = case['state'] == 'shot'
        color = '#17624b' if shot else '#8c601a'
        title = (('LLEGÓ AL REMATE' if shot else 'TERMINÓ SIN REMATE') if spanish else
                 ('REACHED A SHOT' if shot else 'ENDED WITHOUT A SHOT'))
        duration = f"{case['seconds']}s"
        finish = ('Remate' if shot else 'Cambio de posesión') if spanish else ('Shot' if shot else 'Possession changes')
        count = case['completed_passes']
        passes = f'{count} ' + (('pase completado' if count == 1 else 'pases completados') if spanish else ('completed pass' if count == 1 else 'completed passes'))
        outcome_names = {'saved': ('parado', 'saved'), 'off_target': ('fuera', 'off target'), 'goal': ('gol', 'goal')}
        if shot:
            outcome = outcome_names.get(case['end_outcome'], (case['end_outcome'],case['end_outcome']))[0 if spanish else 1]
            note = ('Resultado del remate: ' if spanish else 'Recorded shot outcome: ') + outcome
        else:
            note = (f"Pases fallidos registrados: {case['failed_passes']}." if spanish else
                    f"Failed passes recorded: {case['failed_passes']}.")
        e = lambda value: escape(str(value), quote=True)
        cards.append(f'''<article style="--accent:{color}"><div class="label">{e(title)}</div>
<h2>{e(duration)}</h2><div class="time">{e(case['recovery_time'])} → {e(case['end_time'])}</div>
<div class="sequence"><span>{'Recuperación' if spanish else 'Ball recovered'}</span><b>→</b><span>{e(passes)}</span><b>→</b><span>{e(finish)}</span></div>
<p>{e(note)}</p><footer>{e(case['team'])} · Recovery #{case['recovery_id']}<br>Sequence IDs: {e(', '.join(map(str,case['sequence_ids'])))}</footer></article>''')
    return '''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>
*{box-sizing:border-box}body{margin:0;font-family:"Segoe UI",Arial,sans-serif;background:transparent;color:#182f2b}.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}article{border:1px solid #d8dfd8;border-top:4px solid var(--accent);border-radius:12px;padding:22px;background:#ffffff}.label{color:var(--accent);font-size:13px;font-weight:750;letter-spacing:1.3px}h2{font-size:52px;margin:12px 0 0;letter-spacing:-2px}.time{color:#53665f;font-size:15px}.sequence{display:flex;align-items:center;flex-wrap:wrap;gap:6px;margin:16px 0}.sequence span{background:#edf1eb;padding:7px 12px;border-radius:6px;font-size:15px}.sequence b{color:var(--accent)}p,footer{font-size:15px;line-height:1.5;color:#53665f}footer{border-top:1px solid #d8dfd8;padding-top:12px}@media(max-width:440px){.grid{grid-template-columns:1fr}article{padding:16px}}
</style></head><body><div class="grid">''' + ''.join(cards) + '</div></body></html>'


def broadcast_card_html(story):
    """Escaped, self-contained HTML: no external assets, scripts, or network calls."""
    from html import escape
    spanish = story['language'] == 'Español'
    state = story.get('lifecycle_state', 'waiting')
    labels = ({'developing': 'EN DESARROLLO', 'shot': 'REMATE OBSERVADO', 'closed': 'CERRADA SIN REMATE', 'waiting': 'ESPERANDO'} if spanish else
              {'developing': 'DEVELOPING', 'shot': 'SHOT OBSERVED', 'closed': 'CLOSED WITHOUT A SHOT', 'waiting': 'WAITING'})
    colors = {'developing': '#f2ca70', 'shot': '#74e6bd', 'closed': '#b8c3db', 'waiting': '#b8c3db'}
    if state == 'shot':
        title = (f"Recuperación → remate en {story['seconds_to_shot']} s" if spanish else
                 f"Recovery → shot in {story['seconds_to_shot']}s")
    elif state == 'closed':
        title = 'Balón recuperado. Sin remate.' if spanish else 'Ball won. No shot followed.'
    elif state == 'developing':
        title = 'Balón recuperado. ¿Qué sigue?' if spanish else 'Ball won. What happens next?'
    else:
        title = story['headline']
    method = ('AI-prepared wording · selected live' if story['generation_method'] == 'ai_prepared_selected_live'
              else 'Rule-based wording · selected live')
    ids = ', '.join(map(str, story['evidence_event_ids']))
    esc = lambda value: escape(str(value), quote=True)
    return f'''<!doctype html><html lang="{'es' if spanish else 'en'}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>MatchLens story card</title>
<style>
*{{box-sizing:border-box}}body{{margin:0;background:transparent;font-family:"Segoe UI",Arial,sans-serif}}
article{{background:#153b32;color:#f5f7fc;border:1px solid #285447;border-left:6px solid {colors[state]};border-radius:10px;padding:26px 30px;max-width:1100px;margin:0 auto}}
.top{{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;font-size:13px;letter-spacing:1.5px;font-weight:700}}
.state{{color:{colors[state]}}}.brand{{color:#b7c4da}}.team{{margin-top:22px;color:#b7c4da;font-size:15px}}
h2{{font-size:clamp(28px,3.5vw,40px);line-height:1.16;letter-spacing:-1px;margin:8px 0 16px}}
p{{font-size:18px;line-height:1.6;max-width:900px;margin:0 0 22px}}
footer{{display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap;border-top:1px solid #304159;padding-top:14px;color:#bac8dc;font-size:13px;line-height:1.5}}
@media(max-width:550px){{article{{padding:18px}}p{{font-size:15px}}}}
</style></head><body><article aria-label="Recovery outcome story">
<div class="top"><span class="brand">MATCHLENS · SYNTHETIC REPLAY</span><span class="state">{esc(labels[state])} · {'Hasta' if spanish else 'As of'} {esc(story['match_time'])}</span></div>
<div class="team">{esc(story.get('recovery_team', story['favorite_team']))} · {esc(story['viewing_mode'])} · {'Recuperación' if spanish else 'Recovered'} {esc(story.get('recovery_time', '—'))}</div>
<h2>{esc(title)}</h2><p>{esc(story['explanation'])}</p>
<footer><span>Evidence: {esc(ids)} · Recovery #{esc(story.get('recovery_event_id', '—'))}</span><span>{esc(method)}</span></footer>
</article></body></html>'''

