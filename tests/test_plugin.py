"""Linux administration: the rights and how they are had, the framework's services under systemd or OpenRC
(started when stopped, never the SSH server), the apps' systemd user units read, run, made and removed, the
processes; the platform's boot service (0.5.0) as a system unit or an OpenRC service, written as root through sudo -n,
started, stopped and removed (asked twice), never as root; all through a stand-in for the commands (nothing runs here,
nothing is written to /etc: the stand-in keeps the files); only on a native Linux machine: on Windows, macOS or in a WSL
distribution nothing runs at all."""
from __future__ import annotations

import inspect
import json
import re
import sys

import pytest

from liminal_libs.machines.admin import ACCEPT_REMOVAL, PLATFORM_APP, AdminError, BootApp, BootRefused, RemovalRefused
from liminal_libs.machines.linux import Shell
from liminal_libs.machines import linux as linux_mod

import plugin_platform_admin_linux.__main__ as cli
from plugin_platform_admin_linux import (MACHINE, UNITS, LinuxAdminPlugin, app_of_unit, blocks, boot_service, boot_unit,
                                         boot_unit_text, openrc_text, root_write, state_of, unit_text, unit_word, why_not_native)

SYSTEMD_SHOW = {
    "docker": "LoadState=loaded\nActiveState=inactive\nUnitFileState=enabled\nDescription=Docker Application Container Engine\n",
    "containerd": "LoadState=loaded\nActiveState=active\nUnitFileState=enabled\nDescription=containerd container runtime\n",
    "ufw": "LoadState=loaded\nActiveState=active\nUnitFileState=enabled\nDescription=Uncomplicated firewall\n",
    "firewalld": "LoadState=not-found\nActiveState=inactive\nUnitFileState=\nDescription=firewalld.service\n",
    "systemd-resolved": "LoadState=loaded\nActiveState=active\nUnitFileState=enabled\nDescription=Network Name Resolution\n",
    "ssh": "LoadState=loaded\nActiveState=inactive\nUnitFileState=disabled\nDescription=OpenBSD Secure Shell server\n",
    "sshd": "LoadState=not-found\nActiveState=inactive\nUnitFileState=\nDescription=sshd.service\n",
}


class FakeLinux:
    def __init__(self, init="systemd", sudo_ok=True, units=None):
        self.init = init
        self.sudo_ok = sudo_ok
        self.units = dict(units or {"liminal-integrator": ("active", "enabled", "/usr/bin/python3 -m liminal_integrator service run --daemon")})
        self.calls: list[list[str]] = []
        self.started: list[str] = []

    def __call__(self, args, timeout):
        self.calls.append(list(args))
        cmd = args[args.index("--exec") + 1:] if "--exec" in args else (args[2:] if args[:2] == ["sudo", "-n"] else args)
        if cmd[:2] == ["sh", "-c"] and "/run/systemd/system" in cmd[2]:
            return 0, self.init + "\n", ""
        if cmd[:2] == ["sh", "-c"] and "systemctl show" in cmd[2] and "--user" not in cmd[2]:
            return 0, "".join(f"== {n}\n{SYSTEMD_SHOW[n]}" for n in SYSTEMD_SHOW), ""
        if cmd[:2] == ["sh", "-c"] and "systemctl --user show" in cmd[2]:
            out = []
            for unit in UNITS.values():
                if unit in self.units:
                    active, enabled, exe = self.units[unit]
                    out.append(f"== {unit}\nLoadState=loaded\nActiveState={active}\nUnitFileState={enabled}\n"
                               f"ExecStart={{ path={exe.split()[0]} ; argv[]={exe} ; ignore_errors=no }}\n")
                else:
                    out.append(f"== {unit}\nLoadState=not-found\nActiveState=inactive\nUnitFileState=\nExecStart=\n")
            return 0, "".join(out), ""
        if cmd[:2] == ["sh", "-c"] and " status >/dev/null" in cmd[2]:
            return 0, "docker 3\ncontainerd 0\nufw 0\nfirewalld 1\nsystemd-resolved 1\nssh 3\nsshd 1\n", ""
        if cmd == ["true"]:
            return (0, "", "") if self.sudo_ok else (1, "", "sudo: a password is required\n")
        if cmd[:1] in (["systemctl"], ["rc-service"], ["service"]):
            if "--user" not in cmd:
                self.started.append(" ".join(cmd))
            return 0, "", ""
        if cmd[:2] == ["ps", "-eo"]:
            return 0, ("    1  1200 /sbin/init\n 4242 524288 /usr/bin/python3 -m liminal_charts gui --no-browser --port 8765\n"
                       " 4300   2048 ps -eo pid=,rss=,args=\n"), ""
        return 0, "ran\n", ""


