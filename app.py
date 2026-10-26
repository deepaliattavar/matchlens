from design import CSS, masthead, context_note
from producer import audience_story, review_key, producer_bundle
from scenarios import context_storyline, scenario_suite
from preparation import snapshot_id, prepare_assets, approved_asset, write_report
from analytics import recovery_context, context_explanation, contextual_candidates
from analytics import summarize_recoveries, generate_scenario, validate_events, pressure_links, team_metrics, build_story, recap_text, contrast_cases
from narration import ai_packet, ai_prompt, check_ai_draft, wording_path, wording_key, load_wording_library, make_wording_entry, apply_wording
from local_ai import local_ai_worker, LocalModelRunner
from presentation import contrast_html, broadcast_card_html
import streamlit as st
import pandas as pd
from pathlib import Path
import hashlib
import random
import time
import json














# Local-only AI integration. There is deliberately no cloud endpoint or API key.
# ChatSession API reference: microsoft/Foundry-Local/sdk_v2/python/examples/chat_completion.py
from local_ai import LOCAL_MODELS












@st.cache_resource
def local_runner():
    return LocalModelRunner()


def run_local_ai(model, packet):
    return local_runner().request(model, packet)


def story_cache_key(packet, model):
    # A clock tick alone does not change a story. Outcome/evidence changes do.
    stable = dict(packet['source_story'])
    stable.pop('as_of_event_id', None)
    stable.pop('match_time', None)
    return hashlib.sha256(json.dumps({'story': stable, 'evidence': packet['evidence'],
                                     'model': model, 'profile': packet.get('generation_profile', 'Quick draft')}, sort_keys=True).encode()).hexdigest()






def collect_ai_result():
    pending = st.session_state.get('ai_pending')
    if not pending or not pending['future'].done():
        return
    try:
        result = pending['future'].result()
    except Exception as error:
        result = {'error': str(error)}
    cache = st.session_state.setdefault('ai_results', {})
    cache[pending['key']] = result
    while len(cache) > 24:
        cache.pop(next(iter(cache)))
    st.session_state.pop('ai_pending', None)
    return True


@st.cache_resource
def ai_executor():
    from concurrent.futures import ThreadPoolExecutor
    return ThreadPoolExecutor(max_workers=1)


def render_local_ai(story, events, model):
    packet = ai_packet(story, events)
    packet['generation_profile'] = st.selectbox('Draft size', ['Quick draft', 'Full draft'], help='Quick: shorter prompt and 160 output tokens. Full: 256 tokens. Truncated or invalid drafts still fail checks.')
    key = story_cache_key(packet, model)
    cache = st.session_state.setdefault('ai_results', {})
    approved = st.session_state.setdefault('ai_approved', {})
    collect_ai_result()
    pending = st.session_state.get('ai_pending')
    st.subheader('Local AI producer')
    st.caption('No paid API or cloud inference. Model files may download on first use. AI drafts require your review.')
    if st.session_state.playing:
        st.info('Pause replay to generate an explanation for a fixed moment.')
    if st.button('Explain this moment with local AI', key='generate_local_ai',
                 disabled=bool(pending) or st.session_state.get('preparation_future') is not None or st.session_state.playing):
        if key not in cache:
            st.session_state.ai_pending = {
                'key': key, 'future': ai_executor().submit(run_local_ai, model, packet),
                'clock': story['match_time'],
            }
            st.rerun()
        else:
            st.info('Reusing a prepared draft: the supporting facts and viewing mode have not changed.')
    if pending:
        if st.button('Cancel local generation', key='cancel_local_ai'):
            local_runner().cancel()
        st.caption('Replay stays available. Loading has a 10-minute overall limit; generation stops after 120 seconds. Cancelling releases this app’s model process.')
    result = cache.get(key)
    if not result:
        return story
    if 'error' in result:
        st.warning(result['error'])
        if result.get('details'):
            with st.expander('Local setup error details'):
                st.code(result['details'])
        if st.button('Clear failed attempt to retry', key='retry_ai'):
            cache.pop(key, None)
            st.rerun()
        return story
    draft, issues = check_ai_draft(result['raw'], packet)
    st.caption(f"Local model: {result['model']} · Generation: {result['generation_seconds']}s · Setup: {result['setup_seconds']}s · Warm model: {result.get('warm_model', False)}")
    st.caption(f"Profile: {result.get('generation_profile', 'legacy')} · Output limit: {result.get('max_output_tokens', 'unknown')} tokens. A lower limit is not a measured speed guarantee.")
    st.caption('Prepared from event ' + str(result.get('prepared_at_event', story['as_of_event_id'])) + '. Reused only while facts, evidence and viewing preferences still match.')
    if issues:
        st.warning('AI draft rejected by basic checks. Keeping the rule-based story.')
        with st.expander('Inspect rejected draft and check results'):
            st.code(result['raw'])
            for issue in issues:
                st.write('• ' + issue)
        return story
    st.write('**AI draft — review against the evidence before approving:**')
    st.write(draft['explanation'])
    st.caption('Checks passed for JSON structure, evidence IDs, numeric values and supported timing phrases. A single JSON code fence is accepted without changing its contents. These checks do not prove factual correctness or translation quality.')
    if key not in approved:
        if st.button('Approve this draft for the story card', key='approve_local_ai'):
            approved[key] = True
            st.rerun()
    else:
        if st.button('Use the rule-based story instead', key='revert_local_ai'):
            approved.pop(key, None)
            st.rerun()
    if key in approved:
        return {**story, 'explanation': draft['explanation'],
                'generation_method': 'human_reviewed_local_ai', 'model': result['model'],
                'model_id': result['model_id'], 'generation_seconds': result['generation_seconds'],
                'basic_checks_passed': True, 'human_reviewed': True,
                'source_explanation': story['explanation'],
                'prepared_at_event': result.get('prepared_at_event', story['as_of_event_id']),
                'original_model_output': result['raw'], 'actual_prompt': result.get('prompt')}
    return story


