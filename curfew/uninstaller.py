#!/usr/bin/env python3
import subprocess
import os

def get_scripts_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts')

def uninstall():
    try:
        script_path = os.path.join(get_scripts_path(), 'uninstall.sh')
        env = os.environ.copy()
        env['CURFEW_CONFIG'] = os.environ.get('CURFEW_CONFIG', 'config.json')
        env['CURFEW_STATUS'] = os.environ.get('CURFEW_STATUS', 'status.json')
        
        result = subprocess.run(['pkexec', 'bash', script_path], capture_output=True, text=True, env=env)
        
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        
        if result.returncode == 0:
            return True
        else:
            return False
    except Exception as e:
        print(f"卸载失败: {e}")
        return False