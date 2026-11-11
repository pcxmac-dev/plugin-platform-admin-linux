"""Linux administration for Liminal (the user, 2026-11-07: "a windows and linux admin plugin for platform") on the
native Linux machine the platform runs on, and nowhere else (the user, 2026-11-08: "the scope of linux administration
is only on native linux O/S"; "it's not for administrating WSL instances"): on Windows, on macOS and inside a WSL
distribution it runs no command at all (Liminal's WSL distributions are the WSL plugins'). Through the library's
machines.linux.Shell on this machine: whether the platform has root's rights and how they are had (root; sudo
without a password); the services the framework relies on (Docker and containerd, the firewall, DNS), started when
stopped, under systemd or OpenRC or the service command, and the SSH server shown but never started on its own; the
framework's startups as systemd user units (liminal-charts, liminal-integrator, liminal-login, liminal-platform),
read, run, ended, made or removed when asked; the framework's processes running. The library's Admin base holds the
checks, the status and the setup.

At boot, before anyone signs in (0.5.0; the user, 2026-11-11: "also windows and linux admin, need sections for
starting the platform, or an app that inherits the platform object as a service, headless"; "on boot"): the platform,
or an app inheriting it, as a system service started by the init: under systemd a system unit
/etc/systemd/system/liminal-<app>-boot.service (WantedBy=multi-user.target, User= the platform's own user, never root,
Restart=on-failure, SIGINT to stop), under OpenRC an init script /etc/init.d/liminal-<app>-boot in the default
runlevel (supervise-daemon, command_user, respawned). A system unit rather than a user unit with `loginctl
enable-linger`: lingering would start every enabled user unit of the user's at boot, the startups at logon above
too, and keep them running after the user signs out; OpenRC has no user units at all, so one shape serves both. Written
only on this native Linux machine, as root through `sudo -n` (never asking for a password), each change confirmed on
the page, a removal twice.

    python -m plugin_platform_admin_linux status | setup [STEP ...] | services | startups | boot | processes
                                          | service NAME start|stop|restart | startup APP run|end|enable|disable
                                          | startup APP start|stop --boot | register APP [--boot [--port N]]
                                          | unregister APP [--boot --accept-removal] | run [--elevated] -- COMMAND
"""
from __future__ import annotations

import os
import re
import shlex
from pathlib import Path

from liminal_libs import web
from liminal_libs.machines import linux
from liminal_libs.machines.admin import Admin, AdminError, BootApp, BootRefused, Startup, SystemService, app_of, boot_command
from liminal_libs.machines.linux import Shell
from liminal_libs.machines.plugin import CommandError

__version__ = "0.5.0"
UNITS = {"charts": "liminal-charts", "integrator": "liminal-integrator", "login": "liminal-login", "platform": "liminal-platform"}
TASK_VERBS = {"run": "start", "end": "stop", "enable": "enable", "disable": "disable"}
RESTART_SECONDS = 10
# the boot services (0.5.0)
SYSTEMD_DIR = "/etc/systemd/system"
OPENRC_DIR = "/etc/init.d"
LOG_DIR = "/var/log"
BOOT_UNIT = re.compile(r"liminal-([a-z][a-z0-9]*)-boot(?:\.service)?")
USER_NAME = re.compile(r"[a-z_][a-z0-9_-]{0,31}")  # an account a unit's User= or command_user names
WORD = re.compile(r"[A-Za-z0-9_./+@:,=-]+")  # a word a unit or an init script carries as it is
SPACED = re.compile(r"[A-Za-z0-9_./+@:,=%$ -]+")  # a word a unit carries once quoted (% and $ doubled)
BACKOFF = (6, 600)  # systemd 254 and later: RestartSteps, RestartMaxDelaySec (older ones say the keys are unknown and go on)
END = "LIMINAL_FILE"  # the here-document's end when a file is written as root


