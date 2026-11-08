"""Linux administration: the rights and how they are had, the framework's services under systemd or OpenRC
(started when stopped, never the SSH server), the apps' systemd user units read, run, made and removed (made
only on this machine), the processes, all through a stand-in for the commands (nothing runs here)."""
from __future__ import annotations

import sys

import pytest

from liminal_libs.machines.admin import AdminError
from liminal_libs.machines.linux import Shell
from liminal_libs.machines import linux as linux_mod

from plugin_platform_admin_linux import MACHINE, UNITS, LinuxAdminPlugin, blocks, state_of, unit_text

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


def plugin(fake, target="wsl:Liminal-Ubuntu", home=None):
    return LinuxAdminPlugin(shell=Shell(target, runner=fake), home=home)


def test_the_plugin_reads_services_startups_and_processes_under_systemd():
    assert MACHINE.name == "admin-linux" and MACHINE.options == ("ADMIN_LINUX_TARGET",) and MACHINE.STEPS == ("privileges", "services", "startup")
    a = plugin(FakeLinux())
    st = a.status()
    services = {s["name"]: s for s in st["services"]}
    assert (services["docker"]["state"], services["containerd"]["state"], services["firewalld"]["state"]) == ("stopped", "running", "absent")
    assert services["docker"]["title"] == "Docker Application Container Engine" and not services["ssh"]["mayStart"]
    startups = {s["app"]: s for s in st["startups"]}
    assert startups["integrator"]["state"] == "running" and "liminal_integrator service run" in startups["integrator"]["command"]
    assert startups["charts"]["state"] == "absent"
    assert st["processes"] == [{"pid": 4242, "app": "charts", "command": "/usr/bin/python3 -m liminal_charts gui --no-browser --port 8765", "memoryMb": 512}]
    assert st["elevated"] and st["elevation"] == "root in WSL's Liminal-Ubuntu through wsl -u root"
    assert st["summary"] == "elevated; services: 3 running, stopped: docker, ssh; startups: integrator; 1 Liminal process(es)"
    assert blocks("== a\nX=1\n== b\nY=2\n") == {"a": {"X": "1"}, "b": {"Y": "2"}} and state_of({}) == "absent"


def test_the_setup_starts_docker_never_ssh_and_says_how_root_is_had(monkeypatch):
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
    assert plugin(FakeLinux(), target="local").elevation() == "not root; sudo without a password"
    assert "asks for a password" in plugin(FakeLinux(sudo_ok=False), target="local").elevation()


def test_a_user_unit_is_made_here_and_never_in_wsl(tmp_path, monkeypatch):
    monkeypatch.setattr(linux_mod.os, "geteuid", lambda: 1000, raising=False)
    fake = FakeLinux()
    a = plugin(fake, target="local", home=tmp_path)
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
    with pytest.raises(AdminError):
        plugin(FakeLinux(), target="wsl:Liminal-Ubuntu", home=tmp_path).register("platform", python=sys.executable)
    assert "ExecStart=" in unit_text("charts", ["/usr/bin/python3", "-m", "liminal_charts", "gui"])


def test_a_target_not_liminals_is_never_touched():
    """WSL's default distribution or the user's own: no command runs there, the status says why, the setup changes
    nothing (liminal-libs 1.25.0)."""
    from liminal_libs.machines.linux import Shell

    ran: list = []
    p = LinuxAdminPlugin(shell=Shell("wsl:Ubuntu", runner=lambda args, timeout: ran.append(args) or (0, b"", b"")))
    st = p.status()
    assert (st["present"], st["valid"], st["summary"]) == (False, False, "not on Liminal's") and "WSL's Ubuntu is not Liminal's" in st["why"]
    assert [d["ok"] for d in p.setup(log=lambda m: None)] == [False] and ran == []