@st.fragment(run_every=1)
def poll_local_ai():
    st.empty()  # Reserve a stable render slot for this timer fragment.
    if collect_ai_result():
        st.rerun()
    status = local_runner().status
    elapsed = int(time.monotonic()-status.get('started', time.monotonic()))
    st.info(f"Local AI: {status['stage']} · {max(0, elapsed)}s elapsed")


















def render_wording_library(story, draft_story, events):
    st.divider()
    st.subheader('Save reusable wording')
    st.caption('Review once for this outcome, pressure condition, audience and language. Live replay substitutes the current team and shot interval. Evidence always comes from the current sequence.')
    if not story.get('lifecycle_state'):
        st.info('Reveal a recovery to prepare wording.')
        return
    library = load_wording_library()
    key = wording_key(story)
    st.caption('Current wording slot: ' + key)
    if key in library.get('templates', {}):
        st.success('A reviewed template is saved for this situation.')
        st.code(library['templates'][key]['template'])
    supplied_pending = {
        'explanation': 'Riverside recovered the ball; outcome pending. Same-team pressure was recorded within the preceding five seconds; this is an association, not proof of causation.',
        'evidence_event_ids': [3, 5],
    }
    can_seed = (story['lifecycle_state'] == 'developing' and story['pressure_linked']
                and story['language'] == 'English' and story['viewing_mode'] == 'Casual Fan'
                and story['evidence_event_ids'] == [3, 5] and story['recovery_team'] == 'Riverside')
    if draft_story.get('generation_method') == 'human_reviewed_local_ai':
        initial = json.dumps({k: draft_story[k] for k in ['explanation', 'evidence_event_ids']}, ensure_ascii=False, indent=2)
        provenance = {'origin': 'foundry_local', 'model': draft_story['model'],
                      'model_id': draft_story['model_id'], 'generation_seconds': draft_story['generation_seconds'],
                      'prompt': draft_story.get('actual_prompt'),
                      'original_model_output': draft_story.get('original_model_output')}
    else:
        initial = json.dumps(supplied_pending, indent=2) if can_seed else ''
        provenance = {'origin': 'user_supplied_ai_draft', 'model': 'not independently verified'}
    form_id = hashlib.sha256((key + str(story['evidence_event_ids'])).encode()).hexdigest()[:12]
    with st.form('wording_form_' + form_id):
        raw = st.text_area('AI draft JSON — paste an existing result or use the reviewed result above', value=initial, height=150, key='wording_raw_' + form_id)
        reviewed = st.checkbox('I reviewed the facts, language and reusable wording for this situation.', key='wording_review_' + form_id)
        save = st.form_submit_button('Save wording for live reuse')
    if save:
        if provenance['origin'] == 'foundry_local' and raw.strip() != initial.strip():
            provenance = {**provenance, 'origin': 'human_edited_foundry_local_draft'}
        data, issues = check_ai_draft(raw, ai_packet(story, events))
        if not reviewed:
            issues.append('Review and check the approval box first.')
        if issues:
            st.error('Not saved: ' + ' '.join(issues))
        else:
            try:
                entry = make_wording_entry(story, data['explanation'], provenance)
                # Prevent player-specific wording from being generalized to all recoveries.
                if any(str(name) in entry['template'] for name in events.player.unique()):
                    raise ValueError('Remove player names before saving reusable wording.')
                library.setdefault('templates', {})[key] = entry
                path = wording_path()
                path.parent.mkdir(parents=True, exist_ok=True)
                temporary = path.with_suffix('.tmp')
                temporary.write_text(json.dumps(library, indent=2, ensure_ascii=False), encoding='utf-8')
                temporary.replace(path)
                st.success('Saved on this computer. Replay can now reuse it without running the model.')
                st.rerun()
            except (ValueError, OSError) as error:
                st.error(str(error))
    st.download_button('Export reviewed wording library', json.dumps(library, indent=2, ensure_ascii=False),
                       file_name='wording_library.json', mime='application/json')
    if key in library.get('templates', {}) and st.button('Remove wording for this situation'):
        library['templates'].pop(key)
        try:
            wording_path().write_text(json.dumps(library, indent=2, ensure_ascii=False), encoding='utf-8')
            st.rerun()
        except OSError as error:
            st.error(str(error))
    st.caption('Include data/wording_library.json with your project to share approved wording. Empty slots use rule-based explanations. Exported provenance distinguishes local generation from pasted drafts.')


