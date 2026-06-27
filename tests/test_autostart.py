#!/usr/bin/env python3
import pytest
from unittest.mock import patch, MagicMock
from curfew.autostart import setup_autostart, setup_cron, create_symlink

def test_setup_autostart_cron():
    with patch('curfew.autostart.setup_cron') as mock_setup_cron:
        setup_autostart('cron')
        mock_setup_cron.assert_called_once()

def test_setup_autostart_manual():
    with patch('curfew.autostart.setup_cron') as mock_setup_cron:
        setup_autostart('manual')
        mock_setup_cron.assert_not_called()

def test_setup_cron_task_exists():
    with patch('curfew.autostart.subprocess.run') as mock_run, \
         patch('curfew.autostart.create_symlink', return_value=True):
        mock_run.return_value = type('result', (), {'stdout': '@reboot curfew daemon', 'stderr': '', 'returncode': 0})()
        
        setup_cron()
        
        assert mock_run.call_count == 1

def test_setup_cron_add_task():
    mock_run_result = type('result', (), {'stdout': '', 'stderr': '', 'returncode': 0})()
    
    with patch('curfew.autostart.subprocess.run') as mock_run, \
         patch('curfew.autostart.subprocess.Popen') as mock_popen, \
         patch('curfew.autostart.create_symlink', return_value=True):
        
        mock_run.return_value = mock_run_result
        
        mock_process = type('process', (), {'communicate': lambda input=None: None, 'returncode': 0})()
        mock_popen.return_value = mock_process
        
        setup_cron()
        
        assert mock_run.call_count == 1
        mock_popen.assert_called_once()

def test_setup_cron_error():
    with patch('curfew.autostart.subprocess.run') as mock_run, \
         patch('curfew.autostart.create_symlink', return_value=True):
        mock_run.side_effect = Exception('test error')
        
        setup_cron()

def test_create_symlink_success():
    mock_result = MagicMock()
    mock_result.stdout = '软链接已创建'
    mock_result.stderr = ''
    mock_result.returncode = 0
    
    with patch('curfew.autostart.subprocess.run', return_value=mock_result):
        result = create_symlink()
        assert result is True

def test_create_symlink_failure():
    mock_result = MagicMock()
    mock_result.stdout = 'curfew 未安装'
    mock_result.stderr = ''
    mock_result.returncode = 1
    
    with patch('curfew.autostart.subprocess.run', return_value=mock_result):
        result = create_symlink()
        assert result is False

def test_create_symlink_exception():
    with patch('curfew.autostart.subprocess.run', side_effect=Exception('test error')):
        result = create_symlink()
        assert result is False