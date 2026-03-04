#!/usr/bin/env python3
"""
test-job-protocol-v2.py - v0.2 验收测试

测试:
1. 原子写入 + 文件锁
2. CAS 更新 (rev 版本号)
3. Lease 机制
4. 结构化日志
5. jobctl 工具
"""

import json
import os
import sys
import time
import subprocess
import threading
from datetime import datetime, timezone, timedelta
from pathlib import Path

# 添加 tools 目录到 path
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_DIR = SCRIPT_DIR.parent
JOBS_DIR = PROJECT_DIR / "jobs"
TOOLS_DIR = PROJECT_DIR / "tools"

sys.path.insert(0, str(TOOLS_DIR))

from joblib import (
    atomic_write_json, read_status_with_rev, update_status_cas,
    StatusUpdateConflict, acquire_lease, renew_lease, release_lease,
    is_lease_expired, write_log_event, mark_acked, is_acked,
    calculate_notify_delay, should_notify, record_notify,
    classify_error, ErrorClass
)


def run_cmd(cmd: str, cwd: str = None) -> tuple:
    """运行命令"""
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
    """提取 job_id"""
    for line in output.split("\n"):
        if line.startswith("Job ID:"):
            return line.split(":")[1].strip()
    return None


def test_atomic_write():
    """测试 1: 原子写入"""
    print("\n[TEST 1] Atomic write...")
    
    test_file = JOBS_DIR / "test_atomic.json"
    
    # 写入
    atomic_write_json(test_file, {"test": "data", "ts": time.time()})
    
    assert test_file.exists(), "File not created"
    
    data = json.loads(test_file.read_text())
    assert data["test"] == "data", "Data mismatch"
    
    # 清理
    test_file.unlink()
    
    print("  ✅ Atomic write works")
    return True


def test_cas_update():
    """测试 2: CAS 更新"""
    print("\n[TEST 2] CAS update...")
    
    # 创建测试 job
    rc, out, _ = run_cmd("python3 job-submit-ocl 'CAS test' --title 'CAS Test'", cwd=str(TOOLS_DIR))
    job_id = extract_job_id(out)
    
    if not job_id:
        print("  ❌ Failed to create job")
        return False
    
    job_dir = JOBS_DIR / job_id
    
    # 读取状态
    status, rev = read_status_with_rev(job_dir)
    assert rev == 0, f"Initial rev should be 0, got {rev}"
    
    # 成功更新 (正确的 rev)
    status, new_rev = update_status_cas(job_dir, {"test_field": "value"}, rev)
    assert new_rev == 1, f"Rev should be 1, got {new_rev}"
    
    # 再次读取
    status, current_rev = read_status_with_rev(job_dir)
    assert current_rev == 1, f"Current rev should be 1, got {current_rev}"
    
    # 冲突更新 (错误的 rev)
    try:
        update_status_cas(job_dir, {"test_field": "value2"}, rev)  # 旧的 rev
        print("  ❌ Should have raised StatusUpdateConflict")
        return False
    except StatusUpdateConflict:
        pass  # 期望的
    
    print("  ✅ CAS update works")
    return True


def test_lease_mechanism():
    """测试 3: Lease 机制"""
    print("\n[TEST 3] Lease mechanism...")
    
    # 创建测试 job
    rc, out, _ = run_cmd("python3 job-submit-ocl 'Lease test' --title 'Lease Test'", cwd=str(TOOLS_DIR))
    job_id = extract_job_id(out)
    
    if not job_id:
        print("  ❌ Failed to create job")
        return False
    
    job_dir = JOBS_DIR / job_id
    
    # 清理残留锁
    lock_file = job_dir / ".lock"
    if lock_file.exists():
        lock_file.unlink()
    
    # 更新为 RUNNING
    update_status_cas(job_dir, {"state": "RUNNING", "attempt": 1}, 0)
    
    # 等待锁释放
    time.sleep(0.1)
    
    # 获取 lease
    owner1 = "worker:1"
    assert acquire_lease(job_dir, owner1, duration_minutes=2), "Failed to acquire lease"
    
    # 检查 lease
    assert not is_lease_expired(job_dir), "Lease should not be expired"
    
    # 另一个 worker 尝试获取 (应该失败)
    owner2 = "worker:2"
    assert not acquire_lease(job_dir, owner2, duration_minutes=2), "Should not acquire lease held by others"
    
    # 原持有者续租
    assert renew_lease(job_dir, owner1, duration_minutes=2), "Failed to renew lease"
    
    # 释放 lease
    assert release_lease(job_dir, owner1), "Failed to release lease"
    
    # 现在 lease 应该过期
    assert is_lease_expired(job_dir), "Lease should be expired after release"
    
    # 另一个 worker 现在可以获取
    assert acquire_lease(job_dir, owner2, duration_minutes=2), "Should acquire released lease"
    
    print("  ✅ Lease mechanism works")
    return True


