#!/usr/bin/env python3
import pytest
from unittest.mock import patch, MagicMock
from curfew.curfew_main import get_uptime_seconds

def test_get_uptime_seconds():
    with patch('curfew.curfew_main.subprocess.run') as mock_run:
        mock_run.return_value.stdout = '9000'
        
        result = get_uptime_seconds()
        assert result == 9000

def test_get_uptime_seconds_large():
    with patch('curfew.curfew_main.subprocess.run') as mock_run:
        mock_run.return_value.stdout = '86400'
        
        result = get_uptime_seconds()
        assert result == 86400

def test_get_uptime_seconds_zero():
    with patch('curfew.curfew_main.subprocess.run') as mock_run:
        mock_run.return_value.stdout = '0'
        
        result = get_uptime_seconds()
        assert result == 0

def test_get_uptime_seconds_error():
    with patch('curfew.curfew_main.subprocess.run') as mock_run:
        mock_run.side_effect = Exception('test error')
        
        result = get_uptime_seconds()
        assert result == 0