def render_recovery_selector(events, favorite):
    recoveries = summarize_recoveries(events)
    if favorite != 'Both teams':
        recoveries = recoveries[recoveries.team == favorite]
    if recoveries.empty:
        return None
    names = {int(r.recovery_event_id): f'{r.team} · recovery at {r.recovery_time} · event {int(r.recovery_event_id)}'
             for r in recoveries.itertuples()}
    options = ['Follow latest'] + list(names)
    if st.session_state.get('recovery_watch') not in options:
        st.session_state.recovery_watch = 'Follow latest'
    suggested = contextual_candidates(events, favorite)
    if suggested:
        with st.expander('Suggested story — transparent editorial rules'):
            st.dataframe(suggested, hide_index=True, width='stretch')
            st.caption('First shot after prior no-shot outcomes ranks above other shots, closed outcomes, and pending recoveries. Ties prefer the newest recovery. This is a rule-based suggestion, not AI ranking.')
    chosen = st.selectbox('Recovery to follow', options, key='recovery_watch',
                          format_func=lambda value: names.get(value, value))
    return None if chosen == 'Follow latest' else chosen


def render_lifecycle(story, events):
    state = story.get('lifecycle_state')
    if not state:
        return
    spanish = story['language'] == 'Español'
    labels = ({'developing': 'EN DESARROLLO', 'shot': 'REMATE OBSERVADO', 'closed': 'CERRADA SIN REMATE'} if spanish else
              {'developing': 'DEVELOPING', 'shot': 'SHOT OBSERVED', 'closed': 'CLOSED WITHOUT A SHOT'})
    st.caption(f"Recovery #{story['recovery_event_id']} · {labels[state]}")
    if state == 'developing':
        st.info('Balón recuperado. Desenlace pendiente.' if spanish else 'Ball won. Outcome still developing.')
    elif state == 'shot':
        st.success((f"Recuperación → remate en {story['seconds_to_shot']} segundos." if spanish else
                    f"Recovery → shot in {story['seconds_to_shot']} seconds."))
    else:
        st.info('La posesión terminó sin un remate registrado.' if spanish else 'Possession ended without a recorded shot.')
    if story['viewing_mode'] == 'Analyst':
        recovery_pos = events.index[events.event_id == story['recovery_event_id']][0]
        sequence = events.iloc[recovery_pos:]
        changes = sequence.index[sequence.possession_id != story['possession_id']]
        if len(changes):
            sequence = sequence.loc[:changes[0]]  # Include the boundary evidence.
        st.dataframe(sequence[['event_id', 'time', 'team', 'player', 'event_type', 'outcome', 'possession_id']],
                     hide_index=True, width='stretch')
        st.caption('Full observed possession sequence, including the first boundary event when present. Pressure evidence is shown below the card.')


def render_recovery_recap(events, favorite, language):
    recoveries = summarize_recoveries(events)
    if favorite != 'Both teams':
        recoveries = recoveries[recoveries.team == favorite]
    spanish = language == 'Español'
    st.subheader('¿Qué pasó después de recuperar el balón?' if spanish else 'What came from winning the ball back?')
    counts = recoveries.status.value_counts()
    shot = int(counts.get('Shot observed', 0))
    closed = int(counts.get('No shot recorded before possession changed', 0))
    pending = int(counts.get('No shot yet in the revealed events', 0))
    for col, label, value in zip(st.columns(3),
        ['Con remate', 'Cerradas sin remate', 'Pendientes'] if spanish else ['Reached a shot', 'Closed without a shot', 'Still developing'],
        [shot, closed, pending]):
        col.metric(label, value)
    text = (f'{len(recoveries)} recuperaciones: {shot} con remate, {closed} cerradas sin remate y {pending} pendientes.' if spanish else
            f"{len(recoveries)} {'recovery' if len(recoveries) == 1 else 'recoveries'}: {shot} reached a shot, {closed} ended without a recorded shot, and {pending} remain unresolved.")
    st.write(text)
    st.caption('Developing recoveries are kept separate until an outcome is observed.')
    if not recoveries.empty:
        with st.expander('Recovery ledger — one row per story'):
            st.dataframe(recoveries, hide_index=True, width='stretch')
    st.download_button('Download recovery recap', f'As of {events.iloc[-1].time} · {favorite}\n{text}\nSynthetic partial sequence; not a final match result.',
                       file_name='matchlens_recovery_recap.txt')






