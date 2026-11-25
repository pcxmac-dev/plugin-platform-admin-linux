"""The plugin's run() and its command line's `run` (the review's finding PLT-H1, checked 2026-11-23): run() runs a
command on this machine as the platform's own user, and as root only when `elevated` is said, through the sudo the
library's Shell puts in front of it (shell_sudo(), from test_plugin.py: read from the library; `sudo -n --` since
liminal-libs 1.80.0, the package's floor since 0.8.1). The command line (0.8.1) takes `--elevated` only as its first
word, before the command's `--`: every word after that is the command's own, the first too; until 0.8.1 an
`--elevated` anywhere ran the command as root and was taken out of it. All through a stand-in for the commands:
nothing runs here."""
from __future__ import annotations

import re
from pathlib import Path

from liminal_libs.machines import linux as linux_mod

import plugin_platform_admin_linux.__main__ as cli

from test_plugin import FakeLinux, plugin, shell_sudo

GREP = ["grep", "boot", "notes.txt"]  # a command; nothing runs it
PYPROJECT = Path(__file__).parent.parent / "pyproject.toml"


def test_a_command_runs_as_the_platforms_user_and_as_root_only_when_elevated(monkeypatch):
    monkeypatch.setattr(linux_mod.os, "geteuid", lambda: 1000, raising=False)  # not root: root is had through sudo
    sudo, fake = shell_sudo(), FakeLinux()
    assert sudo[:1] == ["sudo"]  # the library's sudo, whatever it puts after it
    a = plugin(fake)
    assert a.run(*GREP) == "ran\n" and fake.calls == [GREP]  # nothing in front: the platform's own user
    assert a.run(*GREP, elevated=False) == "ran\n" and fake.calls[-1] == GREP
    assert a.run(*GREP, root=True) == "ran\n" and fake.calls[-1] == GREP  # root= is the shell's word, not run()'s
    assert a.run(*GREP, elevated=True) == "ran\n" and fake.calls[-1] == [*sudo, *GREP]
    assert a.run("-u", "nobody", "id") == "ran\n" and fake.calls[-1] == ["-u", "nobody", "id"]  # no sudo to read its -u
    assert a.run("-u", "nobody", "id", elevated=True) == "ran\n"
    assert fake.calls[-1] == [*sudo, "-u", "nobody", "id"]  # after sudo's own words: -u is the command's
    # a platform that is root runs it as itself, elevated or not: there is no one else to run it as
    monkeypatch.setattr(linux_mod.os, "geteuid", lambda: 0, raising=False)
    as_root = FakeLinux()
    assert plugin(as_root).run(*GREP) == plugin(as_root).run(*GREP, elevated=True) == "ran\n"
    assert as_root.calls == [GREP, GREP]


def test_an_elevated_command_comes_after_sudos_own_double_dash_from_the_library_it_needs():
    """run --elevated promises that no word of the command is read as sudo's (the review of 0.8.1, 2026-11-24): it
    needs liminal-libs 1.80.0, whose Shell puts `sudo -n --` before a command run as root. Before, `sudo -n`, and
    `run --elevated -- -u nobody id` ran id as nobody. The package says so (its floor), and the library the tests run
    on must hold it, or the test above would pass on its `sudo -n` alone."""
    assert shell_sudo()[:1] == ["sudo"] and shell_sudo()[-1:] == ["--"]
    floor = re.search(r'"liminal-libs>=(\d+)\.(\d+)\.(\d+)"', PYPROJECT.read_text(encoding="utf-8"))
    assert floor and tuple(int(n) for n in floor.groups()) >= (1, 80, 0)


def test_the_command_line_takes_elevated_only_as_its_first_word(monkeypatch, capsys):
    """`run -- X` as you; `run --elevated -- X` as root; `run -- X --elevated`: X with its own word, as you (until 0.8.1
    the word was taken out of X and X ran as root); `run -- --elevated X`: the command's first word, as you (the review
    of 0.8.1: a parse taking the `--` first and --elevated after it ran X as root); `run --elevated -- X --elevated`: X
    with its own word, as root; `run --elevated` with no command: the usage, nothing run."""
    monkeypatch.setattr(linux_mod.os, "geteuid", lambda: 1000, raising=False)
    sudo, fake = shell_sudo(), FakeLinux()
    monkeypatch.setattr(cli, "MACHINE", plugin(fake))
    assert cli.main(["run", "--", *GREP]) == 0 and fake.calls[-1] == GREP
    assert cli.main(["run", "--elevated", "--", *GREP]) == 0 and fake.calls[-1] == [*sudo, *GREP]
    assert cli.main(["run", "--", *GREP, "--elevated"]) == 0 and fake.calls[-1] == [*GREP, "--elevated"]  # its own word
    assert cli.main(["run", "--", "grep", "--elevated", "notes.txt"]) == 0
    assert fake.calls[-1] == ["grep", "--elevated", "notes.txt"]  # the review's case: once grep notes.txt, as root
    assert cli.main(["run", "grep", "--elevated", "notes.txt"]) == 0  # without the `--`, still the first word only
    assert fake.calls[-1] == ["grep", "--elevated", "notes.txt"]
    assert cli.main(["run", "--", "--elevated", *GREP]) == 0 and fake.calls[-1] == ["--elevated", *GREP]  # its first word
    assert cli.main(["run", "--elevated", "--", "grep", "--elevated", "notes.txt"]) == 0
    assert fake.calls[-1] == [*sudo, "grep", "--elevated", "notes.txt"]  # as root, the command's own word kept
    assert capsys.readouterr().out == "ran\n" * 7 and len(fake.calls) == 7
    for alone in (["run", "--elevated"], ["run", "--elevated", "--"], ["run", "--"], ["run"]):
        assert cli.main(alone) == 2, alone  # no command: the usage
        assert "run [--elevated] -- COMMAND" in capsys.readouterr().err
    assert len(fake.calls) == 7  # nothing run
