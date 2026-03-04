#!/usr/bin/env python3
"""
test-job-protocol-p2.py - P2 验收测试

测试:
1. SQLite 索引
2. Worker Pool
3. 安全边界
"""

import json
import os
import sys
import time
import subprocess
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_DIR = SCRIPT_DIR.parent
JOBS_DIR = PROJECT_DIR / "jobs"
TOOLS_DIR = PROJECT_DIR / "tools"

sys.path.insert(0, str(TOOLS_DIR))


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


def test_sqlite_index():
    """测试 1: SQLite 索引"""
    print("\n[TEST 1] SQLite index...")
    
    # 初始化
    rc, out, err = run_cmd("python3 jobindex init", cwd=str(TOOLS_DIR))
    if rc != 0:
        print(f"  ❌ Init failed: {err}")
        return False
    
    # 创建测试 job
    rc, out, _ = run_cmd("python3 job-submit-ocl 'Index test' --title 'Index Test'", cwd=str(TOOLS_DIR))
    job_id = extract_job_id(out)
    
    if not job_id:
        print("  ❌ Failed to create job")
        return False
    
    # 同步到索引
    rc, out, err = run_cmd("python3 jobindex sync", cwd=str(TOOLS_DIR))
    if rc != 0:
        print(f"  ❌ Sync failed: {err}")
        return False
    
    # 查询
    rc, out, err = run_cmd("python3 jobindex query --state QUEUED", cwd=str(TOOLS_DIR))
    if rc != 0:
        print(f"  ❌ Query failed: {err}")
        return False
    
    if job_id not in out:
        print(f"  ❌ Job not found in index: {out}")
        return False
    
    # 统计
    rc, out, err = run_cmd("python3 jobindex stats", cwd=str(TOOLS_DIR))
    if rc != 0:
        print(f"  ❌ Stats failed: {err}")
        return False
    
    stats = json.loads(out)
    if stats.get("total", 0) < 1:
        print(f"  ❌ Stats wrong: {out}")
        return False
    
    print(f"  ✅ SQLite index works (total={stats['total']})")
    return True


def test_path_validation():
    """测试 2: 路径验证"""
    print("\n[TEST 2] Path validation...")
    
    # 测试允许的路径
    rc, out, _ = run_cmd(
        "python3 job-validator check-path /home/moonlight/Project/test",
        cwd=str(TOOLS_DIR)
    )
    if rc != 0 or "allowed" not in out.lower():
        print(f"  ❌ Allowed path rejected: {out}")
        return False
    
    # 测试不允许的路径
    rc, out, _ = run_cmd(
        "python3 job-validator check-path /etc/passwd",
        cwd=str(TOOLS_DIR)
    )
    if rc == 0 or "not allowed" not in out.lower():
        print(f"  ❌ Forbidden path accepted: {out}")
        return False
    
    # 测试路径遍历
    from joblib import check_path_traversal
    
    if check_path_traversal("../../../etc/passwd"):
        print(f"  ❌ Path traversal not detected")
        return False
    
    if not check_path_traversal("/home/user/project"):
        print(f"  ❌ Safe path rejected")
        return False
    
    print("  ✅ Path validation works")
    return True


def test_command_injection():
    """测试 3: 命令注入检测"""
    print("\n[TEST 3] Command injection detection...")
    
    from joblib import check_command_injection
    
    # 测试安全命令
    safe_commands = [
        "ls -la",
        "python3 script.py",
        "make build",
    ]
    
    for cmd in safe_commands:
        is_safe, msg = check_command_injection(cmd)
        if not is_safe:
            print(f"  ❌ Safe command rejected: {cmd} - {msg}")
            return False
    
    # 测试危险命令
    dangerous_commands = [
        "ls; rm -rf /",
        "cat file | grep secret",
        "echo $HOME",
        "`whoami`",
    ]
    
    for cmd in dangerous_commands:
        is_safe, msg = check_command_injection(cmd)
        if is_safe:
            print(f"  ❌ Dangerous command accepted: {cmd}")
            return False
    
    print("  ✅ Command injection detection works")
    return True


def test_input_sanitization():
    """测试 4: 输入净化"""
    print("\n[TEST 4] Input sanitization...")
    
    from joblib import sanitize_input
    
    # 测试正常输入
    normal = "This is a normal task description"
    clean = sanitize_input(normal)
    if clean != normal:
        print(f"  ❌ Normal input modified: {clean}")
        return False
    
    # 测试控制字符
    dirty = "Task\x00name\x1f with control chars"
    clean = sanitize_input(dirty)
    if "\x00" in clean or "\x1f" in clean:
        print(f"  ❌ Control chars not removed: {repr(clean)}")
        return False
    
    # 测试长度限制
    long_text = "x" * 20000
    clean = sanitize_input(long_text, max_length=1000)
    if len(clean) > 1000:
        print(f"  ❌ Length limit not applied: {len(clean)}")
        return False
    
    print("  ✅ Input sanitization works")
    return True


def test_sensitive_filter():
    """测试 5: 敏感信息过滤"""
    print("\n[TEST 5] Sensitive info filtering...")
    
    from joblib import filter_sensitive_from_result
    
    result = """
API_KEY=sk-1234567890abcdef
password=secret123
Token: bearer xyz789
Normal output here
"""
    
    filtered = filter_sensitive_from_result(result)
    
    if "sk-1234567890abcdef" in filtered:
        print(f"  ❌ API key not filtered")
        return False
    
    if "secret123" in filtered:
        print(f"  ❌ Password not filtered")
        return False
    
    if "bearer xyz789" in filtered:
        print(f"  ❌ Token not filtered")
        return False
    
    if "Normal output" not in filtered:
        print(f"  ❌ Normal output filtered")
        return False
    
    print("  ✅ Sensitive info filtering works")
    return True


def test_spec_validation():
    """测试 6: Spec 验证"""
    print("\n[TEST 6] Spec validation...")
    
    from joblib import validate_spec
    
    # 测试有效 spec
    valid_spec = {
        "job_id": "test_123",
        "title": "Test Job",
        "task_type": "ai_task",
        "inputs": {
            "repo": "/home/moonlight/Project/test",
            "goal": "Test task"
        }
    }
    
    is_valid, errors = validate_spec(valid_spec)
    if not is_valid:
        print(f"  ❌ Valid spec rejected: {errors}")
        return False
    
    # 测试无效 spec
    invalid_spec = {
        "title": "Missing job_id"
    }
    
    is_valid, errors = validate_spec(invalid_spec)
    if is_valid:
        print(f"  ❌ Invalid spec accepted")
        return False
    
    # 测试路径不在白名单
    bad_path_spec = {
        "job_id": "test_456",
        "title": "Bad Path",
        "task_type": "ai_task",
        "inputs": {
            "repo": "/etc/passwd"
        }
    }
    
    is_valid, errors = validate_spec(bad_path_spec)
    if is_valid:
        print(f"  ❌ Bad path spec accepted")
        return False
    
    print("  ✅ Spec validation works")
    return True


def main():
    print("=" * 60)
    print("Job Protocol P2 Acceptance Tests")
    print("=" * 60)
    
    tests = [
        ("SQLite index", test_sqlite_index),
        ("Path validation", test_path_validation),
        ("Command injection", test_command_injection),
        ("Input sanitization", test_input_sanitization),
        ("Sensitive filter", test_sensitive_filter),
        ("Spec validation", test_spec_validation),
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
