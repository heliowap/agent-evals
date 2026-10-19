from contextlib import suppress
import json
import os
from pathlib import Path
import signal
import subprocess
import tempfile
import time


IMAGE_TAG = "opencode-code-workspace:node24.9.0-ts5.9.3"
NODE_VERSION = "v24.9.0"
TSC_VERSION = "Version 5.9.3"


def engine_endpoint(docker="docker"):
    if os.environ.get("DOCKER_HOST"):
        endpoint = os.environ["DOCKER_HOST"]
    else:
        current = docker_command([docker, "context", "show"]).strip()
        endpoint = json.loads(docker_command([docker, "context", "inspect", current]))[0]["Endpoints"]["docker"]["Host"]
    if not endpoint.startswith("unix://"):
        raise ValueError("This isolation protocol requires a local Unix Docker endpoint")
    return endpoint


def docker_command(argv, timeout=30):
    process = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
    if process.returncode:
        raise RuntimeError(f"Docker operation failed ({argv[1]}): {process.stderr[-1600:].strip()}")
    return process.stdout


def image_info(docker="docker", image=IMAGE_TAG, build=False):
    if build:
        docker_command([docker, "build", "--pull", "--tag", image, str(Path(__file__).parent)], timeout=600)
    info = json.loads(docker_command([docker, "image", "inspect", image]))[0]
    if not info["Id"].startswith("sha256:"):
        raise ValueError("Docker image needs an immutable content ID")
    return {"id": info["Id"], "tag": image, "architecture": info["Architecture"], "os": info["Os"],
            "repo_digests": info.get("RepoDigests", [])}


