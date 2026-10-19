import base64
import hashlib
import json
import shlex
import tarfile
import urllib.request
from pathlib import Path

from harbor.agents.installed.base import NonZeroAgentExitCodeError, with_prompt_template
from harbor.agents.installed.opencode import OpenCode

ROOT = Path(__file__).resolve().parent


def download_binary(arch):
    target = ROOT / "binaries" / arch / "opencode"
    if target.exists():
        return target
    package = f"@opencode/cli-linux-{arch}"
    with urllib.request.urlopen(f"https://registry.npmjs.org/{package}/2.0.24") as response:
        metadata = json.load(response)
    with urllib.request.urlopen(metadata["dist"]["tarball"]) as response:
        archive = response.read()
    expected = metadata["dist"]["integrity"].removeprefix("sha512-")
    actual = base64.b64encode(hashlib.sha512(archive).digest()).decode()
    if actual != expected:
        raise ValueError("OpenCode npm archive integrity mismatch")
    target.parent.mkdir(parents=True, exist_ok=True)
    archive_path = target.parent / "package.tgz"
    archive_path.write_bytes(archive)
    with tarfile.open(archive_path) as tar:
        source = tar.extractfile("package/bin/opencode")
        if source is None:
            raise ValueError("OpenCode binary missing from npm archive")
        target.write_bytes(source.read())
    target.chmod(0o755)
    (target.parent / "metadata.json").write_text(json.dumps({
        "package": package, "version": "2.0.24", "integrity": metadata["dist"]["integrity"],
        "binary_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
    }, indent=2) + "\n")
    return target


class OpenCodeV2(OpenCode):
    async def install(self, environment):
        await self.ensure_system_dependencies(environment, ("bash", "coreutils", "git", "curl"))
        result = await self.exec_as_agent(environment, command="uname -m")
        machine = result.stdout.strip()
        arch = {"x86_64": "x64", "aarch64": "arm64"}[machine]
        binary = download_binary(arch)
        await environment.upload_file(binary, "/tmp/tbeval-opencode")
        await self.exec_as_root(environment, command="install -m 755 /tmp/tbeval-opencode /usr/local/bin/opencode")
        result = await self.exec_as_agent(environment, command="opencode --version")
        if "2.0.24" not in result.stdout:
            raise RuntimeError("Unexpected OpenCode version")

    @with_prompt_template
    async def run(self, instruction, environment, context):
        self._instruction = instruction
        env = dict(self.model_connection.env)
        env.update({
            "OPENCODE_FAKE_VCS": "git",
            "XDG_DATA_HOME": (self.environment_logs_dir / "opencode" / "xdg-data").as_posix(),
            "XDG_STATE_HOME": (self.environment_logs_dir / "opencode" / "xdg-state").as_posix(),
        })
        await self.exec_as_agent(environment, command=self._build_register_config_command(), env=env)
        model = self.model_name + (f"#{self.options.variant}" if self.options.variant else "")
        output = shlex.quote((self.environment_logs_dir / self._OUTPUT_FILENAME).as_posix())
        result = await self.exec_as_agent(environment, command=(
            "set -o pipefail; opencode run --standalone --format json --thinking --auto "
            f"--model {shlex.quote(model)} -- {shlex.quote(instruction)} "
            f"2>&1 </dev/null | stdbuf -oL tee {output}"
        ), env=env)
        if result.return_code:
            raise NonZeroAgentExitCodeError(f"OpenCode exited {result.return_code}")
        if messages := self._error_messages():
            raise NonZeroAgentExitCodeError("OpenCode emitted errors: " + "; ".join(messages[:3]))
        events = self._parse_stdout()
        if not any(event.get("type") == "step_finish" for event in events):
            raise NonZeroAgentExitCodeError("No completed OpenCode steps in output")