class BootLinux(FakeLinux):
    """A native Linux machine whose boot services are kept in memory: what the root scripts write is kept here, never in
    /etc; the units' and services' states answered as systemctl and OpenRC would."""

    def __init__(self, init="systemd", **kw):
        super().__init__(init=init, **kw)
        self.files: dict[str, str] = {}  # /etc/... -> its text
        self.modes: dict[str, str] = {}
        self.active: dict[str, str] = {}  # unit or service -> active | inactive
        self.enabled: set[str] = set()
        self.root_scripts: list[str] = []

    def _read_systemd(self, script):
        names = script.split("for u in ", 1)[1].split(" $(", 1)[0].split()
        names += [p.rsplit("/", 1)[1] for p in self.files if p.startswith("/etc/systemd/system/")]
        out = []
        for n in dict.fromkeys(names):
            text = self.files.get(f"/etc/systemd/system/{n}")
            if text is None:
                out.append(f"== {n}\nLoadState=not-found\nActiveState=inactive\nSubState=dead\nUnitFileState=\nExecStart=\nUser=\n")
                continue
            exe = re.search(r"^ExecStart=(.*)$", text, re.M).group(1)
            user = re.search(r"^User=(.*)$", text, re.M).group(1)
            out.append(f"== {n}\nLoadState=loaded\nActiveState={self.active.get(n, 'inactive')}\nSubState=running\n"
                       f"UnitFileState={'enabled' if n in self.enabled else 'disabled'}\n"
                       f"ExecStart={{ path={exe.split()[0]} ; argv[]={exe} ; ignore_errors=no ; start_time=[n/a] }}\nUser={user}\n")
        return "".join(out)

    def _read_openrc(self, script):
        names = script.split("for n in ", 1)[1].split(" $(", 1)[0].split()
        names += [p.rsplit("/", 1)[1] for p in self.files if p.startswith("/etc/init.d/")]
        out = []
        for n in dict.fromkeys(names):
            text = self.files.get(f"/etc/init.d/{n}")
            if text is None:
                out.append(f"== {n}\nFile=no\n")
                continue
            kept = "\n".join(line for line in text.splitlines() if re.match(r"(command|command_args|command_user|error_log)=", line))
            out.append(f"== {n}\nFile=yes\n{kept}\nStatus={0 if self.active.get(n) == 'active' else 3}\n"
                       f"Default={'yes' if n in self.enabled else 'no'}\n")
        return "".join(out)

    def __call__(self, args, timeout):
        cmd = args[args.index("--exec") + 1:] if "--exec" in args else (args[2:] if args[:2] == ["sudo", "-n"] else args)
        script = cmd[2] if cmd[:2] == ["sh", "-c"] else ""
        if "<<'LIMINAL_FILE'" in script:  # a boot service written as root
            self.calls.append(list(args))
            self.root_scripts.append(script)
            m = re.search(r"cat > (\S+)\.liminal-new <<'LIMINAL_FILE'\n(.*?)LIMINAL_FILE\n", script, re.S)
            path, text = m.group(1), m.group(2)
            name = path.rsplit("/", 1)[1]
            self.files[path], self.modes[path] = text, re.search(r"chmod (\d+) ", script).group(1)
            self.active.setdefault(name, "inactive")
            if f"systemctl enable {name}" in script or f"rc-update add {name} default" in script:
                self.enabled.add(name)
            return 0, "registered\n", ""
        if script.startswith("if [ -e /etc/"):  # a boot service removed as root
            self.calls.append(list(args))
            self.root_scripts.append(script)
            path = re.search(r"if \[ -e (\S+) \]", script).group(1)
            name = path.rsplit("/", 1)[1]
            existed = self.files.pop(path, None) is not None
            self.active.pop(name, None)
            self.enabled.discard(name)
            return 0, ("removed\n" if existed else "absent\n"), ""
        if "/etc/systemd/system/liminal-*-boot.service" in script:  # the boot units read
            self.calls.append(list(args))
            return 0, self._read_systemd(script), ""
        if "/etc/init.d/liminal-*-boot;" in script:  # the OpenRC boot services read
            self.calls.append(list(args))
            return 0, self._read_openrc(script), ""
        if cmd[:2] in (["systemctl", "start"], ["systemctl", "stop"]) and cmd[2].endswith("-boot.service"):
            self.calls.append(list(args))
            self.active[cmd[2]] = "active" if cmd[1] == "start" else "inactive"
            return 0, "", ""
        if cmd[:1] == ["rc-service"] and cmd[1].endswith("-boot"):
            self.calls.append(list(args))
            self.active[cmd[1]] = "active" if cmd[2] == "start" else "inactive"
            return 0, "", ""
        return super().__call__(args, timeout)


