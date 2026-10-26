"""Small synthetic conformance scenarios; authored semantics, randomized timing.

Expected results are assigned while constructing events, independently of the
analytics under test. These are published regression cases, not held-out research.
"""
import random
import pandas as pd


def scenario_suite():
    cases=[]
    for team in ['Riverside','Northbridge']:
        other='Northbridge' if team=='Riverside' else 'Riverside'
        for outcome in ['pending','closed','shot','rebound']:
            for pressure in ['linked','outside_window','absent']:
                seed=len(cases)+801
                rng=random.Random(seed)
                rows=[]; clock=0
                def emit(t,kind,result,pid,delay):
                    nonlocal clock
                    clock+=delay
                    rows.append(dict(event_id=len(rows)+1,time=f'{clock//60:02d}:{clock%60:02d}',team=t,
                                     player='Leo Grant' if t=='Riverside' else 'Sam Cole',
                                     event_type=kind,outcome=result,possession_id=pid))
                emit(other,'pass','completed',1,3)
                if pressure!='absent':emit(team,'pressure','applied',1,2)
                emit(other,'pass','failed',1,1)
                emit(team,'recovery','controlled',2,1 if pressure!='outside_window' else 6)
                recovery_id=len(rows); recovery_clock=clock
                emit(team,'pass','completed',2,rng.randint(2,5))
                expected={'recovery_id':recovery_id,'state':'developing','seconds_to_shot':None,'pressure_linked':pressure=='linked'}
                if outcome=='closed':
                    emit(team,'pass','failed',2,3)
                    emit(other,'recovery','controlled',3,1)
                    expected['state']='closed'
                    # Later unrelated shot must not be assigned to the first recovery.
                    emit(other,'shot','off_target',3,5)
                elif outcome in ['shot','rebound']:
                    emit(team,'shot','saved',2,rng.randint(3,8))
                    expected.update(state='shot',seconds_to_shot=clock-recovery_clock)
                    if outcome=='rebound':emit(team,'shot','off_target',2,2)
                cases.append(dict(name=f'{team}: {outcome}, pressure {pressure}',seed=seed,team=team,events=rows,expected=expected))
    return cases


def context_storyline():
    rows=[];clock=0;pid=0
    def emit(team,kind,outcome,delay=2):
        nonlocal clock
        clock+=delay
        rows.append(dict(event_id=len(rows)+1,time=f'{clock//60:02d}:{clock%60:02d}',team=team,
                         player='Leo Grant' if team=='Riverside' else 'Sam Cole',event_type=kind,outcome=outcome,possession_id=pid))
    for duration in [None,None,None,18,12,10,8]:
        pid+=1;emit('Northbridge','goal_kick','completed' if rows else 'completed')
        emit('Riverside','pressure','applied')
        emit('Northbridge','pass','failed',1)
        pid+=1;emit('Riverside','recovery','controlled',1)
        emit('Riverside','pass','completed',3)
        if duration is None:
            emit('Riverside','pass','failed',2)
            pid+=1;emit('Northbridge','recovery','controlled',1)
            emit('Northbridge','pass','completed',2)
            emit('Riverside','touch','out_of_play',1)  # Last touch beyond Northbridge goal line: goal kick.
        else:
            emit('Riverside','shot','off_target',duration-3)
    pid+=1;emit('Northbridge','goal_kick','completed',4)
    return pd.DataFrame(rows)
