# Changelog

## 0.9.0 (2026-11-26)

Liminal's own user and group on Linux, made, changed and removed from the plugin's page or by one root command (Monday
list item 19, part one, release one; the user, 2026-11-25: "Accounts and elevation"). The plugin is now built on the
library's Linux standard interface, `liminal_libs.machines.linuxadmin.LinuxAdmin` (liminal-libs 1.102.0),
which holds what the plain package `liminal_libs.linuxsys` knows of this Linux: its facts, how root is had, the
account tool, and the journal of what Liminal made.

- **The page.** "How root is had" and "Liminal's user and group" come first, then the sections as before, and a "This
  Linux" table last (after "Under WSL" inside a distribution). How root is had: root, sudo or sudo-rs (whose
  password), doas, su, run0 or pkexec only, or nothing; what a change asks here; that sudo writes each change's script
  into the system's log. Liminal's user and group: the system group `liminal` (its number, made by Liminal or found),
  Liminal's own system user `liminal` (its shell and home; adopted where it is a Liminal distribution's login user),
  each member and whether the running platform has it, a change stopped part way, and the one root command.
- **Its forms.** Make them... (the group with the platform's user in it, and Liminal's own system user), Add a
  member..., Remove a member..., and Remove them..., which takes back what the journal
  `/var/lib/liminal-linux/MADE` says Liminal made (the user's answer 2) and is always asked twice. Each is asked only
  from the page (`linux_apply`, `linux_member` and `linux_undo` are `PAGE_ONLY_HOOKS`, the user's answer 6),
  confirmed with its plan's sha256, and built again from fresh facts before it runs: a system that changed since is
  refused. A member other than the platform's user is asked twice by name, and so is a found group with a person in
  it. Where no password is asked (root, or sudo's listing giving ALL without one), every change is asked twice.
- **The password field** is there only where sudo asks for one: "Your password for sudo", or root's under openSUSE's
  targetpw. It goes to sudo once, on its standard input after sudo's own prompt, and is never kept or shown; a wrong
  one is one failed sign-in and the form is offered again. Where doas or su gives root, where the platform runs as a
  system account, or where nothing gives root, the page has no form and shows the one command to run once in a
  terminal: `sudo <python> -I -B -m liminal_libs.linuxsys apply` (or after `doas`, or in `su -c '...'`). A terminal in
  the page for doas and su comes later (the user's answer 7).
- **Starting the platform again.** A member is in the running platform only once the platform is started again from a
  new terminal (a new terminal tab under WSL): the page says so on the member's row until it is.
- **How root is had is read once.** The rights the services' and boot services' sections say, `elevation()` and
  `may_elevate()` come from the library's one Elevation: sudo's listing (`sudo -n -l`), read at most once in 5 min,
  each read possibly writing a line in the system's log. `sudo -n true` is no longer run. Those changes still run
  through `sudo -n` and never ask a password; their password fields are a later release's.
- **When the platform stops** mid-change, the base's `app_stopping` ends a sudo still at its prompt (nothing ran) and
  lets a script that has begun finish its step; the next status says what is left, and Make them... again finishes it.
- **The cards.** sudo's says the conversation (`-S -k -u root -p <prompt>`), the listing and `sudo -V`, sudo-rs and
  OpenDoas among its links. Two new cards come from the library's `linuxsys.plan.TOOLS`, every program its probe and
  root scripts run: "Linux accounts (shadow, BusyBox, systemd-sysusers)" and "The system's tools (the probe and the
  root script)". `api_facts` says whether root was had without a password when last read.
- **The command line.** `accounts` shows Liminal's user and group as the page's table does, and `accounts --json` the
  facts as the page reads them (`linux_facts`). Neither changes anything: the usage names the one root command.
- `pyproject.toml`: liminal-libs>=1.102.0 (was 1.80.0), the release with `machines.linuxadmin` and `linuxsys`.
- Nothing runs as Liminal's user yet (the user's answer 10), no capability is given it (answer 9), and no grant,
  unit, package or folder of state is made: those are later releases'.
- Tests: `tests/test_accounts.py` (new), on the library's recorded machines (`liminal_libs.linuxsys.standin`; no
  process starts, no sudo runs): the two sections and their forms sent as the platform's page sends them, one sudo
  per confirmed click, the password only on sudo's standard input, Remove them... giving the first tree back, the
  found group asked by name, the names Liminal cannot take refused in words, doas, su and a service account showing
  the command, the command line's `accounts`, the library floor. `tests/conftest.py` refuses the base's real readers
  in every test and fails one that reached them. `tests/test_apis.py` drives the new forms and holds every program
  the machines played to a card; `tests/test_who_asks.py` the three new page-only hooks; `tests/test_contract.py` the
  library's node check. The old tests read how root is had from a recorded machine.

## 0.8.1 (2026-11-24)

The command line's `run` takes `--elevated` only as its first word, before the command's `--` (the review's finding
PLT-H1, checked 2026-11-23). And from the review of that change, 2026-11-24, each finding checked a second time:
`register` takes no program from an ask, the changes are asked only from the page, and the library it needs is 1.80.0.

- **run's `--elevated`.** It took the word from anywhere, the command's own words after `--` included, and took it out
  of them: `run -- grep --elevated notes.txt` ran `grep notes.txt` as root. Now `run -- COMMAND` runs the command as
  you and `run --elevated -- COMMAND` as root (through the library's `sudo -n --` unless you are root); every word
  after `--` is the command's own, an `--elevated` among them, the first too; `run --elevated` with no command shows
  the usage and runs nothing. The plugin's `run()` was right already: as the platform's own user unless `elevated` is
  said. Since liminal-platform 0.34.1 no route of the platform's asks it (`POST /api/machines/<name>/run` is gone; the
  user, 2026-11-23: "Remove it"), only this command line and `liminal-platform machine admin-linux run`, each in its
  own process.
- **`register` takes no program from an ask** (the review's first finding, rated high; there since 0.1.0, at boot
  since 0.5.0). The library's `register(app, at, port, python)` takes the Python a startup runs, and the platform's
  `POST /api/machines/admin-linux/ask` hands an ask's arguments on as they come. So another account on this machine
  could put a program at `/tmp/x` and ask `register` with `["charts", "logon", null, "/tmp/x"]`: your user unit
  `liminal-charts.service` then ran it at every logon, and `startup` ran it at once. With `["platform", "boot", null,
  "/tmp/x"]` root wrote a system unit running it at every boot, as your user. The page never sends that argument. Now
  the plugin's own `register(app, at, port)` has none: an ask naming a program is refused as too many arguments (the
  platform answers 400) before anything is written or run, and a startup runs this Python, the platform's own.
