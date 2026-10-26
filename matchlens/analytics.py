"""Deterministic football analytics. Functions receive revealed events only."""
import pandas as pd
import random

def summarize_recoveries(events):
    """Return one row per controlled recovery in a single-match event log.

    CSV row order breaks ties when two events share a timestamp.
    Search only the current, contiguous possession; stop at its boundary.
    No shot observed does not prove failure if the sample ends mid-possession.
    """
    rows = []
    ordered = events.reset_index(drop=True)

    for position, recovery in ordered.iterrows():
        if (
            recovery["event_type"] != "recovery"
            or recovery["outcome"] != "controlled"
        ):
            continue

        first_shot = None
        possession_ended = False

        for next_position in range(position + 1, len(ordered)):
            event = ordered.iloc[next_position]

            if event["possession_id"] != recovery["possession_id"]:
                possession_ended = True
                break

            if (
                first_shot is None
                and event["team"] == recovery["team"]
                and event["event_type"] == "shot"
            ):
                first_shot = event

        seconds_to_shot = None
        shot_id = None
        shot_time = None

        if first_shot is not None:
            status = "Shot observed"
            seconds_to_shot = int(
                first_shot["elapsed_seconds"]
                - recovery["elapsed_seconds"]
            )
            shot_id = first_shot["event_id"]
            shot_time = first_shot["time"]
        elif possession_ended:
            status = "No shot recorded before possession changed"
        else:
            status = "No shot yet in the revealed events"

        rows.append({
            "recovery_event_id": recovery["event_id"],
            "team": recovery["team"],
            "player": recovery["player"],
            "possession_id": recovery["possession_id"],
            "recovery_time": recovery["time"],
            "shot_event_id": shot_id,
            "shot_time": shot_time,
            "seconds_to_shot": seconds_to_shot,
            "status": status,
        })

    columns = [
        "recovery_event_id", "team", "player", "possession_id",
        "recovery_time", "shot_event_id", "shot_time",
        "seconds_to_shot", "status",
    ]
    result = pd.DataFrame(rows, columns=columns)
    result["seconds_to_shot"] = pd.array(
        result["seconds_to_shot"], dtype="Int64"
    )
    return result


def generate_scenario(seed=42):
    """Seeded fictional event sequence, designed to exercise three situations.

    Pressure without a turnover, recoveries without shots, then recoveries
    with shots. These are authored scenarios, not calibrated probabilities.
    """
    rng = random.Random(seed)
    rows, clock, possession = [], 0, 0
    players = {'Northbridge': ['Alex Reed', 'Sam Cole', 'Jamie Vale'],
               'Riverside': ['Leo Grant', 'Noah Blake', 'Max Ellis']}

    def emit(team, kind, outcome, player=None, delay=None):
        nonlocal clock
        clock += delay if delay is not None else rng.randint(3, 7)
        rows.append(dict(event_id=len(rows)+1, time=f'{clock//60:02d}:{clock%60:02d}',
                         team=team, player=player or rng.choice(players[team]),
                         event_type=kind, outcome=outcome, possession_id=possession))

    next_start = ('kickoff', 'completed', 'Alex Reed')
    for cycle in range(12):
        possession += 1
        emit('Northbridge', *next_start)
        for _ in range(rng.randint(2, 4)):
            emit('Northbridge', 'pass', 'completed')
        emit('Riverside', 'pressure', 'applied', 'Leo Grant')
        if cycle < 4:
            # The pressured team keeps the ball and reaches a shot.
            emit('Northbridge', 'pass', 'completed', delay=1)
            emit('Northbridge', 'shot', 'saved', 'Jamie Vale')
            possession += 1
            emit('Riverside', 'goalkeeper_claim', 'controlled', 'Owen Marsh', delay=1)
        else:
            emit('Northbridge', 'pass', 'failed', delay=1)
            possession += 1
            emit('Riverside', 'recovery', 'controlled', 'Leo Grant', delay=1)
        emit('Riverside', 'pass', 'completed', 'Leo Grant')
        if cycle < 8:
            emit('Riverside', 'pass', 'failed', 'Noah Blake')
            next_start = ('recovery', 'controlled', 'Sam Cole')
        else:
            outcome = ['saved', 'off_target', 'goal', 'saved'][cycle-8]
            emit('Riverside', 'shot', outcome, 'Noah Blake')
            next_start = {
                'saved': ('goalkeeper_claim', 'controlled', 'Ellis Ward'),
                'off_target': ('goal_kick', 'completed', 'Ellis Ward'),
                'goal': ('kickoff', 'completed', 'Alex Reed'),
            }[outcome]
    possession += 1
    emit('Northbridge', *next_start)
    emit('Northbridge', 'pass', 'completed')  # Intentionally open final possession.
    return pd.DataFrame(rows)