def render_contrast(events, favorite, language):
    spanish = language == 'Español'
    st.subheader('Dos recuperaciones. Dos desenlaces.' if spanish else 'Two recoveries. Two different endings.')
    st.write('Recuperar el balón inicia la historia. La siguiente secuencia revela el desenlace.' if spanish else
             'Winning the ball starts the story. The next sequence reveals the outcome.')
    cases = contrast_cases(events, favorite)
    if not cases:
        st.info('La comparación aparecerá cuando se observen un remate y una posesión cerrada sin remate del mismo equipo.' if spanish else
                'The comparison appears once the same team has an observed shot outcome and a possession closed without a shot. Pending recoveries stay unresolved.')
        st.caption('To see the example: choose Riverside in the sidebar, then Jump to a key moment → 4. Compare both outcomes.')
        return
    html = contrast_html(cases, spanish)
    if hasattr(st, 'iframe'):
        st.iframe(html, height='content', alt='Two synthetic recovery sequences compared')
    else:
        import streamlit.components.v1 as components
        components.html(html, height=350, scrolling=True)
    st.caption('Each timer ends at its own outcome: a shot or a possession change. Compare the sequences, not the speed.')
    with st.expander('Comparison evidence & export'):
        st.caption('First observed shot outcome and first closed-without-shot outcome for one team. These examples are not a representative study.')
        st.write('Each panel starts at the controlled recovery. The shot panel stops at the first same-team shot; the other panel stops at the first event in a different possession. Pass counts cover the recovery team in that interval. Sequence IDs show the events used.')
        st.write('A saved shot is not a goal; a possession without a shot is not automatically worthless. The available events do not establish tactical causes, chance quality or coaching effectiveness.')
        ids = sorted({i for case in cases for i in case['sequence_ids'] + case['evidence_ids']})
        st.dataframe(events[events.event_id.isin(ids)], hide_index=True, width='stretch')
        st.download_button('Export the comparison HTML', html, file_name='matchlens_two_recoveries.html', mime='text/html')




DEMO_SCRIPT = (Path(__file__).resolve().parent/'docs'/'DEMO_GUIDE.txt').read_text(encoding='utf-8')


@st.fragment(run_every=1)
def poll_preparation():
    st.empty()
    future = st.session_state.get('preparation_future')
    if future is not None and future.done():
        try:
            future.result()
        except Exception as error:
            st.session_state.preparation_error = str(error)
        st.session_state.pop('preparation_future', None)
        st.rerun()


def render_asset_preparation(events, story, model, enabled):
    if not story.get('recovery_event_id'):
        return story
    key = snapshot_id(events, story['recovery_team'], story['recovery_event_id'])
    path = Path(__file__).resolve().parent/'data'/'preparations'/(key+'.json')
    try:
        report = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
    except (OSError, ValueError):
        report = {}
    busy = st.session_state.get('preparation_future') is not None or bool(st.session_state.get('ai_pending'))
    with st.expander('AI preparation — six assets with an audit trail'):
        st.write('Prepare fan, analyst and recap drafts in English and Spanish from this exact revealed snapshot. Each draft keeps its prompt, evidence, model identity, checks and human review. This can take several minutes locally.')
        st.caption('Snapshot assets apply only to this exact event prefix and recovery. Reusable wording templates remain a separate preparation option.')
        if st.button('Prepare six local AI drafts', disabled=not enabled or busy or st.session_state.playing):
            st.session_state.preparation_future = ai_executor().submit(prepare_assets, events.copy(), story.copy(), model, run_local_ai, path)
            st.session_state.preparation_error = None
            st.rerun()
        if not enabled:
            st.caption('Enable optional local generation in the sidebar to prepare new drafts. Reviewed existing assets can be used without generation.')
        if busy:
            st.info('A local job is running. Replay remains available; drafts belong to the snapshot captured when the job started.')
        if st.session_state.get('preparation_error'):
            st.error(st.session_state.preparation_error)
        assets = report.get('assets', [])
        if assets:
            st.caption(f"Saved preparation status: {report.get('status')} · {len(assets)}/6 results")
            for asset in assets:
                with st.expander(asset['asset_id']):
                    issues = asset.get('validation_issues', [])
                    if issues:
                        st.warning('Basic checks or inference failed: ' + '; '.join(issues))
                    st.code(asset.get('result', {}).get('raw', asset.get('result', {}).get('error','')), language='json')
                    st.write('Source facts: ' + asset.get('facts',''))
                    st.caption('Evidence IDs: '+str(asset.get('evidence_event_ids',[])))
                    button_key=key+'|'+asset['asset_id']
                    if not issues and not asset.get('human_reviewed'):
                        reviewed = st.checkbox('I checked factual meaning and language against the source.', key='review_'+button_key)
                        if st.button('Approve snapshot asset', key='approve_'+button_key, disabled=busy or not reviewed):
                            asset['human_reviewed']=True
                            asset['approved_utc']=__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()
                            write_report(path,report); st.rerun()
                    elif asset.get('human_reviewed'):
                        st.success('Human-reviewed snapshot asset')
            st.download_button('Download full AI preparation audit',json.dumps(report,indent=2,ensure_ascii=False),file_name='matchlens_preparation_audit.json',mime='application/json')
        else:
            st.caption('No drafts saved for this moment yet.')
    asset=approved_asset(report,events,story,story['viewing_mode'],story['language']) if report else None
    if asset:
        story={**story, 'explanation':asset['explanation'], 'evidence_event_ids':asset['evidence_event_ids'],
               'generation_method':'ai_prepared_selected_live','preparation_snapshot_id':key,
               'wording_provenance':{'origin':'foundry_local_snapshot_preparation','model_alias':report.get('model_alias')}}
    recap=approved_asset(report,events,story,'Recap',story['language']) if report else None
    if recap:
        with st.expander('Reviewed AI recap for this snapshot'):
            st.write(recap['explanation'])
            st.caption('Evidence: '+str(recap['evidence_event_ids']))
    return story


