#!/usr/bin/env python3
"""
joblib.py - Job 协议核心库

v0.2 增强:
1. 原子写入 + 文件锁
2. CAS 更新 (rev 版本号)
3. Lease 机制
4. 结构化日志 (ndjson)
"""

import json
import os
import fcntl
import time
import random
import hashlib
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from contextlib import contextmanager

# ============ 原子写入 ============

def atomic_write(path: Path, content: str | bytes, mode: str = "w"):
    """
    原子写入：write temp → fsync → rename
    
    保证：要么完整写入，要么不变（不会出现撕裂/部分写入）
    """
    temp_path = path.with_suffix(path.suffix + ".tmp")
    
    if isinstance(content, bytes):
        mode = "wb"
    
    with open(temp_path, mode) as f:
        f.write(content)
        f.flush()
        os.fsync(f.fileno())
    
    os.rename(temp_path, path)


def atomic_write_json(path: Path, data: dict):
    """原子写入 JSON"""
    atomic_write(path, json.dumps(data, indent=2))


# ============ 文件锁 ============

@contextmanager
def file_lock(lock_path: Path, timeout: float = 5.0, blocking: bool = True):
    """
    文件锁上下文管理器
    
    用法:
        with file_lock(job_dir / ".lock"):
            # 临界区操作
            update_status(...)
    """
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_fd = open(lock_path, "w")
    
    try:
        if blocking:
            # 带超时的阻塞获取
            start = time.time()
            while True:
                try:
                    fcntl.flock(lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except (IOError, OSError):
                    if time.time() - start > timeout:
                        raise TimeoutError(f"Lock timeout: {lock_path}")
                    time.sleep(0.05)
        else:
            fcntl.flock(lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        
        yield lock_fd
        
    finally:
        try:
            fcntl.flock(lock_fd.fileno(), fcntl.LOCK_UN)
        except:
            pass
        finally:
            try:
                lock_fd.close()
            except:
                pass
            # 清理锁文件（可选）
            try:
                if lock_path.exists():
                    lock_path.unlink()
            except:
                pass


# ============ CAS 更新 (Compare-And-Swap) ============

class StatusUpdateConflict(Exception):
    """状态更新冲突 - rev 不匹配"""
    pass


def read_status_with_rev(job_dir: Path) -> Tuple[dict, int]:
    """读取 status + rev"""
    status_path = job_dir / "status.json"
    if not status_path.exists():
        return None, 0
    
    with open(status_path) as f:
        status = json.load(f)
    
    rev = status.get("_rev", 0)
    return status, rev


def update_status_cas(job_dir: Path, updates: dict, expected_rev: int = None, use_lock: bool = True) -> Tuple[dict, int]:
    """
    CAS 更新 status.json
    
    Args:
        job_dir: Job 目录
        updates: 要更新的字段
        expected_rev: 期望的 rev (None 表示自动读取当前 rev)
        use_lock: 是否使用锁 (嵌套调用时设为 False)
    
    Returns:
        (new_status, new_rev)
    
    Raises:
        StatusUpdateConflict: 如果 rev 冲突
    """
    status_path = job_dir / "status.json"
    lock_path = job_dir / ".lock"
    
    def do_update():
        # 读取当前状态
        current_status, current_rev = read_status_with_rev(job_dir)
        
        if current_status is None:
            current_status = {}
            current_rev = 0
        
        # 检查 rev
        if expected_rev is not None and current_rev != expected_rev:
            raise StatusUpdateConflict(
                f"Rev mismatch: expected {expected_rev}, got {current_rev}"
            )
        
        # 更新
        new_rev = current_rev + 1
        current_status.update(updates)
        current_status["_rev"] = new_rev
        current_status["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        # 原子写入
        atomic_write_json(status_path, current_status)
        
        return current_status, new_rev
    
    if use_lock:
        with file_lock(lock_path):
            return do_update()
    else:
        return do_update()


def update_status_safe(job_dir: Path, updates: dict, max_retries: int = 3) -> dict:
    """
    安全更新 (带重试)
    
    自动处理冲突，最多重试 max_retries 次
    """
    for attempt in range(max_retries):
        try:
            status, rev = update_status_cas(job_dir, updates)
            return status
        except StatusUpdateConflict:
            if attempt == max_retries - 1:
                raise
            time.sleep(0.1 * (attempt + 1))  # 退避
    
    return None


# ============ Lease 机制 ============

def acquire_lease(job_dir: Path, owner: str, duration_minutes: int = 2) -> bool:
    """
    获取 lease
    
    Args:
        job_dir: Job 目录
        owner: 租约持有者 (如 worker_session)
        duration_minutes: 租约时长 (分钟)
    
    Returns:
        是否成功获取
    """
    status_path = job_dir / "status.json"
    lock_path = job_dir / ".lock"
    
    with file_lock(lock_path):
        status, rev = read_status_with_rev(job_dir)
        
        if status is None:
            return False
        
        now = datetime.now(timezone.utc)
        lease_until = status.get("lease_until")
        
        # 检查是否有有效 lease
        if lease_until:
            lease_until_dt = datetime.fromisoformat(lease_until.replace("Z", "+00:00"))
            if now < lease_until_dt and status.get("lease_owner") != owner:
                # lease 被其他人持有
                return False
        
        # 获取 lease
        new_lease_until = now + timedelta(minutes=duration_minutes)
        updates = {
            "lease_owner": owner,
            "lease_until": new_lease_until.isoformat()
        }
        
        update_status_cas(job_dir, updates, rev, use_lock=False)
        return True


def renew_lease(job_dir: Path, owner: str, duration_minutes: int = 2) -> bool:
    """
    续租
    
    只有时 lease_owner 是自己才能续租
    """
    status_path = job_dir / "status.json"
    lock_path = job_dir / ".lock"
    
    with file_lock(lock_path):
        status, rev = read_status_with_rev(job_dir)
        
        if status is None:
            return False
        
        if status.get("lease_owner") != owner:
            return False
        
        now = datetime.now(timezone.utc)
        new_lease_until = now + timedelta(minutes=duration_minutes)
        
        updates = {
            "lease_until": new_lease_until.isoformat()
        }
        
        update_status_cas(job_dir, updates, rev, use_lock=False)
        return True


def release_lease(job_dir: Path, owner: str) -> bool:
    """释放 lease"""
    status_path = job_dir / "status.json"
    lock_path = job_dir / ".lock"
    
    with file_lock(lock_path):
        status, rev = read_status_with_rev(job_dir)
        
        if status is None:
            return False
        
        if status.get("lease_owner") != owner:
            return False
        
        updates = {
            "lease_owner": None,
            "lease_until": None
        }
        
        update_status_cas(job_dir, updates, rev, use_lock=False)
        return True


def is_lease_expired(job_dir: Path) -> bool:
    """检查 lease 是否过期"""
    status, _ = read_status_with_rev(job_dir)
    
    if status is None:
        return True
    
    lease_until = status.get("lease_until")
    if not lease_until:
        return True
    
    now = datetime.now(timezone.utc)
    lease_until_dt = datetime.fromisoformat(lease_until.replace("Z", "+00:00"))
    
    return now > lease_until_dt


# ============ 结构化日志 ============

def write_log_event(job_dir: Path, event: dict):
    """
    写入结构化日志事件
    
    格式: ndjson (每行一个 JSON)
    """
    log_path = job_dir / "logs.ndjson"
    
    # 添加时间戳
    event["ts"] = datetime.now(timezone.utc).isoformat()
    
    # 追加写入
    with open(log_path, "a") as f:
        f.write(json.dumps(event) + "\n")
        f.flush()


def log_worker_event(job_dir: Path, phase: str, message: str, level: str = "INFO", **extra):
    """记录 worker 事件"""
    event = {
        "source": "worker",
        "phase": phase,
        "level": level,
        "message": message,
        **extra
    }
    write_log_event(job_dir, event)


def log_watchdog_event(job_dir: Path, action: str, message: str, level: str = "INFO", **extra):
    """记录 watchdog 事件"""
    event = {
        "source": "watchdog",
        "action": action,
        "level": level,
        "message": message,
        **extra
    }
    write_log_event(job_dir, event)


# ============ ACK 管理 ============

def mark_acked(job_dir: Path, acked_by: str = "main_session"):
    """标记为已 ACK"""
    ack_path = job_dir / "ack.json"
    
    ack_data = {
        "acked_at": datetime.now(timezone.utc).isoformat(),
        "acked_by": acked_by
    }
    
    atomic_write_json(ack_path, ack_data)
    
    # 更新 status
    update_status_safe(job_dir, {"acked_at": ack_data["acked_at"]})


def is_acked(job_dir: Path) -> bool:
    """检查是否已 ACK"""
    return (job_dir / "ack.json").exists()


# ============ 通知退避 ============

def calculate_notify_delay(attempt: int, base_seconds: float = 30.0, max_seconds: float = 3600.0) -> float:
    """
    计算通知延迟 (指数退避 + 抖动)
    
    Args:
        attempt: 尝试次数
        base_seconds: 基础延迟
        max_seconds: 最大延迟
    
    Returns:
        延迟秒数
    """
    # 指数退避: base * 2^attempt
    delay = base_seconds * (2 ** min(attempt, 10))  # 最多 2^10 = 1024 倍
    delay = min(delay, max_seconds)
    
    # 抖动: ±20%
    jitter = delay * 0.2 * random.random()
    delay = delay + jitter - delay * 0.1
    
    return delay


def should_notify(job_dir: Path, cooldown_seconds: float = 60.0) -> bool:
    """
    判断是否应该发送通知
    
    基于 notify_count 和 last_notify_at
    """
    status, _ = read_status_with_rev(job_dir)
    
    if status is None:
        return True
    
    last_notify = status.get("last_notify_at")
    if not last_notify:
        return True
    
    last_notify_dt = datetime.fromisoformat(last_notify.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    
    # 检查冷却时间
    notify_count = status.get("notify_count", 0)
    delay = calculate_notify_delay(notify_count)
    
    return (now - last_notify_dt).total_seconds() > max(delay, cooldown_seconds)


def record_notify(job_dir: Path):
    """记录通知发送"""
    status, rev = read_status_with_rev(job_dir)
    
    if status is None:
        return
    
    notify_count = status.get("notify_count", 0) + 1
    
    updates = {
        "notify_count": notify_count,
        "last_notify_at": datetime.now(timezone.utc).isoformat()
    }
    
    update_status_cas(job_dir, updates, rev)


# ============ 错误分类 ============

class ErrorClass:
    TRANSIENT = "TRANSIENT"      # 临时错误，可重试
    PERMANENT = "PERMANENT"      # 永久错误，需人工介入
    TIMEOUT = "TIMEOUT"          # 超时
    CANCELLED = "CANCELLED"      # 被取消


def classify_error(error: Exception | str) -> str:
    """
    分类错误
    
    Returns:
        ErrorClass 常量
    """
    error_str = str(error).lower()
    
    # 超时
    if "timeout" in error_str or "timed out" in error_str:
        return ErrorClass.TIMEOUT
    
    # 取消
    if "cancel" in error_str or "abort" in error_str:
        return ErrorClass.CANCELLED
    
    # 临时错误 (网络、IO)
    transient_keywords = ["connection", "network", "io", "temporarily", "retry"]
    for kw in transient_keywords:
        if kw in error_str:
            return ErrorClass.TRANSIENT
    
    # 默认永久错误
    return ErrorClass.PERMANENT


def should_retry(error_class: str, attempt: int, max_attempts: int) -> bool:
    """判断是否应该重试"""
    if attempt >= max_attempts:
        return False
    
    return error_class in (ErrorClass.TRANSIENT, ErrorClass.TIMEOUT)


# ============ 常量 ============

JOBS_DIR = Path(__file__).parent.parent / "jobs"

# ============ 通用工具 ============

def generate_job_id() -> str:
    """生成唯一 job_id"""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    short_hash = hashlib.md5(os.urandom(8)).hexdigest()[:8]
    return f"{ts}_{short_hash}"


def parse_iso_time(s: str) -> Optional[datetime]:
    """解析 ISO 时间字符串"""
    if not s:
        return None
    
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    
    try:
        return datetime.fromisoformat(s)
    except:
        return None
