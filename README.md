# plugin-platform-admin-linux

Linux administration for Liminal: root's rights and how they are had, the services the framework relies on, the apps' systemd user units, the platform's at boot, the framework's processes.

The user's words (2026-11-07): "the platform is the interface for the software/hardware which facilitates the
liminal framework"; "i also need a windows and linux firewall plugin for the platform"; "and a windows and
linux admin plugin for platform".

## What it does

A machine plugin of the platform (`liminal_libs.machines.admin.Admin`, plugin API 2.2), through the library's
`machines.linux.Shell`, on the Linux the platform itself runs on (a machine of its own, or a WSL distribution it runs
inside) and nowhere else:

- The rights: root; sudo without a password (`sudo -n`, never a password asked).
- The services the framework relies on: docker, containerd, ufw or firewalld, systemd-resolved; under systemd,
  OpenRC or the service command; the setup starts those stopped; an SSH server (ssh, sshd) is shown and never
  started by it.
- The apps' startups as systemd user units (liminal-charts, liminal-integrator, liminal-login, liminal-platform),
  as the integrator makes its own: read, run, ended, enabled, disabled, made (`register`: the unit written into
  `~/.config/systemd/user`, enabled, not started) or removed when asked; the setup makes none. A unit runs
  without a login once `loginctl enable-linger` is set; to start the platform before anyone signs in, use its boot
  service (below), which leaves your user units as they are.
- The platform at boot, before anyone signs in (below).
- The framework's processes: their app, command line and memory.

Its page is its own tables, each change through a form confirmed in the page's dialog: **Services the framework relies
on** (Start…, Stop…, Restart…), **Startups at your logon** (Register…, Run…, End…, Remove…), **At boot, before anyone
signs in** (below) and **The framework's processes**.

The plugin is valid whenever it reads this machine, as root or not (0.6.0): the rights are a fact on its page. A change
that needs root (a service's, a boot service's) has it through `sudo -n`, never asking for a password; where sudo asks
for one, the change says it needs root. A startup at your logon is your own user unit: no root.

## At boot, before anyone signs in

The user's words (2026-11-11): "also windows and linux admin, need sections for starting the platform, or an app that
inherits the platform object as a service, headless"; "on boot".

The plugin's page has a section, **At boot, before anyone signs in**: a row for each app a boot service may start, the
platform first, then any app whose App class inherits the platform's (`liminal_platform.app.PlatformApp`: the app the
plugin is attached to, or one an installed distribution names under the `liminal.apps` entry points, as
`lab = "liminal_lab.app:LabApp"`). Each row says whether a boot service is registered for it, its state (running,
starting, restarting, stopped, failed, disabled, not registered), the command it runs, the account it runs as and
where its log goes, with its buttons: **Register…** (its port), **Start…**, **Stop…**, **Remove…**. Each change is
confirmed in the page's dialog with the exact change; a removal is asked twice.

What it makes, by the machine's init:

- **systemd**: a system unit, `/etc/systemd/system/liminal-<app>-boot.service` (`liminal-platform-boot.service`
  beside the user unit `liminal-platform.service`): `WantedBy=multi-user.target`, `Wants=`/`After=network-online.target`,
  `User=` the platform's own user (never root), `ExecStart=<this Python> -m <module> serve --no-browser --port N`,
  `Restart=on-failure`, `RestartSec=10` (systemd 254 and later: `RestartSteps=6`, `RestartMaxDelaySec=600`, the wait
  growing to 10 min while it keeps failing; older ones say the keys are unknown and go on), `KillSignal=SIGINT` (as
  Ctrl+C: it closes what it holds). Its output: `journalctl -u liminal-<app>-boot.service`.
- **OpenRC**: an init script, `/etc/init.d/liminal-<app>-boot`, in the default runlevel: `supervisor=supervise-daemon`,
  `command_user` the platform's own user (never root), respawned 10 s after a failure, stopped by SIGINT, its errors in
  `/var/log/liminal-<app>-boot.log`.
- Any other init (the service command alone): none; the section says why.

Why a system unit and not a user unit with `loginctl enable-linger`: lingering starts the user's systemd manager at
boot, and with it every enabled user unit, the startups at your logon (Startups, above) too, and keeps them running
after you sign out, so "at your logon" would quietly become "always". A system unit starts only the app asked for, and
OpenRC has no user units at all, so one shape serves both inits.

- **Written only here**, on this Linux, as root through `sudo -n`: one root
  script writes the file beside its place and moves it in, owned by root (0644 for a unit, 0755 for an init script),
  then enables it; never a password asked.
- **Never root.** It runs as the platform's own user; a platform run as root through sudo gives it the user sudo was
  run by (`SUDO_USER`), and one run as root otherwise is refused.
- **No browser, headless.** `--no-browser`, and never `--until-quiet`, so it stays up until stopped.
- **None of your shell's variables.** A system unit starts with systemd's environment, not your profile's: a key you
  keep only in your shell is not there. Never put one in the unit itself (every user may read
  `/etc/systemd/system`); a file only you can read, named by a drop-in's `EnvironmentFile=`, keeps it private.
- **One port each.** A boot service and the platform at your logon cannot share a port; the port field says what wants
  which port, and a confirmation says so when it is the same.

