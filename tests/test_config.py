#!/usr/bin/env python3
"""配置模块测试 - 使用 Pydantic 模型"""

import json
import os
import sys
from unittest.mock import patch

import pytest

from curfew.config import (
    load_config,
    save_config,
    validate_config_data,
    get_config_file,
    create_default_config,
    AppConfig,
    TimeSlot,
    RestrictedHours,
    ContinuousUsageLimits,
)


def test_load_config_file_exists(tmp_path):
    """测试成功加载存在的配置文件"""
    config_file = tmp_path / 'config.json'
    config_data = {
        'autostart_type': 'manual',
        'shutdown_command': ['systemctl', 'suspend'],
        'debug': False,
        'restricted_hours': {
            'workday': [
                {'start_hour': 23, 'start_minute': 0, 'end_hour': 6, 'end_minute': 0}
            ],
            'weekend': [],
            'holiday': []
        },
        'continuous_usage_limits': {
            'workday': 45,
            'weekend': 45,
            'holiday': 45
        }
    }
    
    with open(config_file, 'w') as f:
        json.dump(config_data, f)
    
    with patch.dict(os.environ, {'CURFEW_CONFIG': str(config_file)}):
        config = load_config()
        
        # 验证返回的是 AppConfig 实例（通过类型检查，不用 isinstance 来避免模块重新加载问题）
        assert hasattr(config, 'autostart_type')
        assert config.autostart_type == 'manual'
        assert config.shutdown_command == ['systemctl', 'suspend']
        assert config.debug is False
        assert len(config.restricted_hours.workday) == 1
        assert config.continuous_usage_limits.workday == 45


def test_load_config_file_not_exists(tmp_path):
    """测试加载不存在的配置文件时抛出异常"""
    config_file = tmp_path / 'nonexistent.json'
    
    with patch.dict(os.environ, {'CURFEW_CONFIG': str(config_file)}):
        if 'curfew.config' in sys.modules:
            del sys.modules['curfew.config']
        from curfew.config import load_config as reload_load_config
        with pytest.raises(FileNotFoundError):
            reload_load_config()


