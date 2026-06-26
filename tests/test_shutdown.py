#!/usr/bin/env python3
import pytest
from unittest.mock import patch
from shutdown import shutdown

def test_shutdown_with_debug_mode():
    with patch('shutdown.subprocess.run') as mock_run:
        shutdown(['shutdown', 'now'], debug=True)
        mock_run.assert_not_called()

def test_shutdown_with_test_mode():
    with patch('shutdown.subprocess.run') as mock_run:
        shutdown(['shutdown', 'now'], test_mode=True)
        mock_run.assert_not_called()

def test_shutdown_without_debug_or_test():
    with patch('shutdown.subprocess.run') as mock_run:
        shutdown(['shutdown', 'now'], debug=False)
        mock_run.assert_called_once_with(['shutdown', 'now'], check=True)

def test_shutdown_suspend_command():
    with patch('shutdown.subprocess.run') as mock_run:
        shutdown(['systemctl', 'suspend'], debug=False)
        mock_run.assert_called_once_with(['systemctl', 'suspend'], check=True)
