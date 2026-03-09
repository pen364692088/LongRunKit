# LongRunKit

**异步 Job 协议 v0.2** - 解决长任务被中断的问题。

## v0.2 增强 (P0 已完成)

| 改进 | 状态 | 描述 |
|------|------|------|
| 原子写入 + 文件锁 | ✅ | write temp → fsync → rename，防止写入撕裂 |
| CAS 更新 (rev) | ✅ | 版本号冲突检测，避免并发覆盖 |
| Lease 机制 | ✅ | 防止 watchdog/worker 互相抢活 |
| ACK + 通知退避 | ✅ | 指数退避 + 抖动，避免补发风暴 |
| 结构化日志 | ✅ | ndjson 格式，方便解析分析 |
| jobctl | ✅ | ls/show/tail/ack/cancel/retry |
| 错误分类 | ✅ | TRANSIENT/PERMANENT/TIMEOUT/CANCELLED |

## 问题背景

当前长任务会被中断，根因：
1. 工具语义不匹配：`subtask-orchestrate run` 是异步注册，不是阻塞返回
2. 链路不可靠：spawn/announce/后台 exec 在不同环境可能不稳定
3. 用户新消息会打断等待中的任务

## 解决方案

把所有"长任务/复杂任务"统一为 **异步 Job**：

```
主会话 → submit job → 立即返回 job_id (永不阻塞)
Worker → 执行 + 落盘 result + sessions_send 回传
Watchdog → 60~120s 巡检，STUCK 重试，DONE 未 ACK 补发
```

## 核心原则

1. **主会话永不阻塞** - submit 立即返回 job_id
2. **双保险握手** - 结果落盘 + 通知回传
3. **Watchdog 兜底** - STUCK 重试，通知补发
4. **Lease 保护** - 防止 watchdog 误判活跃 worker

## 快速开始

### 提交任务

```bash
# 基础提交
python3 tools/job-submit-ocl "任务描述" --repo /path/to/repo

# 带等待
python3 tools/job-submit-ocl "任务描述" --follow
```

### 管理任务

```bash
# 列出任务
python3 tools/jobctl ls

# 查看详情
python3 tools/jobctl show <job_id>

# 查看日志
python3 tools/jobctl tail <job_id>

# 确认任务
python3 tools/jobctl ack <job_id>

# 取消任务
python3 tools/jobctl cancel <job_id> --reason "不再需要"

# 重试任务
python3 tools/jobctl retry <job_id>
```

### 自动启动机制 (v0.3 新增)

防止任务在 QUEUED 状态卡住：

```bash
# 提交时自动启动 worker (--auto-start)
python3 tools/job-submit-ocl "任务描述" --repo /path/to/repo --auto-start

# 检查并确保 worker 运行
python3 tools/job-auto-start ensure

# 查看 pool 状态
python3 tools/job-auto-start status
```

### Systemd 集成

```bash
# 安装服务
cp systemd/longrunkit-job-pool.service ~/.config/systemd/user/
cp systemd/longrunkit-job-watchdog.* ~/.config/systemd/user/
systemctl --user daemon-reload

# 方式 1: 持续运行的 pool
systemctl --user enable longrunkit-job-pool
systemctl --user start longrunkit-job-pool

# 方式 2: 定时检查 (每 5 分钟)
systemctl --user enable longrunkit-job-watchdog.timer
systemctl --user start longrunkit-job-watchdog.timer
```

## 启动 Watchdog

```bash
# 单次检查
python3 tools/job-watchdog-v3 --once

# 持续运行
python3 tools/job-watchdog-v3 --interval 60

# 定时任务 (cron)
*/2 * * * * cd /path/to/LongRunKit && python3 tools/job-watchdog-v3 --once
```

## 目录结构