class CodeContainer:
    def __init__(self, work, image, docker="docker", readonly=False):
        self.work = work.resolve()
        self.image = image
        self.docker = docker
        self.readonly = readonly
        self.id = None

    def __enter__(self):
        if "," in str(self.work):
            raise ValueError("Workspace path cannot contain a comma")
        if self.readonly:
            (self.work / ".build").mkdir(exist_ok=True)
        mount = f"type=bind,src={self.work},dst=/workspace" + (",readonly" if self.readonly else "")
        argv = [self.docker, "run", "--detach", "--network", "none", "--read-only", "--cap-drop", "ALL",
                "--security-opt", "no-new-privileges", "--pids-limit", "128", "--memory", "1g", "--cpus", "2",
                "--user", f"{os.getuid()}:{os.getgid()}", "--workdir", "/workspace", "--mount", mount,
                "--tmpfs", "/tmp:rw,nosuid,nodev,size=128m,mode=1777", "--env", "HOME=/tmp",
                "--env", "PYTHONPATH=/workspace", "--env", "PYTHONDONTWRITEBYTECODE=1"]
        if self.readonly:
            argv += ["--tmpfs", "/workspace/.build:rw,nosuid,nodev,size=128m,mode=1777"]
        argv += [self.image, "sleep", "infinity"]
        self.id = docker_command(argv).strip()
        if not self.id or not all(c in "0123456789abcdef" for c in self.id):
            raise ValueError("Docker did not return a container identity")
        try:
            self.inspect()
        except BaseException:
            self.__exit__(None, None, None)
            raise
        return self

    def inspect(self):
        info = json.loads(docker_command([self.docker, "inspect", self.id]))[0]
        host = info["HostConfig"]
        binds = [m for m in info["Mounts"] if m["Type"] == "bind"]
        good = (host["NetworkMode"] == "none" and host["ReadonlyRootfs"] and not host["Privileged"]
                and "ALL" in host["CapDrop"] and "no-new-privileges" in host["SecurityOpt"]
                and host["PidsLimit"] == 128 and host["Memory"] == 1_073_741_824
                and host["NanoCpus"] == 2_000_000_000 and len(binds) == 1
                and binds[0]["Source"] == str(self.work) and binds[0]["Destination"] == "/workspace"
                and binds[0]["RW"] is (not self.readonly)
                and info["Config"]["User"] == f"{os.getuid()}:{os.getgid()}")
        good = good and (not self.image.startswith("sha256:") or info["Image"] == self.image)
        if not good:
            raise ValueError("Container isolation settings differ from the frozen policy")
        return {"id": info["Id"], "image": info["Image"], "network": "none", "binds": binds,
                "readonly_root": True, "uid": info["Config"]["User"], "pids": 128, "memory": host["Memory"]}

    def exec_argv(self, argv, timeout=60):
        started = time.monotonic()
        process = subprocess.Popen([self.docker, "exec", "--workdir", "/workspace", self.id, *argv],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
        timed_out = False
        try:
            stdout, stderr = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            self.stop()
            os.killpg(process.pid, signal.SIGKILL)
            stdout, stderr = process.communicate()
        return {"passed": process.returncode == 0 and not timed_out, "exit_code": process.returncode,
                "timeout": timed_out, "stdout": stdout.decode(errors="replace")[-65536:],
                "stderr": stderr.decode(errors="replace")[-65536:], "wall_s": time.monotonic() - started}

    def stop(self):
        if self.id:
            state = json.loads(docker_command([self.docker, "inspect", self.id]))[0]["State"]
            if state["Running"]:
                try:
                    docker_command([self.docker, "kill", self.id], timeout=15)
                except RuntimeError:
                    state = json.loads(docker_command([self.docker, "inspect", self.id]))[0]["State"]
                    if state["Running"]:
                        raise
            state = json.loads(docker_command([self.docker, "inspect", self.id]))[0]["State"]
            if state["Running"]:
                raise ValueError("Container process tree is still running")
            return {"stopped": True, "state": state}

    def __exit__(self, *_):
        if self.id:
            with suppress(Exception):
                docker_command([self.docker, "rm", "--force", self.id], timeout=15)


def prove_isolation(image, docker="docker"):
    with tempfile.TemporaryDirectory(prefix="namespace-") as folder:
        root = Path(folder)
        work = root / "workspace"
        work.mkdir()
        sentinel = root / "operator-secret"
        sentinel.write_text("PRIVATE SENTINEL")
        (work / "escape").symlink_to(sentinel)
        proof = r'''import os, pathlib, socket, subprocess
p = pathlib.Path('/workspace')
assert not pathlib.Path('/var/run/docker.sock').exists()
assert not pathlib.Path('/root/.local/share/opencode/opencode.db').exists()
assert 'CLIPROXY_API_KEY' not in os.environ and 'OPENCODE_PASSWORD' not in os.environ
try:
    (p/'escape').read_text()
except (OSError, FileNotFoundError):
    pass
else:
    raise AssertionError('Symlink exposed operator files')
try:
    pathlib.Path('/etc/proof').write_text('x')
except OSError:
    pass
else:
    raise AssertionError('Container root is writable')
s = socket.socket()
s.settimeout(.5)
try:
    s.connect(('1.1.1.1', 443))
except OSError:
    pass
else:
    raise AssertionError('External network is reachable')
finally:
    s.close()
(p/'written.txt').write_text('workspace writable')
assert (p/'written.txt').read_text() == 'workspace writable'
'''
        with CodeContainer(work, image, docker) as container:
            inspected = container.inspect()
            result = container.exec_argv(["python3", "-B", "-c", proof])
            versions = {name: container.exec_argv(command) for name, command in {
                "node": ["node", "--version"], "typescript": ["tsc", "--version"], "python": ["python3", "--version"]}.items()}
            if not result["passed"] or any(not v["passed"] for v in versions.values()):
                raise ValueError("Namespace or toolchain proof failed")
            if versions["node"]["stdout"].strip() != NODE_VERSION or versions["typescript"]["stdout"].strip() != TSC_VERSION:
                raise ValueError("Container toolchain differs from the pinned versions")
            background = container.exec_argv(["sh", "-c", "sleep 90 >/dev/null 2>&1 & echo $! > /workspace/background.pid"])
            if not background["passed"]:
                raise ValueError("Could not start subprocess cancellation proof")
            container.stop()
            state = json.loads(docker_command([docker, "inspect", container.id]))[0]["State"]
            if state["Running"]:
                raise ValueError("Container cancellation left processes running")
        if sentinel.read_text() != "PRIVATE SENTINEL" or (work / "written.txt").read_text() != "workspace writable":
            raise ValueError("Isolation proof changed operator sentinel or lost patch")
        return {"passed": True, "inspection": inspected, "namespace": result, "versions": versions,
                "subprocesses_stopped": True, "workspace_preserved": True}
