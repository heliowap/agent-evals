import json
import os
import signal
import subprocess
import time

import runtime


def complete_lines(path):
    if not path.exists():
        return []
    text = path.read_text()
    return [json.loads(line) for line in text[:text.rfind("\n") + 1].splitlines() if line.strip()]


def limit_reason(elapsed, calls, budget):
    if elapsed >= budget.seconds:
        return "time"
    if calls >= budget.calls:
        return "calls"
    return None


def invoke(candidate, work, root, binary, env, container, budget):
    result = {"reason": None, "interrupt": None, "hard_kill": False, "container_stopped": False}
    with runtime.local_server(binary, work, env) as server:
        session = runtime.api(binary, work, server, "session.create", data={
            "agent": runtime.AGENT, "model": candidate.identity,
            "location": {"directory": str(work)}, "title": "Project change",
        })["data"]
        session_id = session["id"]
        argv = [binary, "run", "--server", server["url"], "--session", session_id, "--auto", "--format", "json",
                "--agent", runtime.AGENT, "--model", candidate.selection, (root / "request.txt").read_text()]
        started = time.monotonic()
        with (root / "run.stdout.jsonl").open("wb") as stdout, (root / "run.stderr").open("wb") as stderr:
            process = subprocess.Popen(argv, cwd=work, env=server["env"], stdin=subprocess.DEVNULL,
                                       stdout=stdout, stderr=stderr, start_new_session=True)
            try:
                while process.poll() is None:
                    events = complete_lines(root / "observations.jsonl")
                    calls = sum(event.get("event") == "request" and event.get("session_id") == session_id for event in events)
                    reason = limit_reason(time.monotonic() - started, calls, budget)
                    if reason:
                        result["reason"] = reason
                        try:
                            result["interrupt"] = runtime.api(binary, work, server, "session.interrupt",
                                                              {"sessionID": session_id}, timeout=5)
                        except Exception as error:
                            result["interrupt_error"] = str(error)
                        finally:
                            container.stop()
                            result["container_stopped"] = True
                        try:
                            process.wait(timeout=budget.grace)
                        except subprocess.TimeoutExpired:
                            result["hard_kill"] = True
                            os.killpg(process.pid, signal.SIGKILL)
                            process.wait()
                        break
                    time.sleep(.05)
            finally:
                if process.poll() is None:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
                result["execution_s"] = time.monotonic() - started
                if not result["container_stopped"]:
                    container.stop()
                    result["container_stopped"] = True
        final_events = complete_lines(root / "observations.jsonl")
        final_calls = sum(event.get("event") == "request" and event.get("session_id") == session_id for event in final_events)
        if result["reason"] is None and (result["execution_s"] > budget.seconds or final_calls > budget.calls):
            result["reason"] = "time" if result["execution_s"] > budget.seconds else "calls"
            result["late_limit_detected"] = True
        result["calls_at_exit"] = final_calls
        result.update(wall_s=time.monotonic() - started, exit_code=process.returncode, session_id=session_id)
        runtime.save(root / "control.json", result)
        export = runtime.api(binary, work, server, "experimental.session.export", {"sessionID": session_id})["data"]
        runtime.save(root / "session.json", export)
    return result, export