def test_structured_logging():
    """测试 4: 结构化日志"""
    print("\n[TEST 4] Structured logging...")
    
    # 创建测试 job
    rc, out, _ = run_cmd("python3 job-submit-ocl 'Log test' --title 'Log Test'", cwd=str(TOOLS_DIR))
    job_id = extract_job_id(out)
    
    if not job_id:
        print("  ❌ Failed to create job")
        return False
    
    job_dir = JOBS_DIR / job_id
    
    # 写入事件
    write_log_event(job_dir, {"source": "worker", "phase": "start", "message": "Starting"})
    write_log_event(job_dir, {"source": "worker", "phase": "execute", "message": "Executing"})
    write_log_event(job_dir, {"source": "watchdog", "action": "check", "message": "Checking"})
    
    # 读取日志
    log_path = job_dir / "logs.ndjson"
    assert log_path.exists(), "Log file not created"
    
    lines = log_path.read_text().strip().split("\n")
    assert len(lines) == 3, f"Expected 3 log lines, got {len(lines)}"
    
    # 解析日志
    for line in lines:
        event = json.loads(line)
        assert "ts" in event, "Missing timestamp"
        assert "source" in event, "Missing source"
        assert "message" in event, "Missing message"
    
    print("  ✅ Structured logging works")
    return True


def test_notify_backoff():
    """测试 5: 通知退避"""
    print("\n[TEST 5] Notify backoff...")
    
    # 创建测试 job
    rc, out, _ = run_cmd("python3 job-submit-ocl 'Notify test' --title 'Notify Test'", cwd=str(TOOLS_DIR))
    job_id = extract_job_id(out)
    
    if not job_id:
        print("  ❌ Failed to create job")
        return False
    
    job_dir = JOBS_DIR / job_id
    
    # 初始应该可以通知
    assert should_notify(job_dir), "Should allow initial notify"
    
    # 记录通知
    record_notify(job_dir)
    
    # 立即再次通知应该被阻止 (cooldown)
    # 注：由于时间精度，可能需要等一小会儿
    time.sleep(0.1)
    
    # 计算延迟
    delay = calculate_notify_delay(1)
    assert delay > 0, "Delay should be positive"
    
    print(f"  ✅ Notify backoff works (delay={delay:.1f}s)")
    return True


def test_ack_management():
    """测试 6: ACK 管理"""
    print("\n[TEST 6] ACK management...")
    
    # 创建测试 job
    rc, out, _ = run_cmd("python3 job-submit-ocl 'ACK test' --title 'ACK Test'", cwd=str(TOOLS_DIR))
    job_id = extract_job_id(out)
    
    if not job_id:
        print("  ❌ Failed to create job")
        return False
    
    job_dir = JOBS_DIR / job_id
    
    # 初始未 ACK
    assert not is_acked(job_dir), "Should not be acked initially"
    
    # 标记 ACK
    mark_acked(job_dir, "test_session")
    
    # 现在应该 ACK
    assert is_acked(job_dir), "Should be acked after marking"
    
    # 检查 ack.json
    ack_path = job_dir / "ack.json"
    assert ack_path.exists(), "ack.json not created"
    
    ack_data = json.loads(ack_path.read_text())
    assert ack_data["acked_by"] == "test_session", "Wrong acked_by"
    
    print("  ✅ ACK management works")
    return True


