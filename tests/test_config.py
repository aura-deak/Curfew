#!/usr/bin/env python3
import pytest
import os
import sys
import json
from unittest.mock import patch, mock_open

def test_load_config_file_exists(tmp_path):
    config_file = tmp_path / 'config.json'
    config_data = {'key': 'value'}
    
    with open(config_file, 'w') as f:
        json.dump(config_data, f)
    
    with patch.dict(os.environ, {'CURFEW_CONFIG': str(config_file)}):
        if 'config' in sys.modules:
            del sys.modules['config']
        from config import load_config
        assert load_config() == config_data

def test_load_config_file_not_exists(tmp_path):
    config_file = tmp_path / 'nonexistent.json'
    
    with patch.dict(os.environ, {'CURFEW_CONFIG': str(config_file)}):
        if 'config' in sys.modules:
            del sys.modules['config']
        from config import load_config
        with pytest.raises(FileNotFoundError):
            load_config()

def test_save_config(tmp_path):
    config_file = tmp_path / 'config.json'
    config_data = {'key': 'value'}
    
    with patch.dict(os.environ, {'CURFEW_CONFIG': str(config_file)}):
        if 'config' in sys.modules:
            del sys.modules['config']
        from config import save_config
        save_config(config_data)
        
        with open(config_file, 'r') as f:
            assert json.load(f) == config_data

def test_save_config_with_directory(tmp_path):
    config_dir = tmp_path / 'subdir'
    config_file = config_dir / 'config.json'
    config_data = {'key': 'value'}
    
    with patch.dict(os.environ, {'CURFEW_CONFIG': str(config_file)}):
        if 'config' in sys.modules:
            del sys.modules['config']
        from config import save_config
        save_config(config_data)
        
        assert config_dir.exists()
        with open(config_file, 'r') as f:
            assert json.load(f) == config_data

def test_load_status_file_exists(tmp_path):
    status_file = tmp_path / 'status.json'
    status_data = {'consecutive_seconds': 300}
    
    with open(status_file, 'w') as f:
        json.dump(status_data, f)
    
    with patch.dict(os.environ, {'CURFEW_STATUS': str(status_file)}):
        if 'config' in sys.modules:
            del sys.modules['config']
        from config import load_status
        assert load_status() == status_data

def test_load_status_file_not_exists(tmp_path):
    status_file = tmp_path / 'nonexistent.json'
    
    with patch.dict(os.environ, {'CURFEW_STATUS': str(status_file)}):
        if 'config' in sys.modules:
            del sys.modules['config']
        from config import load_status
        assert load_status() == {'consecutive_seconds': 0}

def test_load_status_file_corrupted(tmp_path):
    status_file = tmp_path / 'status.json'
    
    with open(status_file, 'w') as f:
        f.write('invalid json')
    
    with patch.dict(os.environ, {'CURFEW_STATUS': str(status_file)}):
        if 'config' in sys.modules:
            del sys.modules['config']
        from config import load_status
        assert load_status() == {'consecutive_seconds': 0}

def test_default_config_path():
    with patch.dict(os.environ, {}, clear=True):
        if 'config' in sys.modules:
            del sys.modules['config']
        from config import CONFIG_FILE
        assert CONFIG_FILE == 'config.json'

def test_default_status_path():
    with patch.dict(os.environ, {}, clear=True):
        if 'config' in sys.modules:
            del sys.modules['config']
        from config import load_status
        status = load_status()
        assert status == {'consecutive_seconds': 0}
