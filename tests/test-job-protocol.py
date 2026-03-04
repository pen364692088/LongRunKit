#!/usr/bin/env python3
"""
test-job-protocol.py - 验收测试

验收标准:
1. 用户在主会话连续发消息，长任务依然能完成并产出 result.md
2. 主会话不会因为等待长任务而被 SIGTERM
3. 任意一次 worker 被杀/无回传：watchdog 能重试
4. DONE 但通知丢失：watchdog 能补发
"""

import json
import os
import sys
import time
import subprocess
from datetime import datetime, timezone
from pathlib import Path

# 正确计算路径
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_DIR = SCRIPT_DIR.parent
JOBS_DIR = PROJECT_DIR / "jobs"
TOOLS_DIR = PROJECT_DIR / "tools"


def run_cmd(cmd: str, cwd: str = None) -> tuple:
    """运行命令，返回 (returncode, stdout, stderr)"""
    result = subprocess.run(
        cmd,
        shell=True,
        cwd=cwd or str(TOOLS_DIR),
        capture_output=True,
        text=True,
        timeout=30
    )
    return result.returncode, result.stdout, result.stderr


def extract_job_id(output: str) -> str:
    """从输出中提取 job_id"""
    for line in output.split("\n"):
        if line.startswith("Job ID:"):
            return line.split(":")[1].strip()
    return None


def test_submit_creates_job():
    """测试 1: submit 创建 job 目录和文件"""
    print("\n[TEST 1] Submit creates job files...")
    
    rc, out, err = run_cmd(
        "python3 job-submit-ocl 'Test task 1' --title 'Test Job 1'",
        cwd=str(TOOLS_DIR)
    )
    
    if rc != 0:
        print(f"  ❌ Submit failed: {err}")
        return None
    
    if "Job ID:" not in out:
        print(f"  ❌ No job ID in output: {out}")
        return None
    
    job_id = extract_job_id(out)
    if not job_id:
        print(f"  ❌ Failed to extract job ID")
        return None
    
    # 检查文件存在
    job_dir = JOBS_DIR / job_id
    if not (job_dir / "spec.json").exists():
        print(f"  ❌ spec.json not created")
        return None
    
    if not (job_dir / "status.json").exists():
        print(f"  ❌ status.json not created")
        return None
    
    # 检查状态
    status = json.loads((job_dir / "status.json").read_text())
    if status["state"] != "QUEUED":
        print(f"  ❌ Unexpected state: {status['state']}")
        return None
    
    print(f"  ✅ Job created: {job_id}")
    return job_id


def test_worker_executes_job(job_id: str):
    """测试 2: worker 执行任务并完成握手"""
    print(f"\n[TEST 2] Worker executes job {job_id}...")
    
    if not job_id:
        print("  ⏭️ Skipped (no job_id)")
        return False
    
    rc, out, err = run_cmd(
        f"python3 job-worker-v2 {job_id} --no-callback",
        cwd=str(TOOLS_DIR)
    )
    
    if rc != 0:
        print(f"  ❌ Worker failed: {err}")
        return False
    
    if "DONE" not in out:
        print(f"  ❌ Job not completed: {out}")
        return False
    
    # 检查状态
    job_dir = JOBS_DIR / job_id
    status = json.loads((job_dir / "status.json").read_text())
    
    if status["state"] != "DONE":
        print(f"  ❌ Unexpected state: {status['state']}")
        return False
    
    if status["attempt"] != 1:
        print(f"  ❌ Unexpected attempt: {status['attempt']}")
        return False
    
    # 检查结果
    if not (job_dir / "result.md").exists():
        print(f"  ❌ result.md not created")
        return False
    
    result = (job_dir / "result.md").read_text()
    if "Test task 1" not in result:
        print(f"  ❌ Result missing task info")
        return False
    
    print(f"  ✅ Job completed, result written")
    return True


def test_idempotency():
    """测试 3: 幂等性 - 已完成的 job 不重复执行"""
    print("\n[TEST 3] Idempotency check...")
    
    # 先创建一个新 job
    rc, out, err = run_cmd(
        "python3 job-submit-ocl 'Test idempotency' --title 'Idempotency Test'",
        cwd=str(TOOLS_DIR)
    )
    
    if rc != 0:
        print(f"  ❌ Submit failed: {err}")
        return False
    
    job_id = extract_job_id(out)
    if not job_id:
        print(f"  ❌ Failed to extract job ID")
        return False
    
    # 执行一次
    run_cmd(f"python3 job-worker-v2 {job_id}", cwd=str(TOOLS_DIR))
    
    # 检查 attempt
    job_dir = JOBS_DIR / job_id
    status1 = json.loads((job_dir / "status.json").read_text())
    attempt1 = status1["attempt"]
    
    # 再执行一次
    run_cmd(f"python3 job-worker-v2 {job_id}", cwd=str(TOOLS_DIR))
    
    status2 = json.loads((job_dir / "status.json").read_text())
    attempt2 = status2["attempt"]
    
    # attempt 应该不变
    if attempt1 != attempt2:
        print(f"  ❌ Attempt changed: {attempt1} -> {attempt2}")
        return False
    
    print(f"  ✅ Idempotency preserved (attempt={attempt1})")
    return True