def test_error_classification():
    """测试 7: 错误分类"""
    print("\n[TEST 7] Error classification...")
    
    # 测试各种错误
    tests = [
        ("connection timeout", ErrorClass.TIMEOUT),
        ("network error", ErrorClass.TRANSIENT),
        ("file not found", ErrorClass.PERMANENT),
        ("cancelled by user", ErrorClass.CANCELLED),
    ]
    
    for error_str, expected_class in tests:
        actual_class = classify_error(error_str)
        if actual_class != expected_class:
            print(f"  ❌ '{error_str}' -> {actual_class}, expected {expected_class}")
            return False
    
    print("  ✅ Error classification works")
    return True


def test_jobctl():
    """测试 8: jobctl 工具"""
    print("\n[TEST 8] jobctl tool...")
    
    # 创建测试 job
    rc, out, _ = run_cmd("python3 job-submit-ocl 'Jobctl test' --title 'Jobctl Test'", cwd=str(TOOLS_DIR))
    job_id = extract_job_id(out)
    
    if not job_id:
        print("  ❌ Failed to create job")
        return False
    
    # 测试 ls
    rc, out, _ = run_cmd("python3 jobctl ls", cwd=str(TOOLS_DIR))
    assert rc == 0, f"jobctl ls failed: {out}"
    assert job_id in out, f"Job not listed: {out}"
    
    # 测试 show
    rc, out, _ = run_cmd(f"python3 jobctl show {job_id}", cwd=str(TOOLS_DIR))
    assert rc == 0, f"jobctl show failed: {out}"
    assert "Jobctl Test" in out, f"Title not shown: {out}"
    
    # 测试 ack
    rc, out, _ = run_cmd(f"python3 jobctl ack {job_id}", cwd=str(TOOLS_DIR))
    assert rc == 0, f"jobctl ack failed: {out}"
    
    # 验证 ack
    assert is_acked(JOBS_DIR / job_id), "Job not acked"
    
    print("  ✅ jobctl works")
    return True


def test_concurrent_writes():
    """测试 9: 并发写入"""
    print("\n[TEST 9] Concurrent writes...")
    
    # 创建测试 job
    rc, out, _ = run_cmd("python3 job-submit-ocl 'Concurrent test' --title 'Concurrent Test'", cwd=str(TOOLS_DIR))
    job_id = extract_job_id(out)
    
    if not job_id:
        print("  ❌ Failed to create job")
        return False
    
    job_dir = JOBS_DIR / job_id
    
    # 并发写入测试
    results = []
    errors = []
    
    def writer(writer_id: int):
        try:
            for i in range(5):
                status, rev = read_status_with_rev(job_dir)
                update_status_cas(job_dir, {f"writer_{writer_id}": i}, rev)
                results.append((writer_id, i))
        except StatusUpdateConflict:
            errors.append(writer_id)
    
    threads = [threading.Thread(target=writer, args=(i,)) for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    # 检查结果
    final_status, final_rev = read_status_with_rev(job_dir)
    
    # rev 应该增加了 (至少有一些成功)
    assert final_rev > 0, f"Rev should have increased, got {final_rev}"
    
    print(f"  ✅ Concurrent writes handled (rev={final_rev}, conflicts={len(errors)})")
    return True


def main():
    print("=" * 60)
    print("Job Protocol v0.2 Acceptance Tests")
    print("=" * 60)
    
    tests = [
        ("Atomic write", test_atomic_write),
        ("CAS update", test_cas_update),
        ("Lease mechanism", test_lease_mechanism),
        ("Structured logging", test_structured_logging),
        ("Notify backoff", test_notify_backoff),
        ("ACK management", test_ack_management),
        ("Error classification", test_error_classification),
        ("jobctl tool", test_jobctl),
        ("Concurrent writes", test_concurrent_writes),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            ok = test_func()
            results.append((name, ok))
        except Exception as e:
            print(f"  ❌ Error: {e}")
            results.append((name, False))
    
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