st.set_page_config(page_title='MatchLens', page_icon='⚽', layout='wide')
st.markdown(CSS, unsafe_allow_html=True)
st.markdown(masthead(), unsafe_allow_html=True)
team_names = ['Northbridge', 'Riverside']


st.title('Ball won. What happens next?')
st.markdown('<div class="ml-intro">See what follows a recovery. Choose a story, check the evidence, and export a card for your audience.</div>', unsafe_allow_html=True)
if st.session_state.get('ai_pending'):
    with st.container():
        poll_local_ai()
if st.session_state.get('preparation_future') is not None:
    with st.container():
        poll_preparation()

with st.sidebar:
    st.header('Replay & audience')
    replay_controls = st.container()
    source = st.selectbox('Event source', ['Original 21-event sample', 'Context storyline', 'Scenario laboratory', 'Generated demonstration'])
    lab_cases = scenario_suite()
    lab_index = st.selectbox('Laboratory case', range(len(lab_cases)), format_func=lambda i: lab_cases[i]['name']) if source == 'Scenario laboratory' else 0
    seed = st.number_input('Scenario seed', min_value=0, max_value=99999, value=42) if source == 'Generated demonstration' else 42
    st.divider()
    st.subheader('Your audience')
    mode = st.selectbox('Viewing mode', ['Casual Fan', 'Analyst'])
    favorite = st.selectbox('Team to follow', ['Both teams'] + team_names, index=2)
    language = st.selectbox('Story language', ['English', 'Español'])
    interval = st.select_slider('Seconds per event', options=[0.5, 1.0, 2.0, 3.0], value=1.0)
    
    st.divider()
    with st.expander('Local AI setup', expanded=False):
        st.subheader('Zero-cost local AI')
        enable_generation = st.checkbox('Enable optional local generation', value=False,
                                        help='Not needed to replay or reuse saved wording. Use the documented backed-up context workaround first if the local generator runs out of memory; native inference still needs a laptop check.')
        local_model = st.selectbox('Local model', LOCAL_MODELS, disabled=not enable_generation)
        st.caption('Recommended on this laptop: leave generation off during replay. Saved reviewed wording and rule-based stories need no model call. Local AI preparation can take several minutes and may run out of memory.')
        if st.button('Release local model memory', disabled=bool(st.session_state.get('ai_pending')) or st.session_state.get('preparation_future') is not None, key='release_model'):
            local_runner().close()
            st.success('Local model process released. Prepared story results remain cached.')

try:
    if source == 'Context storyline':
        full = context_storyline()
    elif source == 'Scenario laboratory':
        full = pd.DataFrame(lab_cases[lab_index]['events'])
    elif source == 'Generated demonstration':
        full = generate_scenario(int(seed))
    else:
        full = pd.read_csv(Path(__file__).resolve().parent/'data'/'sample_events.csv', dtype={'time': str})
    full = validate_events(full)
except (OSError, ValueError, pd.errors.ParserError) as error:
    st.error(str(error))
    st.stop()

signature = hashlib.sha256((source+full.to_csv(index=False)).encode()).hexdigest()
if st.session_state.get('dataset_signature') != signature:
    st.session_state.update(dataset_signature=signature, visible_count=0, playing=False, last_tick=time.monotonic())


def demo_jump(position):
    st.session_state.update(visible_count=position, playing=False, last_tick=time.monotonic(),
                            recovery_watch='Follow latest')


def advance():
    st.session_state.visible_count = min(st.session_state.visible_count+1, len(full))
    st.session_state.last_tick = time.monotonic()
    if st.session_state.visible_count >= len(full):
        st.session_state.playing = False


def toggle_play():
    st.session_state.playing = not st.session_state.playing
    st.session_state.last_tick = time.monotonic()


def reset():
    st.session_state.update(visible_count=0, playing=False, last_tick=time.monotonic())


# A small timer fragment triggers a full redraw only when a new event is due.
# No blocking sleep loop: Pause and the viewer controls remain responsive.
@st.fragment(run_every=0.5)
def replay_timer():
    st.empty()  # Keep fragment updates separate from replay controls.
    if st.session_state.playing and time.monotonic()-st.session_state.last_tick >= interval:
        advance()
        st.rerun()