def validate_events(df):
    required = {'event_id', 'time', 'team', 'player', 'event_type', 'outcome', 'possession_id'}
    if not required.issubset(df.columns):
        raise ValueError('Missing columns: ' + ', '.join(sorted(required-set(df.columns))))
    if df.empty or df[list(required)].isna().any().any():
        raise ValueError('The dataset is empty or contains missing required values.')
    if df.event_id.duplicated().any():
        raise ValueError('Event IDs must be unique.')
    df = df.copy()
    df['time'] = df['time'].astype(str).str.strip()
    if not df.time.str.fullmatch(r'\d+:[0-5]\d').all():
        raise ValueError('Use minutes:seconds for timestamps, such as 00:14.')
    df['elapsed_seconds'] = df.time.map(lambda s: int(s.split(':')[0])*60+int(s.split(':')[1]))
    if not df.elapsed_seconds.is_monotonic_increasing:
        raise ValueError('Events must be ordered by match time.')
    # A possession ID cannot reappear after its contiguous sequence has ended.
    segments = df.loc[df.possession_id.ne(df.possession_id.shift()), 'possession_id']
    if segments.duplicated().any():
        raise ValueError('A possession ID reappears after its possession ended.')
    return df.reset_index(drop=True)


def pressure_links(events):
    rows = []
    for pos in range(1, len(events)):
        recovery = events.iloc[pos]
        previous = events.iloc[pos-1].possession_id
        if recovery.event_type != 'recovery' or recovery.outcome != 'controlled' or previous == recovery.possession_id:
            continue
        match = None
        for j in range(pos-1, -1, -1):
            event = events.iloc[j]
            if event.possession_id != previous:
                break
            gap = int(recovery.elapsed_seconds-event.elapsed_seconds)
            if event.team == recovery.team and event.event_type == 'pressure' and 0 <= gap <= 5:
                match = event
                break
        rows.append(dict(recovery_event_id=recovery.event_id, team=recovery.team,
                         pressure_event_id=None if match is None else match.event_id,
                         seconds_after_pressure=None if match is None else int(recovery.elapsed_seconds-match.elapsed_seconds)))
    return pd.DataFrame(rows, columns=['recovery_event_id', 'team', 'pressure_event_id', 'seconds_after_pressure'])


def team_metrics(events):
    rows = []
    for team in sorted(events.team.unique()):
        own = events[events.team == team]
        passes = own[own.event_type == 'pass']
        completed = int(passes.outcome.eq('completed').sum())
        rows.append(dict(team=team, passes=len(passes), completed=completed,
                         pass_accuracy=None if passes.empty else round(100*completed/len(passes), 1),
                         shots=int(own.event_type.eq('shot').sum()),
                         goals=int(((own.event_type == 'shot') & (own.outcome == 'goal')).sum()),
                         pressures=int(own.event_type.eq('pressure').sum())))
    return pd.DataFrame(rows)


