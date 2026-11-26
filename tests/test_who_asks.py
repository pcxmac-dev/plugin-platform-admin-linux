"""Who may ask the plugin's changes, and what an ask may name (0.8.1, the review of PLT-H1's fix, 2026-11-24). Its
changes are asked only from its page (PAGE_ONLY_HOOKS, as liminal-libs 1.66.0's apps/asking.py and liminal-platform
0.34.0 read them): a service started, stopped or restarted, and a startup run, ended, turned on or off, made or removed,
at your logon or at boot. Another plugin's ask is refused, and so is an ask that names no one; over HTTP the platform
also asks its login whether you are at the page. Before, any program on this machine asked them with two headers: ufw
stopped as root, the SSH server started. Its reads are asked by anyone, as before. And register takes no program from
an ask, the page's included: a startup runs this Python (the test's, given to the constructor). Before, a fourth
argument named the program, which a user unit then ran at every logon, or root's system unit at every boot. Asked
through the library's own App (its ask names who asks as the platform's does), over a stand-in for the commands:
nothing runs, no server is started, nothing is written but in the test's own folder."""
from __future__ import annotations

import pytest

from liminal_libs import internal
from liminal_libs.apps import App, asking
from liminal_libs.apps.authorization import EnvironmentLogin
from liminal_libs.machines import linux as linux_mod
from liminal_libs.machines.plugin import MachinePlugin

from test_plugin import PLATFORM, SUDO, VENV, BootLinux, plugin

CHANGES = ("service", "startup", "register", "unregister",
           "linux_apply", "linux_member", "linux_undo")  # 0.9.0: Liminal's user and group, the user's answer 6
READS = ("present", "status", "processes", "linux_facts")
PROGRAM = "/tmp/x"  # a program another account could put there; nothing runs it here
BOOT_UNIT = "/etc/systemd/system/liminal-platform-boot.service"


class Neighbour(MachinePlugin):
    """Another plugin of the platform, asking the admin plugin through its app as any plugin may (a container plugin,
    or the MCP plugin for a local agent)."""

    name, title = "neighbour", "Neighbour"

    def wants(self, hook, *args):
        """Not a hook: one of the admin plugin's asked through the app."""
        return self.app.ask("admin-linux", hook, *args)


class Platform(App):
    """The library's App asking as the platform does: from its page's route, the page named in so many words, or from
    its own code, no one named."""

    NAME, TITLE, ICON = "platform", "Platform", "chip"

    def from_page(self, hook, *args):
        """As the page's route asks a hook."""
        with asking.asking(asking.PAGE):
            return self.ask("admin-linux", hook, *args)

    def on_its_own(self, hook, *args):
        """As the app's own code asks a hook."""
        return self.ask("admin-linux", hook, *args)


@pytest.fixture
def attached(monkeypatch, tmp_path):
    """The plugin on a Linux machine under systemd, the platform not root (root through sudo without a password), its
    user units in the test's folder and its boot units kept by the stand-in, attached with another plugin to an app;
    let go after."""
    monkeypatch.setattr(linux_mod.os, "geteuid", lambda: 1000, raising=False)
    fake = BootLinux()
    admin, neighbour = plugin(fake, home=tmp_path, apps=[PLATFORM]), Neighbour()
    app = Platform(log=lambda m: None, login=EnvironmentLogin(env={}))
    app.attach(admin)
    app.attach(neighbour)
    yield app, admin, neighbour, fake, tmp_path
    app.detach(neighbour.name)
    app.detach(admin.name)


