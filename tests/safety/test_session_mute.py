"""Tests for grid.safety.session_mute."""

from __future__ import annotations

import time

import pytest

from grid.safety.session_mute import (
    SessionMuteRegistry,
    default_registry,
    mute_session,
    session_is_muted,
    unmute_session,
)


@pytest.fixture
def reg() -> SessionMuteRegistry:
    r = SessionMuteRegistry()
    return r


def test_permanent_mute_until_unmute(reg: SessionMuteRegistry) -> None:
    reg.mute("sess-a")
    assert reg.is_muted("sess-a")
    reg.unmute("sess-a")
    assert not reg.is_muted("sess-a")


def test_ttl_expires(reg: SessionMuteRegistry) -> None:
    reg.mute("sess-b", ttl_seconds=0.05)
    assert reg.is_muted("sess-b")
    time.sleep(0.08)
    assert not reg.is_muted("sess-b")


def test_empty_session_id_noop(reg: SessionMuteRegistry) -> None:
    reg.mute("")
    reg.unmute("")
    assert not reg.is_muted("")


def test_clear(reg: SessionMuteRegistry) -> None:
    reg.mute("x")
    reg.mute("y")
    reg.clear()
    assert not reg.is_muted("x")
    assert not reg.is_muted("y")


def test_module_helpers_use_default_registry() -> None:
    sid = "module-helper-test-session"
    try:
        mute_session(sid)
        assert session_is_muted(sid)
        unmute_session(sid)
        assert not session_is_muted(sid)
    finally:
        default_registry.unmute(sid)
