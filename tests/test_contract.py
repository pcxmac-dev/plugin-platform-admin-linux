"""Every plugin here conforms to the class contract (plugin API 2.2): liminal_libs.sources.conformance, read
from the plugin alone (nothing runs); and it serves as its liminal-net node (0.9.0, the library's node check on
stand-ins): it ends on TERM within its deadline with nothing left, a change of Liminal's user and group included."""
from __future__ import annotations

import plugin_platform_admin_linux as module
from liminal_libs.linuxsys import standin
from liminal_libs.sources.conformance import assert_module_conforms, assert_module_serves, node_problems

from plugin_platform_admin_linux import LinuxAdminPlugin


def test_every_plugin_here_conforms_to_the_class_contract():
    found = assert_module_conforms(module)
    assert found and all(p.api == "2.2" and not p.is_record for p in found)
    assert {p.SYSTEM for p in found} == {"platform"} and {p.KIND for p in found} == {"machine"}
    assert all(p.apis and p.interface()["apis"] == [a.name for a in p.apis] for p in found)  # what it attaches to (2.2)


def test_it_is_drawn_under_the_platforms_os_plugins():
    """Its section of the platform's list (liminal-platform 0.26.0; the user, 2026-11-15: "then OS plugins"): OS plugins,
    beside the machine's own, the virtualization and the cloud plugins."""
    assert {p.SECTION for p in assert_module_conforms(module)} == {"os"}


def test_it_serves_as_a_node_and_ends_on_term_with_nothing_left(may_reach_linux):
    """The library's node check (conformance.node_problems, on stand-ins: no process, no host): the module's own
    plugin, whose readers are refused here, and the plugin on a recorded machine, whose app_stopping (LinuxAdmin's)
    runs inside the platform's stop."""
    assert assert_module_serves(module)
    on_ubuntu = LinuxAdminPlugin(native="", user=("pat", "/home/pat"), apps=[], python="/usr/bin/python3",
                                 linux=standin.Machine("wsl-ubuntu-24.04"))
    assert node_problems(on_ubuntu) == []