def seek_event():
    st.session_state.visible_count = st.session_state.replay_position
    st.session_state.playing = False
    st.session_state.last_tick = time.monotonic()


# Persistent sidebar controls are outside all timed fragment containers.
with replay_controls:
    st.divider()
    st.subheader('Replay controls')
    st.session_state.replay_position = st.session_state.visible_count
    st.slider('Event position', min_value=0, max_value=len(full),
              key='replay_position', on_change=seek_event,
              help='Jump to an event. Moving this slider pauses automatic replay.')
    st.button('Pause' if st.session_state.playing else 'Play', on_click=toggle_play,
              key='replay_play', width='stretch',
              disabled=st.session_state.visible_count >= len(full), type='primary')
    next_col, reset_col = st.columns(2)
    next_col.button('Next event', on_click=advance, key='replay_next', width='stretch',
                    disabled=st.session_state.playing or st.session_state.visible_count >= len(full))
    reset_col.button('Reset', on_click=reset, key='replay_reset', width='stretch')
    if source == 'Original 21-event sample':
        with st.expander('Jump to a key moment', expanded=True):
            st.caption('Choose '+team_names[1]+' to follow both recoveries. These buttons navigate the synthetic sample.')
            for label, position in [('1. Ball won', 5), ('2. Shot observed', 7), ('3. Second recovery', 12), ('4. Compare both outcomes', 15)]:
                st.button(label, key=f'demo_{position}', on_click=demo_jump, args=(position,), width='stretch')


if st.session_state.playing:
    with st.container():
        replay_timer()

# The analytics boundary: no function below receives unrevealed events.
events = full.iloc[:st.session_state.visible_count].copy().reset_index(drop=True)
clock = events.iloc[-1].time if len(events) else '00:00'
a, b, c = st.columns(3)
a.metric('Replay clock', clock)
b.metric('Events revealed', f'{len(events)} / {len(full)}')
c.metric('Playback', 'Playing' if st.session_state.playing else ('Complete' if len(events) == len(full) else 'Paused'))
st.progress(len(events)/len(full))
if len(events) == len(full):
    st.info('Replay complete. Select a recovery below, or Reset to watch again.')
if events.empty:
    st.markdown('<div class="ml-empty"><div class="ml-kicker">Start with a story</div><h2>Two recoveries. Two different endings.</h2><p>One sequence reaches a shot. Another ends without one. Explore the evidence behind both, or start the replay to watch each story develop.</p></div>', unsafe_allow_html=True)
    if source == 'Original 21-event sample':
        st.button('Explore the two-recovery example', type='primary', on_click=demo_jump, args=(15,))
    st.caption('Prefer to watch it unfold? Select Play in the left sidebar.')
    st.stop()

story_tab, overview_tab, studio_tab, about_tab = st.tabs(['Story desk', 'Match overview', 'Wording studio', 'Methods & checks'])

with overview_tab:
    with st.expander('Score and match statistics', expanded=True):
        metrics = team_metrics(events)
        for col, row in zip(st.columns(2), metrics.to_dict('records')):
            with col:
                st.subheader(row['team'])
                st.metric('Recorded goals', row['goals'])
                accuracy = 'N/A' if pd.isna(row['pass_accuracy']) else f"{row['pass_accuracy']:.1f}%"
                st.write(f"Shots: **{row['shots']}** · Pass accuracy: **{accuracy}** · Pressures: **{row['pressures']}**")
        st.caption('Both-team totals from revealed events. Pass accuracy = completed / attempted passes. Goals count only recorded shot events with outcome goal.')
player = None
if mode == 'Player Focus':
    choices = events if favorite == 'Both teams' else events[events.team == favorite]
    if not choices.empty:
        player = st.selectbox('Player with recorded actions', sorted(choices.player.unique()))

