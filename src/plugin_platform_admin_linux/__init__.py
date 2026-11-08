"""Linux administration for Liminal (the user, 2026-11-07: "a windows and linux admin plugin for platform"): on a
Linux machine or in a WSL distribution (ADMIN_LINUX_TARGET: local, wsl or wsl:<distribution>), through the
library's machines.linux.Shell: whether the platform has root's rights and how they are had (root; sudo
without a password; WSL's root); the services the framework relies on (Docker and containerd, the firewall,
DNS), started when stopped, under systemd or OpenRC or the service command, and the SSH server shown but never
started on its own; the framework's startups as systemd user units (liminal-charts, liminal-integrator,
liminal-login, liminal-platform), read, run, ended, made or removed when asked (made only on this machine:
the apps do not run in WSL); the framework's processes running. The library's Admin base holds the checks,
the status and the setup.

    python -m plugin_platform_admin_linux status | setup [STEP ...] | services | startups | processes
                                          | service NAME start|stop|restart | startup APP run|end|enable|disable
                                          | register APP | unregister APP | run [--elevated] -- COMMAND
"""
from __future__ import annotations

import os
import re
import shlex
from pathlib import Path

from liminal_libs.machines.admin import Admin, AdminError, Startup, SystemService, app_of
from liminal_libs.machines.linux import Shell
from liminal_libs.machines.plugin import CommandError

__version__ = "0.2.0"
TARGET_VAR = "ADMIN_LINUX_TARGET"
UNITS = {"charts": "liminal-charts", "integrator": "liminal-integrator", "login": "liminal-login", "platform": "liminal-platform"}
TASK_VERBS = {"run": "start", "end": "stop", "enable": "enable", "disable": "disable"}
RESTART_SECONDS = 10


def blocks(text: str) -> dict[str, dict[str, str]]:
    """`== name` headed blocks of Key=Value lines (systemctl show), by name."""
    out: dict[str, dict[str, str]] = {}
    current = None
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("== "):
            current = line[3:].strip()
            out[current] = {}
        elif current is not None and "=" in line:
            k, _, v = line.partition("=")
            out[current][k] = v
    return out


def state_of(fields: dict) -> str:
    """A unit's state in the framework's words: absent when systemd knows none of that name."""
    if not fields or fields.get("LoadState") in ("not-found", "") or fields.get("LoadState", "").startswith("error"):
        return "absent"
    active = fields.get("ActiveState", "")
    return "running" if active == "active" else ("stopped" if active in ("inactive", "failed", "deactivating") else active or "unknown")


def unit_text(app: str, command: list[str]) -> str:
    """A user unit starting `app` for good, as the integrator's own unit does."""
    return ("[Unit]\n"
            f"Description=The Liminal {app} app (made by the Liminal platform)\n"
            "After=network-online.target\n\n"
            "[Service]\n"
            f"ExecStart={' '.join(shlex.quote(c) for c in command)}\n"
            "Restart=on-failure\n"
            f"RestartSec={RESTART_SECONDS}\n"
            "KillSignal=SIGINT\n\n"
            "[Install]\n"
            "WantedBy=default.target\n")


