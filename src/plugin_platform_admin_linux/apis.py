"""What Linux administration attaches to (plugin API 2.2, liminal_libs.sources.apis; the user, 2026-11-11: "each plugin
should reflect the the API its attached to, and present links that provide documentation ... it should also expose more
of what the API is about"): systemd's systemctl and its unit files, OpenRC, the SysV service command, sudo (how root's
rights are had) and procps' ps, each as its makers' pages describe it. Every address was read on 2026-11-11
(`VERIFIED`). `facts` says what the plugin kept of them while it ran (asking nothing): whether sudo ran without a
password, when last asked.

0.9.0 (Liminal's user and group): the sudo card says sudo's conversation and its listing, and two cards come
from the library's linuxsys.plan.TOOLS, every program its probe and root scripts run: the account tools
(shadow, BusyBox, systemd-sysusers) and the system's tools. `facts` now says whether root is had without a
password as the library read it (sudo's listing, at most once in 5 min)."""
from __future__ import annotations

import time

from liminal_libs.linuxsys.plan import TOOLS
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
    maker="the sudo project (classic sudo); the Trifecta Tech Foundation (sudo-rs, Ubuntu's sudo since 25.10)",
    about=("sudo runs a command as another user, root by default, as the sudoers policy allows. The plugin has root's "
           "rights through it when the platform is not root. The services' and boot services' changes run with -n: "
           "where sudo would ask for a password the command fails at once, and the page says a change needs root. A "
           "change of Liminal's user and group (0.9.0) runs its one script through sudo's conversation: sudo's own "
           "prompt, then the password typed on the page's form on its standard input, once, never kept. How root is "
           "had is read from `sudo -V` and the listing `sudo -n -l`, at most once in 5 min (each read may write a line "
           "in the system's log)."),
    kind="command",
    base=("sudo -S -k -u root -p <prompt> -- /bin/sh -c <script> (Liminal's user and group); sudo -n <command> (the "
          "services, the boot services)"),
    version="sudo 1.9 (its -n, -S, -k, -p and -l); sudo-rs 0.2 (Ubuntu 25.10 and later), with its own words",
    auth=("the platform's user, as /etc/sudoers allows: Liminal's user and group with the user's own password (root's "
          "under openSUSE's targetpw), typed on the form, or none where the listing says no password is asked; the "
          "services' and boot services' changes only where sudo needs no password (NOPASSWD), never asking one"),
    limits="one try per click: a wrong password counts as a failed sign-in",
    costs="",
    links=(
        Link("sudo(8)", SUDO + "sudo.man/", "reference"),
        Link("sudoers(5)", SUDO + "sudoers.man/", "reference"),
        Link("sudo.conf(5)", SUDO + "sudo.conf.man/", "reference"),
        Link("sudo", "https://www.sudo.ws/", "docs"),
        Link("sudo's changes", "https://www.sudo.ws/releases/changelog/", "changelog"),
        Link("sudo's source", "https://github.com/sudo-project/sudo", "source"),
        Link("sudo-rs", "https://github.com/trifectatechfoundation/sudo-rs", "source"),
        Link("OpenDoas", "https://github.com/Duncaen/OpenDoas", "source"),
    ),
    areas=(
        Area("Running as root", "a command run as root, refused at once where a password would be asked", SUDO + "sudo.man/",
             covered="the services' and boot services' changes, and the reads that need root, through sudo -n"),
        Area("The password on standard input", "-S reads it from standard input, after the prompt -p names; -k asks "
             "it again whatever the time stamp", SUDO + "sudo.man/",
             covered=("a change of Liminal's user and group: the password written once, after sudo's own prompt (a "
                      "marker of the change's own), never in an argument or the environment")),
        Area("The policy", "who may run what as whom, with a password or without (sudoers)", SUDO + "sudoers.man/",
             covered="the plugin's rights come from it: a password typed on the form, none, or no change"),
        Area("Asking what is allowed", "the commands the user may run (sudo -l)", SUDO + "sudo.man/",
             covered=("the listing, read with -n at most once in 5 min: whether a change asks for a password here, the "
                      "last matching rule deciding")),
        Area("The log", "each command sudo runs, written to the system's log", SUDO + "sudoers.man/",
             covered="the page says that sudo writes each change's script into this system's log"),
        Area("The time stamp", "a password asked once, then remembered for a while (sudo -v, -k)", SUDO + "sudo.man/"),
        Area("doas and su", "root through OpenDoas, or su with root's password: each asks only in a terminal",
             "https://github.com/Duncaen/OpenDoas",
             covered="found and named: the page shows the one root command to run in a terminal (the user's answer 7)"),
    ),
    calls=(
        Call("sudo -V", "sudo's version, and whether it is sudo or sudo-rs", "Running as root",
             used="the probe (how root is had)", docs=SUDO + "sudo.man/"),
        Call("env LC_ALL=C sudo -n -l", "what the user may run, without asking a password", "Asking what is allowed",
             used="whether a change asks for a password here (at most once in 5 min)", docs=SUDO + "sudo.man/"),
        Call("env LC_ALL=C sudo -S -k -u root -p <prompt> -- /bin/sh -c <script> liminal <nonce>",
             "a shell script as root, the password on standard input after sudo's own prompt", "The password on standard input",
             used="Make them..., Add or Remove a member..., Remove them... (Liminal's user and group)",
             docs=SUDO + "sudo.man/", writes=True),
        Call("sudo -n <command>", "a command as root, never asking a password", "Running as root",
             used="the services' and boot services' changes; the reads that need root", docs=SUDO + "sudo.man/", writes=True),
        Call("sudo -n sh -c <script>", "a shell script as root", "Running as root",
             used="a boot service's unit or script written whole, or removed", docs=SUDO + "sudo.man/", writes=True),
        Call("sudo -v", "the time stamp renewed (asks a password)", "The time stamp", docs=SUDO + "sudo.man/"),
        Call("doas <command>", "a command as root through OpenDoas (a password only in a terminal)", "doas and su",
             docs="https://github.com/Duncaen/OpenDoas", writes=True),
        Call("su -c <command>", "a command as root, root's password typed in a terminal", "doas and su",
             docs=MAN7 + "man1/su.1.html", writes=True),
    ),
    verified="2026-11-17",
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

