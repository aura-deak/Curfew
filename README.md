!\[Stone Badge]\(https\://stone.professorlee.work/api/stone/alu-deak/Curfew null)

网络上说说就得了，现实中谁不想急头白脸的在readme里养一只石墩子做宠物（

# Curfew - 让时间管理更智能，让生活更有规律。

Curfew 是一个智能的开机启动工具，帮助您管理电脑的使用时间，在设定的禁用时段自动执行关机操作。

> \[!IMPORTANT]
> 本项目仅支持 Linux 系统。
>
> 这是一个不负责任的作者，因为已知的用户只有作者自己。请自行解决旧版兼容性问题。\
> 升级前请务必做好配置备份，如有问题请自行调试。

## 📖 使用场景

- 限制自己使用电脑的时间，培养良好的时间管理习惯，避免沉迷于电脑

## 🚀 快速开始

### 1. 安装 uv

[uv](https://docs.astral.sh/uv/) 是一个现代的 Python 包管理器，用于依赖管理和环境隔离。

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. 安装 curfew 命令

将 curfew 安装为全局命令，可在任何地方直接调用：

```bash
uv tool install --python-preference only-system .
```

安装后即可使用 `curfew` 命令启动程序。

### 3. 首次配置

运行配置向导，按照提示完成设置：

```bash
curfew init
```

配置过程中，您需要：

- 设置禁用时段（24小时制）
- 选择自启动方式（cron/手动）
- 配置关机命令

### 4. 启动 Web 界面

启动 GUI 配置界面：

```bash
curfew web
```

访问 `http://localhost:8080` 进行可视化配置管理。

## ⚙️ 运行方式

安装后可在任何地方直接调用 `curfew` 命令：

```bash
# 直接运行（默认 daemon 模式）
curfew

# 启动 Web 管理界面
curfew web

# 查看帮助
curfew -h
```

### 开机自启（推荐）

通过 cron 定时任务实现开机自启动：

```bash
curfew init  # 在配置向导中选择 cron 自启动
```

## 🔧 技术特性

- **全局命令**：通过 `uv tool install` 安装后，可在任何地方直接调用 `curfew` 命令
- **定时检测**：每秒检查一次当前时间，支持跨天时段设置
- **日期类型识别**：自动区分工作日、周末、节假日
- **连续使用时间限制**：通过 `uptime -r` 命令获取系统运行时间
- **Web 管理界面**：基于 Flask 的可视化配置界面
- **环境隔离**：使用 uv 管理依赖，确保环境一致性

## 🧪 单元测试

运行测试套件：

```bash
PYTHONPATH=. uv run pytest tests/ -v --cov=.
```

测试覆盖：

- 时间检查逻辑
- 日期类型判断
- 配置加载/保存
- uptime 解析
- 关机命令调用
- cron 配置功能

## ⚙️ 配置说明

### 调试模式

如需测试功能而不实际执行关机操作，可将 config.json 中的 "debug" 设置为 true 。

### 环境变量

| 变量名            | 说明     | 默认值         |
| -------------- | ------ | ----------- |
| CURFEW\_CONFIG | 配置文件路径 | config.json |
| CURFEW\_STATUS | 状态文件路径 | status.json |

## 💡 小贴士

- **跨天设置**：支持跨天的禁用时段，如晚上 11 点到早上 7 点
- **权限要求**：设置 cron 任务需要用户权限
- **测试建议**：首次使用时，建议将 debug 设置为 true 进行测试
- **日志查看**：daemon 模式下日志输出到标准输出，可通过 systemd journal 或 nohup 查看

