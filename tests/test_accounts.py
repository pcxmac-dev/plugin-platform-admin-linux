"""Liminal's user and group on the plugin's page (0.9.0; Monday list item 19, release one, the user, 2026-11-25:
"Accounts and elevation"): "How root is had" and "Liminal's user and group" first, their forms sent as the platform's
page sends them (Make them..., Add a member..., Remove a member..., Remove them... asked twice), one sudo per confirmed
click, the password field only where sudo asks for one, asked twice where none is asked, the words on starting the
platform again, the one root command where the page cannot make a change, the rights the other sections say read from
the same Elevation, and the command line's `accounts`. Every machine is one of the library's recorded machines
(liminal_libs.linuxsys.standin): no process starts, nothing is written but in the stand-in's tree, no sudo runs."""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

import liminal_libs

from liminal_libs.apps import asking
from liminal_libs.linuxsys import shared, standin
from liminal_libs.machines import linux as linux_mod

import plugin_platform_admin_linux
import plugin_platform_admin_linux.__main__ as cli

from test_plugin import UBUNTU, VENV, FakeLinux, plugin, table_of

ALICE = "alice:x:1001:1001:Alice:/home/alice:/bin/bash\n"


@pytest.fixture(autouse=True)
def not_root(monkeypatch):
    """The platform runs as the recorded machine's user, pat (uid 1000), as it does on the user's Ubuntu."""
    monkeypatch.setattr(linux_mod.os, "geteuid", lambda: 1000, raising=False)


def on(name: str = UBUNTU, overlay: str | None = None, sudo_ok: bool = False):
    """The plugin on a recorded machine: its services' commands through FakeLinux (sudo -n as `sudo_ok` says), how
    root is had and Liminal's accounts through the recorded machine."""
    m = standin.Machine(name, overlay)
    return plugin(FakeLinux(sudo_ok=sudo_ok), linux=m), m


def forms(p) -> dict:
    return {f["id"]: f for f in p.status()["forms"]}


def args_of(form: dict, accepted=(), password=None) -> list:
    """The hook's arguments as the platform's page sends them (platform.js argsOf): each field in order, an accept
    true only through its own confirmation, a password only where the form has its field."""
    out = []
    for x in form["fields"]:
        out.append(x["name"] in accepted if x["type"] == "accept" else password if x["type"] == "password"
                   else x["value"])
    return out


def send(p, form: dict, accepted=(), password=None):
    with asking.asking(asking.PAGE):
        return p.ask(form["hook"], *args_of(form, accepted, password))


def click(p, form: dict, password=None):
    """One confirmed click as the page makes it: sent; a refusal naming one of the form's accepts confirmed once, then
    sent again with it and the same password."""
    try:
        return send(p, form, (), password)
    except shared.Refused as e:
        if e.accept not in [x["name"] for x in form["fields"] if x["type"] == "accept"]:
            raise
        return send(p, form, (e.accept,), password)


def rows(p) -> list:
    return table_of(p.status(), "Liminal's user and group")["rows"]


def row(p, what: str):
    return next(r for r in rows(p) if (r[0]["text"] if isinstance(r[0], dict) else r[0]) == what)


# ---- the page ------------------------------------------------------------------------------------------------------


def test_its_two_sections_come_first_and_say_how_root_is_had_and_the_one_command():
    p, m = on()
    st = p.status()
    titles = [t["title"] for t in st["tables"]]
    assert titles[:2] == ["How root is had", "Liminal's user and group"] and titles[-1] == "This Linux"
    root = st["tables"][0]["rows"][0]
    assert root[0]["text"] == "sudo" and root[1]["text"] == "a password, typed on the change's form"
    assert root[1]["sub"] == "Your password for sudo" and root[2] == "sudo writes each change's script into this system's log"
    assert row(p, "The group liminal")[1] == "not here" and row(p, "The user liminal")[1]["text"] == "not here"
    line = row(p, "The one command")[1]["text"]
    assert line == f"sudo {VENV} -I -B -m liminal_libs.linuxsys apply"  # the plugin's Python, the one it runs
    make = forms(p)["linux-make"]
    assert make["hook"] == "linux_apply" and make["confirm"]["title"] == "Make Liminal's user and group?"
    assert [x["name"] for x in make["fields"]] == ["parts", "digest", "accept_members", "accept_unasked", "password"]
    field = make["fields"][-1]
    assert field["type"] == "password" and field["note"].startswith("used for this once, never kept; one try")
    assert "linux-undo" not in forms(p) and m.sudo_runs == 0  # nothing of Liminal's to take back; no sudo to draw it
    assert st["summary"].endswith("the group liminal: not here")


