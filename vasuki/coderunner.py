"""Run a player's Python solution against test cases in a separate process.

Safety model (good enough for a local practice app, NOT a hardened sandbox):
  * a fresh `python3 -I` subprocess per run (isolated mode: no site-packages,
    no cwd on sys.path, ignores PYTHON* env vars), started in an empty temp dir
  * CPU-time, memory and output-size limits (resource.setrlimit, POSIX only)
  * a wall-clock timeout on the parent side (the only limit on Windows)
  * a small import blocklist for os/sys/subprocess/socket/... inside the child

Do not expose this to untrusted users on the public internet without a real
sandbox (containers / seccomp / a judge service).
"""
import json
import os
import subprocess
import sys
import tempfile

from . import config

_HARNESS = r'''
import builtins, copy, json, sys, io

_BLOCKED = {"os", "sys", "subprocess", "socket", "shutil", "pathlib", "ctypes",
            "multiprocessing", "threading", "signal", "resource", "importlib",
            "builtins", "inspect", "gc", "pickle", "marshal", "urllib", "http",
            "requests", "asyncio", "pty", "fcntl", "tempfile", "glob", "io"}
_real_import = builtins.__import__
def _guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
    if name.split(".")[0] in _BLOCKED:
        raise ImportError("import of '%s' is not allowed here" % name)
    return _real_import(name, globals, locals, fromlist, level)

payload = json.loads(sys.stdin.read())
out = sys.stdout
safe_builtins = {k: getattr(builtins, k) for k in dir(builtins)
                 if k not in ("open", "exec", "eval", "compile", "input", "breakpoint",
                              "exit", "quit", "help", "__import__", "globals", "vars", "memoryview")}
safe_builtins["__import__"] = _guarded_import
sys.setrecursionlimit(5000)
ns = {"__builtins__": safe_builtins, "__name__": "solution"}

def emit(obj):
    out.write(json.dumps(obj))
    out.flush()

try:
    sys.stdout = io.StringIO()          # swallow the player's print()s
    exec(compile(payload["code"], "solution.py", "exec"), ns)
except BaseException as e:
    emit({"compile_error": "%s: %s" % (type(e).__name__, e)})
    raise SystemExit(0)

fn = ns.get(payload["func"])
if not callable(fn):
    emit({"compile_error": "Function '%s' was not defined." % payload["func"]})
    raise SystemExit(0)

def norm(v, unordered):
    if unordered and isinstance(v, (list, tuple)):
        try:
            return sorted((norm(x, False) for x in v), key=lambda x: json.dumps(x, sort_keys=True))
        except TypeError:
            return list(v)
    if isinstance(v, tuple):
        return [norm(x, False) for x in v]
    if isinstance(v, list):
        return [norm(x, False) for x in v]
    return v

results = []
unordered = payload["compare"] == "unordered"
for t in payload["tests"]:
    try:
        got = fn(*copy.deepcopy(t["args"]))
        try:
            json.dumps(got)
            shown = got
        except TypeError:
            shown = repr(got)
        ok = norm(got, unordered) == norm(t["expected"], unordered)
        results.append({"ok": ok, "got": shown})
    except RecursionError:
        results.append({"ok": False, "error": "RecursionError: maximum recursion depth exceeded"})
    except BaseException as e:
        results.append({"ok": False, "error": "%s: %s" % (type(e).__name__, e)})
emit({"results": results})
'''


def _limits():
    try:
        import resource
        cpu = int(config.CODE_TIME_LIMIT) + 1
        resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu))
        mem = 256 * 1024 * 1024
        for lim in ("RLIMIT_AS", "RLIMIT_DATA"):
            if hasattr(resource, lim):
                try:
                    resource.setrlimit(getattr(resource, lim), (mem, mem))
                except (ValueError, OSError):
                    pass
        resource.setrlimit(resource.RLIMIT_FSIZE, (1 << 20, 1 << 20))
    except Exception:
        pass


def _child_env():
    """Minimal environment for the child interpreter.

    POSIX gets a bare PATH. Windows can't start Python without SYSTEMROOT and
    friends, so keep just those (no user variables are passed through).
    """
    if os.name != "nt":
        return {"PATH": "/usr/bin:/bin"}
    keep = ("SYSTEMROOT", "SYSTEMDRIVE", "WINDIR", "TEMP", "TMP", "PATH", "PATHEXT", "COMSPEC")
    return {k: os.environ[k] for k in keep if k in os.environ}


def run(code: str, func: str, tests: list, compare: str = "exact") -> dict:
    """Return {"error": str} or {"results": [{"ok", "got"|"error"}, ...]}."""
    if len(code) > 20000:
        return {"error": "Code is too long (20k characters max)."}
    payload = json.dumps({"code": code, "func": func, "tests": tests, "compare": compare})
    with tempfile.TemporaryDirectory() as tmp:
        try:
            proc = subprocess.run(
                [sys.executable, "-I", "-S", "-c", _HARNESS],
                input=payload, capture_output=True, text=True, cwd=tmp,
                timeout=config.CODE_TIME_LIMIT + 3,
                env=_child_env(),
                preexec_fn=_limits if os.name == "posix" else None,
            )
        except subprocess.TimeoutExpired:
            return {"error": "Time limit exceeded — is there an infinite loop?"}
    if not proc.stdout.strip():
        if proc.returncode and proc.returncode < 0:
            return {"error": "Time or memory limit exceeded."}
        tail = (proc.stderr or "").strip().splitlines()[-1:] or ["no output"]
        return {"error": "Runtime crashed: " + tail[0][:300]}
    try:
        data = json.loads(proc.stdout)
    except ValueError:
        return {"error": "Unreadable output from the runner."}
    if "compile_error" in data:
        return {"error": data["compile_error"]}
    return data
