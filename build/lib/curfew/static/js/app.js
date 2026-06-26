const API_BASE = '';

async function apiGet(endpoint) {
    const response = await fetch(`${API_BASE}${endpoint}`);
    if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
    }
    return await response.json();
}

async function apiPost(endpoint, data) {
    const response = await fetch(`${API_BASE}${endpoint}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    });
    if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
    }
    return await response.json();
}

function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    document.body.appendChild(notification);

    setTimeout(() => {
        notification.remove();
    }, 3000);
}

function formatTime(hour, minute) {
    return `${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}`;
}

function formatSecondsToHMS(seconds) {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

function getDateTypeName(dateType) {
    const names = {
        'workday': '工作日',
        'weekend': '周末',
        'holiday': '节假日'
    };
    return names[dateType] || dateType;
}

function renderTimeBar(periods, container) {
    if (!container) return;

    const hours = Array.from({length: 24}, (_, i) => i);

    let segmentsHTML = '';
    periods.forEach(period => {
        const startFraction = (period.start_hour * 60 + period.start_minute) / (24 * 60);
        const endFraction = (period.end_hour * 60 + period.end_minute) / (24 * 60);

        if (endFraction <= startFraction) {
            const width1 = (1 - startFraction) * 100;
            const width2 = endFraction * 100;
            segmentsHTML += `<div class="time-bar-segment" style="left: ${startFraction * 100}%; width: ${width1}%;"></div>`;
            segmentsHTML += `<div class="time-bar-segment" style="left: 0%; width: ${width2}%;"></div>`;
        } else {
            const width = (endFraction - startFraction) * 100;
            segmentsHTML += `<div class="time-bar-segment" style="left: ${startFraction * 100}%; width: ${width}%;"></div>`;
        }
    });

    container.innerHTML = `
        <div class="time-bar">
            ${segmentsHTML}
        </div>
        <div class="time-bar-labels">
            <span>0</span>
            <span>6</span>
            <span>12</span>
            <span>18</span>
            <span>24</span>
        </div>
    `;
}

let statusTimer = null;

async function updateStatus() {
    try {
        const status = await apiGet('/api/status');
        const config = await apiGet('/api/config');
        const statusEl = document.getElementById('status-indicator');
        const timeEl = document.getElementById('current-time');
        const dateTypeEl = document.getElementById('date-type');
        const consecutiveTimeEl = document.getElementById('consecutive-time');
        const consecutiveLimitEl = document.getElementById('consecutive-limit');

        if (statusEl) {
            statusEl.className = `status-indicator ${status.is_in_curfew ? 'curfew' : 'normal'}`;
            statusEl.innerHTML = status.is_in_curfew ?
                '<span>🔒 宵禁中</span>' :
                '<span>✓ 正常</span>';
        }

        if (timeEl) {
            timeEl.textContent = status.current_time;
        }

        if (dateTypeEl) {
            dateTypeEl.textContent = getDateTypeName(status.date_type);
        }

        if (consecutiveTimeEl) {
            consecutiveTimeEl.textContent = formatSecondsToHMS(status.consecutive_seconds || 0);
        }

        if (consecutiveLimitEl) {
            const limit = config?.continuous_usage_limits?.[status.date_type] || 0;
            consecutiveLimitEl.textContent = limit > 0 ? `${limit} 分钟` : '无限制';
        }

        await loadScheduleForToday();
    } catch (error) {
        console.error('Failed to update status:', error);
    }
}

async function loadScheduleForToday() {
    try {
        const status = await apiGet('/api/status');
        const config = await apiGet('/api/config');
        const periods = config.restricted_hours[status.date_type] || [];

        const timeBarContainer = document.getElementById('time-bar-container');
        renderTimeBar(periods, timeBarContainer);
    } catch (error) {
        console.error('Failed to load schedule:', error);
    }
}

function startStatusUpdates() {
    if (statusTimer) clearInterval(statusTimer);
    statusTimer = setInterval(updateStatus, 1000);
}

function stopStatusUpdates() {
    if (statusTimer) {
        clearInterval(statusTimer);
        statusTimer = null;
    }
}

async function loadConfig() {
    try {
        return await apiGet('/api/config');
    } catch (error) {
        showNotification('加载配置失败，请先运行main.py初始化系统', 'error');
        return null;
    }
}

async function saveConfig(config) {
    try {
        await apiPost('/api/config', config);
        showNotification('配置已保存', 'success');
        return true;
    } catch (error) {
        showNotification('保存配置失败', 'error');
        return false;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const path = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav a');
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href === path || (path === '/' && href === '/')) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
});