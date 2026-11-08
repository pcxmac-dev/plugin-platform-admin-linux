# Changelog

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
