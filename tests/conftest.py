"""Pytest configuration and shared fixtures.

For tests of the pure protocol layer no HA fixtures are needed (we don't
even import ``homeassistant`` from those tests).  The
``pytest-homeassistant-custom-component`` plugin's auto-discovery of HA
fixtures is enabled in commit 3 when the HA-side tests land.
"""

from __future__ import annotations