- **The changes are asked only from the page** (`PAGE_ONLY_HOOKS`, liminal-libs 1.66.0's word; the review's second
  finding, rated medium): `service`, `startup`, `register` and `unregister`, at your logon and at boot. Another
  plugin's ask of one is refused (403), and liminal-platform 0.34.0 refuses one over HTTP (401) unless its login shows
  that you are at the page. Before, any program on this machine asked them with the two headers PLT-H1 named, the
  page's dialog being the only confirmation: ufw, firewalld or Docker stopped as root, the SSH server started. A
  platform that holds no login asks them as before. The setup and the command line call the plugin's code directly,
  not through an ask, so they work as before; so do its reads (`present`, `status`, `processes`).
- `pyproject.toml`: liminal-libs>=1.80.0 (was 1.49.0), the release whose Shell puts `sudo -n --` before a command run
  as root (the review's third finding, rated low). `run --elevated` relies on it: with an older one `run --elevated --
  -u nobody id` runs id as nobody, sudo reading `-u` as its own, and the tests passed there, sudo's words read from
  that library.
- Tests: `tests/test_run.py`, over a stand-in shell (nothing runs): a command as you, and as root only when elevated, a
  dash first too (sudo's words read from the library's Shell, `shell_sudo()` from `tests/test_plugin.py`, held to end
  with `--` and the package's floor at 1.80.0); the command line's cases, `run -- --elevated COMMAND` among them (the
  review's fourth finding: a parse taking the `--` first and `--elevated` after it ran that command as root, and no
  test said otherwise). `tests/test_who_asks.py`, through the library's own App: the changes refused to another plugin
  and to no one, nothing run, the page's ask run, its reads asked by anyone; `register` refusing a program, the page's
  ask included, nothing written or run.

## 0.8.0 (2026-11-15)

It works on any Linux the platform runs on, a WSL distribution included (the user: "wsl and firewall linux should
always work under linux, if wsl prevents or misses some capability this should reflect in the plugin"). Until now it
refused whenever the kernel was WSL's, which read the user's words of 2026-11-08 ("it's not for administrating WSL
instances") too widely: those ruled out a platform on Windows reaching into a WSL distribution, and that stays so. A
platform running inside a distribution administers that Linux as any other. With liminal-libs 1.57.0 (the library's
check no longer refuses a WSL kernel): its services, the startups at logon and the boot service are read and changed
there, and its page carries an "Under WSL" table saying what WSL changes: whether systemd is the init, that the
distribution runs only while Windows keeps it started, and that "at boot" there means when the distribution starts.
With an older library it is as it was. On Windows and macOS nothing changes: no command runs.

## 0.7.1 (2026-11-15)

Drawn under the platform's OS plugins section, in the list on the left (the user: "then OS plugins" (the WSL distributions, the admin and the firewall plugins, as chosen)): `SECTION = "os"`, liminal-libs 1.51.0's machine-plugin attribute. liminal-platform 0.26.0 draws it; an older platform keeps the plugin under Machine plugins. Nothing else changes.

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