def test_the_other_sections_rights_come_from_the_same_reading_and_sudo_n_true_is_gone():
    m = standin.Machine(UBUNTU)
    fake = FakeLinux(sudo_ok=False)
    p = plugin(fake, linux=m)
    st = p.status()
    assert "sudo asks for a password here" in table_of(st, "Services the framework relies on")["note"]
    assert not p.may_elevate() and p.elevation().startswith("not root, and sudo asks for a password")
    free, _ = on(overlay="nopasswd-all", sudo_ok=True)
    assert free.may_elevate() and free.elevation() == "not root; sudo without a password"
    assert "As root through sudo without a password" in table_of(free.status(), "Services the framework relies on")["note"]
    assert free.api_facts()["sudo"]["Without a password"].startswith("yes (read ")
    listings = [c for c in m.calls if c["argv"][-2:] == ["-n", "-l"]]
    assert len(listings) == 1  # sudo's listing read once for the whole page (at most once in 5 min)
    assert fake.calls and not [c for c in fake.calls if c[-1:] == ["true"]]  # no sudo -n true any more


def test_make_them_asks_sudo_once_and_says_to_start_the_platform_again_from_a_new_terminal():
    p, m = on()
    done = click(p, forms(p)["linux-make"], standin.PASSWORD)
    assert done["ok"] and done["said"] == "done" and m.sudo_runs == 1
    assert standin.PASSWORD not in json.dumps(done) and standin.PASSWORD not in json.dumps(p.status())
    sudo = [c for c in m.calls if "-S" in c["argv"]]
    assert len(sudo) == 1 and standin.PASSWORD not in " ".join(sudo[0]["argv"]) and sudo[0]["stdin"] == (
        standin.PASSWORD + "\n").encode()
    group = row(p, "The group liminal")[1]
    assert group["sub"].startswith("a system group; made by Liminal")
    pat = row(p, "pat")
    assert pat[1] == "a member; not yet in the running platform: start the platform again from a new terminal tab"
    assert pat[2]["form"] == "linux-member-remove:pat"
    assert "linux-make" not in forms(p) and "linux-undo" in forms(p)


def test_remove_them_is_asked_twice_and_gives_the_first_tree_back():
    p, m = on()
    first = m.snapshot()
    click(p, forms(p)["linux-make"], standin.PASSWORD)
    undo = forms(p)["linux-undo"]
    assert undo["confirm"]["danger"] and undo["confirm"]["yes"] == "Remove them"
    with pytest.raises(shared.Refused) as e:
        send(p, undo, (), standin.PASSWORD)
    assert e.value.accept == "accept_removal" and m.sudo_runs == 1  # refused before sudo started
    assert send(p, undo, ("accept_removal",), standin.PASSWORD)["ok"] and m.sudo_runs == 2
    assert m.snapshot() == first and row(p, "The group liminal")[1] == "not here"


def test_a_member_other_than_the_platform_s_user_is_asked_twice_by_name():
    p, m = on()
    m.files["/etc/passwd"] += ALICE
    click(p, forms(p)["linux-make"], standin.PASSWORD)
    add = forms(p)["linux-member-add:alice"]
    with pytest.raises(shared.Refused) as e:
        send(p, add, (), standin.PASSWORD)
    assert e.value.accept == "accept_member" and "it gives alice every Liminal privilege" in str(e.value)
    runs = m.sudo_runs
    assert send(p, add, ("accept_member",), standin.PASSWORD)["ok"] and m.sudo_runs == runs + 1
    assert "alice" in m.groups()["liminal"].members
    remove = forms(p)["linux-member-remove:alice"]
    assert click(p, remove, standin.PASSWORD)["ok"] and "alice" not in m.groups()["liminal"].members


def test_where_no_password_is_asked_there_is_no_field_and_every_change_is_asked_twice():
    p, m = on(overlay="nopasswd-all", sudo_ok=True)
    make = forms(p)["linux-make"]
    assert "password" not in [x["name"] for x in make["fields"]]
    with pytest.raises(shared.Refused) as e:
        send(p, make)
    assert e.value.accept == "accept_unasked" and str(e.value).startswith("no password is asked here")
    assert m.sudo_runs == 0 and send(p, make, ("accept_unasked",))["ok"] and m.sudo_runs == 1


def test_a_wrong_password_is_one_try_and_the_form_is_offered_again():
    p, m = on()
    with pytest.raises(ValueError) as e:
        send(p, forms(p)["linux-make"], (), "not it")
    assert "not it" not in str(e.value) and m.sudo_runs == 0 and not m.eof_at_prompt
    assert click(p, forms(p)["linux-make"], standin.PASSWORD)["ok"]


@pytest.mark.parametrize("name, words, line", [
    ("alpine-3.24", "takes a password only from a terminal", "doas "),
    ("debian-13-su", "takes a password only from a terminal", "su -c "),
    ("service-account", "Liminal's service account, which has no password", ""),
])
def test_where_the_page_cannot_change_them_it_shows_the_one_command_and_no_form(name, words, line):
    p, _ = on(name)
    assert not [f for f in forms(p) if f.startswith("linux-")]
    assert words in row(p, "Changes here")[1]
    command = row(p, "The one command")[1]["text"]
    assert command.startswith(line) and "-I -B -m liminal_libs.linuxsys apply" in command


