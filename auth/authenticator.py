"""
多因素认证模块
支持密码、TOTP、生物识别等多种认证方式
"""
import os
import json
import time
import secrets
import hashlib
import hmac
import base64
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import struct


@dataclass
class User:
    user_id: str
    username: str
    password_hash: str
    salt: str
    created_at: float
    mfa_enabled: bool = False
    mfa_secret: Optional[str] = None
    failed_attempts: int = 0
    locked_until: Optional[float] = None
    roles: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_locked(self) -> bool:
        if self.locked_until is None:
            return False
        return time.time() < self.locked_until
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'user_id': self.user_id,
            'username': self.username,
            'password_hash': self.password_hash,
            'salt': self.salt,
            'created_at': self.created_at,
            'mfa_enabled': self.mfa_enabled,
            'mfa_secret': self.mfa_secret,
            'failed_attempts': self.failed_attempts,
            'locked_until': self.locked_until,
            'roles': self.roles,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        return cls(**data)


@dataclass
class Session:
    session_id: str
    user_id: str
    created_at: float
    expires_at: float
    last_activity: float
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    active: bool = True
    
    def is_expired(self) -> bool:
        return time.time() > self.expires_at
    
    def is_valid(self) -> bool:
        return self.active and not self.is_expired()
    
    def refresh(self, timeout_minutes: int = 30) -> None:
        self.last_activity = time.time()
        self.expires_at = self.last_activity + (timeout_minutes * 60)