def why_not_native(system: str | None = None, release: str | None = None, env=None) -> str:
    """Why the machine the platform runs on is not a native Linux one, in words ("" when it is: the only machine this
    plugin administers): the library's check (liminal-libs 1.27.0, shared with the Linux firewall) naming Linux
    administration. `system`, `release` and `env` stand in for sys.platform, the kernel's release and the environment."""
    return linux.why_not_native("Linux administration", system, release, env)


def blocks(text: str) -> dict[str, dict[str, str]]:
    """`== name` headed blocks of Key=Value lines (systemctl show), by name."""
    out: dict[str, dict[str, str]] = {}
    current = None
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("== "):
            current = line[3:].strip()
            out[current] = {}
        elif current is not None and "=" in line:
            k, _, v = line.partition("=")
            out[current][k] = v
    return out


def state_of(fields: dict) -> str:
    """A unit's state in the framework's words: absent when systemd knows none of that name."""
    if not fields or fields.get("LoadState") in ("not-found", "") or fields.get("LoadState", "").startswith("error"):
        return "absent"
    active = fields.get("ActiveState", "")
    return "running" if active == "active" else ("stopped" if active in ("inactive", "failed", "deactivating") else active or "unknown")


def unit_text(app: str, command: list[str]) -> str:
    """A user unit starting `app` for good, as the integrator's own unit does."""
    return ("[Unit]\n"
            f"Description=The Liminal {app} app (made by the Liminal platform)\n"
            "After=network-online.target\n\n"
            "[Service]\n"
            f"ExecStart={' '.join(shlex.quote(c) for c in command)}\n"
            "Restart=on-failure\n"
            f"RestartSec={RESTART_SECONDS}\n"
            "KillSignal=SIGINT\n\n"
            "[Install]\n"
            "WantedBy=default.target\n")


# -- the boot services (0.5.0) ---------------------------------------------------------------------------------------
def boot_unit(app: str) -> str:
    """An app's boot unit under systemd: liminal-<app>-boot.service, a system unit beside its user unit liminal-<app>.service."""
    return f"liminal-{app}-boot.service"


def boot_service(app: str) -> str:
    """An app's boot service under OpenRC: /etc/init.d/liminal-<app>-boot."""
    return f"liminal-{app}-boot"


def app_of_unit(name: str) -> str:
    """The app a boot unit or service is for ("" for one not named as one: liminal-platform.service, a user unit)."""
    m = BOOT_UNIT.fullmatch(name or "")
    return m.group(1) if m else ""


def plain(title: str) -> str:
    """A title as a unit's Description= or an init script's description="..." carries it: letters, digits, spaces, ._()-."""
    return re.sub(r"[^A-Za-z0-9 ._()-]", "", str(title or "")).strip() or "Liminal"


def unit_word(word: str) -> str:
    """A word of ExecStart= as systemd reads it: % and $ doubled (its specifiers, its variables), one with a space in
    double quotes; BootRefused for one a unit cannot carry safely (a quote, a backslash, a control character)."""
    if WORD.fullmatch(word):
        return word
    if not SPACED.fullmatch(word or ""):
        raise BootRefused(f"{word!r} cannot be written into a unit safely: a boot service runs a Python whose path has letters, "
                          "digits, spaces and ._/+@:,=- only")
    w = word.replace("%", "%%").replace("$", "$$")
    return f'"{w}"' if " " in w else w


def boot_unit_text(app: BootApp, command: list[str], user: str) -> str:
    """A system unit starting `app` at boot, as `user` (never root), started again after a failure, stopped by SIGINT."""
    return ("[Unit]\n"
            f"Description={plain(app.title)} at boot, before anyone signs in (made by the Liminal platform)\n"
            "Wants=network-online.target\n"
            "After=network-online.target\n\n"
            "[Service]\n"
            "Type=simple\n"
            f"User={user}\n"
            f"ExecStart={' '.join(unit_word(c) for c in command)}\n"
            "Restart=on-failure\n"
            f"RestartSec={RESTART_SECONDS}\n"
            f"RestartSteps={BACKOFF[0]}\n"
            f"RestartMaxDelaySec={BACKOFF[1]}\n"
            "KillSignal=SIGINT\n"
            "TimeoutStopSec=30\n\n"
            "[Install]\n"
            "WantedBy=multi-user.target\n")