VENV = "/home/ciara/liminal/.venv/bin/python"
PLATFORM = BootApp("platform", "Liminal Platform", "liminal_platform", 8775, PLATFORM_APP, "/home/ciara/LiminalData/platform/logs/platform.log")
LAB = BootApp("lab", "Liminal Lab", "liminal_lab", 8790, "liminal_lab.app.LabApp")


def table_of(st, title):
    return next(t for t in st["tables"] if t["title"] == title)


def boot_table(st):
    return table_of(st, "At boot, before anyone signs in")


def plugin(fake, home=None, apps=(), user=("ciara", "/home/ciara"), answering=()):
    """The plugin on a native Linux machine (the test's word), its commands through the stand-in; its boot apps the
    test's (none by default: nothing of the platform imported), its account the test's."""
    return LinuxAdminPlugin(shell=Shell("local", runner=fake), home=home, native="", user=user, apps=list(apps),
                            logs=None, python=VENV, listening=lambda port: port in answering)


def test_the_plugin_reads_services_startups_and_processes_under_systemd(monkeypatch):
    assert MACHINE.name == "admin-linux" and MACHINE.options == () and MACHINE.STEPS == ("privileges", "services", "startup")
    monkeypatch.setattr(linux_mod.os, "geteuid", lambda: 0, raising=False)  # the platform runs as root
    a = plugin(FakeLinux())
    st = a.status()
    services = {s["name"]: s for s in st["frameworkServices"]}
    assert (services["docker"]["state"], services["containerd"]["state"], services["firewalld"]["state"]) == ("stopped", "running", "absent")
    assert services["docker"]["title"] == "Docker Application Container Engine" and not services["ssh"]["mayStart"]
    startups = {s["app"]: s for s in st["logonStartups"]}
    assert startups["integrator"]["state"] == "running" and "liminal_integrator service run" in startups["integrator"]["command"]
    assert startups["charts"]["state"] == "absent"
    assert st["frameworkProcesses"] == [{"pid": 4242, "app": "charts", "command": "/usr/bin/python3 -m liminal_charts gui --no-browser --port 8765", "memoryMb": 512}]
    assert st["elevated"] and st["elevation"] == "the platform runs as root" and st["valid"] and st["why"] == ""
    assert st.get("applies", True)
    assert st["summary"] == "elevated; services: 3 running, stopped: docker, ssh; startups: integrator; 1 Liminal process(es)"
    assert blocks("== a\nX=1\n== b\nY=2\n") == {"a": {"X": "1"}, "b": {"Y": "2"}} and state_of({}) == "absent"


