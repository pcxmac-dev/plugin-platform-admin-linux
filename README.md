# plugin-platform-admin-linux

Linux administration for Liminal: root's rights and how they are had, the services the framework relies on, the apps' systemd user units, the framework's processes.

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
  without a login once `loginctl enable-linger` is set.
- The framework's processes: their app, command line and memory.

## Native Linux only

The user's words (2026-11-08): "the scope of linux administration is only on native linux O/S"; "it's not for
administrating WSL instances". The plugin administers the Linux machine the platform runs on and nothing else: on
Windows, on macOS and inside a WSL distribution (its kernel's release names Microsoft or WSL, or WSL's variables are
set) it runs no command at all. Its status says why, so the platform shows it disabled, and its setup and every
command are refused. Liminal's WSL distributions are the WSL plugins' to install, update and log in to. It has no
variables (`ADMIN_LINUX_TARGET` is gone since 0.3.0).

## From the command line

```
python -m plugin_platform_admin_linux status
python -m plugin_platform_admin_linux setup            # everything; or one step: setup services
python -m plugin_platform_admin_linux services
python -m plugin_platform_admin_linux startups
python -m plugin_platform_admin_linux register platform
python -m plugin_platform_admin_linux startup platform run
python -m plugin_platform_admin_linux processes
```

The platform app drives the same hooks from its page.
