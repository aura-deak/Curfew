#!/usr/bin/env python3
import time as time_module
from datetime import datetime
from unittest.mock import patch, MagicMock, mock_open

import pytest

from curfew.timer import get_active_time, clear_active_time_cache


@pytest.fixture(autouse=True)
def _fresh_active_time_cache():
    """每个用例前清空 get_active_time 的缓存，保证用例之间相互独立。

    get_active_time() 现带 TTL 缓存（避免每循环都启动 journalctl 子进程，
    这是总使用时间"走时慢"的根因）。因此用例前需清理缓存，才能验证
    每次都真实采样 subprocess / /proc/uptime 的行为。
    """
    clear_active_time_cache()
    yield
    clear_active_time_cache()


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
