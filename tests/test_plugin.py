"""Linux administration: the rights and how they are had, the framework's services under systemd or OpenRC
(started when stopped, never the SSH server), the apps' systemd user units read, run, made and removed, the
processes, all through a stand-in for the commands (nothing runs here); only on a native Linux machine: on Windows,
macOS or in a WSL distribution nothing runs at all."""
from __future__ import annotations

import sys

import pytest

from liminal_libs.machines.admin import AdminError
from liminal_libs.machines.linux import Shell
from liminal_libs.machines import linux as linux_mod

from plugin_platform_admin_linux import MACHINE, UNITS, LinuxAdminPlugin, blocks, state_of, unit_text, why_not_native

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


def plugin(fake, home=None):
    """The plugin on a native Linux machine (the test's word), its commands through the stand-in."""
    return LinuxAdminPlugin(shell=Shell("local", runner=fake), home=home, native="")


def test_the_plugin_reads_services_startups_and_processes_under_systemd(monkeypatch):
    assert MACHINE.name == "admin-linux" and MACHINE.options == () and MACHINE.STEPS == ("privileges", "services", "startup")
    monkeypatch.setattr(linux_mod.os, "geteuid", lambda: 0, raising=False)  # the platform runs as root
    a = plugin(FakeLinux())
    st = a.status()
    services = {s["name"]: s for s in st["services"]}
    assert (services["docker"]["state"], services["containerd"]["state"], services["firewalld"]["state"]) == ("stopped", "running", "absent")
    assert services["docker"]["title"] == "Docker Application Container Engine" and not services["ssh"]["mayStart"]
    startups = {s["app"]: s for s in st["startups"]}
    assert startups["integrator"]["state"] == "running" and "liminal_integrator service run" in startups["integrator"]["command"]
    assert startups["charts"]["state"] == "absent"
    assert st["processes"] == [{"pid": 4242, "app": "charts", "command": "/usr/bin/python3 -m liminal_charts gui --no-browser --port 8765", "memoryMb": 512}]
    assert st["elevated"] and st["elevation"] == "the platform runs as root" and st["valid"] and st["why"] == ""
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
    assert {s["name"]: s["state"] for s in st["services"]}["docker"] == "stopped"
    plugin(openrc).setup(log=lambda m: None, steps=("services",))
    assert openrc.started == ["rc-service docker start"]
    monkeypatch.setattr(linux_mod.os, "geteuid", lambda: 1000, raising=False)
    assert plugin(FakeLinux()).elevation() == "not root; sudo without a password"
    assert "asks for a password" in plugin(FakeLinux(sudo_ok=False)).elevation()


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
        p = LinuxAdminPlugin(shell=Shell("local", runner=lambda args, timeout: ran.append(args) or (0, b"", b"")), native=note)
        st = p.status()
        assert (st["present"], st["valid"], st["summary"], st["why"]) == (False, False, "not a native Linux machine", note)
        assert not p.present()
        said: list = []
        assert p.setup(log=said.append) == [{"step": "privileges", "ok": False, "detail": note}]
        assert said == [f"admin-linux: privileges: FAILED: {note}"]
        for ask in (lambda: p.run("true"), lambda: p.service("docker", "start"), lambda: p.startup("platform", "run"),
                    lambda: p.register("platform", python=sys.executable), lambda: p.unregister("platform"),
                    p.services, p.startups, p.processes):
            with pytest.raises(AdminError, match="native Linux machine"):
                ask()
        assert ran == []  # nothing ran anywhere
