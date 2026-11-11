# Changelog

## 0.7.0 (2026-11-11)

Its API on its page, plugin API 2.2 (the user: "each plugin should reflect the the API its attached to, and present
links that provide documentation, the plugin interface should more or less contain what it already has, BUT, it should
also expose more of what the API is about"). Five cards (`apis.py`), each with the makers' pages, every part of the API
said covered or not, and every call the plugin makes beside the API's other notable ones:
- systemd (systemctl): systemctl(1), systemd.unit(5), systemd.service(5), systemd.exec(5), the targets, its news and
  source; the services read and changed, the user units at your logon, the system unit at boot and the files written.
- OpenRC: its user, service script and supervise-daemon guides, rc-service(8), rc-update(8), openrc-run(8).
- SysV service: service(8), update-rc.d(8), init(8).
- sudo: sudo(8), sudoers(5): `sudo -n`, never a password.
- ps (procps-ng): ps(1), proc(5).

`api_facts()` says what the plugin kept while it ran, asking nothing: whether sudo ran without a password, when last
asked. Tests: the cards name every command the plugin runs and every file it writes, over every read and change on
stand-in machines under systemd, OpenRC and SysV scripts; a link check runs with LIMINAL_VENDOR_PAGES=1. Needs
liminal-libs>=1.49.0.

## 0.6.0 (2026-11-11)

Its page says what it does, and works without root (the user: "the administration plugins don't seem to work right
especially linux which doesn't say anything about startup"), on liminal-libs 1.48.0:
- Where it does not act (Windows, macOS, a WSL distribution) its reason goes on to say what it does on a native Linux
  machine running the platform (a remote, say): the services, the startups at logon (systemd user units) and the
  platform at boot (liminal-platform-boot.service, a system unit: headless, as the platform's user, never root). Its
  status also carries two tables, its sections and the unit it would install at boot (an example), with no forms: the
  platform's page draws them once it shows tables for a plugin not for this machine.
- Valid whenever it reads this machine: not root no longer disables it. Each change says how it has root (sudo without a
  password) or that it needs it; under OpenRC the services are read as the platform's user when sudo asks for a password.
- Its page draws its own tables with confirmed forms: the services (Start…, Stop…, Restart…, as root through sudo -n),
  the startups at your logon (Register…, Run…, End…, Remove…: your own user units, no root), at boot (0.5.0's section),
  the framework's processes. The status's lists are frameworkServices, logonStartups, bootServices, frameworkProcesses.

## 0.5.0 (2026-11-11)

The platform at boot, before anyone signs in (the user: "also windows and linux admin, need sections for starting the
platform, or an app that inherits the platform object as a service, headless"; "on boot"), on liminal-libs 1.47.0:
- A section on the plugin's page, At boot, before anyone signs in: the platform and each app inheriting it, its boot
  service's state, command, account and log, and its buttons: Register… (the port), Start…, Stop…, Remove… (asked
  twice), each confirmed in the page's dialog. Through the startups' own hooks: `register(app, "boot", port)`,
  `startup(app, "start" | "stop", "boot")`, `unregister(app, "boot", accept_removal)`.
- Under systemd a system unit, `/etc/systemd/system/liminal-<app>-boot.service` (WantedBy=multi-user.target, User= the
  platform's own user, Restart=on-failure, SIGINT to stop); under OpenRC an init script, `/etc/init.d/liminal-<app>-boot`,
  in the default runlevel (supervise-daemon, command_user, respawned); none under another init. A system unit rather
  than a user unit with lingering, which would start every user unit at boot and keep them after sign-out.
- Written on this native Linux machine only, by one root script through `sudo -n` (the file beside its place, moved in,
  owned by root), never as root's own service: a platform run as root registers for the user sudo was run by, or is
  refused. A path a unit or an init script cannot carry safely is refused.
- Read in one script for them all (`systemctl show`, or the init script and `rc-service status`): a unit running whose
  page does not answer yet is starting, one restarting after a failure says so, one not enabled is disabled.
- Valid when not root but sudo runs without a password.
- The command line: `boot`, `register APP --boot [--port N]`, `startup APP start|stop --boot`, `unregister APP --boot
  --accept-removal`.

## 0.4.0 (2026-11-08)

On liminal-libs 1.27.0: the native-Linux check is the library's (`machines.linux.why_not_native`,
`MachinePlugin.not_for_here`), shared with the Linux firewall (the user: "Yes, firewall too"); off a native Linux
machine its status is the library's (`applies` False, the summary "not for this machine") and the library's setup
refuses; `why_not_native` stays importable from this module.

## 0.3.1 (2026-11-08)

Off a native Linux machine its status says `applies` False beside the reason, so the platform shows it as not for
this machine and offers no setup (liminal-platform 0.4.2): none can make it valid there.

## 0.3.0 (2026-11-08)

Native Linux only (the user: "the scope of linux administration is only on native linux O/S"; "it's not for
administrating WSL instances"): the plugin administers the Linux machine the platform runs on and nothing else. On
Windows (where 0.2.0 took Liminal's WSL distribution), on macOS and inside a WSL distribution (its kernel's release
naming Microsoft or WSL, or WSL's variables set) it runs no command: not present, not valid, the reason in words
(`why_not_native`), the setup and every command refused. `ADMIN_LINUX_TARGET` is gone; Liminal's WSL distributions
are the WSL plugins'.

## 0.2.0 (2026-11-07)

On liminal-libs 1.25.0: without a target named, Liminal's own WSL distribution on Windows (Liminal-Ubuntu, then
Liminal-Fedora, Liminal-Gentoo), this machine on Linux; on a target that is not Liminal's (WSL's default distribution,
the user's own) the plugin runs no command: its status says why and its setup changes nothing. Valid only with the
rights on Liminal's (`valid`, `why`).

## 0.1.0 (2026-11-07)

The first release: linux administration for the platform, on the library's Admin base
(liminal-libs 1.20.1).
