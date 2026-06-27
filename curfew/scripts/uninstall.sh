#!/bin/bash
CONFIG_FILE="${CURFEW_CONFIG:-config.json}"
STATUS_FILE="${CURFEW_STATUS:-status.json}"
LINK="/usr/local/bin/curfew"

echo "开始卸载 Curfew..."

SUCCESS=true

if [ -f "$CONFIG_FILE" ]; then
    rm -f "$CONFIG_FILE"
    if [ $? -eq 0 ]; then
        echo "已删除配置文件: $CONFIG_FILE"
    else
        echo "删除配置文件失败 $CONFIG_FILE"
        SUCCESS=false
    fi
else
    echo "配置文件不存在: $CONFIG_FILE"
fi

if [ -f "$STATUS_FILE" ]; then
    rm -f "$STATUS_FILE"
    if [ $? -eq 0 ]; then
        echo "已删除状态文件: $STATUS_FILE"
    else
        echo "删除状态文件失败 $STATUS_FILE"
        SUCCESS=false
    fi
else
    echo "状态文件不存在: $STATUS_FILE"
fi

CURRENT_CRON=$(crontab -l 2>/dev/null)
if [ -n "$CURRENT_CRON" ]; then
    NEW_CRON=$(echo "$CURRENT_CRON" | grep -v "curfew")
    if [ "$NEW_CRON" != "$CURRENT_CRON" ]; then
        echo "$NEW_CRON" | crontab -
        if [ $? -eq 0 ]; then
            echo "已移除 curfew cron 任务"
        else
            echo "移除 cron 任务失败"
            SUCCESS=false
        fi
    else
        echo "未找到 curfew cron 任务，跳过移除"
    fi
else
    echo "crontab 为空或不存在，跳过移除"
fi

if [ -e "$LINK" ] || [ -L "$LINK" ]; then
    rm -f "$LINK"
    if [ $? -eq 0 ]; then
        echo "已删除软链接: $LINK"
    else
        echo "删除软链接失败"
        SUCCESS=false
    fi
else
    echo "软链接不存在，跳过移除"
fi

if [ "$SUCCESS" = true ]; then
    echo ""
    echo "卸载完成！"
    echo "Curfew 配置已清除，包括："
    echo "- 配置文件"
    echo "- 状态文件"
    echo "- cron 定时任务"
    echo "- 软链接"
    exit 0
else
    echo ""
    echo "卸载过程中部分操作失败，请检查上述错误信息"
    exit 1
fi