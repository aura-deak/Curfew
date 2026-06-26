#!/usr/bin/env python3
import pytest
from unittest.mock import patch
from autostart import setup_autostart, setup_cron

def test_setup_autostart_cron():
    with patch('autostart.setup_cron') as mock_setup_cron:
        setup_autostart('cron')
        mock_setup_cron.assert_called_once()

def test_setup_autostart_manual():
    with patch('autostart.setup_cron') as mock_setup_cron:
        setup_autostart('manual')
        mock_setup_cron.assert_not_called()

def test_setup_cron_uv_not_found():
    with patch('autostart.subprocess.run') as mock_run:
        mock_run.return_value.stdout = ''
        mock_run.return_value.stderr = ''
        mock_run.return_value.returncode = 0
        
        setup_cron()
        
        assert mock_run.call_count == 1

def test_setup_cron_task_exists():
    with patch('autostart.subprocess.run') as mock_run:
        mock_run.side_effect = [
            type('result', (), {'stdout': '/usr/bin/uv', 'stderr': '', 'returncode': 0})(),
            type('result', (), {'stdout': '@reboot uv run python curfew.py', 'stderr': '', 'returncode': 0})(),
        ]
        
        setup_cron()
        
        assert mock_run.call_count == 2

def test_setup_cron_add_task():
    mock_run_result1 = type('result', (), {'stdout': '/usr/bin/uv', 'stderr': '', 'returncode': 0})()
    mock_run_result2 = type('result', (), {'stdout': '', 'stderr': '', 'returncode': 0})()
    
    with patch('autostart.subprocess.run') as mock_run, \
         patch('autostart.subprocess.Popen') as mock_popen:
        
        mock_run.side_effect = [mock_run_result1, mock_run_result2]
        
        mock_process = type('process', (), {'communicate': lambda *args: None, 'returncode': 0})()
        mock_popen.return_value = mock_process
        
        setup_cron()
        
        assert mock_run.call_count == 2
        mock_popen.assert_called_once()

def test_setup_cron_error():
    with patch('autostart.subprocess.run') as mock_run:
        mock_run.side_effect = Exception('test error')
        
        setup_cron()
