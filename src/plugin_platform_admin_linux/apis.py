"""What Linux administration attaches to (plugin API 2.2, liminal_libs.sources.apis; the user, 2026-11-11: "each plugin
should reflect the the API its attached to, and present links that provide documentation ... it should also expose more
of what the API is about"): systemd's systemctl and its unit files, OpenRC, the SysV service command, sudo (how root's
rights are had) and procps' ps, each as its makers' pages describe it. Every address was read on 2026-11-11
(`VERIFIED`). `facts` says what the plugin kept of them while it ran (asking nothing): whether sudo ran without a
password, when last asked."""
from __future__ import annotations

import time

from liminal_libs.sources.apis import Api, Area, Call, Link

VERIFIED = "2026-11-11"
SYSTEMD = "https://www.freedesktop.org/software/systemd/man/latest/"
OPENRC = "https://github.com/OpenRC/openrc/blob/master/"
SUDO = "https://www.sudo.ws/docs/man/"
MAN7 = "https://man7.org/linux/man-pages/"

SYSTEMCTL = Api(
    name="systemd (systemctl)",
    maker="the systemd project",
    about=("systemd, the init and service manager most Linux distributions run as PID 1, with a manager of its own for "
           "each signed-in user; systemctl asks either about its units and starts, stops, enables and reloads them, and "
           "unit files describe what a unit runs, when and as whom. The plugin reads and changes the services the "
           "framework relies on, keeps each app's startup at your logon as a user unit, and the platform's start at boot "
           "as a system unit that runs as you, never root."),
    kind="command",
    base="systemctl (the system manager as root through sudo -n; systemctl --user as you)",
    version=("systemd 262's manual; RestartSteps= and RestartMaxDelaySec= need systemd 254 or later (older ones skip the "
             "keys and go on)"),
    auth=("your own user units: as you, no root; system units and the services: root, had through sudo without a "
          "password (never asked for one)"),
    limits="",
    costs="",
    links=(
        Link("systemd's manual pages", SYSTEMD, "docs"),
        Link("systemctl(1)", SYSTEMD + "systemctl.html", "reference"),
        Link("systemd.unit(5)", SYSTEMD + "systemd.unit.html", "reference"),
        Link("systemd.service(5)", SYSTEMD + "systemd.service.html", "reference"),
        Link("systemd.exec(5)", SYSTEMD + "systemd.exec.html", "reference"),
        Link("systemd.special(7): the targets", SYSTEMD + "systemd.special.html", "reference"),
        Link("systemd.io", "https://systemd.io/", "guide"),
        Link("systemd's news", "https://github.com/systemd/systemd/blob/main/NEWS", "changelog"),
        Link("systemd's source", "https://github.com/systemd/systemd", "source"),
    ),
    areas=(
        Area("Units and their state", "each unit's load, active and enabled state and its properties", SYSTEMD + "systemctl.html",
             covered="the framework's services (docker, containerd, ufw, firewalld, systemd-resolved; ssh shown only), the "
                     "apps' user units, the platform's boot unit"),
        Area("Starting and stopping", "a unit started, stopped or restarted now", SYSTEMD + "systemctl.html",
             covered="Start…, Stop…, Restart… of a service; Run… and End… of a startup; Start… and Stop… at boot"),
        Area("Enabling at boot or logon", "a unit wanted by a target, so it starts with it", SYSTEMD + "systemctl.html",
             covered="a user unit enabled (default.target), a boot unit enabled (multi-user.target)"),
        Area("The user manager", "a manager of each signed-in user's own units (systemctl --user)", SYSTEMD + "systemd.html",
             covered="the apps' startups at your logon, in ~/.config/systemd/user"),
        Area("Unit files", "[Unit], [Service] and [Install]: what runs, its restarts, its signal, as whom", SYSTEMD + "systemd.unit.html",
             covered=("written by the plugin: ExecStart=, Restart=on-failure, RestartSec=10, RestartSteps= and "
                      "RestartMaxDelaySec= (a boot unit), KillSignal=SIGINT, User= (never root), WantedBy=")),
        Area("Reloading the manager", "systemd reading its unit files again", SYSTEMD + "systemctl.html",
             covered="after a unit is written or removed"),
        Area("The journal", "the units' logs", SYSTEMD + "journalctl.html",
             covered="a boot unit's output is in it: the page names journalctl -u as its log"),
        Area("Lingering", "a user's manager started at boot and kept after logout (loginctl enable-linger)",
             SYSTEMD + "loginctl.html"),
        Area("Timers", "units started on a calendar or after a time", SYSTEMD + "systemd.timer.html"),
        Area("Transient units", "a command run as a unit of its own (systemd-run)", SYSTEMD + "systemd-run.html"),
    ),
    calls=(
        Call("systemctl show -p LoadState,ActiveState,UnitFileState,Description <unit>", "a service's state and description",
             "Units and their state", used="the services the framework relies on", docs=SYSTEMD + "systemctl.html"),
        Call("systemctl --user show -p LoadState,ActiveState,UnitFileState,ExecStart <unit>", "a user unit's state and command",
             "The user manager", used="the startups at your logon", docs=SYSTEMD + "systemctl.html"),
        Call("systemctl show -p LoadState,ActiveState,SubState,UnitFileState,ExecStart,User <unit>",
             "a boot unit's state, command and user", "Units and their state", used="the platform at boot",
             docs=SYSTEMD + "systemctl.html"),
        Call("systemctl start <unit>", "a unit started", "Starting and stopping", used="Start… (a service; at boot); the setup",
             docs=SYSTEMD + "systemctl.html", writes=True),
        Call("systemctl stop <unit>", "a unit stopped", "Starting and stopping", used="Stop… (a service; at boot)",
             docs=SYSTEMD + "systemctl.html", writes=True),
        Call("systemctl restart <unit>", "a unit stopped and started", "Starting and stopping", used="Restart… (a service)",
             docs=SYSTEMD + "systemctl.html", writes=True),
        Call("systemctl --user start <unit>", "a user unit started", "The user manager", used="Run… (a startup at logon)",
             docs=SYSTEMD + "systemctl.html", writes=True),
        Call("systemctl --user stop <unit>", "a user unit stopped", "The user manager", used="End… (a startup at logon)",
             docs=SYSTEMD + "systemctl.html", writes=True),
        Call("systemctl --user enable <unit>", "a user unit wanted at logon", "Enabling at boot or logon",
             used="Register…; Enable… (a startup at logon)", docs=SYSTEMD + "systemctl.html", writes=True),
        Call("systemctl --user disable <unit>", "a user unit no longer wanted", "Enabling at boot or logon",
             used="Disable… (a startup at logon)", docs=SYSTEMD + "systemctl.html", writes=True),
        Call("systemctl --user disable --now <unit>", "a user unit stopped and no longer wanted", "The user manager",
             used="Remove… (a startup at logon)", docs=SYSTEMD + "systemctl.html", writes=True),
        Call("systemctl --user daemon-reload", "the user manager's unit files read again", "Reloading the manager",
             used="after a user unit is written or removed", docs=SYSTEMD + "systemctl.html", writes=True),
        Call("systemctl daemon-reload", "the system manager's unit files read again", "Reloading the manager",
             used="after a boot unit is written or removed", docs=SYSTEMD + "systemctl.html", writes=True),
        Call("systemctl enable <unit>", "a unit wanted at boot", "Enabling at boot or logon", used="the platform registered at boot",
             docs=SYSTEMD + "systemctl.html", writes=True),
        Call("systemctl disable --now <unit>", "a unit stopped and no longer wanted at boot", "Enabling at boot or logon",
             used="the platform's boot unit removed (asked twice)", docs=SYSTEMD + "systemctl.html", writes=True),
        Call("systemctl reset-failed <unit>", "a unit's failed state forgotten", "Units and their state",
             used="after a boot unit is removed", docs=SYSTEMD + "systemctl.html", writes=True),
        Call("~/.config/systemd/user/liminal-<app>.service", "a user unit file", "Unit files",
             used="written for a startup at your logon, removed with it", docs=SYSTEMD + "systemd.unit.html", writes=True),
        Call("/etc/systemd/system/liminal-<app>-boot.service", "a system unit file", "Unit files",
             used="written as root (whole, or not at all) for the platform at boot", docs=SYSTEMD + "systemd.service.html",
             writes=True),
        Call("journalctl -u <unit>", "a unit's log", "The journal", docs=SYSTEMD + "journalctl.html"),
        Call("loginctl enable-linger <user>", "a user's manager kept from boot to after logout", "Lingering",
             docs=SYSTEMD + "loginctl.html", writes=True),
        Call("systemctl mask <unit>", "a unit nothing can start", "Starting and stopping", docs=SYSTEMD + "systemctl.html",
             writes=True),
        Call("systemd-run <command>", "a command run as a transient unit", "Transient units", docs=SYSTEMD + "systemd-run.html",
             writes=True),
    ),
    verified=VERIFIED,
)

