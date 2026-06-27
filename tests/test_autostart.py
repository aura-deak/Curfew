#!/usr/bin/env python3
import pytest
from unittest.mock import patch, MagicMock
from curfew.autostart import setup_autostart, create_systemd_service

def test_setup_autostart_systemd():
    with patch('curfew.autostart.create_systemd_service') as mock_create_service:
        setup_autostart('systemd')
        mock_create_service.assert_called_once()

def test_setup_autostart_manual():
    with patch('curfew.autostart.create_systemd_service') as mock_create_service:
        setup_autostart('manual')
        mock_create_service.assert_not_called()

def test_create_systemd_service_success():
    mock_run = MagicMock(return_value=type('result', (), {'stdout': '', 'stderr': '', 'returncode': 0})())
    
    with patch('curfew.autostart.subprocess.run', mock_run), \
         patch('curfew.autostart.os.makedirs'), \
         patch('builtins.open', MagicMock()):
        
        result = create_systemd_service()
        assert result is True
        assert mock_run.call_count == 3

def test_create_systemd_service_daemon_reload_fail():
    def side_effect(args, **kwargs):
        if 'daemon-reload' in args:
            return type('result', (), {'stdout': '', 'stderr': 'error', 'returncode': 1})()
        return type('result', (), {'stdout': '', 'stderr': '', 'returncode': 0})()
    
    with patch('curfew.autostart.subprocess.run', side_effect=side_effect), \
         patch('curfew.autostart.os.makedirs'), \
         patch('builtins.open', MagicMock()):
        
        result = create_systemd_service()
        assert result is False

def test_create_systemd_service_enable_fail():
    def side_effect(args, **kwargs):
        if 'enable' in args:
            return type('result', (), {'stdout': '', 'stderr': 'error', 'returncode': 1})()
        return type('result', (), {'stdout': '', 'stderr': '', 'returncode': 0})()
    
    with patch('curfew.autostart.subprocess.run', side_effect=side_effect), \
         patch('curfew.autostart.os.makedirs'), \
         patch('builtins.open', MagicMock()):
        
        result = create_systemd_service()
        assert result is False

def test_create_systemd_service_start_fail():
    def side_effect(args, **kwargs):
        if 'start' in args:
            return type('result', (), {'stdout': '', 'stderr': 'error', 'returncode': 1})()
        return type('result', (), {'stdout': '', 'stderr': '', 'returncode': 0})()
    
    with patch('curfew.autostart.subprocess.run', side_effect=side_effect), \
         patch('curfew.autostart.os.makedirs'), \
         patch('builtins.open', MagicMock()):
        
        result = create_systemd_service()
        assert result is False

def test_create_systemd_service_exception():
    with patch('curfew.autostart.os.makedirs', side_effect=Exception('test error')):
        result = create_systemd_service()
        assert result is False