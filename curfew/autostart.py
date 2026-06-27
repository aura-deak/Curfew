#!/usr/bin/env python3
import subprocess

def setup_autostart(autostart_type):
    if autostart_type == 'cron':
        setup_cron()
    else:
        print("请稍后自行设置自启动")

def setup_cron():
    try:
        curfew_path = subprocess.run(['which', 'curfew'], capture_output=True, text=True).stdout.strip()
        if not curfew_path:
            print("未找到 curfew 命令，请确保已安装 curfew")
            return
        
        cron_command = f'@reboot {curfew_path} daemon'
        
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        current_cron = result.stdout
        
        if 'curfew daemon' in current_cron:
            print("cron 任务已存在，跳过设置")
            return
        
        if current_cron and not current_cron.endswith('\n'):
            current_cron += '\n'
        new_cron = current_cron + cron_command + '\n'
        
        process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE, text=True)
        process.communicate(input=new_cron)
        
        if process.returncode == 0:
            print("cron 定时任务已设置")
        else:
            print("设置 cron 定时任务失败")
    except Exception as e:
        print(f"设置 cron 定时任务失败: {e}")
