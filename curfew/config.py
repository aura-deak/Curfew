#!/usr/bin/env python3
import os
import json

def get_config_file():
    return os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config")) + "/curfew/config.json"

def get_systemd_service_file():
    return os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config")) + "/systemd/user/curfew.service"

def load_config():
    config_file = get_config_file()
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            config = json.load(f)
        return config
    
    raise FileNotFoundError("配置文件不存在，请先运行 main.py 进行配置")

def save_config(config):
    config_file = get_config_file()
    dir_path = os.path.dirname(config_file)
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=4)