## On Linux, the platform's own

The plugin administers the Linux the platform itself runs on and nothing else. That is a machine of its own, or a WSL
distribution the platform runs inside (0.8.0; the user, 2026-11-15: "wsl and firewall linux should always work under
linux, if wsl prevents or misses some capability this should reflect in the plugin"). Inside WSL its page carries an
"Under WSL" table (the library's `machines.linux.wsl_table`, liminal-libs 1.57.0) saying what WSL changes: whether
systemd is the init there (a distribution without it has no units to make or start), that the distribution runs only
while Windows keeps it started, and that a service enabled at boot starts when the distribution starts, not when the
PC does. Rights are as on any Linux: root, or sudo without a password; where sudo asks for one, the page says so and
changes are refused.

On Windows and on macOS it runs no command at all: a platform there does not reach into a WSL distribution from
outside (the user, 2026-11-08: "it's not for administrating WSL instances"). Its status says why and that it does not
apply (`applies` False), so the platform shows it disabled with no setup offered; its setup and every command are
refused. Its reason goes on to say what it does on Linux (its services, the startups at logon and the platform at
boot, 0.6.0); its status also carries its sections and the unit it would install at boot as tables, with no forms, for
a page that shows them. Liminal's WSL distributions are the WSL plugins' to install, update and log in to. It has no
variables (`ADMIN_LINUX_TARGET` is gone since 0.3.0). The check is the library's (`machines.linux.why_not_native`),
shared with the Linux firewall. Until 0.8.0 a WSL kernel was refused too, the platform's own included.

## From the command line

```
python -m plugin_platform_admin_linux status
python -m plugin_platform_admin_linux setup            # everything; or one step: setup services
python -m plugin_platform_admin_linux services
python -m plugin_platform_admin_linux startups
python -m plugin_platform_admin_linux register platform
python -m plugin_platform_admin_linux startup platform run
python -m plugin_platform_admin_linux boot                                    # the boot services
python -m plugin_platform_admin_linux register platform --boot --port 8775    # as root through sudo -n
python -m plugin_platform_admin_linux startup platform start --boot
python -m plugin_platform_admin_linux unregister platform --boot --accept-removal
python -m plugin_platform_admin_linux processes
python -m plugin_platform_admin_linux run -- systemctl --user list-units      # as you
python -m plugin_platform_admin_linux run --elevated -- systemctl status ufw  # as root, through sudo -n --
```

The platform app drives the same hooks from its page, its changes only from there (0.8.1): `service`, `startup`,
`register` and `unregister` are its `PAGE_ONLY_HOOKS`, so another plugin's ask of one is refused, and the platform asks
its login whether you are at the page before it asks one over HTTP. A startup runs this Python, the platform's own: no
ask names the program. `run` is the command line's alone (no route of the platform's asks it since liminal-platform
0.34.1): `--elevated` counts only as its first word, before the command's `--`, and every word after `--` is the
command's own. It needs liminal-libs 1.80.0, whose `sudo -n --` reads no word of the command as sudo's.

## Its API

The user's words (2026-11-11): "each plugin should reflect the the API its attached to, and present links that provide
documentation, the plugin interface should more or less contain what it already has, BUT, it should also expose more of
what the API is about". Since 0.7.0 (plugin API 2.2) the plugin declares what it attaches to (`apis.py`), and the
platform's page draws each card: what the API is, its links, every part of it (those the plugin uses first, the rest
under "more of the API") and every call it makes, with the API's other notable calls beside them.

- **systemd (systemctl)**: [systemctl(1)](https://www.freedesktop.org/software/systemd/man/latest/systemctl.html),
  [systemd.unit(5)](https://www.freedesktop.org/software/systemd/man/latest/systemd.unit.html),
  [systemd.service(5)](https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html)
  (RestartSteps= and RestartMaxDelaySec= since systemd 254), [systemd's news](https://github.com/systemd/systemd/blob/main/NEWS):
  the services, the user units at your logon, the system unit at boot.
- **OpenRC**: [its user guide](https://github.com/OpenRC/openrc/blob/master/user-guide.md),
  [rc-service(8)](https://github.com/OpenRC/openrc/blob/master/man/rc-service.8),
  [rc-update(8)](https://github.com/OpenRC/openrc/blob/master/man/rc-update.8),
  [supervise-daemon](https://github.com/OpenRC/openrc/blob/master/supervise-daemon-guide.md): the services, and the init
  script at boot.
- **SysV service**: [service(8)](https://manpages.ubuntu.com/manpages/resolute/man8/service.8.html), where the init is
  neither.
- **sudo**: [sudo(8)](https://www.sudo.ws/docs/man/sudo.man/), [sudoers(5)](https://www.sudo.ws/docs/man/sudoers.man/):
  root's rights through `sudo -n`, never a password asked.
- **ps (procps-ng)**: [ps(1)](https://man7.org/linux/man-pages/man1/ps.1.html): the framework's processes.

`api_facts()` says what the plugin kept of them while it ran, asking nothing: whether sudo ran without a password, when
last asked. Every address on the cards was read on 2026-11-11; the test `test_the_cards_pages_answer` asks each of them
again when `LIMINAL_VENDOR_PAGES=1` is set (it is skipped otherwise).
