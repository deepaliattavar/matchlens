"""Small deterministic guards, not a general semantic fact checker."""
import json
import re


def parse_draft(raw):
    """Accept a JSON object or exactly one enclosing JSON code fence.

    Never extract an object from surrounding prose or repair its contents.
    The original model text remains in the generation audit.
    """
    if not isinstance(raw,str):raise ValueError('Expected text')
    text=raw.strip()
    match=re.fullmatch(r'```(?:json)?\s*\n?(.*?)\n?```',text,flags=re.S|re.I)
    if match:text=match.group(1).strip()
    def unique(pairs):
        out={}
        for key,value in pairs:
            if key in out:raise ValueError('Duplicate JSON key')
            out[key]=value
        return out
    return json.loads(text,object_pairs_hook=unique)


def claim_text(text):
    """Mask only specific uncertainty phrases, not arbitrary negated sentences."""
    return re.sub(r'\b(?:does not prove (?:that )?it caused|does not establish that it caused)\b','[uncertainty]',text.lower())


def pressure_gap(packet):
    story=packet['source_story']
    recovery=next((e for e in packet.get('evidence',[]) if e.get('event_id')==story.get('recovery_event_id')),None)
    if recovery is None:return None
    def seconds(e):
        if 'elapsed_seconds' in e:return int(e['elapsed_seconds'])
        minutes,secs=e['time'].split(':');return int(minutes)*60+int(secs)
    gaps=[seconds(recovery)-seconds(e) for e in packet.get('evidence',[])
          if e.get('event_type')=='pressure' and e.get('team')==recovery.get('team')
          and 0<=seconds(recovery)-seconds(e)<=5]
    return min(gaps) if gaps else None


def pressure_issues(text,packet):
    if not re.search(r'\b(?:pressure|presión)\b',text.lower()):return []
    # Check timing clauses that explicitly attach a duration to pressure.
    normalized=text.lower()
    for word,num in [('five','5'),('two','2'),('three','3'),('four','4'),('one','1'),('cinco','5'),('dos','2'),('tres','3'),('cuatro','4'),('uno','1')]:
        normalized=re.sub(r'\b'+word+r'\b',num,normalized)
    issues=[]
    for clause in re.split(r'[.;!?]',normalized):
        if not re.search(r'\b(?:pressure|presión)\b',clause):continue
        times=re.findall(r'\b(\d+)\s+(?:seconds?|segundos?)\b',clause)
        for number in times:
            window=bool(re.search(r'(?:within (?:the )?(?:preceding |previous |last )?|en los |dentro de los )'+number+r'\s+(?:seconds?|segundos?)',clause))
            if window:
                if int(number)!=5 or not packet['source_story'].get('pressure_linked'):
                    issues.append('Pressure window is unsupported by the recorded link.')
            else:
                gap=pressure_gap(packet)
                if gap is None or int(number)!=gap:
                    issues.append(f'Pressure timing does not match the evidence (observed gap: {gap if gap is not None else "unavailable"} seconds). Use within the preceding five seconds for reusable wording.')
    return list(dict.fromkeys(issues))
