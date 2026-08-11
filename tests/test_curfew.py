#!/usr/bin/env python3
import time as time_module
from datetime import datetime
from unittest.mock import patch, MagicMock, mock_open

import pytest

from curfew.timer import get_active_time


def test_get_uptime_seconds():
    """测试从 journalctl 获取唤醒时间，uptime 约为 9000 秒"""
    with patch('curfew.timer.subprocess.run') as mock_run:
        past = time_module.time() - 9000
        timestamp = datetime.fromtimestamp(past).isoformat()
        mock_run.return_value.stdout = f'{timestamp} ... PM: suspend exit'

        result = get_active_time()
        assert 8999 <= result <= 9001


def test_get_uptime_seconds_large():
    """测试大 uptime 值（86400 秒 = 1 天）"""
    with patch('curfew.timer.subprocess.run') as mock_run:
        past = time_module.time() - 86400
        timestamp = datetime.fromtimestamp(past).isoformat()
        mock_run.return_value.stdout = f'{timestamp} ... PM: suspend exit'

        result = get_active_time()
        assert 86399 <= result <= 86401


def test_get_uptime_seconds_zero():
    """测试刚唤醒后 uptime 接近 0"""
    with patch('curfew.timer.subprocess.run') as mock_run:
        past = time_module.time() - 1
        timestamp = datetime.fromtimestamp(past).isoformat()
        mock_run.return_value.stdout = f'{timestamp} ... PM: suspend exit'

        result = get_active_time()
        assert 0 <= result <= 2


def test_get_uptime_seconds_error():
    """测试 subprocess 出错时回退到 /proc/uptime"""
    with patch('curfew.timer.subprocess.run', side_effect=Exception('test error')):
        with patch('builtins.open', mock_open(read_data='0.00 0.00\n')):
            result = get_active_time()
            assert result == 0