def openrc_text(app: BootApp, command: list[str], user: str, home: str = "") -> str:
    """An OpenRC init script starting `app` at boot as `user` (never root), supervised and respawned, its errors in
    /var/log/liminal-<app>-boot.log; BootRefused for a command it cannot carry safely."""
    bad = [w for w in command if not WORD.fullmatch(w)]
    if bad:
        raise BootRefused(f"{bad[0]!r} cannot be written into an init script safely: a boot service runs a Python whose path has "
                          "letters, digits and ._/+@:,=- only")
    name, (exe, *args) = boot_service(app.name), command
    env = f'supervise_daemon_args="--env HOME={home}"\n' if home and WORD.fullmatch(home) else ""
    return ("#!/sbin/openrc-run\n"
            f"# {plain(app.title)} at boot, before anyone signs in (made by the Liminal platform)\n\n"
            f'description="{plain(app.title)} at boot, before anyone signs in"\n'
            "supervisor=supervise-daemon\n"
            f'command="{exe}"\n'
            f'command_args="{" ".join(args)}"\n'
            f'command_user="{user}"\n'
            f"{env}"
            f'error_log="{LOG_DIR}/{name}.log"\n'
            f"respawn_delay={RESTART_SECONDS}\n"
            "respawn_max=0\n"
            'retry="SIGINT/30/SIGKILL/5"\n\n'
            "depend() {\n\tuse net\n\tafter firewall\n}\n\n"
            'start_pre() {\n\tcheckpath --file --owner "$command_user" --mode 0640 "$error_log"\n}\n')


def root_write(path: str, text: str, mode: str) -> str:
    """The sh writing `text` to `path` as root, whole or not at all (a file beside it moved into place), owned by root."""
    if f"\n{END}\n" in f"\n{text}" or not text.endswith("\n"):
        raise BootRefused(f"{path} cannot be written: its text holds a line of its own end")
    new = f"{path}.liminal-new"
    return (f"set -e\numask 022\ncat > {new} <<'{END}'\n{text}{END}\n"
            f"chmod {mode} {new}\nchown root:root {new}\nmv -f {new} {path}\n")


def unquoted(value: str) -> str:
    v = str(value or "").strip()
    return v[1:-1] if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'" else v


