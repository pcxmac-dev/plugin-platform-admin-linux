"""`python -m plugin_platform_admin_linux status | setup [STEP ...] | services | startups | processes | service NAME start|stop|restart
| startup APP run|end|enable|disable | register APP | unregister APP | run [--elevated] -- COMMAND`: the plugin from the
command line (the platform app drives the same hooks)."""
from __future__ import annotations

import json
import sys

from liminal_libs.machines.plugin import CommandError

from . import MACHINE

USAGE = ("python -m plugin_platform_admin_linux status | setup [STEP ...] | services | startups | processes | service NAME start|stop|restart "
         "| startup APP run|end|enable|disable | register APP | unregister APP | run [--elevated] -- COMMAND")


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
        if what in ("services", "startups"):
            items = MACHINE.services() if what == "services" else MACHINE.startups()
            print(json.dumps([i.describe() for i in items], indent=1))
            return 0
        if what == "processes":
            print(json.dumps(MACHINE.processes(), indent=1))
            return 0
        if what == "service" and len(rest) == 2:
            MACHINE.service(rest[0], rest[1])
            print(f"{rest[0]}: {rest[1]} asked")
            return 0
        if what == "startup" and len(rest) == 2:
            MACHINE.startup(rest[0], rest[1])
            print(f"{rest[0]}: {rest[1]} asked")
            return 0
        if what == "register" and rest:
            print(json.dumps(MACHINE.register(rest[0]).describe(), indent=1))
            return 0
        if what == "unregister" and rest:
            print("removed" if MACHINE.unregister(rest[0]) else f"{rest[0]} had no startup")
            return 0
        if what == "run":
            elevated = "--elevated" in rest
            rest = [w for w in rest if w != "--elevated"]
            command = rest[1:] if rest[:1] == ["--"] else rest
            if command:
                print(MACHINE.run(*command, elevated=elevated), end="")
                return 0
    except CommandError as e:
        print(str(e), file=sys.stderr)
        return 1
    print(USAGE, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