def build_story(events, mode, favorite, player, language, recovery_id=None):
    """A deterministic evidence packet. An AI adapter can consume it later."""
    if events.empty:
        return None
    spanish = language == 'Español'
    evidence = []
    lifecycle = {}
    if mode == 'Player Focus':
        own = events[events.player == player]
        if own.empty:
            return None
        latest = own.iloc[-1]
        evidence = own.event_id.tolist()
        headline = f'{player}: {len(own)} ' + ('acciones registradas' if spanish else 'recorded actions')
        text = (f'Última acción: {latest.event_type} ({latest.outcome}) a las {latest.time}. '
                'Solo se mide la participación con eventos registrados.' if spanish else
                f'Latest action: {latest.event_type} ({latest.outcome}) at {latest.time}. '
                'This measures recorded involvement; off-ball work is not measured.')
    else:
        recoveries = summarize_recoveries(events)
        if favorite != 'Both teams':
            recoveries = recoveries[recoveries.team == favorite]
        if recovery_id is not None:
            recoveries = recoveries[recoveries.recovery_event_id == recovery_id]
        if recoveries.empty:
            own = events if favorite == 'Both teams' else events[events.team == favorite]
            if own.empty:
                return None
            latest = own.iloc[-1]
            evidence = [latest.event_id]
            headline = 'Esperando una recuperación' if spanish else 'Waiting for a recovery'
            text = ('Aún no se ha registrado una recuperación controlada para esta selección. '
                    'Un evento de presión por sí solo no demuestra que se haya recuperado el balón.' if spanish else
                    'No controlled recovery has been recorded for this selection yet. '
                    'A pressure event alone does not establish that the ball was won back.')
        else:
            r = recoveries.iloc[-1]
            evidence = [r.recovery_event_id]
            links = pressure_links(events)
            link = links[links.recovery_event_id == r.recovery_event_id]
            linked = not link.empty and pd.notna(link.iloc[0].pressure_event_id)
            if linked:
                evidence.insert(0, link.iloc[0].pressure_event_id)
            if r.status == 'Shot observed':
                evidence.append(r.shot_event_id)
                seconds = int(r.seconds_to_shot)
                headline = f'{r.team}: ' + ('recuperación → remate' if spanish else 'recovery → shot')
                text = (f'{r.team} recuperó el balón y remató {seconds} segundos después, en la misma posesión. '
                        'Esto muestra una transición que terminó en remate; no demuestra la calidad de la ocasión.' if spanish else
                        f'{r.team} won the ball back and took a shot {seconds} seconds later in the same possession. '
                        'That shows a turnover becoming an attempt; it does not establish the quality of the chance.')
            elif r.status == 'No shot recorded before possession changed':
                # Cite the event that proves the possession has ended, too.
                position = events.index[events.event_id == r.recovery_event_id][0]
                boundary = events.iloc[position+1:]
                boundary = boundary[boundary.possession_id != r.possession_id]
                if not boundary.empty:
                    evidence.append(boundary.iloc[0].event_id)
                headline = f'{r.team}: ' + ('recuperación sin remate' if spanish else 'recovery without a shot')
                text = ('La posesión terminó sin un remate registrado tras la recuperación. '
                        'Recuperar el balón no siempre produce una ocasión de tiro.' if spanish else
                        'The possession ended without a recorded shot after this recovery. '
                        'Winning the ball back does not always produce a shooting opportunity.')
            else:
                headline = f'{r.team}: ' + ('balón recuperado; desenlace pendiente' if spanish else 'ball recovered; outcome pending')
                text = ('Aún no se ha observado un remate ni un cambio de posesión. '
                        'Es demasiado pronto para juzgar el resultado de esta recuperación.' if spanish else
                        'No subsequent shot or possession change has been observed yet. '
                        'It is too early to judge the outcome of this recovery.')
            if linked:
                text += (' Se registró presión del mismo equipo en los cinco segundos anteriores; no prueba causalidad.' if spanish else
                         ' Same-team pressure was recorded within the preceding five seconds; this is an association, not proof of causation.')
            lifecycle = dict(recovery_event_id=int(r.recovery_event_id), possession_id=int(r.possession_id),
                             recovery_team=r.team, recovery_time=r.recovery_time,
                             lifecycle_state={'Shot observed': 'shot', 'No shot recorded before possession changed': 'closed',
                                              'No shot yet in the revealed events': 'developing'}[r.status],
                             pressure_linked=bool(linked),
                             seconds_to_shot=None if pd.isna(r.seconds_to_shot) else int(r.seconds_to_shot))
            if mode == 'Analyst':
                text += f' [Possession {r.possession_id}; recovery {r.recovery_time}; status: {r.status}.]'
    # IDs are normalized for machine-readable output; all must be observed.
    evidence = [int(x) for x in evidence]
    assert set(evidence).issubset(set(events.event_id))
    return dict(headline=headline, explanation=text, evidence_event_ids=evidence,
                as_of_event_id=int(events.iloc[-1].event_id),
                match_time=events.iloc[-1].time, language=language, viewing_mode=mode,
                favorite_team=favorite, selected_player=player if mode == 'Player Focus' else None,
                generation_method='rule_based', synthetic=True,
                suggested_display_seconds=8, **lifecycle)