def test_save_config(tmp_path):
    """测试保存配置到文件"""
    config_file = tmp_path / 'config.json'
    
    with patch.dict(os.environ, {'CURFEW_CONFIG': str(config_file)}):
        config = create_default_config()
        save_config(config)
        
        # 验证文件已创建
        assert config_file.exists()
        
        # 验证文件内容
        with open(config_file, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data['autostart_type'] == 'manual'
        assert saved_data['shutdown_command'] == ['systemctl', 'suspend']
        assert saved_data['debug'] is False


def test_save_config_with_directory(tmp_path):
    """测试保存配置时自动创建目录"""
    config_dir = tmp_path / 'subdir' / 'nested'
    config_file = config_dir / 'config.json'
    
    with patch.dict(os.environ, {'CURFEW_CONFIG': str(config_file)}):
        config = create_default_config()
        save_config(config)
        
        # 验证目录已创建
        assert config_dir.exists()
        # 验证文件已创建
        assert config_file.exists()


def test_default_config_path():
    """测试默认配置文件路径"""
    with patch.dict(os.environ, {}, clear=True):
        if 'curfew.config' in sys.modules:
            del sys.modules['curfew.config']
        from curfew.config import get_config_file as reload_get_config_file
        
        expected_path = os.path.expanduser("~/.config/curfew.json")
        assert reload_get_config_file() == expected_path


def test_create_default_config():
    """测试创建默认配置"""
    config = create_default_config()
    
    assert isinstance(config, AppConfig)
    assert config.autostart_type == 'manual'
    assert config.shutdown_command == ['systemctl', 'suspend']
    assert config.debug is False
    assert len(config.restricted_hours.workday) == 0
    assert config.continuous_usage_limits.workday == 0


def test_timeslot_validation():
    """测试 TimeSlot 时间验证"""
    # 有效的 TimeSlot
    slot = TimeSlot(start_hour=9, end_hour=17)
    assert slot.start_hour == 9
    assert slot.start_minute == 0
    assert slot.end_hour == 17
    
    # 无效的小时应抛出异常
    with pytest.raises(ValueError):
        TimeSlot(start_hour=25, end_hour=17)


def test_config_serialization(tmp_path):
    """测试配置序列化和反序列化"""
    config_file = tmp_path / 'config.json'
    
    # 创建一个包含数据的配置
    config = AppConfig(
        autostart_type='systemd',
        shutdown_command=['shutdown', 'now'],
        restricted_hours=RestrictedHours(
            workday=[TimeSlot(start_hour=23, end_hour=6)]
        ),
        continuous_usage_limits=ContinuousUsageLimits(workday=60, weekend=120),
        debug=True
    )
    
    with patch.dict(os.environ, {'CURFEW_CONFIG': str(config_file)}):
        # 保存配置
        save_config(config)
        
        # 加载配置
        loaded_config = load_config()
        
        # 验证加载的配置与原始配置相同
        assert loaded_config.autostart_type == 'systemd'
        assert loaded_config.shutdown_command == ['shutdown', 'now']
        assert loaded_config.debug is True
        assert loaded_config.continuous_usage_limits.workday == 60
        assert loaded_config.continuous_usage_limits.weekend == 120
        assert len(loaded_config.restricted_hours.workday) == 1
        assert loaded_config.restricted_hours.workday[0].start_hour == 23


def test_validate_config_data_valid():
    """测试验证有效的配置数据"""
    valid_data = {
        'autostart_type': 'systemd',
        'shutdown_command': ['shutdown', 'now'],
        'debug': True,
        'restricted_hours': {
            'workday': [{'start_hour': 23, 'start_minute': 0, 'end_hour': 6, 'end_minute': 0}],
            'weekend': [],
            'holiday': []
        },
        'continuous_usage_limits': {
            'workday': 60,
            'weekend': 120,
            'holiday': 0
        }
    }
    
    config = validate_config_data(valid_data)
    assert config.autostart_type == 'systemd'
    assert config.debug is True


def test_validate_config_data_invalid_type():
    """测试验证无效类型的配置数据"""
    invalid_data = {
        'autostart_type': 'systemd',
        'shutdown_command': ['shutdown', 'now'],
        'debug': 'not_a_bool',  # ❌ 应该是 bool
        'restricted_hours': {'workday': [], 'weekend': [], 'holiday': []},
        'continuous_usage_limits': {'workday': 0, 'weekend': 0, 'holiday': 0}
    }
    
    with pytest.raises(ValueError):
        validate_config_data(invalid_data)


def test_validate_config_data_invalid_time():
    """测试验证无效时间范围的配置数据"""
    invalid_data = {
        'autostart_type': 'systemd',
        'shutdown_command': ['shutdown', 'now'],
        'debug': False,
        'restricted_hours': {
            'workday': [{'start_hour': 25, 'start_minute': 0, 'end_hour': 6, 'end_minute': 0}],  # ❌ 小时超出范围
            'weekend': [],
            'holiday': []
        },
        'continuous_usage_limits': {'workday': 0, 'weekend': 0, 'holiday': 0}
    }
    
    with pytest.raises(ValueError):
        validate_config_data(invalid_data)


def test_validate_config_data_empty_shutdown_command():
    """测试验证空关机命令"""
    invalid_data = {
        'autostart_type': 'systemd',
        'shutdown_command': [],  # ❌ 不能为空
        'debug': False,
        'restricted_hours': {'workday': [], 'weekend': [], 'holiday': []},
        'continuous_usage_limits': {'workday': 0, 'weekend': 0, 'holiday': 0}
    }
    
    with pytest.raises(ValueError):
        validate_config_data(invalid_data)
