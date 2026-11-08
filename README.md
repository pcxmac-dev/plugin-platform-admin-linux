# plugin-platform-admin-linux

Linux administration for Liminal: root's rights and how they are had, the services the framework relies on, the apps' systemd user units, the framework's processes.

The user's words (2026-11-07): "the platform is the interface for the software/hardware which facilitates the
liminal framework"; "i also need a windows and linux firewall plugin for the platform"; "and a windows and
linux admin plugin for platform".

## What it does

A machine plugin of the platform (`liminal_libs.machines.admin.Admin`, plugin API 2.1), through the library's
`machines.linux.Shell`, on a Linux machine or in a WSL distribution:

- The rights: root; sudo without a password (`sudo -n`, never a password asked); WSL's root.
- The services the framework relies on: docker, containerd, ufw or firewalld, systemd-resolved; under systemd,
  OpenRC or the service command; the setup starts those stopped; an SSH server (ssh, sshd) is shown and never
  started by it.
- The apps' startups as systemd user units (liminal-charts, liminal-integrator, liminal-login, liminal-platform),
  as the integrator makes its own: read, run, ended, enabled, disabled, made (`register`: the unit written into
  `~/.config/systemd/user`, enabled, not started) or removed when asked, made only on this machine (the apps do
  not run in WSL); the setup makes none. A unit runs without a login once `loginctl enable-linger` is set.
- The framework's processes: their app, command line and memory.

Variables: `ADMIN_LINUX_TARGET`: `local`, `wsl` or `wsl:<distribution>`; unset, Liminal's own WSL distribution on
Windows (Liminal-Ubuntu first) and this machine on Linux. On a target that is not Liminal's (the user's own
distribution) the plugin runs no command at all.

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