OPENRC_API = Api(
    name="OpenRC",
    maker="the OpenRC project",
    about=("OpenRC, a dependency-based init system (Gentoo's own, and Alpine's): services are openrc-run scripts in /etc/init.d, "
           "started and stopped with rc-service and put in a runlevel with rc-update, a daemon supervised and respawned "
           "by supervise-daemon. Where it is the init, the plugin reads and changes the framework's services with it and "
           "writes the platform's start at boot as an init script in the default runlevel, run as you, never root."),
    kind="command",
    base="rc-service and rc-update, as root through sudo -n",
    version="OpenRC with supervise-daemon (its supervisor= setting)",
    auth="root, had through sudo without a password (a status is read as you when sudo asks for one)",
    limits="",
    costs="",
    links=(
        Link("OpenRC's user guide", OPENRC + "user-guide.md", "docs"),
        Link("Service script guide", OPENRC + "service-script-guide.md", "guide"),
        Link("supervise-daemon guide", OPENRC + "supervise-daemon-guide.md", "guide"),
        Link("rc-service(8)", OPENRC + "man/rc-service.8", "reference"),
        Link("rc-update(8)", OPENRC + "man/rc-update.8", "reference"),
        Link("openrc-run(8)", OPENRC + "man/openrc-run.8", "reference"),
        Link("OpenRC on Gentoo", "https://wiki.gentoo.org/wiki/OpenRC", "guide"),
        Link("OpenRC's news", OPENRC + "NEWS.md", "changelog"),
        Link("OpenRC's source", "https://github.com/OpenRC/openrc", "source"),
    ),
    areas=(
        Area("Services", "a service's status, and starting, stopping, restarting it", OPENRC + "man/rc-service.8",
             covered="the framework's services read by their status, and Start…, Stop…, Restart…"),
        Area("Runlevels", "the services each runlevel starts (boot, default...)", OPENRC + "man/rc-update.8",
             covered="the platform's boot service added to the default runlevel, and deleted from it"),
        Area("Service scripts", "openrc-run scripts: command, command_args, command_user, depend()", OPENRC + "service-script-guide.md",
             covered="written as root for the platform at boot: its command, as you, its error log, after the network"),
        Area("Supervision", "supervise-daemon: a daemon watched and respawned", OPENRC + "supervise-daemon-guide.md",
             covered="the boot service supervised, respawned 10 s after a failure, stopped by SIGINT"),
        Area("The status of all services", "every service in each runlevel", OPENRC + "man/rc-status.8"),
        Area("start-stop-daemon", "the older way to start a daemon from a script", OPENRC + "man/start-stop-daemon.8"),
    ),
    calls=(
        Call("rc-service <service> status", "whether a service runs (its exit code)", "Services",
             used="the services the framework relies on; the boot service's state", docs=OPENRC + "man/rc-service.8"),
        Call("rc-service <service> start", "a service started", "Services", used="Start… (a service; at boot); the setup",
             docs=OPENRC + "man/rc-service.8", writes=True),
        Call("rc-service <service> stop", "a service stopped", "Services", used="Stop… (a service; at boot; before a removal)",
             docs=OPENRC + "man/rc-service.8", writes=True),
        Call("rc-service <service> restart", "a service stopped and started", "Services", used="Restart… (a service)",
             docs=OPENRC + "man/rc-service.8", writes=True),
        Call("rc-update add <service> default", "a service put in the default runlevel", "Runlevels",
             used="the platform registered at boot", docs=OPENRC + "man/rc-update.8", writes=True),
        Call("rc-update del <service> default", "a service taken out of the default runlevel", "Runlevels",
             used="the platform's boot service removed (asked twice)", docs=OPENRC + "man/rc-update.8", writes=True),
        Call("rc-update show default", "the default runlevel's services", "Runlevels",
             used="whether the boot service starts at boot", docs=OPENRC + "man/rc-update.8"),
        Call("/etc/init.d/liminal-<app>-boot", "an openrc-run service script (supervise-daemon, command_user, checkpath)",
             "Service scripts", used="written as root (whole, or not at all) for the platform at boot",
             docs=OPENRC + "man/openrc-run.8", writes=True),
        Call("rc-status", "the services of each runlevel and their states", "The status of all services",
             docs=OPENRC + "man/rc-status.8"),
        Call("openrc <runlevel>", "the system switched to a runlevel", "Runlevels", docs=OPENRC + "user-guide.md", writes=True),
    ),
    verified=VERIFIED,
)

