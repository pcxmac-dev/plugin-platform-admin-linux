# plugin-platform-admin-linux

Linux administration for Liminal: root's rights and how they are had, the services the framework relies on, the apps' systemd user units, the platform's at boot, the framework's processes.

The user's words (2026-11-07): "the platform is the interface for the software/hardware which facilitates the
liminal framework"; "i also need a windows and linux firewall plugin for the platform"; "and a windows and
linux admin plugin for platform".

## What it does

A machine plugin of the platform (`liminal_libs.machines.admin.Admin`, plugin API 2.1), through the library's
`machines.linux.Shell`, on the native Linux machine the platform runs on and nowhere else:

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

The plugin is valid when the platform runs as root, or when sudo runs without a password (`sudo -n`): each change
that needs root then has it, never asking for a password.

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

- **Written only here**, on this native Linux machine (never a WSL distribution), as root through `sudo -n`: one root
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

## Native Linux only

The user's words (2026-11-08): "the scope of linux administration is only on native linux O/S"; "it's not for
administrating WSL instances". The plugin administers the Linux machine the platform runs on and nothing else: on
Windows, on macOS and inside a WSL distribution (its kernel's release names Microsoft or WSL, or WSL's variables are
set) it runs no command at all. Its status says why and that it does not apply (`applies` False), so the platform
shows it disabled with no setup offered; its setup and every command are refused. Liminal's WSL distributions are the WSL plugins' to install, update and log in to. It has no
variables (`ADMIN_LINUX_TARGET` is gone since 0.3.0). The check is the library's (`machines.linux.why_not_native`,
liminal-libs 1.27.0), shared with the Linux firewall.

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
```

The platform app drives the same hooks from its page.