class LinuxAdminPlugin(Admin):
    name = "admin-linux"
    title = "Linux administration"
    about = ("The native Linux machine the platform runs on, never a WSL distribution: root's rights and how they are had, "
             "the services the framework relies on, the apps' systemd user units, the platform's at boot, the framework's processes")
    api = "2.1"
    order = 721
    BOOT_SERVICES = True
    SERVICES = (("docker", "Docker Engine", "the containers", True),
                ("containerd", "containerd", "Docker's runtime", True),
                ("ufw", "Uncomplicated Firewall", "the firewall plugin", True),
                ("firewalld", "firewalld", "the firewall plugin", True),
                ("systemd-resolved", "systemd's DNS resolver", "every lookup: the mail record, the feeds", True),
                ("ssh", "OpenSSH server", "remote access (shown; never started by the setup)", False),
                ("sshd", "OpenSSH server", "remote access (shown; never started by the setup)", False))

    def __init__(self, shell: Shell | None = None, runner=None, home: Path | None = None, native: str | None = None,
                 user: tuple[str, str] | None = None, apps=None, logs: Path | None = None, python: str | None = None,
                 listening=None):
        self._shell = shell
        self._runner = runner
        self._home = home
        self._native = native  # a test's word for why_not_native(): "" on a native Linux machine, else why not
        self._user = user  # a test's (name, home) a boot service runs as; None: the platform's own
        self._apps = apps  # a test's boot apps; None: the library's (the platform, the apps inheriting it)
        self._logs = logs  # a test's logs folder; None: the platform's
        self._python = python  # a test's Python; None: this one
        self._listening = listening or web.listening  # whether something answers at a port (a test's stand-in)

    def not_for_here(self) -> str:
        """Why the machine the platform runs on is not a native Linux one, in words ("" when it is): the library's
        status and setup honor it (applies False, nothing changed)."""
        return why_not_native() if self._native is None else self._native

    @property
    def shell(self) -> Shell:
        """This native Linux machine's commands (sudo -n when the platform is not root); refused anywhere else."""
        note = self.not_for_here()
        if note:
            raise AdminError(note)
        sh = self._shell if self._shell is not None else Shell("local", runner=self._runner)
        if sh.target != "local":
            raise AdminError(f"Linux administration is for this native Linux machine, never {sh.where}")
        return sh

    def present(self) -> bool:
        """A native Linux machine, the platform's own: never Windows, macOS or a WSL distribution."""
        if self.not_for_here():
            return False
        try:
            return self.shell.here
        except CommandError:
            return False

    def elevated(self) -> bool:
        return self.shell.root()

    def may_elevate(self) -> bool:
        """Root's rights are had when a change needs them: the platform is root, or sudo runs without a password."""
        sh = self.shell
        if sh.root():
            return True
        try:
            sh.run("true")  # sudo -n true
            return True
        except CommandError:
            return False

    def elevation(self) -> str:
        sh = self.shell
        if sh.root():
            return "the platform runs as root"
        try:
            sh.run("true")  # sudo -n true
            return "not root; sudo without a password"
        except CommandError:
            return "not root, and sudo asks for a password: run the platform as root, or allow it sudo without one"

    def _init(self) -> str:
        """systemd, OpenRC or the service command, as the target has."""
        out = self.shell.sh("if [ -d /run/systemd/system ]; then echo systemd; elif command -v rc-service >/dev/null 2>&1; "
                            "then echo openrc; else echo service; fi", root=False).strip().splitlines()
        return out[-1].strip() if out else "service"

    def services(self) -> list[SystemService]:
        names = [s[0] for s in self.SERVICES]
        init = self._init()
        if init == "systemd":
            script = "; ".join(f"echo '== {n}'; systemctl show -p LoadState,ActiveState,UnitFileState,Description {n}.service" for n in names)
            found = blocks(self.shell.sh(script, root=False))
            return [SystemService(n, found.get(n, {}).get("Description") or title, state_of(found.get(n, {})),
                                  found.get(n, {}).get("UnitFileState", ""), used, may) for n, title, used, may in self.SERVICES]
        probe = "rc-service" if init == "openrc" else "service"
        script = "; ".join(f"{probe} {n} status >/dev/null 2>&1; echo '{n} '$?" for n in names)
        codes = dict(line.split() for line in self.shell.sh(script).splitlines() if len(line.split()) == 2)
        out = []
        for n, title, used, may in self.SERVICES:
            code = codes.get(n, "")
            state = "running" if code == "0" else "stopped" if code == "3" else "absent"
            out.append(SystemService(n, title, state, "", used, may))
        return out

    def _service_action(self, name: str, action: str) -> None:
        init = self._init()
        if init == "systemd":
            self.shell.run("systemctl", action, name)
        elif init == "openrc":
            self.shell.run("rc-service", name, action)
        else:
            self.shell.run("service", name, action)

    def startups(self) -> list[Startup]:
        sh = self.shell  # refused anywhere but a native Linux machine
        script = "; ".join(f"echo '== {u}'; systemctl --user show -p LoadState,ActiveState,UnitFileState,ExecStart {u}.service"
                           for u in UNITS.values())
        try:
            found = blocks(sh.sh(script, root=False))
        except CommandError as e:
            return [Startup(app, unit, "unknown", detail=f"systemd's user units cannot be read: {e}") for app, unit in UNITS.items()]
        out = []
        for app, unit in UNITS.items():
            f = found.get(unit, {})
            state = state_of(f)
            if state not in ("absent", "running") and f.get("UnitFileState") == "disabled":
                state = "disabled"
            elif state == "stopped":
                state = "ready"
            m = re.search(r"argv\[\]=([^;]*)", f.get("ExecStart", ""))
            out.append(Startup(app, f"{unit}.service", state, (m.group(1).strip() if m else ""), f"enabled: {f.get('UnitFileState', '')}"))
        return out

    def _startup_action(self, app: str, action: str) -> None:
        self.shell.run("systemctl", "--user", TASK_VERBS[action], f"{UNITS[app]}.service", root=False)

    def unit_path(self, app: str) -> Path:
        return (self._home or Path.home()) / ".config" / "systemd" / "user" / f"{UNITS[app]}.service"

    def _register(self, app: str, command: list[str]) -> None:
        sh = self.shell  # refused anywhere but a native Linux machine: no unit written
        path = self.unit_path(app)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(unit_text(app, command), encoding="utf-8")
        sh.run("systemctl", "--user", "daemon-reload", root=False)
        sh.run("systemctl", "--user", "enable", f"{UNITS[app]}.service", root=False)

    def _unregister(self, app: str) -> bool:
        sh = self.shell  # refused anywhere but a native Linux machine: nothing removed
        path = self.unit_path(app)
        existed = path.exists()
        sh.run("systemctl", "--user", "disable", "--now", f"{UNITS[app]}.service", root=False, check=False)
        if existed:
            path.unlink()
        sh.run("systemctl", "--user", "daemon-reload", root=False, check=False)
        return existed

    # -- at boot, before anyone signs in (0.5.0) ---------------------------------------------------------------------
    def boot_account(self) -> tuple[str, str]:
        """Who a boot service runs as, with its home: the platform's own user (the one sudo was run by when the platform
        runs as root), never root; BootRefused when there is none such."""
        if self._user is not None:
            name, home = self._user
        else:
            try:
                import pwd

                uid = os.geteuid()
                name = pwd.getpwuid(uid).pw_name
                if uid == 0:
                    name = str(os.environ.get("SUDO_USER") or "").strip()
                home = pwd.getpwnam(name).pw_dir if name and name != "root" else ""
            except (ImportError, AttributeError, KeyError) as e:
                raise BootRefused(f"who the platform runs as is not known here ({e})") from None
        if not name or name == "root":
            raise BootRefused("the platform runs as root: a boot service runs as an ordinary account, never root; start the "
                              "platform as the user it should run as (or through sudo), then register it")
        if not USER_NAME.fullmatch(name):
            raise BootRefused(f"{name!r} is not an account name a unit can carry safely")
        return name, str(home or "")

    def boot_env(self):
        return os.environ

    def boot_logs(self) -> Path:
        return Path(self._logs) if self._logs is not None else super().boot_logs()

    def boot_apps(self) -> list[BootApp]:
        return list(self._apps) if self._apps is not None else super().boot_apps()

    def boot_how(self) -> str:
        init = self._init()  # refused anywhere but a native Linux machine
        if init == "systemd":
            return "a system unit (liminal-<app>-boot.service) started by systemd as you, never root, again after a failure"
        if init == "openrc":
            return "an OpenRC service (liminal-<app>-boot) in the default runlevel, as you, never root, respawned by supervise-daemon"
        raise BootRefused("this machine's init is neither systemd nor OpenRC: no boot service is made here")

    def boot_details(self) -> str:
        if self._init() == "openrc":
            return (f"an OpenRC service, {OPENRC_DIR}/liminal-<app>-boot, in the default runlevel: started at boot, before anyone "
                    "signs in, as you (command_user, never root), supervised by supervise-daemon and started again 10 s after "
                    f"a failure, stopped by SIGINT, its errors in {LOG_DIR}/liminal-<app>-boot.log")
        return (f"a system unit, {SYSTEMD_DIR}/liminal-<app>-boot.service, wanted by multi-user.target: started by systemd at "
                "boot, before anyone signs in, as you (User=, never root), started again 10 s after a failure "
                "(Restart=on-failure; systemd 254 and later wait up to 10 min while it keeps failing), stopped by SIGINT, its "
                "output in systemd's journal. A system unit rather than a user unit with lingering: lingering would start "
                "every user unit of yours at boot, the startups at your logon too, and keep them running after you sign out")

    def boot_rights(self) -> str:
        return "" if self.shell.root() else "As root through sudo without a password (never asked for one)"

    def boot_stopping(self) -> str:
        return "its supervisor sends it SIGINT, as Ctrl+C: it closes what it holds"

    def boot_startups(self, apps: list[BootApp]) -> list[Startup]:
        init = self._init()
        if init == "systemd":
            names = " ".join(boot_unit(a.name) for a in apps)
            script = (f"for u in {names} $(for f in {SYSTEMD_DIR}/liminal-*-boot.service; do [ -e \"$f\" ] && echo \"${{f##*/}}\"; done); "
                      "do echo \"== $u\"; systemctl show -p LoadState,ActiveState,SubState,UnitFileState,ExecStart,User \"$u\"; done")
            read, of = self._systemd_boot, boot_unit
        elif init == "openrc":
            names = " ".join(boot_service(a.name) for a in apps)
            script = (f"for n in {names} $(for f in {OPENRC_DIR}/liminal-*-boot; do [ -e \"$f\" ] && echo \"${{f##*/}}\"; done); do "
                      "echo \"== $n\"; if [ -f \"" + OPENRC_DIR + "/$n\" ]; then echo File=yes; "
                      "grep -E '^(command|command_args|command_user|error_log)=' \"" + OPENRC_DIR + "/$n\"; "
                      "rc-service \"$n\" status >/dev/null 2>&1; echo \"Status=$?\"; "
                      "if rc-update show default 2>/dev/null | grep -q \"^ *$n |\"; then echo Default=yes; else echo Default=no; fi; "
                      "else echo File=no; fi; done")
            read, of = self._openrc_boot, boot_service
        else:
            return []
        found = blocks(self.shell.sh(script, root=False))
        by_app = {app_of_unit(name): f for name, f in found.items() if app_of_unit(name)}
        out = [read(a.name, by_app.pop(a.name, None), a) for a in apps]
        return out + [read(app, f, None) for app, f in sorted(by_app.items())]

    def _absent(self, app: str, name: str, known: BootApp | None, log: str) -> Startup:
        """A boot service not registered: what registering it would make, at the app's own port."""
        try:
            account = self.boot_account()[0]
        except BootRefused:
            account = ""
        port = known.port if known is not None else 0
        would = " ".join(shlex.quote(c) for c in boot_command(known, port, self._python)) if known is not None else ""
        return Startup(app, name, "absent", would, "", "boot", account, log, port)

    def _systemd_boot(self, app: str, f: dict | None, known: BootApp | None) -> Startup:
        unit, log = boot_unit(app), f"journalctl -u {boot_unit(app)}"
        if not f or f.get("LoadState") in ("not-found", "") or f.get("LoadState", "").startswith("error"):
            return self._absent(app, unit, known, log)
        m = re.search(r"argv\[\]=([^;]*)", f.get("ExecStart", ""))
        command = m.group(1).strip() if m else ""
        port = int(p.group(1)) if (p := re.search(r"--port\s+(\d+)", command)) else 0
        active, sub, enabled = f.get("ActiveState", ""), f.get("SubState", ""), f.get("UnitFileState", "")
        state = {"active": "running", "inactive": "stopped", "failed": "failed", "deactivating": "stopping",
                 "activating": "restarting" if sub == "auto-restart" else "starting"}.get(active, active or "unknown")
        if state == "running" and port and not self._listening(port):
            state = "starting"
        if state in ("stopped", "failed") and enabled not in ("enabled", "enabled-runtime"):
            state = "disabled"
        notes = [f"at boot: {enabled or 'not said'}"]
        if not f.get("User") or f.get("User") == "root":
            notes.append("it runs as root: register it again to run as you")
        return Startup(app, unit, state, command, "; ".join(notes), "boot", f.get("User") or "root", log, port)

    def _openrc_boot(self, app: str, f: dict | None, known: BootApp | None) -> Startup:
        name = boot_service(app)
        log = f"{LOG_DIR}/{name}.log"
        if not f or f.get("File") != "yes":
            return self._absent(app, name, known, log)
        command = f"{unquoted(f.get('command', ''))} {unquoted(f.get('command_args', ''))}".strip()
        port = int(p.group(1)) if (p := re.search(r"--port\s+(\d+)", command)) else 0
        code = f.get("Status", "")
        state = "running" if code == "0" else "stopped" if code == "3" else "failed"
        if state == "running" and port and not self._listening(port):
            state = "starting"
        in_default = f.get("Default") == "yes"
        if state in ("stopped", "failed") and not in_default:
            state = "disabled"
        user = unquoted(f.get("command_user", "")).split(":")[0]
        notes = ["at boot: in the default runlevel" if in_default else "not in the default runlevel: it does not start at boot"]
        if state == "failed":
            notes.append(f"its status says {code or 'nothing'}")
        if not user or user == "root":
            notes.append("it runs as root: register it again to run as you")
        return Startup(app, name, state, command, "; ".join(notes), "boot", user or "root", unquoted(f.get("error_log", "")) or log, port)

    def _boot_register(self, app: BootApp, port: int, python: str | None = None) -> None:
        sh = self.shell  # refused anywhere but a native Linux machine: nothing written
        user, home = self.boot_account()
        command = boot_command(app, port, python or self._python)
        init = self._init()
        if init == "systemd":
            unit = boot_unit(app.name)
            script = (root_write(f"{SYSTEMD_DIR}/{unit}", boot_unit_text(app, command, user), "0644")
                      + f"systemctl daemon-reload\nsystemctl enable {unit} >/dev/null 2>&1\necho registered\n")
        elif init == "openrc":
            name = boot_service(app.name)
            script = (root_write(f"{OPENRC_DIR}/{name}", openrc_text(app, command, user, home), "0755")
                      + f"rc-update add {name} default >/dev/null\necho registered\n")
        else:
            raise BootRefused("this machine's init is neither systemd nor OpenRC: no boot service is made here")
        out = sh.sh(script, root=True)
        if "registered" not in out:
            raise CommandError(f"the boot service of {app.name} was not registered: {out.strip() or 'no answer'}")

    def _boot_action(self, boot: Startup, action: str) -> None:
        if self._init() == "openrc":
            self.shell.run("rc-service", boot.name, action)
        else:
            self.shell.run("systemctl", action, boot.name)

    def _boot_unregister(self, boot: Startup) -> bool:
        sh = self.shell  # refused anywhere but a native Linux machine: nothing removed
        if self._init() == "openrc":
            path = f"{OPENRC_DIR}/{boot.name}"
            script = (f"if [ -e {path} ]; then rc-service {boot.name} stop >/dev/null 2>&1 || true; "
                      f"rc-update del {boot.name} default >/dev/null 2>&1 || true; rm -f {path}; echo removed; else echo absent; fi")
        else:
            path = f"{SYSTEMD_DIR}/{boot.name}"
            script = (f"if [ -e {path} ]; then systemctl disable --now {boot.name} >/dev/null 2>&1 || true; rm -f {path}; "
                      f"systemctl daemon-reload; systemctl reset-failed {boot.name} >/dev/null 2>&1 || true; echo removed; "
                      "else echo absent; fi")
        return "removed" in sh.sh(script, root=True)

    def processes(self) -> list[dict]:
        out = []
        for line in self.shell.run("ps", "-eo", "pid=,rss=,args=", root=False).splitlines():
            parts = line.split(None, 2)
            if len(parts) == 3 and parts[0].isdecimal() and "liminal_" in parts[2] and "ps -eo" not in parts[2]:
                out.append({"pid": int(parts[0]), "app": app_of(parts[2]), "command": parts[2],
                            "memoryMb": round(int(parts[1]) / 1024) if parts[1].isdecimal() else 0})
        return out

    def run(self, *command: str, elevated: bool = False, **options) -> str:
        """A command on this machine, its output; `elevated`: as root."""
        return self.shell.run(*command, root=elevated)


MACHINE = LinuxAdminPlugin()
