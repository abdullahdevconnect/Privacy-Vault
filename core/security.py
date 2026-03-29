"""
安全防护模块
提供多层次的安全保护机制

功能:
1. 文件保护 - 防止未授权访问（包括杀毒软件）
2. 应用白名单 - 只有授权应用才能访问
3. 密钥传输加密 - 防止传输过程中泄露
4. 防泄露机制 - 检测和防止密钥泄露
5. 审计追踪 - 记录所有访问行为
"""
import os
import sys
import json
import time
import secrets
import hashlib
import hmac
import platform
import subprocess
from typing import Optional, Dict, Any, List, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.backends import default_backend


@dataclass
class AuthorizedApp:
    """授权应用信息"""
    app_id: str
    app_name: str
    app_signature: str  # 应用签名/指纹
    permissions: Set[str]
    created_at: float
    last_access: Optional[float] = None
    access_count: int = 0
    max_access_count: Optional[int] = None
    expires_at: Optional[float] = None
    ip_whitelist: List[str] = field(default_factory=list)
    trusted: bool = False


@dataclass
class AccessRequest:
    """访问请求"""
    request_id: str
    app_id: str
    key_name: str
    operation: str
    timestamp: float
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None
    granted: bool = False
    reason: Optional[str] = None


class FileProtector:
    """
    文件保护器
    保护数据文件不被未授权程序访问（包括杀毒软件）
    """
    
    def __init__(self, storage_path: Path):
        self.storage_path = Path(storage_path)
        self._protected_files: Set[str] = set()
        self._access_log: List[Dict] = []
    
    def protect_directory(self, directory: Path) -> None:
        """
        保护整个目录
        设置文件权限，防止未授权访问
        """
        if not directory.exists():
            return
        
        if platform.system() == 'Windows':
            self._protect_windows(directory)
        else:
            self._protect_unix(directory)
        
        for file in directory.rglob('*'):
            if file.is_file():
                self._protected_files.add(str(file))
    
    def _protect_windows(self, directory: Path) -> None:
        """
        Windows系统文件保护
        """
        try:
            for file in directory.rglob('*'):
                if file.is_file():
                    os.chmod(str(file), 0o600)
        except Exception as e:
            print(f"Windows文件保护警告: {e}")
    
    def _protect_unix(self, directory: Path) -> None:
        """
        Unix系统文件保护
        """
        try:
            os.chmod(str(directory), 0o700)
            for file in directory.rglob('*'):
                if file.is_file():
                    os.chmod(str(file), 0o600)
                elif file.is_dir():
                    os.chmod(str(file), 0o700)
        except Exception as e:
            print(f"Unix文件保护警告: {e}")
    
    def check_file_integrity(self, file_path: Path) -> Dict[str, Any]:
        """
        检查文件完整性
        """
        if not file_path.exists():
            return {'valid': False, 'reason': '文件不存在'}
        
        result = {
            'valid': True,
            'path': str(file_path),
            'size': file_path.stat().st_size,
            'modified': file_path.stat().st_mtime
        }
        
        stat = file_path.stat()
        if platform.system() != 'Windows':
            mode = oct(stat.st_mode)[-3:]
            result['permissions'] = mode
            if mode != '600' and mode != '400':
                result['warning'] = '文件权限可能已被修改'
        
        return result
    
    def detect_unauthorized_access(self, file_path: Path) -> bool:
        """
        检测未授权访问
        """
        try:
            if platform.system() == 'Windows':
                return self._detect_windows_access(file_path)
            else:
                return self._detect_unix_access(file_path)
        except Exception:
            return False
    
    def _detect_windows_access(self, file_path: Path) -> bool:
        """
        Windows下检测未授权访问
        使用文件句柄检测
        """
        try:
            result = subprocess.run(
                ['handle', str(file_path), '-accepteula'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return True
            return False
        except Exception:
            return False
    
    def _detect_unix_access(self, file_path: Path) -> bool:
        """
        Unix下检测未授权访问
        使用lsof检测
        """
        try:
            result = subprocess.run(
                ['lsof', str(file_path)],
                capture_output=True,
                text=True,
                timeout=5
            )
            return bool(result.stdout.strip())
        except Exception:
            return False
    
    def log_access(self, file_path: Path, operation: str, success: bool) -> None:
        """
        记录文件访问
        """
        self._access_log.append({
            'timestamp': time.time(),
            'file': str(file_path),
            'operation': operation,
            'success': success
        })


class AppWhitelist:
    """
    应用白名单管理器
    只有白名单中的应用才能访问密钥
    """
    
    def __init__(self, storage_path: Path):
        self.storage_path = Path(storage_path)
        self.whitelist_path = self.storage_path / "app_whitelist.json"
        self._authorized_apps: Dict[str, AuthorizedApp] = {}
        self._app_signatures: Dict[str, str] = {}
        self._load_whitelist()
    
    def _load_whitelist(self) -> None:
        """加载白名单"""
        if self.whitelist_path.exists():
            with open(self.whitelist_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for app_id, app_data in data.items():
                self._authorized_apps[app_id] = AuthorizedApp(
                    app_id=app_data['app_id'],
                    app_name=app_data['app_name'],
                    app_signature=app_data['app_signature'],
                    permissions=set(app_data.get('permissions', [])),
                    created_at=app_data['created_at'],
                    last_access=app_data.get('last_access'),
                    access_count=app_data.get('access_count', 0),
                    max_access_count=app_data.get('max_access_count'),
                    expires_at=app_data.get('expires_at'),
                    ip_whitelist=app_data.get('ip_whitelist', []),
                    trusted=app_data.get('trusted', False)
                )
    
    def _save_whitelist(self) -> None:
        """保存白名单"""
        data = {}
        for app_id, app in self._authorized_apps.items():
            data[app_id] = {
                'app_id': app.app_id,
                'app_name': app.app_name,
                'app_signature': app.app_signature,
                'permissions': list(app.permissions),
                'created_at': app.created_at,
                'last_access': app.last_access,
                'access_count': app.access_count,
                'max_access_count': app.max_access_count,
                'expires_at': app.expires_at,
                'ip_whitelist': app.ip_whitelist,
                'trusted': app.trusted
            }
        with open(self.whitelist_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    
    def generate_app_signature(self, app_name: str, api_key: str) -> str:
        """
        生成应用签名
        用于验证应用身份
        """
        signature_data = f"{app_name}:{api_key}:{time.time():.0f}"
        return hashlib.sha3_256(signature_data.encode()).hexdigest()
    
    def add_to_whitelist(
        self,
        app_id: str,
        app_name: str,
        api_key: str,
        permissions: List[str],
        max_access_count: Optional[int] = None,
        expires_hours: Optional[int] = None,
        ip_whitelist: Optional[List[str]] = None,
        trusted: bool = False
    ) -> AuthorizedApp:
        """
        添加应用到白名单
        """
        signature = self.generate_app_signature(app_name, api_key)
        
        app = AuthorizedApp(
            app_id=app_id,
            app_name=app_name,
            app_signature=signature,
            permissions=set(permissions),
            created_at=time.time(),
            max_access_count=max_access_count,
            expires_at=time.time() + expires_hours * 3600 if expires_hours else None,
            ip_whitelist=ip_whitelist or [],
            trusted=trusted
        )
        
        self._authorized_apps[app_id] = app
        self._app_signatures[signature] = app_id
        self._save_whitelist()
        
        return app
    
    def remove_from_whitelist(self, app_id: str) -> bool:
        """从白名单移除应用"""
        if app_id in self._authorized_apps:
            app = self._authorized_apps[app_id]
            if app.app_signature in self._app_signatures:
                del self._app_signatures[app.app_signature]
            del self._authorized_apps[app_id]
            self._save_whitelist()
            return True
        return False
    
    def is_authorized(self, app_id: str, api_key: str) -> Tuple[bool, Optional[str]]:
        """
        检查应用是否授权
        """
        app = self._authorized_apps.get(app_id)
        if not app:
            return False, "应用未在白名单中"
        
        if app.expires_at and time.time() > app.expires_at:
            return False, "应用授权已过期"
        
        if app.max_access_count and app.access_count >= app.max_access_count:
            return False, "应用访问次数已达上限"
        
        return True, None
    
    def verify_signature(self, app_id: str, signature: str) -> bool:
        """
        验证应用签名
        """
        app = self._authorized_apps.get(app_id)
        if not app:
            return False
        return hmac.compare_digest(app.app_signature, signature)
    
    def check_ip_allowed(self, app_id: str, client_ip: str) -> bool:
        """
        检查IP是否允许
        """
        app = self._authorized_apps.get(app_id)
        if not app:
            return False
        
        if not app.ip_whitelist:
            return True
        
        return client_ip in app.ip_whitelist or client_ip == "127.0.0.1"
    
    def record_access(self, app_id: str) -> None:
        """记录访问"""
        if app_id in self._authorized_apps:
            self._authorized_apps[app_id].access_count += 1
            self._authorized_apps[app_id].last_access = time.time()
            self._save_whitelist()
    
    def get_authorized_apps(self) -> List[Dict[str, Any]]:
        """获取所有授权应用"""
        return [
            {
                'app_id': app.app_id,
                'app_name': app.app_name,
                'permissions': list(app.permissions),
                'created_at': app.created_at,
                'last_access': app.last_access,
                'access_count': app.access_count,
                'trusted': app.trusted
            }
            for app in self._authorized_apps.values()
        ]


class SecureKeyTransfer:
    """
    安全密钥传输
    防止密钥在传输过程中泄露
    """
    
    def __init__(self):
        self._session_keys: Dict[str, bytes] = {}
        self._transfer_sessions: Dict[str, Dict] = {}
    
    def create_transfer_session(
        self,
        app_id: str,
        key_name: str,
        requester_public_key: bytes
    ) -> Tuple[str, bytes]:
        """
        创建传输会话
        返回: (session_id, encrypted_session_key)
        """
        session_id = secrets.token_urlsafe(32)
        session_key = secrets.token_bytes(32)
        
        self._session_keys[session_id] = session_key
        
        encrypted_key = self._encrypt_with_public_key(session_key, requester_public_key)
        
        self._transfer_sessions[session_id] = {
            'app_id': app_id,
            'key_name': key_name,
            'created_at': time.time(),
            'expires_at': time.time() + 300,  # 5分钟过期
            'used': False
        }
        
        return session_id, encrypted_key
    
    def prepare_key_for_transfer(
        self,
        session_id: str,
        key_data: bytes
    ) -> Optional[Dict[str, bytes]]:
        """
        准备密钥传输
        返回加密的密钥数据
        """
        session = self._transfer_sessions.get(session_id)
        if not session:
            return None
        
        if time.time() > session['expires_at']:
            del self._transfer_sessions[session_id]
            del self._session_keys[session_id]
            return None
        
        if session['used']:
            return None
        
        session_key = self._session_keys.get(session_id)
        if not session_key:
            return None
        
        nonce = secrets.token_bytes(12)
        cipher = ChaCha20Poly1305(session_key)
        encrypted_data = cipher.encrypt(nonce, key_data, None)
        
        session['used'] = True
        
        return {
            'encrypted_data': encrypted_data,
            'nonce': nonce
        }
    
    def complete_transfer(self, session_id: str) -> None:
        """完成传输，清理会话"""
        if session_id in self._transfer_sessions:
            del self._transfer_sessions[session_id]
        if session_id in self._session_keys:
            del self._session_keys[session_id]
    
    def _encrypt_with_public_key(self, data: bytes, public_key: bytes) -> bytes:
        """
        使用公钥加密
        这里使用简单的HKDF派生
        """
        key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'secure_transfer',
            info=b'key_exchange',
            backend=default_backend()
        ).derive(public_key)
        
        nonce = secrets.token_bytes(12)
        cipher = ChaCha20Poly1305(key)
        return cipher.encrypt(nonce, data, None)


class AntiLeakageSystem:
    """
    防泄露系统
    检测和防止密钥泄露
    """
    
    def __init__(self, storage_path: Path):
        self.storage_path = Path(storage_path)
        self.leakage_log_path = self.storage_path / "leakage_log.json"
        self._leakage_attempts: List[Dict] = []
        self._blocked_apps: Set[str] = set()
        self._suspicious_patterns = [
            b'password',
            b'secret',
            b'key',
            b'token',
            b'api_key',
            b'private_key',
        ]
    
    def detect_leakage_attempt(
        self,
        data: bytes,
        app_id: str,
        operation: str
    ) -> Dict[str, Any]:
        """
        检测泄露尝试
        """
        result = {
            'detected': False,
            'severity': 'none',
            'patterns_found': [],
            'action': 'allow'
        }
        
        for pattern in self._suspicious_patterns:
            if pattern.lower() in data.lower():
                result['detected'] = True
                result['patterns_found'].append(pattern.decode())
        
        if result['detected']:
            if len(result['patterns_found']) >= 3:
                result['severity'] = 'high'
                result['action'] = 'block'
                self._blocked_apps.add(app_id)
            elif len(result['patterns_found']) >= 1:
                result['severity'] = 'medium'
                result['action'] = 'warn'
        
            self._log_leakage_attempt(app_id, operation, result)
        
        return result
    
    def _log_leakage_attempt(
        self,
        app_id: str,
        operation: str,
        result: Dict
    ) -> None:
        """记录泄露尝试"""
        attempt = {
            'timestamp': time.time(),
            'app_id': app_id,
            'operation': operation,
            'severity': result['severity'],
            'patterns': result['patterns_found'],
            'action_taken': result['action']
        }
        self._leakage_attempts.append(attempt)
        self._save_leakage_log()
    
    def _save_leakage_log(self) -> None:
        """保存泄露日志"""
        with open(self.leakage_log_path, 'w', encoding='utf-8') as f:
            json.dump(self._leakage_attempts[-100:], f, indent=2)
    
    def is_app_blocked(self, app_id: str) -> bool:
        """检查应用是否被阻止"""
        return app_id in self._blocked_apps
    
    def unblock_app(self, app_id: str) -> None:
        """解除应用阻止"""
        self._blocked_apps.discard(app_id)
    
    def get_leakage_report(self) -> Dict[str, Any]:
        """获取泄露报告"""
        return {
            'total_attempts': len(self._leakage_attempts),
            'blocked_apps': list(self._blocked_apps),
            'recent_attempts': self._leakage_attempts[-10:]
        }


class SecurityManager:
    """
    安全管理器
    整合所有安全组件
    """
    
    def __init__(self, storage_path: Path):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.file_protector = FileProtector(storage_path)
        self.app_whitelist = AppWhitelist(storage_path)
        self.secure_transfer = SecureKeyTransfer()
        self.anti_leakage = AntiLeakageSystem(storage_path)
        
        self._audit_log: List[Dict] = []
    
    def initialize(self) -> Dict[str, Any]:
        """
        初始化安全系统
        """
        self.file_protector.protect_directory(self.storage_path)
        
        return {
            'status': 'initialized',
            'protected_files': len(self.file_protector._protected_files),
            'authorized_apps': len(self.app_whitelist._authorized_apps)
        }
    
    def authorize_app(
        self,
        app_id: str,
        app_name: str,
        api_key: str,
        permissions: List[str],
        **kwargs
    ) -> AuthorizedApp:
        """
        授权应用
        """
        return self.app_whitelist.add_to_whitelist(
            app_id=app_id,
            app_name=app_name,
            api_key=api_key,
            permissions=permissions,
            **kwargs
        )
    
    def request_key_access(
        self,
        app_id: str,
        api_key: str,
        key_name: str,
        operation: str,
        client_ip: Optional[str] = None,
        requester_public_key: Optional[bytes] = None
    ) -> Dict[str, Any]:
        """
        请求密钥访问
        这是其他智能体调用时的入口
        """
        result = {
            'granted': False,
            'reason': None,
            'session_id': None
        }
        
        if self.anti_leakage.is_app_blocked(app_id):
            result['reason'] = '应用已被阻止'
            self._log_access(app_id, key_name, operation, False, 'app_blocked')
            return result
        
        is_authorized, reason = self.app_whitelist.is_authorized(app_id, api_key)
        if not is_authorized:
            result['reason'] = reason
            self._log_access(app_id, key_name, operation, False, reason)
            return result
        
        if client_ip and not self.app_whitelist.check_ip_allowed(app_id, client_ip):
            result['reason'] = 'IP不在白名单中'
            self._log_access(app_id, key_name, operation, False, 'ip_not_allowed')
            return result
        
        if operation not in self.app_whitelist._authorized_apps[app_id].permissions:
            result['reason'] = f'无权限执行 {operation} 操作'
            self._log_access(app_id, key_name, operation, False, 'no_permission')
            return result
        
        self.app_whitelist.record_access(app_id)
        
        if requester_public_key:
            session_id, encrypted_key = self.secure_transfer.create_transfer_session(
                app_id, key_name, requester_public_key
            )
            result['session_id'] = session_id
            result['encrypted_session_key'] = encrypted_key
        
        result['granted'] = True
        self._log_access(app_id, key_name, operation, True, None)
        
        return result
    
    def prepare_encrypted_key(
        self,
        session_id: str,
        key_data: bytes
    ) -> Optional[Dict[str, bytes]]:
        """
        准备加密的密钥
        """
        leakage_result = self.anti_leakage.detect_leakage_attempt(
            key_data,
            session_id.split('_')[0] if '_' in session_id else 'unknown',
            'key_transfer'
        )
        
        if leakage_result['action'] == 'block':
            return None
        
        return self.secure_transfer.prepare_key_for_transfer(session_id, key_data)
    
    def complete_transfer(self, session_id: str) -> None:
        """完成传输"""
        self.secure_transfer.complete_transfer(session_id)
    
    def _log_access(
        self,
        app_id: str,
        key_name: str,
        operation: str,
        granted: bool,
        reason: Optional[str]
    ) -> None:
        """记录访问"""
        self._audit_log.append({
            'timestamp': time.time(),
            'app_id': app_id,
            'key_name': key_name,
            'operation': operation,
            'granted': granted,
            'reason': reason
        })
    
    def get_audit_log(self, limit: int = 100) -> List[Dict]:
        """获取审计日志"""
        return self._audit_log[-limit:]
    
    def get_security_status(self) -> Dict[str, Any]:
        """获取安全状态"""
        return {
            'protected_files': len(self.file_protector._protected_files),
            'authorized_apps': len(self.app_whitelist._authorized_apps),
            'blocked_apps': len(self.anti_leakage._blocked_apps),
            'leakage_attempts': len(self.anti_leakage._leakage_attempts),
            'active_transfers': len(self.secure_transfer._transfer_sessions)
        }
    
    def revoke_app(self, app_id: str) -> bool:
        """撤销应用授权"""
        return self.app_whitelist.remove_from_whitelist(app_id)
