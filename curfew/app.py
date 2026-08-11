#!/usr/bin/env python3
import os
import webbrowser
from datetime import datetime

from flask import Flask, render_template, jsonify, request

from curfew.config import load_config, save_config, AppConfig

app = Flask(__name__, 
            template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
            static_folder=os.path.join(os.path.dirname(__file__), 'static'))


@app.route('/')
def dashboard():
    """仪表板页面"""
    return render_template('dashboard.html')


@app.route('/schedule')
def schedule_page():
    """时间表页面"""
    return render_template('schedule.html')


@app.route('/api/config', methods=['GET'])
def api_get_config():
    """获取配置的 API 端点"""
    try:
        config = load_config()
        # 使用 model_dump() 将 Pydantic 模型转换为字典
        return jsonify(config.model_dump())
    except FileNotFoundError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': f"获取配置失败: {str(e)}"}), 500


@app.route('/api/config', methods=['POST'])
def api_save_config():
    """保存配置的 API 端点"""
    try:
        raw_data = request.json
        # Pydantic 会自动验证和解析数据
        config = AppConfig(**raw_data)
        save_config(config)
        return jsonify({'success': True})
    except ValueError as e:
        return jsonify({'error': f"配置格式错误: {str(e)}"}), 400
    except Exception as e:
        return jsonify({'error': f"保存配置失败: {str(e)}"}), 500


@app.route('/api/status', methods=['GET'])
def api_get_status():
    """获取当前状态的 API 端点"""
    try:
        from curfew.date_type import get_date_type
        from curfew.curfew_main import is_in_restricted_hours_for_today
        from curfew.timer import get_active_time

        config = load_config()
        
        date_type = get_date_type()
        # 使用 config.restricted_hours 访问 RestrictedHours 对象
        is_in_curfew = is_in_restricted_hours_for_today(config.restricted_hours)
        now = datetime.now().strftime('%H:%M:%S')
        consecutive_seconds = get_active_time()

        banned_until = config.banned_until
        is_banned = False
        ban_remaining_seconds = 0
        if banned_until:
            banned_dt = datetime.fromisoformat(banned_until)
            if datetime.now() < banned_dt:
                is_banned = True
                ban_remaining_seconds = int((banned_dt - datetime.now()).total_seconds())

        data = jsonify({
            'date_type': date_type,
            'is_in_curfew': is_in_curfew,
            'current_time': now,
            'consecutive_seconds': consecutive_seconds,
            'banned_until': banned_until,
            'is_banned': is_banned,
            'ban_remaining_seconds': ban_remaining_seconds,
            'total_usage_seconds': config.total_usage_seconds,
            'total_usage_limit': getattr(config.total_usage_limits, date_type),
            'total_usage_remaining_seconds': max(0, getattr(config.total_usage_limits, date_type, 0) * 60 - config.total_usage_seconds)
        })
        return data
    except FileNotFoundError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': f"获取状态失败: {str(e)}"}), 500


if __name__ == '__main__':
    webbrowser.open('http://localhost:8080')
    app.run(debug=True, port=8080)