def test_the_setup_starts_docker_never_ssh_and_says_how_root_is_had(monkeypatch):
    monkeypatch.setattr(linux_mod.os, "geteuid", lambda: 0, raising=False)
    fake = FakeLinux()
    done = plugin(fake).setup(log=lambda m: None)
    assert [(d["step"], d["ok"]) for d in done] == [("privileges", True), ("services", True), ("startup", None)]
    assert fake.started == ["systemctl start docker"]  # the SSH server stays as it was
    openrc = FakeLinux(init="openrc")
    st = plugin(openrc).status()
    assert {s["name"]: s["state"] for s in st["frameworkServices"]}["docker"] == "stopped"
    plugin(openrc).setup(log=lambda m: None, steps=("services",))
    assert openrc.started == ["rc-service docker start"]
    monkeypatch.setattr(linux_mod.os, "geteuid", lambda: 1000, raising=False)
    assert plugin(FakeLinux()).elevation() == "not root; sudo without a password"
    assert "asks for a password" in plugin(FakeLinux(sudo_ok=False)).elevation()
    # sudo asking for a password: still valid (it reads), each change saying it needs root
    st = plugin(FakeLinux(sudo_ok=False)).status()
    assert st["valid"] and st["why"] == "" and "sudo asks for a password here" in table_of(st, "Services the framework relies on")["note"]
    logon = table_of(st, "Startups at your logon")
    assert "no root is needed" in logon["note"] and {r[0]: r for r in logon["rows"]}["integrator"][3]["title"] == "End…"
    assert [t["title"] for t in st["tables"]] == ["Services the framework relies on", "Startups at your logon",
                                                  "At boot, before anyone signs in", "The framework's processes"]
    # under OpenRC the services are read as root when it may, else as the platform's user: still read, still valid
    openrc = FakeLinux(init="openrc", sudo_ok=False)
    refuse = openrc.__call__

    def no_sudo(args, timeout):
        if args[:2] == ["sudo", "-n"]:
            openrc.calls.append(list(args))
            return 1, "", "sudo: a password is required\n"
        return refuse(args, timeout)
    st = LinuxAdminPlugin(shell=Shell("local", runner=no_sudo), native="", user=("ciara", "/home/ciara"), apps=[]).status()
    assert st["valid"] and {s["name"]: s["state"] for s in st["frameworkServices"]}["docker"] == "stopped"


def test_a_user_unit_is_made_here_and_never_in_wsl(tmp_path, monkeypatch):
    monkeypatch.setattr(linux_mod.os, "geteuid", lambda: 1000, raising=False)
    fake = FakeLinux()
    a = plugin(fake, home=tmp_path)
    a.register("platform", python=sys.executable)
    unit = tmp_path / ".config" / "systemd" / "user" / "liminal-platform.service"
    text = unit.read_text(encoding="utf-8")
    assert "-m liminal_platform serve --no-browser" in text and "WantedBy=default.target" in text and "Restart=on-failure" in text
    cmds = [c for c in fake.calls if c[:2] == ["systemctl", "--user"]]
    assert ["systemctl", "--user", "daemon-reload"] in cmds and ["systemctl", "--user", "enable", "liminal-platform.service"] in cmds
    assert all(c[0] != "sudo" for c in cmds)  # a user's units, never as root
    a.startup("platform", "run")
    assert fake.calls[-1] == ["systemctl", "--user", "start", "liminal-platform.service"]
    assert a.unregister("platform") and not unit.exists() and not a.unregister("platform")
    in_wsl = LinuxAdminPlugin(shell=Shell("wsl:Liminal-Ubuntu", runner=fake), home=tmp_path, native="")
    with pytest.raises(AdminError, match="never WSL's Liminal-Ubuntu"):
        in_wsl.register("platform", python=sys.executable)
    assert not unit.exists()
    assert "ExecStart=" in unit_text("charts", ["/usr/bin/python3", "-m", "liminal_charts", "gui"])