def recap_text(events, language):
    spanish = language == 'Español'
    lines = [('Resumen parcial de eventos sintéticos' if spanish else 'Synthetic sequence recap so far'),
             f'As of {events.iloc[-1].time} | {len(events)} events', '']
    r = summarize_recoveries(events)
    for m in team_metrics(events).to_dict('records'):
        own = r[r.team == m['team']]
        shots = int(own.status.eq('Shot observed').sum())
        pending = int(own.status.eq('No shot yet in the revealed events').sum())
        if spanish:
            lines.append(f"{m['team']}: {m['goals']} goles, {m['shots']} remates; {m['completed']}/{m['passes']} pases completados. "
                         f"{len(own)} recuperaciones controladas; {shots} seguidas de remate y {pending} con desenlace pendiente.")
        else:
            lines.append(f"{m['team']}: {m['goals']} goals, {m['shots']} shots; {m['completed']}/{m['passes']} passes completed. "
                         f"{len(own)} controlled recoveries; {shots} followed by a shot and {pending} with an outcome still pending.")
    lines += ['', 'Plantillas basadas en reglas; no es un resultado final.' if spanish else
              'Rule-based templates; this is not a full-match result.']
    return '\n'.join(lines)


def contrast_cases(events, favorite):
    """First observed shot and closed recovery for one team, never a future outcome.

    This is a purposeful illustration, not a representative sample or matched study.
    """
    recoveries = summarize_recoveries(events)
    teams = list(recoveries.team.unique()) if favorite == 'Both teams' else [favorite]
    for team in teams:
        own = recoveries[recoveries.team == team]
        shots = own[own.status == 'Shot observed']
        closed = own[own.status == 'No shot recorded before possession changed']
        if shots.empty or closed.empty:
            continue
        cases = []
        for row in [shots.iloc[0], closed.iloc[0]]:
            start = events.index[events.event_id == row.recovery_event_id][0]
            sequence = events.iloc[start:]
            boundaries = sequence.index[sequence.possession_id != row.possession_id]
            if row.status == 'Shot observed':
                end = events.index[events.event_id == row.shot_event_id][0]
                sequence = events.loc[start:end]
                kind = 'shot'
            else:
                sequence = events.loc[start:boundaries[0]]
                kind = 'closed'
            same = sequence[(sequence.possession_id == row.possession_id) & (sequence.team == team)]
            cases.append(dict(team=team, state=kind, recovery_id=int(row.recovery_event_id),
                              recovery_time=row.recovery_time, end_time=sequence.iloc[-1].time,
                              seconds=int(sequence.iloc[-1].elapsed_seconds - sequence.iloc[0].elapsed_seconds),
                              completed_passes=int(((same.event_type == 'pass') & (same.outcome == 'completed')).sum()),
                              failed_passes=int(((same.event_type == 'pass') & (same.outcome == 'failed')).sum()),
                              end_outcome=str(sequence.iloc[-1].outcome),
                              sequence_ids=[int(x) for x in sequence.event_id],
                              evidence_ids=build_story(events, 'Casual Fan', team, None, 'English', int(row.recovery_event_id))['evidence_event_ids']))
        return cases
    return []



