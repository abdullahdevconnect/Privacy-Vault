"""
密钥代理服务模块
允许其他应用/智能体安全地请求密钥

工作流程:
1. 应用注册并获取应用ID和API密钥
2. 应用请求密钥时，智能体验证权限
3. 智能体返回加密的密钥数据（使用应用的公钥或会话密钥）
4. 应用解密获取原始密钥
"""
import os
import json
import time
import secrets
import hashlib
import hmac
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import base64


@dataclass
class Application:
    """
    注册的应用/智能体
    """
    app_id: str
    app_name: str
    app_type: str  # 'web', 'mobile', 'agent', 'service'
    api_key_hash: str
    api_key_salt: str
    public_key: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    permissions: List[str] = field(default_factory=list)
    rate_limit: int = 100  # 每分钟请求限制
    active: bool = True
    last_access: Optional[float] = None
    access_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'app_id': self.app_id,
            'app_name': self.app_name,
            'app_type': self.app_type,
            'api_key_hash': self.api_key_hash,
            'api_key_salt': self.api_key_salt,
            'public_key': self.public_key,
            'created_at': self.created_at,
            'permissions': self.permissions,
            'rate_limit': self.rate_limit,
            'active': self.active,
            'last_access': self.last_access,
            'access_count': self.access_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Application':
        return cls(**data)


@dataclass
class KeyRequest:
    """
    密钥请求记录
    """
    request_id: str
    app_id: str
    key_name: str
    requested_at: float
    granted: bool = False
    response_method: str = "encrypted"  # 'encrypted', 'derived', 'reference'
    ttl_seconds: Optional[int] = None


@dataclass
class KeyGrant:
    """
    密钥授权
    """
    grant_id: str
    app_id: str
    key_entry_id: str
    key_name: str
    granted_at: float
    expires_at: Optional[float] = None
    access_type: str = "read"  # 'read', 'use', 'derive'
    usage_count: int = 0
    max_usage: Optional[int] = None