with story_tab:
    st.markdown('<div class="ml-path"><span><b>1</b> Choose a recovery</span><span><b>2</b> Check the evidence</span><span><b>3</b> Download your story</span></div>', unsafe_allow_html=True)
    render_contrast(events, favorite, language)
    st.divider()
    st.subheader('1. Choose your recovery')
    recovery_id = render_recovery_selector(events, favorite)
    analytics_started = time.perf_counter()
    story = build_story(events, mode, favorite, player, language, recovery_id)
    analytics_ms = (time.perf_counter()-analytics_started)*1000
    
    st.caption('Follow latest updates with the replay. Choose a numbered recovery to keep its story in view.')
    if story:
        source_story = story.copy()
        story = apply_wording(source_story, events, load_wording_library())
        # Keep preparation controls in their dedicated workspace.
        with studio_tab:
            st.subheader('Prepare once. Reuse with evidence.')
            st.caption('Drafts stay off the story desk until reviewed. Live replay never waits for a model.')
            story = render_asset_preparation(events, story, local_model, enable_generation)
        story = audience_story(story)
        card_html = broadcast_card_html(story)
        if hasattr(st, 'iframe'):
            st.iframe(card_html, height='content', alt='Selected recovery story with outcome and evidence')
        else:
            import streamlit.components.v1 as components
            components.html(card_html, height=365, scrolling=True)
        if story.get('recovery_event_id'):
            context = recovery_context(events, story['recovery_event_id'])
            story['context'] = context
            story['context_explanation'] = context_explanation(context, language, mode == 'Analyst')
            st.markdown(context_note(story['context_explanation'], language), unsafe_allow_html=True)
            with st.expander('Context evidence and baseline'):
                context_labels = {
                    'recovery_event_id': 'Recovery event', 'team': 'Team',
                    'baseline_as_of_event_id': 'History frozen at event',
                    'previous_recoveries': 'Earlier recoveries',
                    'previous_shot_outcomes': 'Earlier recoveries reaching a shot',
                    'previous_closed_without_shot': 'Earlier recoveries ending without a shot',
                    'previous_unresolved': 'Earlier recoveries still developing',
                    'preceding_no_shot_streak': 'Consecutive earlier recoveries without a shot',
                    'first_shot_after_no_shot_history': 'First shot after earlier no-shot outcomes',
                    'previous_shot_timing_sample': 'Earlier shot timings available',
                    'previous_shot_median_seconds': 'Typical earlier recovery-to-shot time',
                    'current_seconds': 'This recovery-to-shot time',
                    'baseline_evidence_event_ids': 'Earlier evidence event IDs',
                }
                rows = []
                for field, label in context_labels.items():
                    value = context.get(field)
                    if value is None:
                        display = 'Not available yet'
                    elif isinstance(value, bool):
                        display = 'Yes' if value else 'No'
                    elif isinstance(value, list):
                        display = ', '.join(map(str, value)) if value else 'No earlier evidence'
                    elif field in ('previous_shot_median_seconds', 'current_seconds'):
                        display = f'{value:g} seconds'
                    else:
                        display = str(value)
                    rows.append({'Measure': label, 'Value': display})
                st.table(pd.DataFrame(rows))
                st.caption('Baseline is frozen at the recovery start. Shot outcomes resolve the shooting question even if possession continues. Pending cases are never counted as no-shot outcomes. This is descriptive context, not a causal explanation.')
        if mode == 'Analyst':
            render_lifecycle(story, events)
        st.subheader('2. Revisar la evidencia' if language == 'Español' else '2. Check the evidence')
        with st.expander('Why this story? Inspect the evidence', expanded=mode == 'Analyst'):
            st.dataframe(events[events.event_id.isin(story['evidence_event_ids'])], hide_index=True, width='stretch')
            st.caption(f'Rule-based story calculation: {analytics_ms:.1f} ms on this run; excludes rendering, template selection and model generation.')
            st.caption('Follow latest selects the newest recovery; pin a recovery to watch its outcome develop. Each story uses only revealed events. Pressure is associated with recovery, not proven to cause it. A shot does not establish chance quality.')
        overlay = {**story, 'schema_version': 2, 'source_event_id': int(events.iloc[-1].event_id),
                   'replace_on_evidence_change': True, 'preparation_mode': 'reviewed_library_or_rule_fallback',
                   'display_duration_seconds': 8}
        with studio_tab:
            with st.expander('Prepare or edit reusable wording', expanded=False):
                draft_story = render_local_ai(source_story, events, local_model) if enable_generation else source_story
                if not enable_generation:
                    st.caption('Use saved wording or paste a draft below. To generate a new draft, enable Local AI setup in the sidebar.')
                render_wording_library(source_story, draft_story, events)
        st.subheader('3. Export your story')
        st.caption('Check the box below to download the card, evidence and review record. Changes to the story require a new review.')
        if story.get('recovery_event_id'):
            identity = review_key(story, events)
            reviewed = st.checkbox('I checked the story and its supporting events.', key='producer_review_'+identity)
            if reviewed:
                st.download_button('Download story package', producer_bundle(story, events, identity),
                                   file_name='matchlens_producer_package.zip', mime='application/zip', type='primary')
                st.success('Package ready: story card, context, source evidence and review record.')
            else:
                st.button('Download story package', disabled=True, key='export_locked', help='Review the story and check the box above to enable download.')
        with st.expander('More export options'):
            st.download_button('Download preview card', card_html, file_name='matchlens_card.html', mime='text/html')
            st.download_button('Download story data', json.dumps(overlay, indent=2, ensure_ascii=False),
                               file_name='matchlens_story.json', mime='application/json')
            st.caption('Preview card: open in a browser to check the layout. Story data: structured text, timing and evidence for an integration. These exports are unreviewed previews; they do not connect to a video feed.')
    
    else:
        st.info('No recorded actions for this selection yet.')

