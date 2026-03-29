"""
辅助工具函数
"""
import os
import re
import secrets
import hashlib
import time
from datetime import datetime
from typing import Optional, Tuple


def generate_secure_id(prefix: str = "id", length: int = 16) -> str:
    """
    生成安全的随机ID
    """
    random_part = secrets.token_hex(length)
    timestamp = int(time.time() * 1000)
    return f"{prefix}_{timestamp}_{random_part}"


def secure_random_bytes(length: int = 32) -> bytes:
    """
    生成安全的随机字节
    """
    return secrets.token_bytes(length)


def compute_hash(data: bytes, algorithm: str = "sha3_256") -> str:
    """
    计算数据的哈希值
    """
    if algorithm == "sha256":
        return hashlib.sha256(data).hexdigest()
    elif algorithm == "sha3_256":
        return hashlib.sha3_256(data).hexdigest()
    elif algorithm == "sha512":
        return hashlib.sha512(data).hexdigest()
    else:
        raise ValueError(f"不支持的哈希算法: {algorithm}")


def validate_password_strength(password: str) -> Tuple[bool, list]:
    """
    验证密码强度
    返回: (是否通过, 问题列表)
    """
    issues = []
    
    if len(password) < 8:
        issues.append("密码长度至少8个字符")
    
    if len(password) > 128:
        issues.append("密码长度不能超过128个字符")
    
    if not re.search(r'[a-z]', password):
        issues.append("密码应包含小写字母")
    
    if not re.search(r'[A-Z]', password):
        issues.append("密码应包含大写字母")
    
    if not re.search(r'\d', password):
        issues.append("密码应包含数字")
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        issues.append("密码应包含特殊字符")
    
    common_passwords = [
        'password', '123456', 'qwerty', 'admin', 'letmein',
        'welcome', 'monkey', 'dragon', 'master', 'login'
    ]
    if password.lower() in common_passwords:
        issues.append("密码过于常见，请使用更复杂的密码")
    
    return len(issues) == 0, issues


def format_timestamp(timestamp: float, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    格式化时间戳
    """
    dt = datetime.fromtimestamp(timestamp)
    return dt.strftime(format_str)


def sanitize_filename(filename: str) -> str:
    """
    清理文件名，移除危险字符
    """
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    filename = re.sub(r'\.\.', '_', filename)
    filename = filename.strip('. ')
    if not filename:
        filename = "unnamed"
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:250] + ext
    return filename


def bytes_to_human(size_bytes: int) -> str:
    """
    将字节数转换为人类可读格式
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def constant_time_compare(a: bytes, b: bytes) -> bool:
    """
    常量时间比较，防止时序攻击
    """
    return secrets.compare_digest(a, b)


def derive_key_from_password(
    password: str, 
    salt: bytes, 
    iterations: int = 100000,
    key_length: int = 32
) -> bytes:
    """
    从密码派生密钥
    """
    return hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        iterations,
        dklen=key_length
    )