def recovery_context(events, recovery_id):
    """Historical baseline frozen immediately before this recovery, never future data."""
    current = summarize_recoveries(events)
    selected = current[current.recovery_event_id == recovery_id]
    if selected.empty:
        return None
    row = selected.iloc[0]
    position = events.index[events.event_id == recovery_id][0]
    # Include the recovery itself only to close the preceding possession; exclude its row.
    history = summarize_recoveries(events.iloc[:position+1])
    history = history[(history.team == row.team) & (history.recovery_event_id != recovery_id)]
    shot = history[history.status == 'Shot observed']
    closed = history[history.status == 'No shot recorded before possession changed']
    pending = history[history.status == 'No shot yet in the revealed events']
    streak = 0
    for item in history.iloc[::-1].itertuples():
        if item.status != 'No shot recorded before possession changed':
            break
        streak += 1
    median = float(shot.seconds_to_shot.median()) if len(shot) >= 3 else None
    baseline_ids = []
    # Cite every historical recovery and its observed resolving evidence.
    for item in history.itertuples():
        evidence = build_story(events.iloc[:position+1].copy(), 'Casual Fan', row.team, None, 'English', int(item.recovery_event_id))
        baseline_ids.extend(evidence['evidence_event_ids'])
    return dict(recovery_event_id=int(recovery_id), team=row.team, baseline_as_of_event_id=int(events.iloc[position].event_id),
                previous_recoveries=len(history), previous_shot_outcomes=len(shot), previous_closed_without_shot=len(closed),
                previous_unresolved=len(pending), preceding_no_shot_streak=streak,
                first_shot_after_no_shot_history=bool(row.status == 'Shot observed' and len(shot) == 0 and len(closed) > 0 and len(pending) == 0),
                previous_shot_timing_sample=len(shot), previous_shot_median_seconds=median,
                current_seconds=None if pd.isna(row.seconds_to_shot) else int(row.seconds_to_shot),
                baseline_evidence_event_ids=sorted(set(baseline_ids)))


def context_explanation(context, language='English', analyst=False):
    if not context:
        return ''
    c = context
    spanish = language == 'Español'
    if c['first_shot_after_no_shot_history']:
        message = (f"Es la primera recuperación de {c['team']} que llega a un remate en la muestra, tras {c['previous_closed_without_shot']} recuperaciones anteriores cerradas sin remate." if spanish else
                   f"This is {c['team']}'s first recovery to reach a shot in this sample, following {c['previous_closed_without_shot']} earlier recoveries closed without a shot.")
    elif c['previous_recoveries'] == 0:
        message = ('No hay recuperaciones anteriores de este equipo para comparar.' if spanish else 'There are no earlier recoveries for this team to compare with.')
    else:
        message = (f"Antes de esta recuperación: {c['previous_shot_outcomes']} con remate, {c['previous_closed_without_shot']} cerradas sin remate y {c['previous_unresolved']} pendientes." if spanish else
                   f"Before this recovery: {c['previous_shot_outcomes']} reached a shot, {c['previous_closed_without_shot']} closed without a shot, and {c['previous_unresolved']} remained unresolved.")
    if c['current_seconds'] is not None:
        if c['previous_shot_median_seconds'] is not None:
            median = f"{c['previous_shot_median_seconds']:g}"
            message += (f" Intervalo actual: {c['current_seconds']} s; mediana de los {c['previous_shot_timing_sample']} intervalos anteriores: {median} s." if spanish else
                        f" Current interval: {c['current_seconds']}s; median of {c['previous_shot_timing_sample']} earlier shot intervals: {median}s.")
        elif analyst:
            message += (' Se requieren al menos tres intervalos anteriores para mostrar la mediana.' if spanish else
                        'At least three earlier shot intervals are required to display a median.')
    return message


def contextual_candidates(events, favorite):
    """Transparent editorial suggestions, not a learned ranking or autonomous agent."""
    rows = summarize_recoveries(events)
    if favorite != 'Both teams':
        rows = rows[rows.team == favorite]
    candidates = []
    for row in rows.itertuples():
        context = recovery_context(events, int(row.recovery_event_id))
        if context['first_shot_after_no_shot_history']:
            priority, reason = 3, 'First shot-producing recovery after earlier no-shot outcomes'
        elif row.status == 'Shot observed':
            priority, reason = 2, 'Recorded shooting outcome'
        elif row.status == 'No shot recorded before possession changed':
            priority, reason = 1, 'Resolved without a recorded shot'
        else:
            priority, reason = 0, 'Outcome is still developing'
        candidates.append(dict(recovery_id=int(row.recovery_event_id), team=row.team, priority=priority, reason=reason))
    return sorted(candidates, key=lambda x: (x['priority'], x['recovery_id']), reverse=True)
