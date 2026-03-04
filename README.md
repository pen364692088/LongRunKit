# LongRunKit

**异步 Job 协议** - 解决长任务被中断的问题。

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

## 快速开始

### 提交任务

```bash
# 方式 1: 基础提交 (手动 spawn)
python3 tools/job-submit-ocl "任务描述" --repo /path/to/repo

# 方式 2: 带 spawn 的提交 (需要 OpenClaw 环境)
python3 tools/job-submit-with-spawn "任务描述" --repo /path/to/repo

# 方式 3: 等待完成
python3 tools/job-submit-ocl "任务描述" --follow --follow-timeout 300
```

### 查询状态

```bash
# 查看状态
cat jobs/<job_id>/status.json

# 获取结果
cat jobs/<job_id>/result.md
```

### 运行 Worker

```bash
# 手动运行 worker
python3 tools/job-worker-v2 <job_id>

# 通过 sessions_spawn 运行
sessions_spawn runtime=subagent model=baiduqianfancodingplan/qianfan-code-latest \
  task='python3 /path/to/job-worker-v2 <job_id>'
```

### 启动 Watchdog

```bash
# 单次检查
python3 tools/job-watchdog --once

# 持续运行
python3 tools/job-watchdog --interval 60

# 定时任务 (cron)
*/2 * * * * cd /path/to/LongRunKit && python3 tools/job-watchdog --once
```

## 目录结构

```
LongRunKit/
├── jobs/                    # Job 存储目录
│   ├── README.md           # 协议说明
│   └── <job_id>/           # 具体 Job
│       ├── spec.json       # 任务输入与约束
│       ├── status.json     # 状态机 + 心跳 + 错误
│       ├── result.md       # 最终结果
│       └── logs.txt        # 可选日志
├── tools/
│   ├── job-submit          # 基础提交器
│   ├── job-submit-ocl      # OpenClaw 集成提交器
│   ├── job-submit-with-spawn # 带 spawn 的提交器
│   ├── job-worker          # 基础 worker
│   ├── job-worker-v2       # 增强 worker (心跳 + 回传)
│   └── job-watchdog        # 守护巡检
└── tests/
    └── test-job-protocol.py # 验收测试
```

## 状态机

```
QUEUED → RUNNING → DONE
              ↓
            FAILED
              ↓
            STUCK (watchdog 判定)
```

### 状态说明

| 状态 | 说明 |
|------|------|
| QUEUED | 已创建，待 worker 接手 |
| RUNNING | worker 已开始，心跳更新中 |
| DONE | 完成（result 可读） |
| FAILED | 失败（error 可追溯） |
| STUCK | 疑似卡死/丢失（watchdog 判定） |

## Schema

### spec.json

```json
{
  "job_id": "20260303_211200_abcd1234",
  "title": "Task title",
  "task_type": "ai_task | shell_task",
  "inputs": {
    "repo": "/path/to/repo",
    "goal": "Task description",
    "command": "shell command (optional)"
  },
  "constraints": {
    "time_budget_min": 30
  },
  "callbacks": {
    "notify_session": "agent:main"
  },
  "model": "baiduqianfancodingplan/qianfan-code-latest",
  "idempotency_key": "hash of inputs"
}
```

### status.json

```json
{
  "job_id": "20260303_211200_abcd1234",
  "state": "RUNNING",
  "created_at": "2026-03-03T21:12:00Z",
  "updated_at": "2026-03-03T21:15:00Z",
  "heartbeat_at": "2026-03-03T21:15:00Z",
  "attempt": 1,
  "max_attempts": 3,
  "owner_session": "agent:main",
  "worker_session": "agent:main:subagent:xxxx",
  "error": null
}
```

## 与 subtask-orchestrate 集成

`job-submit-with-spawn` 内部调用 `subtask-orchestrate run` 注册任务：

```python
# 注册任务
subtask-orchestrate run "Job <job_id>: <title>" -m <model> --timeout <timeout>

# 等待完成 (可选)
subtask-orchestrate join -t 300 --task-id <task_id>
```

## 验收标准

✅ 用户在主会话连续发消息，长任务依然能完成并产出 result.md  
✅ 主会话不会因为等待长任务而被 SIGTERM  
✅ Worker 被杀/无回传 → watchdog 能在超时后标记 STUCK 并重试  
✅ DONE 但通知丢失 → watchdog 能补发回传通知  
✅ 所有状态变化都有可追溯记录  

## 测试

```bash
# 运行验收测试
python3 tests/test-job-protocol.py
```

## 扩展阅读

- [Agentic Engineering Framework](../AgenticEngineering/) - 多 Agent 协作框架
- [subtask-orchestrate](../../.openclaw/workspace/tools/orchestrator/) - OpenClaw 子任务编排

## License

MIT