def test_only_a_native_linux_machine_is_administered():
    """The user, 2026-11-08: "the scope of linux administration is only on native linux O/S"; "it's not for
    administrating WSL instances": on Windows, macOS or in a WSL distribution no command runs at all, the status says
    why (the platform shows the plugin disabled), the setup and every command are refused."""
    windows = why_not_native("win32", "10", {})
    assert windows == ("Linux administration is for a native Linux machine, and this one runs Windows; "
                       "Liminal's WSL distributions are the WSL plugins'")
    wsl2 = why_not_native("linux", "6.6.87.2-microsoft-standard-WSL2", {"WSL_DISTRO_NAME": "Liminal-Ubuntu"})
    assert "this is WSL's Liminal-Ubuntu on Windows" in wsl2
    assert "this is a WSL distribution on Windows" in why_not_native("linux", "4.4.0-19041-Microsoft", {})  # WSL 1
    assert why_not_native("linux", "6.8.0-48-generic", {"WSL_INTEROP": "/run/WSL/1_interop"})  # WSL's variables
    assert "this one runs macOS" in why_not_native("darwin", "24.1.0", {})
    assert why_not_native("linux", "6.8.0-48-generic", {}) == ""  # a native Linux machine
    if sys.platform == "win32":
        assert why_not_native() == windows
    for note in (windows, wsl2):
        ran: list = []
        p = LinuxAdminPlugin(shell=Shell("local", runner=lambda args, timeout: ran.append(args) or (0, b"", b"")), native=note,
                             apps=[PLATFORM])
        st = p.status()
        assert (st["present"], st["valid"], st["summary"]) == (False, False, "not for this machine")
        assert st["applies"] is False  # not for this machine at all: the platform offers no setup
        # what it does on a native Linux machine, said here (the user: "linux which doesn't say anything about startup")
        assert st["why"].startswith(note + ". On a native Linux machine running the platform (a remote, say) it shows and changes")
        assert "the apps' startups at logon (systemd user units)" in st["why"] and "liminal-platform-boot.service" in st["why"]
        assert [t["title"] for t in st["tables"]] == ["What it does on a native Linux machine", "The unit it would install at boot"]
        sections = {r[0]: r for r in st["tables"][0]["rows"]}
        assert set(sections) == {"Rights", "Services the framework relies on", "Startups at your logon",
                                 "At boot, before anyone signs in", "The framework's processes"}
        assert "liminal-platform.service" in sections["Startups at your logon"][1] and "asked twice" in sections["At boot, before anyone signs in"][2]
        unit = st["tables"][1]
        assert unit["columns"] == [{"title": "/etc/systemd/system/liminal-platform-boot.service"}]
        assert ["User=you"] in unit["rows"] and ["WantedBy=multi-user.target"] in unit["rows"]
        assert ["ExecStart=/home/you/liminal/.venv/bin/python -m liminal_platform serve --no-browser --port 8775"] in unit["rows"]
        assert st["forms"] == [] and not st["why"].endswith(".")  # nothing to change here; the page adds its own period
        assert not p.present()
        said: list = []
        assert p.setup(log=said.append) == [{"step": "privileges", "ok": False, "detail": note}]
        assert said == [f"admin-linux: privileges: FAILED: {note}"]
        for ask in (lambda: p.run("true"), lambda: p.service("docker", "start"), lambda: p.startup("platform", "run"),
                    lambda: p.register("platform", python=sys.executable), lambda: p.unregister("platform"),
                    lambda: p.register("platform", "boot", 8775), lambda: p.startup("platform", "start", "boot"),
                    lambda: p.unregister("platform", "boot", True), lambda: p.boot_startups([PLATFORM]),
                    p.services, p.startups, p.processes):
            with pytest.raises(AdminError, match="native Linux machine"):
                ask()
        assert ran == []  # nothing ran anywhere


