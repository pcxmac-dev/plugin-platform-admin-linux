"""No test reaches this machine's Linux (0.9.0): the library's LinuxAdmin reads the probe and sudo's listing through
proctree and starts sudo's conversation through lifecycle.spawn, and the plugin hands those on unless a test gave it a
recorded machine (`linux=`, liminal_libs.linuxsys.standin.Machine). Here both are refused, and a test that reached
either fails at its end, even where the plugin took the refusal as "cannot be read". A test that means to (the
contract's node check, on the module's own plugin) asks for `may_reach_linux`."""
from __future__ import annotations

import pytest

from liminal_libs.machines.linuxadmin import LinuxAdmin


@pytest.fixture
def may_reach_linux():
    """This test may ask the base's readers: each is still refused, and the test does not fail for it."""
    return True


@pytest.fixture(autouse=True)
def no_real_linux(monkeypatch, request):
    reached: list = []

    def refused(kind):
        def run(self, *args, **kwargs):
            reached.append((kind, args[:1]))
            raise PermissionError(f"a test reached this machine's Linux through LinuxAdmin.{kind}: hand the plugin a "
                                  "recorded machine (linux=)")
        return run

    monkeypatch.setattr(LinuxAdmin, "linux_run", refused("linux_run"))
    monkeypatch.setattr(LinuxAdmin, "linux_spawn", refused("linux_spawn"))
    yield reached
    if "may_reach_linux" not in request.fixturenames:
        assert reached == [], f"a test reached this machine's Linux: {reached[:3]}"
