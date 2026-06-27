#!/usr/bin/env python3
from .config import get_systemd_service_file, get_config_file
import os
import subprocess


systemd_service_file = get_systemd_service_file()

config_file = get_config_file()

def remove_config_file(filepath):
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
            print(f"已删除配置文件: {filepath}")
            return True
        except Exception as e:
            print(f"删除配置文件失败 {filepath}: {e}")
            return False
    else:
        print(f"配置文件不存在: {filepath}")
        return True

def remove_systemd_service():
    try:
        if not os.path.exists(systemd_service_file):
            print("systemd 服务文件不存在，跳过移除")
            return True
        
        result = subprocess.run(['systemctl', '--user', 'stop', 'curfew'], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"stop 失败: {result.stderr}")
            return False
        
        result = subprocess.run(['systemctl', '--user', 'disable', 'curfew'], capture_output=True, text=True)

        if os.path.exists(systemd_service_file):
            os.remove(systemd_service_file)
            print(f"已删除 systemd 服务文件: {systemd_service_file}")
            return False
        
        os.remove(systemd_service_file)
        print(f"已删除 systemd 服务文件: {systemd_service_file}")
        
        result = subprocess.run(['systemctl', '--user', 'daemon-reload'], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"daemon-reload 失败: {result.stderr}")
            return False
        
        return True
    except Exception as e:
        print(f"移除 systemd 服务失败: {e}")
        return False

def uninstall():
    print("开始卸载 Curfew...")
    
    success = True
    success &= remove_config_file(config_file)
    success &= remove_systemd_service()
    
    if success:
        print("\n卸载完成！")
        print("Curfew 配置已清除，包括：")
        print("- 配置文件")
        print("- systemd 服务")
    else:
        print("\n卸载过程中部分操作失败，请检查上述错误信息")
        return False
    
    return True