class MFAHandler:
    """
    多因素认证处理器
    支持TOTP (Time-based One-Time Password)
    """
    
    def __init__(self, digits: int = 6, interval: int = 30):
        self.digits = digits
        self.interval = interval
    
    def generate_secret(self) -> str:
        """
        生成TOTP密钥
        返回标准的Base32编码密钥，兼容Google/Microsoft Authenticator
        """
        # 生成20字节随机密钥
        key = secrets.token_bytes(20)
        # Base32编码（标准格式）
        secret = base64.b32encode(key).decode('utf-8').rstrip('=')
        return secret
    
    def get_totp_uri(self, secret: str, account_name: str, issuer: str = "PrivacyVault") -> str:
        """
        生成TOTP URI，用于生成二维码
        格式: otpauth://totp/Issuer:AccountName?secret=SECRET&issuer=Issuer
        """
        import urllib.parse
        return f"otpauth://totp/{issuer}:{account_name}?secret={secret}&issuer={issuer}&digits=6&period=30"
    
    def generate_totp(self, secret: str, timestamp: Optional[float] = None) -> str:
        """
        生成TOTP验证码
        
        参数:
            secret: Base32编码的密钥
            timestamp: 时间戳（可选）
        """
        if timestamp is None:
            timestamp = time.time()
        
        # 确保密钥格式正确
        secret = secret.upper().replace(' ', '').replace('-', '')
        
        # 补齐Base32填充
        padding = 8 - (len(secret) % 8)
        if padding != 8:
            secret += '=' * padding
        
        try:
            secret_bytes = base64.b32decode(secret, casefold=True)
        except Exception:
            return ""
        
        time_counter = int(timestamp // self.interval)
        counter_bytes = struct.pack('>Q', time_counter)
        hmac_hash = hmac.new(secret_bytes, counter_bytes, hashlib.sha1).digest()
        offset = hmac_hash[-1] & 0x0F
        code = struct.unpack('>I', hmac_hash[offset:offset + 4])[0]
        code = code & 0x7FFFFFFF
        code = code % (10 ** self.digits)
        return str(code).zfill(self.digits)
    
    def verify_totp(
        self, 
        secret: str, 
        code: str, 
        window: int = 2
    ) -> bool:
        """
        验证TOTP验证码
        
        参数:
            secret: Base32编码的密钥
            code: 用户输入的验证码
            window: 时间窗口（前后多少个30秒周期）
        """
        if not code or len(code) != self.digits:
            return False
        
        timestamp = time.time()
        for i in range(-window, window + 1):
            expected = self.generate_totp(secret, timestamp + (i * self.interval))
            if expected and hmac.compare_digest(expected, code):
                return True
        return False
    
    def generate_backup_codes(self, count: int = 10) -> List[str]:
        codes = []
        for _ in range(count):
            code = '-'.join([
                secrets.token_hex(2).upper(),
                secrets.token_hex(2).upper()
            ])
            codes.append(code)
        return codes


class Authenticator:
    """
    认证管理器
    处理用户认证、会话管理和安全策略
    """
    
    def __init__(
        self,
        storage_path: Path,
        max_login_attempts: int = 5,
        lockout_duration_minutes: int = 15,
        session_timeout_minutes: int = 30
    ):
        self.storage_path = Path(storage_path)
        self.users_path = self.storage_path / "users.json"
        self.sessions_path = self.storage_path / "sessions.json"
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.max_login_attempts = max_login_attempts
        self.lockout_duration_minutes = lockout_duration_minutes
        self.session_timeout_minutes = session_timeout_minutes
        
        self._users: Dict[str, User] = {}
        self._sessions: Dict[str, Session] = {}
        self._mfa_handler = MFAHandler()
        
        self._load_data()
    
    def _load_data(self) -> None:
        if self.users_path.exists():
            with open(self.users_path, 'r', encoding='utf-8') as f:
                users_data = json.load(f)
            self._users = {
                uid: User.from_dict(data) 
                for uid, data in users_data.items()
            }
        if self.sessions_path.exists():
            with open(self.sessions_path, 'r', encoding='utf-8') as f:
                sessions_data = json.load(f)
            self._sessions = {
                sid: Session(**data) 
                for sid, data in sessions_data.items()
            }
    
    def _save_users(self) -> None:
        with open(self.users_path, 'w', encoding='utf-8') as f:
            json.dump(
                {uid: user.to_dict() for uid, user in self._users.items()},
                f, indent=2
            )
    
    def _save_sessions(self) -> None:
        with open(self.sessions_path, 'w', encoding='utf-8') as f:
            json.dump(
                {sid: vars(s) for sid, s in self._sessions.items()},
                f, indent=2
            )
    
    def _hash_password(self, password: str, salt: str) -> str:
        iterations = 100000
        return hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            iterations
        ).hex()
    
    def _generate_user_id(self) -> str:
        return f"user_{secrets.token_hex(8)}"
    
    def _generate_session_id(self) -> str:
        return f"sess_{secrets.token_hex(16)}"
    
    def create_user(
        self, 
        username: str, 
        password: str,
        roles: Optional[List[str]] = None,
        enable_mfa: bool = False
    ) -> User:
        if username in [u.username for u in self._users.values()]:
            raise ValueError(f"用户名 '{username}' 已存在")
        salt = secrets.token_hex(16)
        password_hash = self._hash_password(password, salt)
        user = User(
            user_id=self._generate_user_id(),
            username=username,
            password_hash=password_hash,
            salt=salt,
            created_at=time.time(),
            mfa_enabled=enable_mfa,
            mfa_secret=self._mfa_handler.generate_secret() if enable_mfa else None,
            roles=roles or ['user']
        )
        self._users[user.user_id] = user
        self._save_users()
        return user
    
    def authenticate(
        self, 
        username: str, 
        password: str,
        mfa_code: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[Optional[Session], Optional[str]]:
        user = None
        for u in self._users.values():
            if u.username == username:
                user = u
                break
        if not user:
            return None, "用户不存在"
        if user.is_locked():
            remaining = int(user.locked_until - time.time())
            return None, f"账户已锁定，请 {remaining} 秒后重试"
        password_hash = self._hash_password(password, user.salt)
        if not hmac.compare_digest(password_hash, user.password_hash):
            user.failed_attempts += 1
            if user.failed_attempts >= self.max_login_attempts:
                user.locked_until = time.time() + (self.lockout_duration_minutes * 60)
                self._save_users()
                return None, "登录失败次数过多，账户已锁定"
            self._save_users()
            remaining = self.max_login_attempts - user.failed_attempts
            return None, f"密码错误，剩余 {remaining} 次尝试机会"
        if user.mfa_enabled:
            if not mfa_code:
                return None, "需要MFA验证码"
            if not user.mfa_secret or not self._mfa_handler.verify_totp(user.mfa_secret, mfa_code):
                return None, "MFA验证码无效"
        user.failed_attempts = 0
        user.locked_until = None
        self._save_users()
        session = Session(
            session_id=self._generate_session_id(),
            user_id=user.user_id,
            created_at=time.time(),
            expires_at=time.time() + (self.session_timeout_minutes * 60),
            last_activity=time.time(),
            ip_address=ip_address,
            user_agent=user_agent
        )
        self._sessions[session.session_id] = session
        self._save_sessions()
        return session, None
    
    def validate_session(self, session_id: str) -> Tuple[Optional[Session], Optional[User]]:
        session = self._sessions.get(session_id)
        if not session:
            return None, None
        if not session.is_valid():
            del self._sessions[session_id]
            self._save_sessions()
            return None, None
        session.refresh(self.session_timeout_minutes)
        self._save_sessions()
        user = self._users.get(session.user_id)
        return session, user
    
    def logout(self, session_id: str) -> bool:
        if session_id in self._sessions:
            del self._sessions[session_id]
            self._save_sessions()
            return True
        return False
    
    def change_password(
        self, 
        user_id: str, 
        old_password: str, 
        new_password: str
    ) -> Tuple[bool, Optional[str]]:
        user = self._users.get(user_id)
        if not user:
            return False, "用户不存在"
        old_hash = self._hash_password(old_password, user.salt)
        if not hmac.compare_digest(old_hash, user.password_hash):
            return False, "原密码错误"
        new_salt = secrets.token_hex(16)
        new_hash = self._hash_password(new_password, new_salt)
        user.salt = new_salt
        user.password_hash = new_hash
        self._save_users()
        return True, None
    
    def enable_mfa(self, user_id: str) -> Tuple[Optional[str], Optional[str]]:
        user = self._users.get(user_id)
        if not user:
            return None, "用户不存在"
        secret = self._mfa_handler.generate_secret()
        user.mfa_secret = secret
        user.mfa_enabled = True
        self._save_users()
        return secret, None
    
    def disable_mfa(self, user_id: str, code: str) -> Tuple[bool, Optional[str]]:
        user = self._users.get(user_id)
        if not user:
            return False, "用户不存在"
        if not user.mfa_secret:
            return False, "MFA未启用"
        if not self._mfa_handler.verify_totp(user.mfa_secret, code):
            return False, "验证码无效"
        user.mfa_enabled = False
        user.mfa_secret = None
        self._save_users()
        return True, None
    
    def get_user(self, user_id: str) -> Optional[User]:
        return self._users.get(user_id)
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        for user in self._users.values():
            if user.username == username:
                return user
        return None
    
    def delete_user(self, user_id: str) -> bool:
        if user_id in self._users:
            del self._users[user_id]
            for sid in list(self._sessions.keys()):
                if self._sessions[sid].user_id == user_id:
                    del self._sessions[sid]
            self._save_users()
            self._save_sessions()
            return True
        return False
    
    def cleanup_expired_sessions(self) -> int:
        expired_count = 0
        for sid in list(self._sessions.keys()):
            if not self._sessions[sid].is_valid():
                del self._sessions[sid]
                expired_count += 1
        if expired_count > 0:
            self._save_sessions()
        return expired_count
    
    def get_active_sessions(self, user_id: Optional[str] = None) -> List[Session]:
        sessions = []
        for session in self._sessions.values():
            if session.is_valid():
                if user_id is None or session.user_id == user_id:
                    sessions.append(session)
        return sessions