with overview_tab:
    
    render_recovery_recap(events, favorite, language)
    
    
    if mode == 'Analyst':
        st.subheader('Recovery outcomes and pressure evidence')
        recoveries = summarize_recoveries(events)
        links = pressure_links(events)
        combined = recoveries.merge(links.drop(columns='team'), on='recovery_event_id', how='left')
        if favorite != 'Both teams':
            combined = combined[combined.team == favorite]
        a, b = st.columns(2)
        a.metric('Controlled recoveries', len(combined))
        b.metric('Recoveries followed by a recorded shot', int(combined.status.eq('Shot observed').sum()))
        st.dataframe(combined, hide_index=True, width='stretch')
        st.caption('First subsequent same-team shot within the contiguous possession; no time limit. Pressure link: same-team pressure in the preceding possession within five seconds. Association does not prove causation. Blank values mean no qualifying evidence observed.')
        st.subheader('Recorded pressure events by minute')
        pressures = events[events.event_type == 'pressure'].copy()
        if not pressures.empty:
            pressures['minute'] = pressures.elapsed_seconds // 60
            chart = pressures.groupby(['minute', 'team']).size().unstack(fill_value=0)
            chart = chart.reindex(range(int(events.iloc[-1].elapsed_seconds)//60+1), fill_value=0)
            st.bar_chart(chart)
            st.caption('The current minute is incomplete. Counts are not possession-adjusted pressure rates.')
    elif mode == 'Player Focus' and player:
        st.dataframe(events[events.player == player], hide_index=True, width='stretch')
        st.caption('Only recorded actions are measured; off-ball movement, speed, and distance are unavailable.')
    
    with st.expander('Full event-statistics recap'):
        recap = recap_text(events, language)
        st.text(recap)
        st.download_button('Download recap', recap, file_name='matchlens_recap.txt', mime='text/plain')
    with st.expander('Revealed event log'):
        st.dataframe(events, hide_index=True, width='stretch')
        st.download_button('Download revealed events', events.to_csv(index=False),
                           file_name='matchlens_revealed_events.csv', mime='text/csv')
with about_tab:
    with st.expander('Methodology and limitations'):
        st.write('The generated scenario uses a fixed seed for reproducibility and authored football sequences: pressure without a turnover, recoveries without shots, and recoveries followed by shots. Timing and pass counts vary with the seed. This is a demonstration dataset, not a calibrated simulation or a complete match.')
        st.write('Approved reusable wording is saved locally in data/wording_library.json. Reuse requires the same outcome, pressure-link status, audience and language. Team names and shot intervals are filled from current calculations; evidence IDs are never copied from a prepared draft. Only reviewed templates are used. Missing coverage falls back to rule-based wording. This is AI-assisted preparation, not live model generation or multi-agent orchestration.')
        st.write('All analytics, stories, recaps and evidence downloads use the revealed prefix only. Switching source or seed resets replay. English and Spanish stories use authored templates; raw event names and some technical labels remain in English. Optional AI drafts run through Microsoft Foundry Local. Basic checks are incomplete; human review is required before a draft replaces the story. Recaps use rules unless a reviewed AI recap exists for the exact snapshot. AI results are reused only when facts, evidence and viewing preferences are identical. A prepared AI card is not live model generation. Each request has a fresh conversation; model weights stay loaded until released. The preparation audit records model results, basic checks and separate human review. The analytics evaluation report does not measure AI factuality.')
    
    with st.expander('Quality checks & performance', expanded=True):
        report_path = Path(__file__).resolve().parent/'data'/'evaluation_report.json'
        if report_path.exists():
            report = json.loads(report_path.read_text(encoding='utf-8'))
            st.subheader('Tested one event at a time')
            st.write('Checks cover recovery outcomes and how stories update as more events become visible.')
            a, b, c = st.columns(3)
            a.metric('Scenarios passed', f"{report['cases_passed']} / {report['cases']}")
            b.metric('Replay snapshots checked', report['prefixes_evaluated'])
            c.metric('Checks performed', report['assertions'])
            timing = report['analytics_plus_wording_ms']
            environment = report['environment']
            st.table(pd.DataFrame([
                {'Measure': 'Typical processing time (median)', 'Result': f"{timing['median']:.2f} ms"},
                {'Measure': '95th-percentile processing time', 'Result': f"{timing['p95']:.2f} ms"},
                {'Measure': 'Failed checks', 'Result': str(len(report['failures']))},
                {'Measure': 'Snapshots using fallback wording', 'Result': f"{report['rule_fallbacks']} of {report['prefixes_evaluated']}"},
                {'Measure': 'Test environment', 'Result': f"{environment['platform']} · Python {environment['python']}"},
            ]))
            st.caption('Timing covers analytics and wording selection, excluding screen rendering and AI generation. Fallback wording is used when a reviewed template is unavailable.')
            st.write('**What these checks establish:** the authored synthetic scenarios behave as expected. They do not measure real-match accuracy or the factual quality of AI drafts, which still require review.')
            if report['failures']:
                st.write('Checks needing attention')
                st.dataframe(pd.DataFrame(report['failures']), hide_index=True)
            st.download_button('Download full test report', report_path.read_text(encoding='utf-8'), file_name='evaluation_report.json', mime='application/json')
        else:
            st.info('No test report available. Run python evaluate.py to create one.')