SERVICE = Api(
    name="SysV service",
    maker="Debian's init-system-helpers (the service command), and the distributions' SysV scripts",
    about=("The service command runs a System V init script in /etc/init.d (or the init's own unit, where one stands for "
           "it) with start, stop, restart or status. Where the init is neither systemd nor OpenRC, the plugin reads and "
           "changes the framework's services with it; it makes no boot service there."),
    kind="command",
    base="service, as root through sudo -n",
    version="the service command of init-system-helpers (Debian, Ubuntu) and its kin",
    auth="root, had through sudo without a password (a status is read as you when sudo asks for one)",
    limits="",
    costs="",
    links=(
        Link("service(8)", "https://manpages.ubuntu.com/manpages/resolute/man8/service.8.html", "reference"),
        Link("service(8) (Debian)", "https://manpages.debian.org/unstable/init-system-helpers/service.8.en.html", "docs"),
        Link("update-rc.d(8)", "https://manpages.debian.org/unstable/init-system-helpers/update-rc.d.8.en.html", "reference"),
        Link("init(8): SysV init", "https://manpages.debian.org/unstable/sysvinit-core/init.8.en.html", "reference"),
        Link("sysvinit's source", "https://github.com/slicer69/sysvinit", "source"),
    ),
    areas=(
        Area("A script's actions", "start, stop, restart, status of one init script",
             "https://manpages.ubuntu.com/manpages/resolute/man8/service.8.html",
             covered="the framework's services read by their status, and Start…, Stop…, Restart…"),
        Area("Every script's status", "the status of each script in /etc/init.d",
             "https://manpages.ubuntu.com/manpages/resolute/man8/service.8.html"),
        Area("Starting at boot", "a script's links in the runlevels (update-rc.d)",
             "https://manpages.debian.org/unstable/init-system-helpers/update-rc.d.8.en.html"),
    ),
    calls=(
        Call("service <name> status", "whether a script's service runs (its exit code)", "A script's actions",
             used="the services the framework relies on", docs="https://manpages.ubuntu.com/manpages/resolute/man8/service.8.html"),
        Call("service <name> start", "a service started", "A script's actions", used="Start…; the setup",
             docs="https://manpages.ubuntu.com/manpages/resolute/man8/service.8.html", writes=True),
        Call("service <name> stop", "a service stopped", "A script's actions", used="Stop…",
             docs="https://manpages.ubuntu.com/manpages/resolute/man8/service.8.html", writes=True),
        Call("service <name> restart", "a service stopped and started", "A script's actions", used="Restart…",
             docs="https://manpages.ubuntu.com/manpages/resolute/man8/service.8.html", writes=True),
        Call("service --status-all", "every script's status", "Every script's status",
             docs="https://manpages.ubuntu.com/manpages/resolute/man8/service.8.html"),
        Call("update-rc.d <name> defaults", "a script started at boot", "Starting at boot",
             docs="https://manpages.debian.org/unstable/init-system-helpers/update-rc.d.8.en.html", writes=True),
    ),
    verified=VERIFIED,
)

