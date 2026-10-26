"""Inspect or reversibly reduce a CACHED Phi-4-mini context. Never downloads weights.

Stop Streamlit first. Read-only by default; --apply creates a backup; --restore
restores that backup. This is a local workaround, not a guaranteed upstream fix.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil


def bounded_config(data, limit):
    if not isinstance(data.get('model'),dict) or not isinstance(data.get('search',{}),dict):
        raise ValueError('Unrecognized model config structure')
    current = data['model'].get('context_length')
    if type(current) is not int or current < 1:
        raise ValueError('Missing positive model.context_length')
    if not 512 <= limit <= current:
        raise ValueError('Limit must be at least 512 and must not increase the context')
    copy = json.loads(json.dumps(data))
    copy['model']['context_length'] = limit
    copy.setdefault('search', {})['max_length'] = limit
    return copy


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--apply', action='store_true')
    group.add_argument('--restore', action='store_true')
    parser.add_argument('--limit', type=int, default=4096)
    args = parser.parse_args()
    from foundry_local_sdk import Configuration, FoundryLocalManager
    FoundryLocalManager.initialize(Configuration(app_name='matchlens-context-inspection'))
    manager = FoundryLocalManager.instance
    if manager.catalog.get_loaded_models():
        raise SystemExit('Stop Streamlit and unload local models before inspecting/applying this workaround.')
    candidates = [m for m in manager.catalog.get_cached_models() if 'phi-4-mini' in (m.alias+' '+m.id).lower()]
    if len(candidates) != 1:
        raise SystemExit(f'Expected exactly one cached Phi-4-mini variant; found {len(candidates)}. No files changed.')
    model = candidates[0]
    path = Path(model.get_path())/'genai_config.json'
    backup = path.with_name('genai_config.matchlens-backup.json')
    data = json.loads(path.read_text(encoding='utf-8'))
    print(json.dumps({'model_id':model.id,'config':str(path),'context_length':data.get('model',{}).get('context_length'),
                      'search_max_length':data.get('search',{}).get('max_length'),'backup_exists':backup.exists()},indent=2))
    if args.restore:
        if not backup.exists(): raise SystemExit('No MatchLens backup exists. Nothing restored.')
        json.loads(backup.read_text(encoding='utf-8'))
        shutil.copy2(backup,path)
        print('Original configuration restored. Restart the app before loading the model.')
    elif args.apply:
        changed = bounded_config(data,args.limit)
        if not backup.exists(): shutil.copy2(path,backup)
        temp=path.with_suffix('.matchlens-tmp')
        temp.write_text(json.dumps(changed,indent=2),encoding='utf-8');temp.replace(path)
        print(f'Context reduced to {args.limit}. Original backed up. Restart app; hardware inference still needs verification.')
    else:
        print('Inspection only. To apply the backed-up workaround, run with --apply. To undo, run --restore.')


if __name__ == '__main__': main()
