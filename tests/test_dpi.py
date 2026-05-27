from __future__ import annotations

from goat_desktop import __main__ as main_module
from goat_desktop.dpi import enable_dpi_awareness


def test_enable_dpi_awareness_returns_bool() -> None:
    assert isinstance(enable_dpi_awareness(), bool)


def test_main_imports_dpi_awareness_hook() -> None:
    assert main_module.enable_dpi_awareness is enable_dpi_awareness
