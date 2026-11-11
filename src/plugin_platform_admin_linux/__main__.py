"""`python -m plugin_platform_admin_linux status | setup [STEP ...] | services | startups | boot | processes
| service NAME start|stop|restart | startup APP run|end|enable|disable | startup APP start|stop --boot
| register APP [--boot [--port N]] | unregister APP [--boot --accept-removal] | run [--elevated] -- COMMAND`: the plugin
from the command line (the platform app drives the same hooks). `--boot`: the app's boot service (a system unit
liminal-platform-boot.service, or an OpenRC service) rather than its user unit at logon; a boot service's removal is
asked twice, so it needs --accept-removal."""
from __future__ import annotations

import json
import sys

from liminal_libs.machines.plugin import CommandError

from . import MACHINE

USAGE = ("python -m plugin_platform_admin_linux status | setup [STEP ...] | services | startups | boot | processes "
         "| service NAME start|stop|restart | startup APP run|end|enable|disable | startup APP start|stop --boot "
         "| register APP [--boot [--port N]] | unregister APP [--boot --accept-removal] | run [--elevated] -- COMMAND")


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
            elevated = "--elevated" in rest
            rest = [w for w in rest if w != "--elevated"]
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