# -- Liminal's user and group (0.9.0): the account tools and the system's tools, derived from linuxsys.plan.TOOLS -------
# The library names every program its probe and its root scripts run, with its maker and what it is run for
# (liminal_libs.linuxsys.plan.TOOLS); the two cards below take their calls from it, so a program the library adds is on
# a card or a test says it is not. Each call's page is the program's manual page.
ACCOUNT_TOOLS = ("groupadd", "useradd", "usermod", "gpasswd", "userdel", "groupdel", "addgroup", "adduser", "deluser",
                 "delgroup", "systemd-sysusers")
ELEVATION_TOOLS = ("sudo", "doas", "su", "env")  # on the sudo card
SYSUSERS = SYSTEMD + "systemd-sysusers.html"
BUSYBOX = "https://busybox.net/downloads/BusyBox.html"
PAGES = {  # a program's manual page
    "groupadd": MAN7 + "man8/groupadd.8.html", "useradd": MAN7 + "man8/useradd.8.html",
    "usermod": MAN7 + "man8/usermod.8.html", "gpasswd": MAN7 + "man1/gpasswd.1.html",
    "userdel": MAN7 + "man8/userdel.8.html", "groupdel": MAN7 + "man8/groupdel.8.html",
    "addgroup": BUSYBOX, "adduser": BUSYBOX, "deluser": BUSYBOX, "delgroup": BUSYBOX,
    "systemd-sysusers": SYSUSERS, "sh": MAN7 + "man1/sh.1p.html", "awk": MAN7 + "man1/gawk.1.html",
    "flock": MAN7 + "man1/flock.1.html", "getent": MAN7 + "man1/getent.1.html", "sed": MAN7 + "man1/sed.1.html",
    "rpm": MAN7 + "man8/rpm.8.html", "restorecon": MAN7 + "man8/restorecon.8.html",
}
WRITES = {"groupadd", "useradd", "usermod", "gpasswd", "userdel", "groupdel", "addgroup", "adduser", "deluser",
          "delgroup", "systemd-sysusers", "install", "mkdir", "mv", "rm", "rmdir", "sync", "chmod", "chgrp", "restorecon"}
ACCOUNT_AREA = {"groupadd": "shadow", "useradd": "shadow", "usermod": "shadow", "gpasswd": "shadow",
                "userdel": "shadow", "groupdel": "shadow", "addgroup": "BusyBox", "adduser": "BusyBox",
                "deluser": "BusyBox", "delgroup": "BusyBox", "systemd-sysusers": "systemd-sysusers"}