def test_watchdog_detects_stuck():
    """测试 4: watchdog 检测 STUCK 任务"""
    print("\n[TEST 4] Watchdog detects STUCK jobs...")
    
    # 创建一个 job 并设置为 RUNNING (模拟卡住)
    rc, out, err = run_cmd(
        "python3 job-submit-ocl 'Test stuck' --title 'Stuck Test'",
        cwd=str(TOOLS_DIR)
    )
    
    if rc != 0:
        print(f"  ❌ Submit failed: {err}")
        return False
    
    job_id = extract_job_id(out)
    if not job_id:
        print(f"  ❌ Failed to extract job ID")
        return False
    
    # 手动设置为 RUNNING 且心跳时间很久以前
    job_dir = JOBS_DIR / job_id
    status = json.loads((job_dir / "status.json").read_text())
    status["state"] = "RUNNING"
    status["heartbeat_at"] = "2026-01-01T00:00:00Z"  # 很久以前
    status["attempt"] = 1
    with open(job_dir / "status.json", "w") as f:
        json.dump(status, f, indent=2)
    
    # 运行 watchdog (dry-run)
    rc, out, err = run_cmd(
        "python3 job-watchdog --stuck-timeout 1 --dry-run --once",
        cwd=str(TOOLS_DIR)
    )
    
    if "STUCK" not in out:
        print(f"  ❌ Watchdog didn't detect STUCK: {out}")
        return False
    
    print(f"  ✅ Watchdog detected STUCK job")
    return True


def test_watchdog_resends_notification():
    """测试 5: watchdog 补发通知"""
    print("\n[TEST 5] Watchdog resends notification for DONE jobs without ACK...")
    
    # 创建一个已完成的 job
    rc, out, err = run_cmd(
        "python3 job-submit-ocl 'Test notification' --title 'Notification Test'",
        cwd=str(TOOLS_DIR)
    )
    
    if rc != 0:
        print(f"  ❌ Submit failed: {err}")
        return False
    
    job_id = extract_job_id(out)
    if not job_id:
        print(f"  ❌ Failed to extract job ID")
        return False
    
    # 执行完成
    run_cmd(f"python3 job-worker-v2 {job_id} --no-callback", cwd=str(TOOLS_DIR))
    
    # 确保 no ack (不创建 ack.json)
    job_dir = JOBS_DIR / job_id
    if (job_dir / "ack.json").exists():
        (job_dir / "ack.json").unlink()
    
    # 运行 watchdog
    rc, out, err = run_cmd(
        "python3 job-watchdog --dry-run --once",
        cwd=str(TOOLS_DIR)
    )
    
    if "NOACK" not in out:
        print(f"  ❌ Watchdog didn't detect NOACK: {out}")
        return False
    
    print(f"  ✅ Watchdog detected DONE without ACK")
    return True


def main():
    print("=" * 60)
    print("Job Protocol Acceptance Tests")
    print("=" * 60)
    
    results = []
    
    # 测试 1
    job_id = test_submit_creates_job()
    results.append(("Submit creates job", job_id is not None))
    
    # 测试 2
    if job_id:
        ok = test_worker_executes_job(job_id)
        results.append(("Worker executes job", ok))
    else:
        results.append(("Worker executes job", False))
    
    # 测试 3-5
    results.append(("Idempotency", test_idempotency()))
    results.append(("Watchdog detects STUCK", test_watchdog_detects_stuck()))
    results.append(("Watchdog resends notification", test_watchdog_resends_notification()))
    
    # 汇总
    print("\n" + "=" * 60)
    print("Results:")
    print("=" * 60)
    
    passed = 0
    for name, ok in results:
        status = "✅ PASS" if ok else "❌ FAIL"
        print(f"  {status}: {name}")
        if ok:
            passed += 1
    
    print(f"\nTotal: {passed}/{len(results)} passed")
    
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
