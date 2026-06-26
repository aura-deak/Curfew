#!/usr/bin/env python3
import os
from flask import Flask, render_template, jsonify, request
from datetime import datetime
import webbrowser
from .config import load_config, save_config, load_status

app = Flask(__name__, 
            template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
            static_folder=os.path.join(os.path.dirname(__file__), 'static'))

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/schedule')
def schedule_page():
    return render_template('schedule.html')

@app.route('/api/config', methods=['GET'])
def api_get_config():
    config = load_config()
    if config is None:
        return jsonify({'error': '配置文件不存在'}), 404
    return jsonify(config)

@app.route('/api/config', methods=['POST'])
def api_save_config():
    try:
        config = request.json
        save_config(config)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/status', methods=['GET'])
def api_get_status():
    from .date_type import get_date_type
    from .time_check import is_in_restricted_hours_for_today

    config = load_config()
    if config is None:
        return jsonify({'error': '配置文件不存在'}), 404

    date_type = get_date_type()
    is_in_curfew = is_in_restricted_hours_for_today(config.get('restricted_hours', {}))
    now = datetime.now().strftime('%H:%M:%S')
    status = load_status()

    return jsonify({
        'date_type': date_type,
        'is_in_curfew': is_in_curfew,
        'current_time': now,
        'consecutive_seconds': status.get('consecutive_seconds', 0)
    })

if __name__ == '__main__':
    webbrowser.open('http://localhost:8080')
    app.run(debug=True, port=8080)
