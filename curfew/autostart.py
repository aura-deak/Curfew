#!/usr/bin/env python3
import subprocess
import os

SYMLINK_PATH = '/usr/local/bin/curfew'

def get_scripts_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts')

def create_symlink():
    try:
        script_path = os.path.join(get_scripts_path(), 'create_symlink.sh')
        result = subprocess.run(['pkexec', 'env', 'HOME=' + os.environ.get('HOME', ''), 'bash', script_path], capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        
        if result.returncode == 0:
            return True
        else:
            return False
    except Exception as e:
        print(f"创建软链接失败: {e}")
        return False

def setup_autostart(autostart_type):
    if autostart_type == 'cron':
        setup_cron()
    else:
        print("请稍后自行设置自启动")

def setup_cron():
    try:
        create_symlink()
        
        cron_command = f'@reboot curfew daemon'
        
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        current_cron = result.stdout
        
        if 'curfew daemon' in current_cron:
            print("cron 任务已存在，跳过设置")
            return
        
        new_cron = current_cron + '\n' + cron_command + '\n'
        
        process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE, text=True)
        process.communicate(input=new_cron)
        
        if process.returncode == 0:
            print("cron 定时任务已设置")
        else:
            print("设置 cron 定时任务失败")
    except Exception as e:
        print(f"设置 cron 定时任务失败: {e}")