# -- at boot, before anyone signs in (0.5.0) ---------------------------------------------------------------------------
def test_a_boot_unit_is_named_beside_the_user_unit_and_written_safely():
    assert boot_unit("platform") == "liminal-platform-boot.service" and UNITS["platform"] == "liminal-platform"
    assert boot_service("platform") == "liminal-platform-boot" and app_of_unit("liminal-platform-boot.service") == "platform"
    assert app_of_unit("liminal-lab-boot") == "lab" and app_of_unit("liminal-platform.service") == "" and app_of_unit("x-boot") == ""
    assert unit_word(VENV) == VENV and unit_word("/opt/my venv/bin/python") == '"/opt/my venv/bin/python"'
    assert unit_word("/opt/50%/$HOME") == "/opt/50%%/$$HOME"  # systemd's specifiers and variables, as they are
    for bad in ('/opt/a"b/python', "/opt/a\\b/python", "/opt/a\nb", ""):
        with pytest.raises(BootRefused):
            unit_word(bad)
    command = [VENV, "-m", "liminal_platform", "serve", "--no-browser", "--port", "8775"]
    text = boot_unit_text(PLATFORM, command, "ciara")
    assert f"ExecStart={VENV} -m liminal_platform serve --no-browser --port 8775\n" in text and "--until-quiet" not in text
    for line in ("User=ciara", "WantedBy=multi-user.target", "Wants=network-online.target", "After=network-online.target",
                 "Restart=on-failure", "RestartSec=10", "RestartSteps=6", "RestartMaxDelaySec=600", "KillSignal=SIGINT", "Type=simple"):
        assert f"\n{line}\n" in text, line
    assert text.startswith("[Unit]\nDescription=Liminal Platform at boot, before anyone signs in (made by the Liminal platform)\n")
    script = openrc_text(PLATFORM, command, "ciara", "/home/ciara")
    assert script.startswith("#!/sbin/openrc-run\n") and "supervisor=supervise-daemon\n" in script and 'command_user="ciara"\n' in script
    assert f'command="{VENV}"\n' in script and 'command_args="-m liminal_platform serve --no-browser --port 8775"\n' in script
    assert 'error_log="/var/log/liminal-platform-boot.log"\n' in script and "respawn_delay=10\n" in script and "respawn_max=0\n" in script
    assert 'retry="SIGINT/30/SIGKILL/5"' in script and "use net" in script and 'supervise_daemon_args="--env HOME=/home/ciara"' in script
    with pytest.raises(BootRefused):
        openrc_text(PLATFORM, ["/opt/my venv/bin/python", "-m", "liminal_platform"], "ciara")
    with pytest.raises(BootRefused):
        root_write("/etc/x", "a\nLIMINAL_FILE\nb\n", "0644")
    written = root_write("/etc/systemd/system/liminal-platform-boot.service", text, "0644")
    assert written.startswith("set -e\numask 022\ncat > /etc/systemd/system/liminal-platform-boot.service.liminal-new <<'LIMINAL_FILE'\n")
    assert written.endswith("chown root:root /etc/systemd/system/liminal-platform-boot.service.liminal-new\n"
                            "mv -f /etc/systemd/system/liminal-platform-boot.service.liminal-new /etc/systemd/system/liminal-platform-boot.service\n")


