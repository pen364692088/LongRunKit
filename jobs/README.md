# LongRunKit - 异步 Job 协议

## 概述

把长任务统一为异步 Job，解决：
- 主会话被 SIGTERM 中断
- spawn/announce 链路不稳定
- 用户新消息影响任务执行

## 核心原则

1. **主会话永不阻塞** - submit 立即返回 job_id
2. **双保险握手** - 结果落盘 + 通知回传
3. **Watchdog 兜底** - STUCK 重试，通知补发

## 目录结构

```
jobs/
├── <job_id>/
│   ├── spec.json      # 任务输入与约束
│   ├── status.json    # 状态机 + 心跳 + 错误
│   ├── result.md      # 最终结果
│   └── logs.txt       # 可选日志
```

## 状态机

```
QUEUED → RUNNING → DONE
              ↓
            FAILED
              ↓
            STUCK (watchdog 判定)
```

## 工具

- `tools/job-submit` - 创建 job + spawn worker
- `tools/job-worker` - 执行任务 + 落盘结果 + 回传通知
- `tools/job-watchdog` - 巡检 + 重试 + 补发

## Schema

### spec.json
```json
{
  "job_id": "20260303_211200_abcd1234",
  "title": "Task title",
  "task_type": "long_task",
  "inputs": { "repo": "...", "goal": "..." },
  "constraints": { "time_budget_min": 30 },
  "callbacks": { "notify_session": "agent:main" },
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

## 使用流程

1. 提交任务：
   ```bash
   job-submit "任务描述" --repo /path/to/repo
   # 返回 job_id
   ```

2. 查询状态：
   ```bash
   cat jobs/<job_id>/status.json
   ```

3. 获取结果：
   ```bash
   cat jobs/<job_id>/result.md
   ```

## 与 subtask-orchestrate 集成

- `job-submit` 内部调用 `subtask-orchestrate run` 注册任务
- `--follow` 模式基于 job status 等待（非阻塞 stdout）