def test_its_changes_are_said_to_be_asked_only_from_its_page_and_its_reads_by_anyone():
    admin = plugin(BootLinux())
    assert set(internal.page_only(admin)) == set(CHANGES) and internal.plugin_only(admin) == ()  # what the platform reads
    assert internal.problems(admin) == []  # each a hook of its own that someone may ask; register says what it does
    for hook in CHANGES:
        assert asking.refusal(admin, hook, asking.PAGE) == ""
        assert asking.refusal(admin, hook, "neighbour") == (f"admin-linux's {hook} is asked only from its page, never by "
                                                            "another plugin: neighbour asked it.")
        assert asking.refusal(admin, hook, None).endswith("This ask names no asker: neither the page nor a plugin.")
    for hook in READS:
        assert {asking.refusal(admin, hook, who) for who in (asking.PAGE, "neighbour", None)} == {""}


def test_another_plugin_or_no_one_asking_a_change_runs_nothing_and_its_page_does(attached):
    app, admin, neighbour, fake, home = attached
    for ask in (lambda: neighbour.wants("service", "ufw", "stop"),  # the firewall stopped, as root
                lambda: app.on_its_own("service", "firewalld", "stop"),
                lambda: neighbour.wants("service", "ssh", "start"),  # the SSH server, which the setup never starts
                lambda: neighbour.wants("register", "charts"),
                lambda: neighbour.wants("startup", "integrator", "run"),
                lambda: neighbour.wants("register", "platform", "boot", 8775),
                lambda: neighbour.wants("startup", "platform", "start", "boot"),
                lambda: neighbour.wants("unregister", "platform", "boot", True),  # its second confirmation said
                # 0.9.0: Liminal's user and group, each accept and a password given as the page would
                lambda: neighbour.wants("linux_apply", "accounts service-user", "0" * 64, True, True, "words"),
                lambda: neighbour.wants("linux_member", "alice", "add", "0" * 64, True, True, None),
                lambda: app.on_its_own("linux_undo", "0" * 64, True, True, None)):
        with pytest.raises(asking.AskRefused, match="is asked only from its page"):
            ask()
    assert fake.calls == [] and fake.files == {} and list(home.iterdir()) == []  # nothing run, read or written
    assert admin._linux.calls == [] and admin._linux.sudo_runs == 0  # not even the probe: no sudo started
    assert neighbour.wants("present") is True and neighbour.wants("processes")[0]["app"] == "charts"  # reads, as before
    assert app.from_page("service", "ufw", "stop") is None
    assert fake.calls[-1] == [*SUDO, "systemctl", "stop", "ufw"] and fake.started == ["systemctl stop ufw"]


def test_register_takes_no_program_from_an_ask_the_pages_included(attached):
    """The review's case: the library's register took the program a startup runs as its fourth argument, and the
    platform hands an ask's arguments on as they come. Asked from the page too, or of the plugin itself (as the
    platform's ask calls it): refused before anything is written or run. Asked as the page asks it, the startup runs
    this Python (the test's)."""
    app, admin, neighbour, fake, home = attached
    for ask in (lambda: app.from_page("register", "charts", "logon", None, PROGRAM),  # at every logon, as you
                lambda: app.from_page("register", "platform", "boot", None, PROGRAM),  # at every boot, root's unit
                lambda: admin.ask("register", "charts", "logon", None, PROGRAM),
                lambda: admin.ask("register", "platform", "boot", 8775, PROGRAM),
                lambda: admin.ask("register", "charts", python=PROGRAM)):
        with pytest.raises(TypeError):
            ask()
    assert fake.calls == [] and fake.files == {} and list(home.iterdir()) == []  # no unit written, no systemctl, no sudo
    assert app.from_page("register", "charts").app == "charts"  # the page's form: the app and when, nothing more
    unit = (home / ".config" / "systemd" / "user" / "liminal-charts.service").read_text(encoding="utf-8")
    assert f"\nExecStart={VENV} -m liminal_charts gui --no-browser --port 8765\n" in unit
    assert app.from_page("register", "platform", "boot", 8775).at == "boot"  # and at boot, its port
    assert f"\nExecStart={VENV} -m liminal_platform serve --no-browser --port 8775\n" in fake.files[BOOT_UNIT]
