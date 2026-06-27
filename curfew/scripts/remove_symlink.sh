#!/bin/bash
LINK="/usr/local/bin/curfew"

if [ ! -e "$LINK" ] && [ ! -L "$LINK" ]; then
    echo "软链接不存在，跳过移除"
    exit 0
fi

rm -f "$LINK"
echo "已删除软链接: $LINK"
exit 0