"""Optional local-only model process; no hosted API or cloud fallback."""
import json
import time
from pathlib import Path
from narration import ai_prompt
from ai_performance import compact_prompt, output_budget
LOCAL_MODELS = ("phi-4-mini", "qwen2.5-0.5b")

def local_ai_worker():
    """Keep model weights warm; use a fresh conversation for every request."""
    import sys
    from foundry_local_sdk import (
        ChatSession, Configuration, FoundryLocalManager,
        MessageItem, Request, RequestOptions, SearchOptions, TextItem, TextItemType,
    )
    FoundryLocalManager.initialize(Configuration(app_name='matchlens'))
    manager = FoundryLocalManager.instance
    model, active_alias = None, None
    try:
        for line in sys.stdin:
            payload = json.loads(line)
            destination = Path(payload['result_path'])
            alias = payload['model']
            status_path = Path(payload['status_path'])
            def status(stage):
                temp = status_path.with_suffix('.writing')
                temp.write_text(json.dumps({'stage': stage}), encoding='utf-8')
                temp.replace(status_path)
            start = time.perf_counter()
            try:
                if alias not in LOCAL_MODELS:
                    raise ValueError('Only local models in the allowlist are supported.')
                warm = model is not None and active_alias == alias
                if not warm:
                    if model is not None:
                        model.unload()
                        model = None
                    candidate = manager.catalog.get_model(alias)
                    if candidate is None:
                        raise RuntimeError(f'{alias} was not found in the local catalog.')
                    status('Checking / downloading model')
                    candidate.download()
                    status('Loading model into memory')
                    candidate.load()
                    model, active_alias = candidate, alias
                loaded = time.perf_counter()
                status('Generating draft')
                fragments = []
                packet = payload['packet']
                budget = output_budget(packet)
                prompt = packet.get('prompt') or (compact_prompt(packet) if packet.get('generation_profile', 'Quick draft') == 'Quick draft' else ai_prompt(packet))
                with ChatSession(model) as session:
                    session.set_options(RequestOptions(search=SearchOptions(
                        temperature=0.0, max_output_tokens=budget)))
                    with Request().add_item(MessageItem.user(prompt)) as request:
                        with session.process_request(request) as response:
                            for item in response:
                                if isinstance(item, MessageItem):
                                    fragments.extend(p.text for p in item.parts if isinstance(p, TextItem) and p.type == TextItemType.DEFAULT)
                                elif isinstance(item, TextItem) and item.type == TextItemType.DEFAULT:
                                    fragments.append(item.text)
                result = {'raw': ''.join(fragments), 'model': alias,
                          'model_id': str(model.id), 'warm_model': warm,
                          'generation_seconds': round(time.perf_counter()-loaded, 2),
                          'setup_seconds': round(loaded-start, 2),
                          'sdk_version': __import__('importlib.metadata', fromlist=['version']).version('foundry-local-sdk'),
                          'prompt': prompt, 'max_output_tokens': budget,
                          'generation_profile': packet.get('generation_profile', 'Quick draft'),
                          'prompt_characters': len(prompt)}
            except Exception as error:
                result = {'error': f'Local inference failed: {type(error).__name__}: {error}'}
            # Atomic file replacement prevents the parent reading partial JSON.
            temporary = destination.with_suffix('.writing')
            temporary.write_text(json.dumps(result, ensure_ascii=True), encoding='utf-8')
            temporary.replace(destination)
    finally:
        if model is not None:
            model.unload()


class LocalModelRunner:
    """Local process only: serialize requests, retain weights, enforce timeout."""
    def __init__(self):
        import threading
        import atexit
        self.lock = threading.Lock()
        self.cancel_event = threading.Event()
        self.status = {'stage': 'Idle'}
        self.process = None
        self.log = None
        self.active_model = None
        self.busy = False
        atexit.register(self.close)

    def cancel(self):
        # Request thread owns process cleanup; the UI never races close() against it.
        self.cancel_event.set()

    def close(self):
        process = self.process
        self.process = None
        self.active_model = None
        if process is not None:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except Exception:
                    process.kill()
                    process.wait()
            if process.stdin:
                process.stdin.close()
        if self.log is not None:
            self.log.close()
            self.log = None

    def request(self, alias, packet, timeout=600, generation_timeout=120):
        import subprocess
        import tempfile
        import sys
        with self.lock:
            self.busy = True
            self.cancel_event.clear()
            self.status = {'stage': 'Starting local runtime', 'started': time.monotonic()}
            generation_started = None
            start = time.perf_counter()
            try:
                if self.process is None or self.process.poll() is not None:
                    self.close()
                    self.log = tempfile.TemporaryFile(mode='w+b')
                    self.process = subprocess.Popen(
                        [sys.executable, str(Path(__file__).resolve()), '--worker'],
                        stdin=subprocess.PIPE, stdout=self.log, stderr=self.log,
                        text=True, encoding='utf-8',
                        creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
                    )
                with tempfile.TemporaryDirectory(prefix='matchlens-ai-') as folder:
                    result_path = Path(folder)/'result.json'
                    status_path = Path(folder)/'status.json'
                    payload = {'model': alias, 'packet': packet, 'result_path': str(result_path), 'status_path': str(status_path)}
                    self.process.stdin.write(json.dumps(payload, ensure_ascii=True)+'\n')
                    self.process.stdin.flush()
                    while not result_path.exists():
                        if self.cancel_event.is_set():
                            self.close()
                            return {'error': 'Local generation cancelled. Model process released; replay is unchanged.'}
                        if status_path.exists():
                            try:
                                stage = json.loads(status_path.read_text(encoding='utf-8'))['stage']
                                self.status['stage'] = stage
                                if stage == 'Generating draft' and generation_started is None:
                                    generation_started = time.perf_counter()
                            except (OSError, ValueError, KeyError):
                                pass
                        if generation_started is not None and time.perf_counter()-generation_started > generation_timeout:
                            self.close()
                            return {'error': f'Generation exceeded {generation_timeout}s and was stopped. Keep the rule-based story; try a smaller workload later.'}
                        if self.process.poll() is not None:
                            self.log.seek(0)
                            details = self.log.read().decode('utf-8', errors='replace')[-2500:]
                            self.close()
                            return {'error': 'The local model process stopped.', 'details': details}
                        if time.perf_counter()-start > timeout:
                            self.close()
                            return {'error': 'Local request timed out and was stopped. No cloud fallback was used.'}
                        time.sleep(0.1)  # Runs in a worker thread, never the Streamlit UI.
                    result = json.loads(result_path.read_text(encoding='utf-8'))
                result['total_seconds'] = round(time.perf_counter()-start, 2)
                result['prepared_at_event'] = packet['source_story']['as_of_event_id']
                if 'error' not in result:
                    self.active_model = alias
                return result
            except Exception as error:
                self.close()
                return {'error': f'Local AI unavailable: {type(error).__name__}: {error}'}
            finally:
                self.busy = False
                self.status = {'stage': 'Idle'}


if __name__ == "__main__":
    local_ai_worker()
