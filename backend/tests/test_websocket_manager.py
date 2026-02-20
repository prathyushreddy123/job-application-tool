"""Tests for backend/websocket_manager.py"""
from backend.websocket_manager import ConnectionManager


def test_connection_manager_init():
    mgr = ConnectionManager()
    assert mgr.connection_count == 0


def test_disconnect_nonexistent():
    mgr = ConnectionManager()
    # Should not raise
    mgr.disconnect(None)
    assert mgr.connection_count == 0