def test_the_platform_is_registered_at_boot_as_a_system_unit_through_sudo(monkeypatch):
    monkeypatch.setattr(linux_mod.os, "geteuid", lambda: 1000, raising=False)  # not root: sudo without a password
    fake = BootLinux()
    a = plugin(fake, apps=[PLATFORM, LAB])
    st = a.status()
    assert st["valid"] and st["why"] == "" and st["elevation"] == "not root; sudo without a password"
    rows = boot_table(st)["rows"]
    assert [(r[1]["text"], r[2]) for r in rows] == [("liminal-platform-boot.service", "not registered"), ("liminal-lab-boot.service", "not registered")]
    assert rows[0][1]["sub"] == f"would run {VENV} -m liminal_platform serve --no-browser --port 8775" and rows[0][3] == "ciara"
    assert rows[0][4] == {"text": "journalctl -u liminal-platform-boot.service", "sub": f"its own: {PLATFORM.log}"}
    note = boot_table(st)["note"]
    assert "system unit" in note and "never root" in note and "As root through sudo without a password" in note
    register = next(f for f in st["forms"] if f["id"] == "boot-register:platform")
    assert register["note"].startswith("A system unit, /etc/systemd/system/liminal-<app>-boot.service") and "lingering" in register["note"]
    made = a.register("platform", "boot", 8775)
    path = "/etc/systemd/system/liminal-platform-boot.service"
    assert fake.files[path] == boot_unit_text(PLATFORM, [VENV, "-m", "liminal_platform", "serve", "--no-browser", "--port", "8775"], "ciara")
    assert fake.modes[path] == "0644" and "liminal-platform-boot.service" in fake.enabled
    (wrote,) = [c for c in fake.calls if c[:3] == ["sudo", "-n", "sh"] and "LIMINAL_FILE" in c[-1]]
    assert "systemctl daemon-reload\nsystemctl enable liminal-platform-boot.service" in wrote[-1]
    assert (made.state, made.port, made.account, made.at) == ("stopped", 8775, "ciara", "boot") and made.detail == "at boot: enabled"
    a.startup("platform", "start", "boot")
    assert fake.calls[-1] == ["sudo", "-n", "systemctl", "start", "liminal-platform-boot.service"]
    assert {b["app"]: b["state"] for b in a.status()["bootServices"]}["platform"] == "starting"  # nothing answers at its port yet
    up = plugin(fake, apps=[PLATFORM, LAB], answering={8775}).status()
    assert {b["app"]: b["state"] for b in up["bootServices"]}["platform"] == "running" and "at boot: platform (running)" in up["summary"]
    assert boot_table(up)["rows"][0][5]["form"] == "boot-stop:platform"
    with pytest.raises(BootRefused, match="8775 is platform's"):
        a.register("lab", "boot", 8775)
    a.startup("platform", "stop", "boot")
    assert fake.calls[-1] == ["sudo", "-n", "systemctl", "stop", "liminal-platform-boot.service"]
    with pytest.raises(RemovalRefused) as refused:
        a.unregister("platform", "boot")
    assert refused.value.accept == ACCEPT_REMOVAL and path in fake.files
    assert a.unregister("platform", "boot", accept_removal=True)["removed"] and path not in fake.files
    removal = fake.root_scripts[-1]
    assert "systemctl disable --now liminal-platform-boot.service" in removal and f"rm -f {path}" in removal
    assert all(c[:2] == ["sudo", "-n"] for c in fake.calls if "LIMINAL_FILE" in c[-1] or c[-1].startswith("if [ -e /etc/"))


