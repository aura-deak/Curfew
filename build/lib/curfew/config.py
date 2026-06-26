#!/usr/bin/env python3
import os
import json

CONFIG_FILE = os.environ.get('CURFEW_CONFIG', 'config.json')

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        return config
    
    raise FileNotFoundError("配置文件不存在，请先运行 main.py 进行配置")

def save_config(config):
    dir_path = os.path.dirname(CONFIG_FILE)
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

def load_status():
    STATUS_FILE = os.environ.get('CURFEW_STATUS', 'status.json')
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return {'consecutive_seconds': 0}