SUDO_API = Api(
    name="sudo",
    maker="the sudo project",
    about=("sudo runs a command as another user, root by default, as the sudoers policy allows. The plugin has root's "
           "rights through it when the platform is not root, always with -n: when sudo would ask for a password the "
           "command fails at once instead, and the page says a change needs root."),
    kind="command",
    base="sudo -n <command>",
    version="sudo 1.9 (its -n, --non-interactive)",
    auth=("the platform's user, as /etc/sudoers allows: a change runs only where sudo needs no password (NOPASSWD), and "
          "a password is never asked"),
    limits="",
    costs="",
    links=(
        Link("sudo(8)", SUDO + "sudo.man/", "reference"),
        Link("sudoers(5)", SUDO + "sudoers.man/", "reference"),
        Link("sudo", "https://www.sudo.ws/", "docs"),
        Link("sudo's changes", "https://www.sudo.ws/releases/changelog/", "changelog"),
        Link("sudo's source", "https://github.com/sudo-project/sudo", "source"),
    ),
    areas=(
        Area("Running as root", "a command run as root, refused at once where a password would be asked", SUDO + "sudo.man/",
             covered="each change, and the reads that need root, through sudo -n"),
        Area("The policy", "who may run what as whom, with a password or without (sudoers)", SUDO + "sudoers.man/",
             covered="the plugin's rights come from it: no password, or no change"),
        Area("Asking what is allowed", "the commands the user may run (sudo -l)", SUDO + "sudo.man/"),
        Area("The time stamp", "a password asked once, then remembered for a while (sudo -v, -k)", SUDO + "sudo.man/"),
    ),
    calls=(
        Call("sudo -n true", "whether sudo runs without a password", "Running as root",
             used="the rights the page says (asked again after 10 s)", docs=SUDO + "sudo.man/"),
        Call("sudo -n <command>", "a command as root, never asking a password", "Running as root",
             used="each change; the reads that need root", docs=SUDO + "sudo.man/", writes=True),
        Call("sudo -n sh -c <script>", "a shell script as root", "Running as root",
             used="a boot service's unit or script written whole, or removed", docs=SUDO + "sudo.man/", writes=True),
        Call("sudo -l", "what the user may run", "Asking what is allowed", docs=SUDO + "sudo.man/"),
        Call("sudo -v", "the time stamp renewed (asks a password)", "The time stamp", docs=SUDO + "sudo.man/"),
    ),
    verified=VERIFIED,
)