def test_under_openrc_the_boot_service_is_an_init_script_in_the_default_runlevel(monkeypatch):
    monkeypatch.setattr(linux_mod.os, "geteuid", lambda: 0, raising=False)  # the platform runs as root: no sudo
    fake = BootLinux(init="openrc")
    a = plugin(fake, apps=[PLATFORM], user=("ciara", "/home/ciara"))
    st = a.status()
    assert "OpenRC service" in boot_table(st)["note"] and "sudo" not in boot_table(st)["note"]
    a.register("platform", "boot", 8780)
    path = "/etc/init.d/liminal-platform-boot"
    assert fake.modes[path] == "0755" and 'command_args="-m liminal_platform serve --no-browser --port 8780"' in fake.files[path]
    assert "rc-update add liminal-platform-boot default" in fake.root_scripts[-1] and "liminal-platform-boot" in fake.enabled
    assert all(c[:2] != ["sudo", "-n"] for c in fake.calls)  # root already
    boot = {b.app: b for b in a.boot_startups(a.boot_apps())}["platform"]
    assert (boot.state, boot.port, boot.account, boot.log) == ("stopped", 8780, "ciara", "/var/log/liminal-platform-boot.log")
    assert boot.command == f"{VENV} -m liminal_platform serve --no-browser --port 8780" and "default runlevel" in boot.detail
    a.startup("platform", "start", "boot")
    assert fake.calls[-1] == ["rc-service", "liminal-platform-boot", "start"]
    assert a.unregister("platform", "boot", True)["removed"] and path not in fake.files
    assert "rc-update del liminal-platform-boot default" in fake.root_scripts[-1]


def test_a_boot_service_never_runs_as_root_and_an_unknown_init_makes_none(monkeypatch):
    monkeypatch.setattr(linux_mod.os, "geteuid", lambda: 0, raising=False)
    fake = BootLinux()
    a = plugin(fake, apps=[PLATFORM], user=("root", "/root"))
    with pytest.raises(BootRefused, match="never root"):
        a.register("platform", "boot", 8775)
    assert fake.files == {} and fake.root_scripts == []
    assert boot_table(a.status())["rows"][0][3] == "–"  # who it would run as: nobody yet
    plain_init = BootLinux(init="service")
    st = plugin(plain_init, apps=[PLATFORM]).status()
    assert st["bootServices"] == [] and not [f for f in st["forms"] if f["id"].startswith("boot-")]
    assert "neither systemd nor OpenRC" in boot_table(st)["empty"]
    with pytest.raises(BootRefused, match="neither systemd nor OpenRC"):
        plugin(plain_init, apps=[PLATFORM]).register("platform", "boot", 8775)
    assert plain_init.files == {}


def test_the_forms_ask_the_startups_hooks_and_a_unit_made_elsewhere_is_said(monkeypatch):
    monkeypatch.setattr(linux_mod.os, "geteuid", lambda: 0, raising=False)
    fake = BootLinux()
    fake.files["/etc/systemd/system/liminal-gone-boot.service"] = boot_unit_text(LAB, ["/usr/bin/python3", "-m", "liminal_gone", "serve", "--port", "8799"], "ciara")
    a = plugin(fake, apps=[PLATFORM])
    a.register("platform", "boot", 8775)
    st = a.status()
    forms = {f["id"]: f for f in st["forms"]}
    assert {"boot-register:platform", "boot-start:platform", "boot-stop:platform", "boot-remove:platform", "boot-remove:gone"} <= set(forms)
    for f in forms.values():
        params = list(inspect.signature(getattr(a, f["hook"])).parameters)
        assert f["hook"] in a.HOOKS and [x["name"] for x in f["fields"]] == params[:len(f["fields"])]
    assert "SIGINT" in forms["boot-stop:platform"]["confirm"]["words"]
    gone = next(b for b in st["bootServices"] if b["app"] == "gone")
    assert (gone["state"], gone["port"], gone["name"]) == ("disabled", 8799, "liminal-gone-boot.service")


def test_the_command_line_registers_and_removes_a_boot_service(monkeypatch, capsys):
    monkeypatch.setattr(linux_mod.os, "geteuid", lambda: 0, raising=False)
    fake = BootLinux()
    monkeypatch.setattr(cli, "MACHINE", plugin(fake, apps=[PLATFORM]))
    assert cli.main(["register", "platform", "--boot", "--port", "8781"]) == 0 and json.loads(capsys.readouterr().out)["port"] == 8781
    assert cli.main(["unregister", "platform", "--boot"]) == 1 and "--accept-removal" in capsys.readouterr().err
    assert cli.main(["unregister", "platform", "--boot", "--accept-removal"]) == 0 and fake.files == {}
