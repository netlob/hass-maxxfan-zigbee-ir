"""Protocol layer — pure Python, no Home Assistant imports.

Re-exports the public surface so callers can write:

    from custom_components.maxxfan.protocol import MaxxfanState, build_tuya_code

instead of reaching into submodules.  Contents land in commit 2.
"""

from __future__ import annotations

__all__: list[str] = []