def test_a_found_group_holding_a_person_is_asked_twice_by_name_and_kept():
    """The Linux firewall's switch made the system group liminal (the overlay firewall-group), and alice is in it too:
    Make them... takes it as found only once asked by name, then makes the user alone; the group is said found."""
    p, m = on(overlay="firewall-group")
    m.files["/etc/passwd"] += ALICE
    m.files["/etc/group"] = m.files["/etc/group"].replace("liminal:x:994:pat", "liminal:x:994:pat,alice")
    make = forms(p)["linux-make"]
    with pytest.raises(shared.Refused) as e:
        send(p, make, (), standin.PASSWORD)
    assert e.value.accept == "accept_members" and "with alice in it" in str(e.value) and m.sudo_runs == 0
    done = send(p, make, ("accept_members",), standin.PASSWORD)
    assert done["ok"] and m.sudo_runs == 1 and m.groups()["liminal"].gid == 994
    assert row(p, "The group liminal")[1]["sub"] == "a system group; found here: undo keeps it"
    assert row(p, "The user liminal")[1]["sub"].endswith("made by Liminal")


@pytest.mark.parametrize("overlay, words", [
    ("group-1001", "is not a system group (gid 1001): Liminal's user and group are not made; rename that group first"),
    ("system-group-mixed", "has the member www-data, a system account: it may be another program's group"),
    ("person-user", "is a person's account (uid 1001): Liminal's user and group are not made; rename that user first"),
])
def test_a_group_or_user_named_liminal_that_is_not_one_liminal_can_take_is_refused_in_words(overlay, words):
    p, m = on("collision", overlay)
    assert "linux-make" not in forms(p) and words in row(p, "Make them…")[1] and m.sudo_runs == 0


def test_its_changes_are_asked_only_from_its_page():
    p, m = on()
    form = forms(p)["linux-make"]
    calls = len(m.calls)
    for who in ("firewall-linux", None):
        with asking.asking(who), pytest.raises(asking.AskRefused, match="asked only from its page"):
            p.ask("linux_apply", *args_of(form, password=standin.PASSWORD))
    assert m.sudo_runs == 0 and len(m.calls) == calls
    with asking.asking("firewall-linux"):
        facts = p.ask("linux_facts")
    assert facts["applies"] and facts["elevation"]["field"] == "yes" and json.loads(json.dumps(facts)) == facts


def test_not_for_here_reads_nothing_and_refuses_a_change():
    m = standin.Machine(UBUNTU)
    p = plugin(FakeLinux(), linux=m)
    p._native = "Linux administration is for the Linux the platform itself runs on, and this one runs Windows"
    assert p.status()["applies"] is False and p.linux_facts()["applies"] is False and m.calls == []
    with asking.asking(asking.PAGE), pytest.raises(ValueError, match="runs Windows"):
        p.linux_undo("0" * 64)


# ---- the command line ------------------------------------------------------------------------------------------------


def test_the_command_line_shows_them_and_names_the_root_command_for_changes(monkeypatch, capsys):
    p, m = on()
    monkeypatch.setattr(cli, "MACHINE", p)
    assert cli.main(["accounts"]) == 0
    out = capsys.readouterr().out
    assert "The group liminal: not here" in out and f"The one command: sudo {VENV} -I -B -m liminal_libs.linuxsys " \
                                                     "apply (as root, from a terminal: it asks nothing)" in out
    assert cli.main(["accounts", "--json"]) == 0
    facts = json.loads(capsys.readouterr().out)
    assert facts["applies"] and facts["lines"]["apply"].endswith("-I -B -m liminal_libs.linuxsys apply")
    assert m.sudo_runs == 0 and not [c for c in m.calls if "-S" in c["argv"]]  # it changes nothing
    assert cli.main(["accounts", "make"]) == 2
    usage = capsys.readouterr().err
    assert "accounts [--json]" in usage and "-I -B -m liminal_libs.linuxsys apply" in usage
    p._native = "not for this machine"
    assert cli.main(["accounts"]) == 1 and "not for this machine" in capsys.readouterr().err


def test_it_needs_the_library_release_with_the_linux_standard_interface():
    """0.9.0 is built on liminal-libs 1.101.0 (provisional: its number is given at landing): machines.linuxadmin and
    the plain package linuxsys. The package says so, and so do its version's three places."""
    text = (Path(__file__).parent.parent / "pyproject.toml").read_text(encoding="utf-8")
    floor = re.search(r'"liminal-libs>=(\d+)\.(\d+)\.(\d+)"', text)
    assert floor and tuple(int(n) for n in floor.groups()) >= (1, 101, 0)
    assert tuple(int(n) for n in liminal_libs.__version__.split(".")[:3]) >= (1, 101, 0)
    assert re.search(r'^version = "([^"]+)"', text, re.M).group(1) == plugin_platform_admin_linux.__version__ == "0.9.0"