class LinuxAdminPlugin(Admin):
    name = "admin-linux"
    title = "Linux administration"
    about = ("A Linux machine for the framework: root's rights and how they are had, the services it relies on, the apps' "
             "systemd user units, the framework's processes")
    api = "2.1"
    order = 721
    SERVICES = (("docker", "Docker Engine", "the containers", True),
                ("containerd", "containerd", "Docker's runtime", True),
                ("ufw", "Uncomplicated Firewall", "the firewall plugin", True),
                ("firewalld", "firewalld", "the firewall plugin", True),
                ("systemd-resolved", "systemd's DNS resolver", "every lookup: the mail record, the feeds", True),
                ("ssh", "OpenSSH server", "remote access (shown; never started by the setup)", False),
                ("sshd", "OpenSSH server", "remote access (shown; never started by the setup)", False))

    def __init__(self, shell: Shell | None = None, runner=None, home: Path | None = None):
        self._shell = shell
        self._runner = runner
        self._home = home

    @property
    def options(self) -> tuple[str, ...]:
        return (TARGET_VAR,)

    @property
    def shell(self) -> Shell:
        return self._shell if self._shell is not None else Shell(os.environ.get(TARGET_VAR), runner=self._runner)

    def present(self) -> bool:
        try:
            return self.shell.here
        except CommandError:
            return False

    def elevated(self) -> bool:
        return self.shell.root()

    def elevation(self) -> str:
        sh = self.shell
        if sh.target != "local":
            return f"root in {sh.where} through wsl -u root"
        if sh.root():
            return "the platform runs as root"
        try:
            sh.run("true")  # sudo -n true
            return "not root; sudo without a password"
        except CommandError:
            return "not root, and sudo asks for a password: run the platform as root, or allow it sudo without one"

    def _init(self) -> str:
        """systemd, OpenRC or the service command, as the target has."""
        out = self.shell.sh("if [ -d /run/systemd/system ]; then echo systemd; elif command -v rc-service >/dev/null 2>&1; "
                            "then echo openrc; else echo service; fi", root=False).strip().splitlines()
        return out[-1].strip() if out else "service"

    def services(self) -> list[SystemService]:
        names = [s[0] for s in self.SERVICES]
        init = self._init()
        if init == "systemd":
            script = "; ".join(f"echo '== {n}'; systemctl show -p LoadState,ActiveState,UnitFileState,Description {n}.service" for n in names)
            found = blocks(self.shell.sh(script, root=False))
            return [SystemService(n, found.get(n, {}).get("Description") or title, state_of(found.get(n, {})),
                                  found.get(n, {}).get("UnitFileState", ""), used, may) for n, title, used, may in self.SERVICES]
        probe = "rc-service" if init == "openrc" else "service"
        script = "; ".join(f"{probe} {n} status >/dev/null 2>&1; echo '{n} '$?" for n in names)
        codes = dict(line.split() for line in self.shell.sh(script).splitlines() if len(line.split()) == 2)
        out = []
        for n, title, used, may in self.SERVICES:
            code = codes.get(n, "")
            state = "running" if code == "0" else "stopped" if code == "3" else "absent"
            out.append(SystemService(n, title, state, "", used, may))
        return out

    def _service_action(self, name: str, action: str) -> None:
        init = self._init()
        if init == "systemd":
            self.shell.run("systemctl", action, name)
        elif init == "openrc":
            self.shell.run("rc-service", name, action)
        else:
            self.shell.run("service", name, action)

    def startups(self) -> list[Startup]:
        script = "; ".join(f"echo '== {u}'; systemctl --user show -p LoadState,ActiveState,UnitFileState,ExecStart {u}.service"
                           for u in UNITS.values())
        try:
            found = blocks(self.shell.sh(script, root=False))
        except CommandError as e:
            return [Startup(app, unit, "unknown", detail=f"systemd's user units cannot be read: {e}") for app, unit in UNITS.items()]
        out = []
        for app, unit in UNITS.items():
            f = found.get(unit, {})
            state = state_of(f)
            if state not in ("absent", "running") and f.get("UnitFileState") == "disabled":
                state = "disabled"
            elif state == "stopped":
                state = "ready"
            m = re.search(r"argv\[\]=([^;]*)", f.get("ExecStart", ""))
            out.append(Startup(app, f"{unit}.service", state, (m.group(1).strip() if m else ""), f"enabled: {f.get('UnitFileState', '')}"))
        return out

    def _startup_action(self, app: str, action: str) -> None:
        self.shell.run("systemctl", "--user", TASK_VERBS[action], f"{UNITS[app]}.service", root=False)

    def unit_path(self, app: str) -> Path:
        return (self._home or Path.home()) / ".config" / "systemd" / "user" / f"{UNITS[app]}.service"

    def _register(self, app: str, command: list[str]) -> None:
        if self.shell.target != "local":
            raise AdminError(f"the framework's apps run on this machine, not in {self.shell.where}: a unit there would start nothing")
        path = self.unit_path(app)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(unit_text(app, command), encoding="utf-8")
        self.shell.run("systemctl", "--user", "daemon-reload", root=False)
        self.shell.run("systemctl", "--user", "enable", f"{UNITS[app]}.service", root=False)

    def _unregister(self, app: str) -> bool:
        path = self.unit_path(app)
        existed = path.exists()
        self.shell.run("systemctl", "--user", "disable", "--now", f"{UNITS[app]}.service", root=False, check=False)
        if existed:
            path.unlink()
        self.shell.run("systemctl", "--user", "daemon-reload", root=False, check=False)
        return existed

    def processes(self) -> list[dict]:
        out = []
        for line in self.shell.run("ps", "-eo", "pid=,rss=,args=", root=False).splitlines():
            parts = line.split(None, 2)
            if len(parts) == 3 and parts[0].isdecimal() and "liminal_" in parts[2] and "ps -eo" not in parts[2]:
                out.append({"pid": int(parts[0]), "app": app_of(parts[2]), "command": parts[2],
                            "memoryMb": round(int(parts[1]) / 1024) if parts[1].isdecimal() else 0})
        return out

    def run(self, *command: str, elevated: bool = False, **options) -> str:
        """A command on the target, its output; `elevated`: as root."""
        return self.shell.run(*command, root=elevated)


MACHINE = LinuxAdminPlugin()
