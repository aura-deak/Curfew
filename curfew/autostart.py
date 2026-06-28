#!/usr/bin/env python3
from .config import get_systemd_service_file
import subprocess
import os

systemd_service_dir = os.path.expanduser('~/.config/systemd/user')
systemd_service_file = get_systemd_service_file()

def create_systemd_service():
    try:
        os.makedirs(systemd_service_dir, exist_ok=True)
        
        service_content = f'''[Unit]
Description=Curfew - 电脑定时关机/睡眠工具
After=graphical.target

[Service]
Type=simple
ExecStart={os.path.expanduser('~/.local/bin/curfew')}
Restart=on-failure
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
'''
        
        with open(systemd_service_file, 'w') as f:
            f.write(service_content)
        
        print(f"systemd 服务文件已创建: {systemd_service_file}")
        
        result = subprocess.run(['systemctl', '--user', 'daemon-reload'], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"daemon-reload 失败: {result.stderr}")
            return False
        

        result = subprocess.run(['systemctl', '--user', 'enable', 'curfew'], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"enable 失败: {result.stderr}")
            return False
        
        result = subprocess.run(['systemctl', '--user', 'start', 'curfew'], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"start 失败: {result.stderr}")
            return False
        
        print("systemd 服务已启用并启动")
        return True
    except Exception as e:
        print(f"创建 systemd 服务失败: {e}")
        return False

def setup_autostart(autostart_type):
    if autostart_type == 'systemd':
        create_systemd_service()
    else:
        print("请稍后自行设置自启动")