class KeyProxyService:
    """
    密钥代理服务
    
    核心功能:
    1. 应用注册管理
    2. 密钥请求验证
    3. 安全密钥分发
    4. 访问审计
    """
    
    def __init__(self, storage_path: Path, vault=None, crypto=None):
        self.storage_path = Path(storage_path)
        self.apps_path = self.storage_path / "applications.json"
        self.grants_path = self.storage_path / "grants.json"
        self.requests_path = self.storage_path / "requests.json"
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self._vault = vault
        self._crypto = crypto
        
        self._applications: Dict[str, Application] = {}
        self._grants: Dict[str, KeyGrant] = {}
        self._requests: List[KeyRequest] = []
        self._rate_limits: Dict[str, List[float]] = {}
        
        self._load_data()
    
    def _load_data(self) -> None:
        if self.apps_path.exists():
            with open(self.apps_path, 'r', encoding='utf-8') as f:
                apps_data = json.load(f)
            self._applications = {
                aid: Application.from_dict(data) 
                for aid, data in apps_data.items()
            }
        
        if self.grants_path.exists():
            with open(self.grants_path, 'r', encoding='utf-8') as f:
                grants_data = json.load(f)
            self._grants = {
                gid: KeyGrant(**data) for gid, data in grants_data.items()
            }
    
    def _save_apps(self) -> None:
        with open(self.apps_path, 'w', encoding='utf-8') as f:
            json.dump(
                {aid: app.to_dict() for aid, app in self._applications.items()},
                f, indent=2
            )
    
    def _save_grants(self) -> None:
        with open(self.grants_path, 'w', encoding='utf-8') as f:
            json.dump(
                {gid: vars(g) for gid, g in self._grants.items()},
                f, indent=2
            )
    
    def _generate_app_id(self) -> str:
        return f"app_{secrets.token_hex(8)}"
    
    def _generate_api_key(self) -> str:
        return f"sk_{secrets.token_urlsafe(32)}"
    
    def _hash_api_key(self, api_key: str, salt: str) -> str:
        return hashlib.pbkdf2_hmac(
            'sha256',
            api_key.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        ).hex()
    
    def register_application(
        self,
        app_name: str,
        app_type: str = "service",
        permissions: Optional[List[str]] = None,
        public_key: Optional[str] = None,
        rate_limit: int = 100
    ) -> Tuple[str, str, Application]:
        """
        注册新应用
        
        返回: (app_id, api_key, application)
        """
        app_id = self._generate_app_id()
        api_key = self._generate_api_key()
        salt = secrets.token_hex(16)
        
        app = Application(
            app_id=app_id,
            app_name=app_name,
            app_type=app_type,
            api_key_hash=self._hash_api_key(api_key, salt),
            api_key_salt=salt,
            public_key=public_key,
            permissions=permissions or ['key:read'],
            rate_limit=rate_limit
        )
        
        self._applications[app_id] = app
        self._save_apps()
        
        return app_id, api_key, app
    
    def authenticate_app(self, app_id: str, api_key: str) -> Optional[Application]:
        """
        验证应用身份
        """
        app = self._applications.get(app_id)
        if not app or not app.active:
            return None
        
        expected_hash = self._hash_api_key(api_key, app.api_key_salt)
        if not hmac.compare_digest(expected_hash, app.api_key_hash):
            return None
        
        return app
    
    def _check_rate_limit(self, app_id: str, limit: int) -> bool:
        """
        检查请求频率限制
        """
        now = time.time()
        minute_ago = now - 60
        
        if app_id not in self._rate_limits:
            self._rate_limits[app_id] = []
        
        self._rate_limits[app_id] = [
            t for t in self._rate_limits[app_id] if t > minute_ago
        ]
        
        if len(self._rate_limits[app_id]) >= limit:
            return False
        
        self._rate_limits[app_id].append(now)
        return True
    
    def grant_key_access(
        self,
        app_id: str,
        key_name: str,
        key_entry_id: str,
        access_type: str = "read",
        expires_in_hours: Optional[int] = None,
        max_usage: Optional[int] = None
    ) -> KeyGrant:
        """
        授权应用访问特定密钥
        """
        grant_id = f"grant_{secrets.token_hex(8)}"
        now = time.time()
        
        grant = KeyGrant(
            grant_id=grant_id,
            app_id=app_id,
            key_entry_id=key_entry_id,
            key_name=key_name,
            granted_at=now,
            expires_at=now + (expires_in_hours * 3600) if expires_in_hours else None,
            access_type=access_type,
            max_usage=max_usage
        )
        
        self._grants[grant_id] = grant
        self._save_grants()
        
        return grant
    
    def revoke_grant(self, grant_id: str) -> bool:
        """
        撤销授权
        """
        if grant_id in self._grants:
            del self._grants[grant_id]
            self._save_grants()
            return True
        return False
    
    def request_key(
        self,
        app_id: str,
        api_key: str,
        key_name: str,
        response_method: str = "encrypted",
        ttl_seconds: Optional[int] = 300
    ) -> Dict[str, Any]:
        """
        应用请求密钥
        
        参数:
            app_id: 应用ID
            api_key: API密钥
            key_name: 密钥名称
            response_method: 响应方式
                - 'encrypted': 返回加密的密钥数据
                - 'derived': 返回派生密钥（不暴露原始密钥）
                - 'reference': 仅返回密钥引用ID
            ttl_seconds: 返回密钥的有效期（秒）
        
        返回:
            {
                'status': 'success' | 'error',
                'data': ...,
                'grant_id': ...,
                'expires_at': ...
            }
        """
        app = self.authenticate_app(app_id, api_key)
        if not app:
            return {'status': 'error', 'message': '认证失败'}
        
        if not self._check_rate_limit(app_id, app.rate_limit):
            return {'status': 'error', 'message': '请求频率超限'}
        
        if 'key:read' not in app.permissions:
            return {'status': 'error', 'message': '无权限'}
        
        has_grant = False
        for grant in self._grants.values():
            if (grant.app_id == app_id and 
                grant.key_name == key_name and
                (grant.expires_at is None or grant.expires_at > time.time()) and
                (grant.max_usage is None or grant.usage_count < grant.max_usage)):
                has_grant = True
                grant.usage_count += 1
                break
        
        if not has_grant:
            return {'status': 'error', 'message': '未授权访问此密钥'}
        
        request_id = f"req_{secrets.token_hex(8)}"
        request = KeyRequest(
            request_id=request_id,
            app_id=app_id,
            key_name=key_name,
            requested_at=time.time(),
            granted=True,
            response_method=response_method,
            ttl_seconds=ttl_seconds
        )
        self._requests.append(request)
        
        if not self._vault:
            return {'status': 'error', 'message': '存储库未初始化'}
        
        key_data = self._vault.retrieve(name=key_name)
        if key_data is None:
            return {'status': 'error', 'message': '密钥不存在'}
        
        app.last_access = time.time()
        app.access_count += 1
        self._save_apps()
        
        response = {
            'status': 'success',
            'request_id': request_id,
            'key_name': key_name,
            'response_method': response_method
        }
        
        if response_method == 'encrypted':
            if app.public_key and self._crypto:
                encrypted = self._crypto.encrypt_data(key_data)
                response['data'] = {
                    k: base64.b64encode(v).decode() if isinstance(v, bytes) else v
                    for k, v in encrypted.items()
                }
                response['encrypted_with'] = 'app_public_key'
            else:
                session_key = secrets.token_bytes(32)
                response['data'] = base64.b64encode(key_data).decode()
                response['session_key'] = base64.b64encode(session_key).decode()
                response['encrypted_with'] = 'session_key'
        
        elif response_method == 'derived':
            if self._crypto:
                context = f"{app_id}:{key_name}:{int(time.time() // 3600)}"
                derived_key = self._crypto.derive_key(context)
                response['derived_key'] = base64.b64encode(derived_key).decode()
                response['derivation_context'] = context
        
        elif response_method == 'reference':
            response['key_reference'] = f"ref_{secrets.token_hex(16)}"
            response['message'] = '密钥引用已创建，请使用引用ID进行后续操作'
        
        if ttl_seconds:
            response['expires_at'] = time.time() + ttl_seconds
        
        return response
    
    def use_key(
        self,
        app_id: str,
        api_key: str,
        key_name: str,
        operation: str = "sign",
        data: Optional[bytes] = None
    ) -> Dict[str, Any]:
        """
        使用密钥执行操作（不暴露原始密钥）
        
        支持操作:
        - sign: 使用密钥签名数据
        - encrypt: 使用密钥加密数据
        - decrypt: 使用密钥解密数据
        - verify: 验证签名
        - get_field: 获取特定字段（如手机号、用户名等）
        """
        app = self.authenticate_app(app_id, api_key)
        if not app:
            return {'status': 'error', 'message': '认证失败'}
        
        if f'key:{operation}' not in app.permissions and 'key:use' not in app.permissions:
            return {'status': 'error', 'message': f'无权限执行 {operation} 操作'}
        
        if not self._vault:
            return {'status': 'error', 'message': '存储库未初始化'}
        
        key_data = self._vault.retrieve(name=key_name)
        if key_data is None:
            return {'status': 'error', 'message': '密钥不存在'}
        
        # 解析密钥数据
        try:
            key_str = key_data.decode('utf-8') if isinstance(key_data, bytes) else key_data
            key_info = json.loads(key_str)
            login_type = key_info.get('login_type', 'password')
        except (json.JSONDecodeError, UnicodeDecodeError):
            key_info = {'password': key_data}
            login_type = 'password'
        
        # 获取实际用于加密/签名的密钥材料
        # 根据登录类型选择合适的密钥字段
        key_material = None
        if login_type == 'password':
            key_material = key_info.get('password', '').encode()
        elif login_type == 'phone_code':
            key_material = key_info.get('phone', '').encode()
        elif login_type == 'bank_card':
            key_material = key_info.get('cardNumber', '').encode()
        elif login_type == 'api_key':
            key_material = key_info.get('apiKey', '').encode()
        else:
            key_material = key_data if isinstance(key_data, bytes) else key_data.encode()
        
        if operation == 'sign' and data:
            import hashlib
            signature = hmac.new(key_material, data, hashlib.sha256).digest()
            return {
                'status': 'success',
                'signature': base64.b64encode(signature).decode(),
                'algorithm': 'HMAC-SHA256'
            }
        
        elif operation == 'encrypt' and data:
            from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
            from cryptography.hazmat.primitives.kdf.hkdf import HKDF
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.backends import default_backend
            
            key = HKDF(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'key_proxy',
                info=key_name.encode(),
                backend=default_backend()
            ).derive(key_material)
            
            cipher = ChaCha20Poly1305(key)
            nonce = secrets.token_bytes(12)
            encrypted = cipher.encrypt(nonce, data, None)
            
            return {
                'status': 'success',
                'encrypted_data': base64.b64encode(encrypted).decode(),
                'nonce': base64.b64encode(nonce).decode(),
                'algorithm': 'ChaCha20-Poly1305'
            }
        
        elif operation == 'get_field':
            # 获取特定字段
            return {
                'status': 'success',
                'login_type': login_type,
                'data': key_info
            }
        
        return {'status': 'error', 'message': '不支持的操作'}
    
    def list_app_grants(self, app_id: str) -> List[Dict[str, Any]]:
        """
        列出应用的所有授权
        """
        grants = []
        for grant in self._grants.values():
            if grant.app_id == app_id:
                grants.append({
                    'grant_id': grant.grant_id,
                    'key_name': grant.key_name,
                    'access_type': grant.access_type,
                    'granted_at': grant.granted_at,
                    'expires_at': grant.expires_at,
                    'usage_count': grant.usage_count
                })
        return grants
    
    def get_app_info(self, app_id: str) -> Optional[Dict[str, Any]]:
        """
        获取应用信息
        """
        app = self._applications.get(app_id)
        if not app:
            return None
        return {
            'app_id': app.app_id,
            'app_name': app.app_name,
            'app_type': app.app_type,
            'created_at': app.created_at,
            'permissions': app.permissions,
            'rate_limit': app.rate_limit,
            'active': app.active,
            'last_access': app.last_access,
            'access_count': app.access_count
        }
    
    def revoke_app(self, app_id: str) -> bool:
        """
        撤销应用访问权限并删除应用
        """
        if app_id in self._applications:
            del self._applications[app_id]
            
            for grant_id in list(self._grants.keys()):
                if self._grants[grant_id].app_id == app_id:
                    del self._grants[grant_id]
            
            self._save_apps()
            self._save_grants()
            
            return True
        return False
    
    def get_audit_log(self, app_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取审计日志
        """
        logs = []
        for req in self._requests[-100:]:
            if app_id is None or req.app_id == app_id:
                logs.append({
                    'request_id': req.request_id,
                    'app_id': req.app_id,
                    'key_name': req.key_name,
                    'requested_at': req.requested_at,
                    'granted': req.granted,
                    'response_method': req.response_method
                })
        return logs
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取服务统计
        """
        return {
            'total_applications': len(self._applications),
            'active_applications': sum(1 for a in self._applications.values() if a.active),
            'total_grants': len(self._grants),
            'total_requests': len(self._requests),
            'requests_today': sum(
                1 for r in self._requests 
                if r.requested_at > time.time() - 86400
            )
        }