PS = Api(
    name="ps (procps-ng)",
    maker="the procps-ng project",
    about=("ps reports the processes running, each column chosen with -o, read from the kernel's /proc. The plugin lists "
           "the framework's processes with it: those whose command line names a Liminal app, with their memory."),
    kind="command",
    base="ps -eo pid=,rss=,args=",
    version="procps-ng's ps",
    auth="the platform's user: every process's command line is readable",
    limits="",
    costs="",
    links=(
        Link("ps(1)", MAN7 + "man1/ps.1.html", "reference"),
        Link("proc(5)", MAN7 + "man5/proc.5.html", "docs"),
        Link("procps-ng's source", "https://gitlab.com/procps-ng/procps", "source"),
    ),
    areas=(
        Area("Choosing processes and columns", "every process (-e), the columns asked (-o)", MAN7 + "man1/ps.1.html",
             covered="every process: its id, resident memory and command line; Liminal's kept"),
        Area("The kernel's process files", "what ps reads: /proc/<pid>/stat, status, cmdline", MAN7 + "man5/proc.5.html"),
        Area("Process trees and threads", "parents, children, threads", MAN7 + "man1/ps.1.html"),
    ),
    calls=(
        Call("ps -eo pid=,rss=,args=", "every process's id, resident memory and command", "Choosing processes and columns",
             used="the framework's processes table", docs=MAN7 + "man1/ps.1.html"),
        Call("ps -ef --forest", "every process as a tree", "Process trees and threads", docs=MAN7 + "man1/ps.1.html"),
    ),
    verified=VERIFIED,
)

APIS = (SYSTEMCTL, OPENRC_API, SERVICE, SUDO_API, PS)


def facts(plugin) -> dict[str, dict[str, str]]:
    """What the plugin kept of its APIs while it ran (asking nothing): sudo's answer when last asked."""
    kept = getattr(plugin, "_sudo", None)  # (when, ok): sudo -n true, asked again after SUDO_S
    if not kept:
        return {}
    at, ok = kept
    seconds = max(0.0, time.monotonic() - at)
    ago = f"{seconds:.0f} s ago" if seconds < 90 else f"{seconds / 60:.0f} min ago"
    return {SUDO_API.name: {"Without a password": ("yes" if ok else "no: it asks for one") + f" (asked {ago})"}}
