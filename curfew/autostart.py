#!/usr/bin/env python3
import subprocess

def setup_autostart(autostart_type):
    if autostart_type == 'cron':
        setup_cron()
    else:
        print("请稍后自行设置自启动")

def setup_cron():
    try:
        uv_path = subprocess.run(['which', 'uv'], capture_output=True, text=True).stdout.strip()
        if not uv_path:
            print("未找到 uv 命令，请确保已安装 uv")
            return
        
        cron_command = f'@reboot {uv_path} run python curfew.py'
        
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        current_cron = result.stdout
        
        if 'curfew.py' in current_cron:
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