```
LongRunKit/
├── jobs/                    # Job 存储目录
│   └── <job_id>/           # 具体 Job
│       ├── spec.json       # 任务输入与约束
│       ├── status.json     # 状态机 + 心跳 + lease + rev
│       ├── result.md       # 最终结果
│       ├── summary.json    # 执行摘要
│       ├── logs.ndjson     # 结构化日志
│       ├── ack.json        # ACK 记录
│       └── .lock           # 文件锁
├── tools/
│   ├── joblib.py           # 核心库 (原子写入、锁、lease、安全)
│   ├── jobctl              # 管理工具 (ls/show/tail/ack/cancel/retry)
│   ├── job-submit-ocl      # 提交器 (--auto-start 支持)
│   ├── job-worker-v3       # 增强版 worker
│   ├── job-watchdog-v3     # 增强版 watchdog
│   ├── jobindex            # SQLite 索引
│   ├── job-pool            # Worker Pool
│   ├── job-auto-start      # 自动启动机制
│   └── job-validator       # 安全验证
├── systemd/                 # Systemd 服务文件
│   ├── longrunkit-job-pool.service
│   ├── longrunkit-job-watchdog.service
│   └── longrunkit-job-watchdog.timer
└── tests/
    ├── test-job-protocol.py    # v0.1 测试 (5/5)
    ├── test-job-protocol-v2.py # v0.2 测试 (9/9)
    └── test-job-protocol-p2.py # P2 测试 (6/6)
```

## 状态机

```
QUEUED → RUNNING → DONE
              ↓
            FAILED
              ↓
            STUCK (lease 过期 + 无心跳)
              ↓
            CANCELLED (手动取消)
```

## Schema v0.2

### status.json

```json
{
  "job_id": "20260303_211200_abcd1234",
  "state": "RUNNING",
  "_rev": 5,
  "created_at": "2026-03-03T21:12:00Z",
  "updated_at": "2026-03-03T21:15:00Z",
  "heartbeat_at": "2026-03-03T21:15:00Z",
  "attempt": 1,
  "max_attempts": 3,
  "owner_session": "agent:main",
  "worker_session": "worker:12345",
  "lease_owner": "worker:12345",
  "lease_until": "2026-03-03T21:17:00Z",
  "notify_count": 1,
  "last_notify_at": "2026-03-03T21:15:00Z",
  "acked_at": null,
  "error": null,
  "error_class": null
}
```

## Lease 机制

防止 watchdog 在 worker 活跃时误判为 STUCK：

1. Worker 启动时获取 lease (默认 2 分钟)
2. Worker 定期续租 (心跳时)
3. Watchdog 只在 lease 过期后才判定 STUCK
4. Worker 完成时释放 lease

## 通知退避

防止通知补发风暴：

```python
delay = base * 2^attempt ± 20% jitter
```

- 第 1 次：30s
- 第 2 次：60s
- 第 3 次：120s
- ...

## 错误分类

| 类型 | 说明 | 重试 |
|------|------|------|
| TRANSIENT | 临时错误 (网络/IO) | ✅ |
| TIMEOUT | 超时 | ✅ |
| PERMANENT | 永久错误 | ❌ |
| CANCELLED | 用户取消 | ❌ |

## 验收标准

- [x] 用户在主会话连续发消息，长任务依然能完成
- [x] 主会话不会因为等待长任务而被 SIGTERM
- [x] Worker 被杀 → watchdog 能重试
- [x] 通知丢失 → watchdog 能补发
- [x] 并发写入 → CAS 冲突检测
- [x] Watchdog 不会误判活跃 worker (lease 保护)
- [x] 所有状态变化可追溯 (rev + logs.ndjson)

## 测试

```bash
# v0.1 测试 (5/5)
python3 tests/test-job-protocol.py

# v0.2 测试 (9/9)
python3 tests/test-job-protocol-v2.py
```

## 后续改进 (P3)

| 优先级 | 改进 | 状态 |
|--------|------|------|
| P3 | Web UI | 🔜 |
| P3 | Cancel/Pause/Resume | ✅ (jobctl cancel 已实现) |
| P3 | Worker Pool 自动扩缩容 | 🔜 |

## License

MIT