def _tool_calls(names, area_of) -> tuple[Call, ...]:
    """The calls of `names`, as linuxsys.plan.TOOLS says each: its maker, what it is run for, its page."""
    known = {name: (maker, used) for name, maker, used in TOOLS}
    return tuple(Call(name, f"{name} ({known[name][0]})", area_of(name), used=known[name][1],
                      docs=PAGES.get(name, MAN7 + f"man1/{name}.1.html"), writes=name in WRITES)
                 for name in names if name in known)


ACCOUNTS_API = Api(
    name="Linux accounts (shadow, BusyBox, systemd-sysusers)",
    maker="the shadow project (shadow-maint); the BusyBox project; the systemd project",
    about=("The tools that make, change and remove a Linux system's groups and users: shadow's groupadd, useradd, "
           "usermod, gpasswd, userdel and groupdel (most distributions), BusyBox's addgroup, adduser, deluser and "
           "delgroup (Alpine), and systemd-sysusers, which makes them from a file in /etc/sysusers.d (Debian and Ubuntu: "
           "the user's answer 5). The plugin makes Liminal's own system group liminal with the platform's user in it, "
           "and Liminal's own system user liminal; adds and removes the group's members; and takes back what its "
           "journal says Liminal made. Each change is one root script, run once through sudo's conversation (or as "
           "root, or by the one root command), confirmed with its plan's sha256. On NixOS accounts are declared, so the "
           "page shows the lines for its configuration instead."),
    kind="command",
    base="/bin/sh -c <script> as root: the tool of this system, chosen by the library (liminal_libs.linuxsys.accounts)",
    version="shadow 4.13 and later; BusyBox 1.37 (Alpine 3.24); systemd-sysusers of systemd 255 and later",
    auth="root, had through sudo (the password typed on the form), as root, or by the one root command in a terminal",
    limits="the group and the user are named liminal always (the user's answer 8); a system group and user only",
    costs="",
    links=(
        Link("groupadd(8)", PAGES["groupadd"], "reference"),
        Link("useradd(8)", PAGES["useradd"], "reference"),
        Link("usermod(8)", PAGES["usermod"], "reference"),
        Link("gpasswd(1)", PAGES["gpasswd"], "reference"),
        Link("userdel(8)", PAGES["userdel"], "reference"),
        Link("groupdel(8)", PAGES["groupdel"], "reference"),
        Link("login.defs(5)", MAN7 + "man5/login.defs.5.html", "reference"),
        Link("sysusers.d(5)", SYSTEMD + "sysusers.d.html", "reference"),
        Link("systemd-sysusers(8)", SYSUSERS, "reference"),
        Link("BusyBox's commands", BUSYBOX, "docs"),
        Link("shadow's source", "https://github.com/shadow-maint/shadow", "source"),
    ),
    areas=(
        Area("shadow", "groupadd, useradd, usermod, gpasswd, userdel, groupdel: /etc/group, /etc/passwd and their "
             "shadows, with the ranges login.defs gives", PAGES["groupadd"],
             covered=("the group made with --system, the user with --system, no expiry and no login shell; a member "
                      "added and removed with gpasswd; userdel and groupdel take back only what the journal says "
                      "Liminal made")),
        Area("BusyBox", "addgroup, adduser, deluser, delgroup (Alpine)", BUSYBOX,
             covered="the same on Alpine: the group and the user as system ones, a member added and removed"),
        Area("systemd-sysusers", "groups and users made from /etc/sysusers.d at boot or when asked, never removed",
             SYSUSERS, covered="Debian and Ubuntu: /etc/sysusers.d/liminal.conf written, then systemd-sysusers run on it"),
        Area("NixOS", "accounts declared in the system's configuration (users.groups, users.users)",
             "https://nixos.org/manual/nixos/stable/",
             covered="the page shows the lines to declare: nothing is made by a tool there"),
        Area("Passwords and ageing", "passwd, chage: a user's password and its expiry", MAN7 + "man1/passwd.1.html"),
        Area("Subordinate ids", "/etc/subuid and /etc/subgid for user namespaces (usermod --add-subuids)",
             PAGES["usermod"]),
    ),
    calls=_tool_calls(ACCOUNT_TOOLS, lambda name: ACCOUNT_AREA[name]),
    verified="2026-11-24",
)

