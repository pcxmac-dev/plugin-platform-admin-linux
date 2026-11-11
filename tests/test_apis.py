"""What Linux administration attaches to (plugin API 2.2): its cards are sound; they name every command the plugin runs
(the plugin driven through stand-in machines under systemd, OpenRC and SysV scripts over every read and change it
makes) and the files it writes; its facts are what it kept, asked without a command; and the cards' pages answer
(LIMINAL_VENDOR_PAGES=1 only, the one test that reaches the network)."""
from __future__ import annotations

import os
import re
import sys

import pytest

from liminal_libs.machines import linux as linux_mod
from liminal_libs.sources.apis import dead_links, problems
from plugin_platform_admin_linux import MACHINE
from plugin_platform_admin_linux import apis as cards
from test_plugin import PLATFORM, BootLinux, FakeLinux, plugin


def drive(monkeypatch, tmp_path):
    """Every read and change, on three stand-in machines: under systemd as an ordinary user (root through sudo -n: the
    status, the setup, each service change, each startup at logon made, run, ended, turned on and off and removed, the
    platform at boot registered, started, stopped and removed), under OpenRC as root (the same at boot, the services'
    changes) and under SysV scripts (the services). What each ran, and the plugin of the first."""
    monkeypatch.setattr(linux_mod.os, "geteuid", lambda: 1000, raising=False)
    systemd = BootLinux()
    a = plugin(systemd, home=tmp_path, apps=[PLATFORM])
    a.status()
    a.setup(log=lambda m: None)
    for action in ("start", "stop", "restart"):
        a.service("docker", action)
    a.register("platform", python=sys.executable)
    assert a.unit_path("platform").exists()
    for action in ("run", "end", "enable", "disable"):
        a.startup("platform", action)
    assert a.unregister("platform")
    a.register("platform", "boot", 8775)
    a.startup("platform", "start", "boot")
    a.startup("platform", "stop", "boot")
    boot_files = dict(systemd.files)
    assert a.unregister("platform", "boot", accept_removal=True)["removed"]
    monkeypatch.setattr(linux_mod.os, "geteuid", lambda: 0, raising=False)
    openrc = BootLinux(init="openrc")
    o = plugin(openrc, apps=[PLATFORM])
    o.status()
    for action in ("start", "stop", "restart"):
        o.service("docker", action)
    o.register("platform", "boot", 8780)
    boot_files.update(openrc.files)
    o.startup("platform", "start", "boot")
    o.startup("platform", "stop", "boot")
    assert o.unregister("platform", "boot", True)["removed"]
    sysv = FakeLinux(init="service")
    s = plugin(sysv)
    s.status()
    for action in ("start", "stop", "restart"):
        s.service("docker", action)
    return a, [*systemd.calls, *openrc.calls, *sysv.calls], boot_files


def fragments(name: str) -> list[str]:
    """A call's words as they appear in what was run: its name without its placeholders."""
    return [f.strip() for f in re.split(r"<[^>]+>", name) if f.strip()]


def direct(args: list[str]) -> str | None:
    """A command run directly (not a script) as the cards name it; None for a script."""
    cmd = args[2:] if args[:2] == ["sudo", "-n"] else args
    if cmd[:2] == ["sh", "-c"]:
        return None
    if cmd == ["true"]:
        return "sudo -n true"
    if cmd[:2] == ["systemctl", "--user"]:
        return f"systemctl --user {cmd[2]}" + ("" if cmd[2] == "daemon-reload" else
                                               " --now <unit>" if "--now" in cmd else " <unit>")
    if cmd[0] == "systemctl":
        return f"systemctl {cmd[1]} <unit>"
    if cmd[0] == "rc-service":
        return f"rc-service <service> {cmd[2]}"
    if cmd[0] == "service":
        return f"service <name> {cmd[2]}"
    return " ".join(cmd)


def test_the_cards_are_sound_and_each_says_where_its_documentation_is():
    assert problems(MACHINE.apis) == [] and MACHINE.apis == cards.APIS
    assert [a.name for a in MACHINE.apis] == ["systemd (systemctl)", "OpenRC", "SysV service", "sudo", "ps (procps-ng)"]
    assert all(a.docs and a.verified == "2026-11-11" and a.used and a.covered for a in MACHINE.apis)
    assert all(len(a.areas) > len(a.covered) for a in MACHINE.apis)  # more of each API than the plugin uses
    assert cards.SYSTEMCTL.link("reference") == "https://www.freedesktop.org/software/systemd/man/latest/systemctl.html"
    assert not any(c.costs for a in MACHINE.apis for c in a.calls)  # nothing here costs money


def test_the_cards_name_every_command_it_runs_and_the_files_it_writes(monkeypatch, tmp_path):
    a, calls, boot_files = drive(monkeypatch, tmp_path)
    texts = [" ".join(c) for c in calls]
    used = {c.name for api in MACHINE.apis for c in api.used}
    ran = {d for c in calls if (d := direct(c))}
    assert ran <= used, sorted(ran - used)
    for api in MACHINE.apis:
        for call in api.used:
            if call.name.startswith(("~/", "/etc/")):  # a file it writes
                continue
            assert all(any(f in t for t in texts) for f in fragments(call.name)), f"{api.name}: {call.name} is not run"
    assert str(a.unit_path("platform")).replace("\\", "/").endswith(".config/systemd/user/liminal-platform.service")
    assert set(boot_files) == {"/etc/systemd/system/liminal-platform-boot.service", "/etc/init.d/liminal-platform-boot"}
    files = {c.name for c in (*cards.SYSTEMCTL.used, *cards.OPENRC_API.used) if c.name.startswith(("~/", "/etc/"))}
    assert files == {"~/.config/systemd/user/liminal-<app>.service", "/etc/systemd/system/liminal-<app>-boot.service",
                     "/etc/init.d/liminal-<app>-boot"}


def test_its_facts_are_what_it_kept_and_asking_them_runs_nothing(monkeypatch):
    monkeypatch.setattr(linux_mod.os, "geteuid", lambda: 1000, raising=False)
    fake = FakeLinux()
    a = plugin(fake)
    assert a.api_facts() == {} and fake.calls == []
    assert a.may_elevate()
    before = len(fake.calls)
    facts = a.api_facts()
    assert len(fake.calls) == before  # nothing run
    assert facts == {"sudo": {"Without a password": "yes (asked 0 s ago)"}}
    refused = plugin(FakeLinux(sudo_ok=False))
    assert not refused.may_elevate() and refused.api_facts()["sudo"]["Without a password"].startswith("no: it asks for one")


@pytest.mark.skipif(os.environ.get("LIMINAL_VENDOR_PAGES") != "1", reason="reaches the makers' pages: LIMINAL_VENDOR_PAGES=1")
def test_the_cards_pages_answer():
    assert dead_links(MACHINE.apis) == []
