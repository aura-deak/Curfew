#!/bin/bash
TARGET="$HOME/.local/bin/curfew"
LINK="/usr/local/bin/curfew"

if [ ! -f "$TARGET" ]; then
    echo "curfew 未安装在 $TARGET"
    echo "请先运行 'uv tool install --python-preference only-system .' 安装 curfew"
    exit 1
fi

if [ -e "$LINK" ] || [ -L "$LINK" ]; then
    rm -f "$LINK"
fi

ln -sf "$TARGET" "$LINK"
echo "软链接已创建: $LINK -> $TARGET"
exit 0