SYSTEM_TOOLS = Api(
    name="The system's tools (the probe and the root script)",
    maker="the system's own: coreutils (GNU or uutils) or BusyBox, util-linux, glibc or musl, RPM, policycoreutils",
    about=("What the library's probe and root scripts run besides the account tools: the POSIX shell, the core "
           "utilities, flock for the lock, getent for an account through NSS, `rpm -q` where whose password openSUSE's "
           "sudo asks depends on a package, restorecon where SELinux enforces. The probe runs once as the platform's "
           "user and changes nothing; a root script writes the journal /var/lib/liminal-linux/MADE (a line before each "
           "step and one after it), takes the lock, checks its guards, then runs its steps. A script uses only the "
           "options GNU's, uutils' and BusyBox's tools all have."),
    kind="command",
    base="/bin/sh -c <probe> as the platform's user; /bin/sh -c <script> as root",
    version="POSIX sh; coreutils 9 (GNU), uutils 0.2 (Ubuntu 26.04) or BusyBox 1.37; util-linux 2.39 and later",
    auth="the probe: the platform's user; a script: root",
    limits="a script is 96 KiB at most",
    costs="",
    links=(
        Link("The Linux man-pages project", MAN7, "docs"),
        Link("GNU coreutils' manual", "https://www.gnu.org/software/coreutils/manual/", "reference"),
        Link("flock(1)", PAGES["flock"], "reference"),
        Link("getent(1)", PAGES["getent"], "reference"),
        Link("BusyBox's commands", BUSYBOX, "reference"),
        Link("util-linux's source", "https://github.com/util-linux/util-linux", "source"),
    ),
    areas=(
        Area("The shell", "POSIX sh: dash, bash or BusyBox's ash", PAGES["sh"],
             covered="runs the probe and every root script"),
        Area("Files and folders", "install, mkdir, mv, rm, rmdir, stat, sync, sha256sum, chmod, chgrp, cat, ls",
             "https://www.gnu.org/software/coreutils/manual/",
             covered=("the journal's folder and file, the sysusers file, each written beside its place and moved in; "
                      "what Liminal wrote, removed")),
        Area("Text", "cut, sort, tr, sed, awk, date", "https://www.gnu.org/software/coreutils/manual/",
             covered="a field of /etc/group and /etc/passwd, a group's members in one order, the journal's run line"),
        Area("Who and where", "id, uname, getent", PAGES["getent"],
             covered="who the platform runs as, its groups, the machine, an account through NSS"),
        Area("The lock", "flock(1): a lock held on a file for a command's time", PAGES["flock"],
             covered="one change at a time on this system (a folder of its own where flock is missing)"),
        Area("Packages and labels", "rpm -q, restorecon", PAGES["rpm"],
             covered="whose password openSUSE's sudo asks; the SELinux label of what Liminal wrote"),
        Area("Everything else", "the rest of the core utilities and util-linux", MAN7),
    ),
    calls=_tool_calls([t[0] for t in TOOLS if t[0] not in ACCOUNT_TOOLS + ELEVATION_TOOLS],
                      lambda name: next((a for a, names in (
                          ("The shell", ("sh",)),
                          ("Text", ("cut", "sort", "tr", "sed", "awk", "date")),
                          ("Who and where", ("id", "uname", "getent")),
                          ("The lock", ("flock",)),
                          ("Packages and labels", ("rpm", "restorecon"))) if name in names), "Files and folders")),
    verified="2026-11-17",
)

APIS = (SYSTEMCTL, OPENRC_API, SERVICE, SUDO_API, PS, ACCOUNTS_API, SYSTEM_TOOLS)


def facts(plugin) -> dict[str, dict[str, str]]:
    """What the plugin kept of its APIs while it ran (asking nothing): whether root was had without a password when it
    last read how root is had (sudo's listing, read by the library at most once in 5 min)."""
    kept = getattr(plugin, "_sudo", None)  # (when, ok): may_elevate's last answer
    if not kept:
        return {}
    at, ok = kept
    seconds = max(0.0, time.monotonic() - at)
    ago = f"{seconds:.0f} s ago" if seconds < 90 else f"{seconds / 60:.0f} min ago"
    return {SUDO_API.name: {"Without a password": ("yes" if ok else "no: it asks for one") + f" (read {ago})"}}
