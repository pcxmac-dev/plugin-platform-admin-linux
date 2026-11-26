"""`python -m plugin_platform_admin_linux status | setup [STEP ...] | services | startups | boot | processes
| service NAME start|stop|restart | startup APP run|end|enable|disable | startup APP start|stop --boot
| register APP [--boot [--port N]] | unregister APP [--boot --accept-removal] | run [--elevated] -- COMMAND
| accounts [--json]`: the plugin from the command line, in its own process. The platform app asks the same hooks
from its page, its changes only from there (PAGE_ONLY_HOOKS, 0.8.1), but for run(), which no route of the platform's asks since liminal-platform 0.34.1.
`--boot`: the app's boot service (a system unit liminal-platform-boot.service, or an OpenRC service) rather than its
user unit at logon; a boot service's removal is asked twice, so it needs --accept-removal. `run` runs the command as
you, and as root (through the library's `sudo -n --`, liminal-libs 1.80.0, unless you are root) only with `--elevated`
as its first word, before the command's `--` (0.8.1): every word after `--` is the command's own, an `--elevated` among
them.

`accounts` (0.9.0) shows Liminal's user and group as the page's table does: the group liminal, Liminal's own user,
each member and whether the running platform has it, a change stopped part way, and the one root command for this
system; `--json` gives the library's facts as the page reads them (linux_facts). It changes nothing: a change of
Liminal's user and group is asked only from the page (the user's answer 6), or made by that one root command,
`sudo <python> -I -B -m liminal_libs.linuxsys apply`, run once in a terminal."""
from __future__ import annotations

import json
import sys

from liminal_libs.machines.plugin import CommandError

from . import MACHINE

USAGE = ("python -m plugin_platform_admin_linux status | setup [STEP ...] | services | startups | boot | processes "
         "| service NAME start|stop|restart | startup APP run|end|enable|disable | startup APP start|stop --boot "
         "| register APP [--boot [--port N]] | unregister APP [--boot --accept-removal] | run [--elevated] -- COMMAND "
         "| accounts [--json]\n"
         "Liminal's user and group are changed on the platform's page, or as root by one command run in a terminal: "
         "sudo <python> -I -B -m liminal_libs.linuxsys apply (`accounts` names it for this system)")


def _cell(cell) -> str:
    """A cell of the page's table as a line's words: its text, then what it says beneath, in brackets."""
    if isinstance(cell, dict):
        if "form" in cell:
            return ""  # a button of the page's: changes are asked there only
        text, sub = str(cell.get("text", "")), str(cell.get("sub", ""))
        return f"{text} ({sub})" if text and sub else text or sub
    return str(cell or "")


def accounts_text(machine) -> str:
    """Liminal's user and group as the page's table says them, one line a row, the table's note last."""
    tables, _, _, _ = machine.linux_sections()
    table = next(t for t in tables if t["title"] == "Liminal's user and group")
    lines = []
    for row in table["rows"]:
        what, here = _cell(row[0]), _cell(row[1])
        lines.append(f"{what}: {here}" if here else what)
    return "\n".join([*lines, "", table.get("note", "")]).rstrip() + "\n"


def _flags(rest: list[str]) -> tuple[list[str], bool, int | None, bool]:
    """The words, --boot, --port N and --accept-removal of a startup's command."""
    words, boot, port, accept = [], False, None, False
    i = 0
    while i < len(rest):
        w = rest[i]
        if w == "--boot":
            boot = True
        elif w == "--accept-removal":
            accept = True
        elif w == "--port" and i + 1 < len(rest) and rest[i + 1].isdecimal():
            port = int(rest[i + 1])
            i += 1
        else:
            words.append(w)
        i += 1
    return words, boot, port, accept


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    what, rest = (argv[0], argv[1:]) if argv else ("status", [])
    try:
        if what == "status":
            print(json.dumps(MACHINE.status(), indent=1))
            return 0 if MACHINE.present() else 1
        if what == "setup":
            done = MACHINE.setup(log=print, steps=rest or None)
            return 0 if all(d["ok"] is not False for d in done) else 1
        if what in ("services", "startups", "boot"):
            items = (MACHINE.services() if what == "services" else MACHINE.startups() if what == "startups"
                     else MACHINE.boot_startups(MACHINE.boot_apps()))
            print(json.dumps([i.describe() for i in items], indent=1))
            return 0
        if what == "accounts" and rest in ([], ["--json"]):
            facts = MACHINE.linux_facts(fresh=True)
            if not facts.get("applies"):
                print(facts.get("why", "not for this machine"), file=sys.stderr)
                return 1
            print(json.dumps(facts, indent=1) if rest else accounts_text(MACHINE).rstrip("\n"))
            return 0
        if what == "processes":
            print(json.dumps(MACHINE.processes(), indent=1))
            return 0
        if what == "service" and len(rest) == 2:
            MACHINE.service(rest[0], rest[1])
            print(f"{rest[0]}: {rest[1]} asked")
            return 0
        words, boot, port, accept = _flags(rest)
        if what == "startup" and len(words) == 2:
            said = MACHINE.startup(words[0], words[1], "boot" if boot else "logon")
            print(said["said"] if said else f"{words[0]}: {words[1]} asked")
            return 0
        if what == "register" and len(words) == 1:
            made = MACHINE.register(words[0], "boot", port) if boot else MACHINE.register(words[0])
            print(json.dumps(made.describe(), indent=1))
            return 0
        if what == "unregister" and len(words) == 1:
            if boot:
                print(MACHINE.unregister(words[0], "boot", accept)["said"])
            else:
                print("removed" if MACHINE.unregister(words[0]) else f"{words[0]} had no startup")
            return 0
        if what == "run":
            elevated = rest[:1] == ["--elevated"]  # a word of its own, before the command's `--`: never one of its words
            rest = rest[1:] if elevated else rest
            command = rest[1:] if rest[:1] == ["--"] else rest
            if command:
                print(MACHINE.run(*command, elevated=elevated), end="")
                return 0
    except CommandError as e:
        print(str(e) + (" (--accept-removal accepts it)" if getattr(e, "accept", None) else ""), file=sys.stderr)
        return 1
    print(USAGE, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
