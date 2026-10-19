"""Evidence that a pipeline stage ran: each stage's own script appends a record to a log, so proof of a run
doesn't depend on anyone's summary of it afterwards.

    with evidence.logged(book, "7 audio prep", inputs=chapters) as run:
        ...                       # do the work
        run.outputs += scripts    # files written
        run.facts["chapters"] = len(scripts)

Appends one JSON line to BOOK/pipeline.log.jsonl: time, stage, script and args, sha1 of every input and output
(paths relative to BOOK), ok, and facts. A run that raises is logged with ok: false and the error, then re-raised.
The log is append-only and committed with the book. verify.py reads it, together with the artefacts themselves.

Generic: nothing here knows about books or audio. To reuse it on another pipeline, copy this file, call
`logged()` from each stage's script, and write a small checker like verify.py with that pipeline's stage list.
"""
import hashlib
import json
import sys
import time
from contextlib import contextmanager
from pathlib import Path

LOG = "pipeline.log.jsonl"
STATES = ["PASS", "MANUAL", "UNLOGGED", "STALE", "MISSING", "FAIL"]   # best to worst


def sha1(path):
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def hashes(root, paths):
    root = Path(root).resolve()
    out = {}
    for p in paths:
        p = Path(p).resolve()
        if p.is_file():
            out[str(p.relative_to(root)) if p.is_relative_to(root) else str(p)] = sha1(p)
    return out


def log(root, stage, inputs=(), outputs=(), ok=True, **facts):
    """inputs: paths, or a {path: sha1} dict already hashed (e.g. when the run started)."""
    rec = {"time": time.strftime("%Y-%m-%dT%H:%M:%S"), "stage": stage, "script": Path(sys.argv[0]).name,
           "args": sys.argv[1:], "ok": ok, "inputs": inputs if isinstance(inputs, dict) else hashes(root, inputs),
           "outputs": hashes(root, outputs), **facts}
    with open(Path(root) / LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


class Run:
    def __init__(self):
        self.outputs, self.facts = [], {}


@contextmanager
def logged(root, stage, inputs=()):
    """Log a stage run when the block ends: ok if it finished, ok: false with the error if it raised."""
    run, before = Run(), hashes(root, inputs)   # inputs as they were when the run started
    try:
        yield run
    except BaseException as e:
        log(root, stage, before, run.outputs, ok=False, error=f"{type(e).__name__}: {e}", **run.facts)
        raise
    log(root, stage, before, run.outputs, ok=True, **run.facts)


def records(root, stage=None):
    p = Path(root) / LOG
    if not p.exists():
        return []
    recs = [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]
    return [r for r in recs if stage is None or r["stage"] == stage]


def last(root, stage, ok=None):
    recs = [r for r in records(root, stage) if ok is None or r["ok"] == ok]
    return recs[-1] if recs else None


def report(rows, title=""):
    """rows: [(stage, state, detail)] -> printed table; returns the worst state."""
    if title:
        print(title)
    w = max(len(s) for s, _, _ in rows)
    for stage, state, detail in rows:
        print(f"  {stage:<{w}}  {state:<8}  {detail}")
    return max((st for _, st, _ in rows), key=STATES.index)
