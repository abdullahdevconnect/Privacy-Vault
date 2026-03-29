"""
隐私信息储存箱智能体核心引擎
整合所有模块，提供统一的智能体接口
"""
import os
import json
import time
import asyncio
import logging
from typing import Optional, Dict, Any, List, Union, Callable
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum

from .config import Config
from .key_proxy import KeyProxyService, Application, KeyGrant
from .security import SecurityManager, AntiLeakageSystem
from crypto import QuantumCrypto, KeyManager
from sandbox import Vault, SandboxIsolation, IsolationLevel
from auth import Authenticator, AccessControlManager, User, Session


class AgentState(Enum):
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    BUSY = "busy"
    ERROR = "error"
    LOCKED = "locked"


@dataclass
class AgentContext:
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    isolation_context_id: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    operations_count: int = 0


class AgentEngine:
    """
    隐私信息储存箱智能体引擎
    提供安全、隔离的隐私信息管理能力
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = Config()
        if config_path:
            self.config.load_config(config_path)
        
        self._state = AgentState.UNINITIALIZED
        self._context = AgentContext()
        self._crypto: Optional[QuantumCrypto] = None
        self._key_manager: Optional[KeyManager] = None
        self._vault: Optional[Vault] = None
        self._isolation: Optional[SandboxIsolation] = None
        self._authenticator: Optional[Authenticator] = None
        self._access_control: Optional[AccessControlManager] = None
        self._key_proxy: Optional[KeyProxyService] = None
        self._security_manager: Optional[SecurityManager] = None
        
        self._setup_logging()
        self._logger.info(f"智能体引擎创建: {self.config.privacy_vault.name}")
    
    def _setup_logging(self) -> None:
        log_config = self.config.logging
        log_path = Path(log_config.file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._logger = logging.getLogger('PrivacyVaultAgent')
        self._logger.setLevel(getattr(logging, log_config.level))
        
        file_handler = logging.FileHandler(log_config.file, encoding='utf-8')
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        self._logger.addHandler(file_handler)
    
    def initialize(self) -> Dict[str, Any]:
        """
        初始化智能体引擎
        """
        if self._state != AgentState.UNINITIALIZED:
            return {'status': 'already_initialized', 'state': self._state.value}
        
        self._state = AgentState.INITIALIZING
        self._logger.info("开始初始化智能体引擎...")
        
        try:
            self.config.ensure_directories()
            self._crypto = QuantumCrypto(self.config.quantum_crypto.key_size)
            
            crypto_keys_path = self.config.get_storage_path() / "crypto_keys.json"
            if crypto_keys_path.exists():
                self._crypto.load_keys(str(crypto_keys_path))
                crypto_init = {'status': 'loaded', 'mode': 'restored_keys'}
                self._logger.info("从文件加载量子密钥")
            else:
                crypto_init = self._crypto.initialize()
                self._crypto.save_keys(str(crypto_keys_path))
                self._logger.info("生成并保存新的量子密钥")
            
            self._logger.info(f"量子密码模块初始化完成: {crypto_init}")
            self._key_manager = KeyManager(self.config.get_storage_path() / "keys")
            self._key_manager.load_keys()
            self._logger.info(f"密钥管理器初始化完成，已加载 {len(self._key_manager._keys)} 个密钥")
            self._isolation = SandboxIsolation(
                self.config.get_storage_path(),
                IsolationLevel(self.config.sandbox.isolation_level)
            )
            self._logger.info(f"沙盒隔离初始化完成，隔离级别: {self.config.sandbox.isolation_level}")
            self._vault = Vault(self.config.get_storage_path(), self._crypto)
            vault_init = self._vault.initialize()
            self._logger.info(f"存储库初始化完成: {vault_init}")
            self._authenticator = Authenticator(
                self.config.get_storage_path() / "auth",
                self.config.auth.max_login_attempts,
                self.config.auth.lockout_duration_minutes,
                self.config.auth.session_timeout_minutes
            )
            self._logger.info("认证模块初始化完成")
            self._access_control = AccessControlManager(
                self.config.get_storage_path() / "access_control"
            )
            self._logger.info("访问控制模块初始化完成")
            self._key_proxy = KeyProxyService(
                self.config.get_storage_path() / "proxy",
                vault=self._vault,
                crypto=self._crypto
            )
            self._logger.info("密钥代理服务初始化完成")
            
            # 初始化安全管理器
            self._security_manager = SecurityManager(
                self.config.get_storage_path() / "security"
            )
            security_init = self._security_manager.initialize()
            self._logger.info(f"安全管理器初始化完成: {security_init}")
            
            self._state = AgentState.READY
            self._logger.info("智能体引擎初始化完成")
            
            return {
                'status': 'success',
                'state': self._state.value,
                'crypto': crypto_init,
                'vault': vault_init,
                'key_stats': self._key_manager.get_key_stats()
            }
            
        except Exception as e:
            self._state = AgentState.ERROR
            self._logger.error(f"初始化失败: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'state': self._state.value
            }
    
    def register_user(
        self, 
        username: str, 
        password: str,
        roles: Optional[List[str]] = None,
        enable_mfa: bool = False
    ) -> Dict[str, Any]:
        """
        注册新用户
        """
        if self._state != AgentState.READY:
            return {'status': 'error', 'message': '智能体未就绪'}
        
        try:
            user = self._authenticator.create_user(
                username=username,
                password=password,
                roles=roles or ['user'],
                enable_mfa=enable_mfa
            )
            for role in (roles or ['user']):
                self._access_control.assign_role_to_user(user.user_id, role)
            
            self._logger.info(f"用户注册成功: {username}")
            return {
                'status': 'success',
                'user_id': user.user_id,
                'username': user.username,
                'mfa_enabled': user.mfa_enabled,
                'mfa_secret': user.mfa_secret if enable_mfa else None
            }
        except Exception as e:
            self._logger.error(f"用户注册失败: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def login(
        self, 
        username: str, 
        password: str,
        mfa_code: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        用户登录
        """
        if self._state != AgentState.READY:
            return {'status': 'error', 'message': '智能体未就绪'}
        
        session, error = self._authenticator.authenticate(
            username=username,
            password=password,
            mfa_code=mfa_code,
            ip_address=ip_address
        )
        
        if error:
            self._logger.warning(f"登录失败: {username} - {error}")
            return {'status': 'error', 'message': error}
        
        user = self._authenticator.get_user(session.user_id)
        isolation_ctx = self._isolation.create_context()
        self._isolation.activate_context(isolation_ctx.context_id)
        
        self._context = AgentContext(
            session_id=session.session_id,
            user_id=user.user_id,
            isolation_context_id=isolation_ctx.context_id
        )
        
        self._logger.info(f"用户登录成功: {username}")
        return {
            'status': 'success',
            'session_id': session.session_id,
            'user_id': user.user_id,
            'username': user.username,
            'roles': user.roles,
            'expires_at': session.expires_at
        }
    
    def logout(self) -> Dict[str, Any]:
        """
        用户登出
        """
        if not self._context.session_id:
            return {'status': 'error', 'message': '无活动会话'}
        
        self._authenticator.logout(self._context.session_id)
        if self._context.isolation_context_id:
            self._isolation.destroy_context(self._context.isolation_context_id)
        
        self._logger.info(f"用户登出: {self._context.user_id}")
        self._context = AgentContext()
        
        return {'status': 'success'}
    
    def store_data(
        self, 
        name: str, 
        data: Union[bytes, str, Dict[str, Any]],
        tags: Optional[List[str]] = None,
        encrypt: bool = True
    ) -> Dict[str, Any]:
        """
        存储隐私数据
        """
        if self._state != AgentState.READY:
            return {'status': 'error', 'message': '智能体未就绪'}
        
        if not self._context.session_id:
            return {'status': 'error', 'message': '未登录'}
        
        try:
            with self._isolation.isolated_operation('write', name):
                entry = self._vault.store(
                    name=name,
                    data=data,
                    tags=tags,
                    encrypt=encrypt
                )
                
                self._access_control.create_resource(
                    resource_type='vault_entry',
                    name=name,
                    owner_id=self._context.user_id,
                    metadata={'entry_id': entry.metadata.entry_id}
                )
                
                self._context.operations_count += 1
                self._logger.info(f"数据存储成功: {name}")
                
                return {
                    'status': 'success',
                    'entry_id': entry.metadata.entry_id,
                    'name': entry.metadata.name,
                    'size': entry.metadata.size,
                    'encrypted': entry.metadata.encrypted,
                    'checksum': entry.metadata.checksum
                }
        except Exception as e:
            self._logger.error(f"数据存储失败: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def retrieve_data(
        self, 
        entry_id: Optional[str] = None,
        name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        检索隐私数据
        """
        if self._state != AgentState.READY:
            return {'status': 'error', 'message': '智能体未就绪'}
        
        if not self._context.session_id:
            return {'status': 'error', 'message': '未登录'}
        
        try:
            with self._isolation.isolated_operation('read'):
                data = self._vault.retrieve(entry_id=entry_id, name=name)
                
                if data is None:
                    return {'status': 'error', 'message': '数据不存在'}
                
                self._context.operations_count += 1
                self._logger.info(f"数据检索成功: {entry_id or name}")
                
                return {
                    'status': 'success',
                    'data': data.decode('utf-8') if isinstance(data, bytes) else data
                }
        except Exception as e:
            self._logger.error(f"数据检索失败: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def delete_data(self, entry_id: str) -> Dict[str, Any]:
        """
        删除隐私数据
        """
        if self._state != AgentState.READY:
            return {'status': 'error', 'message': '智能体未就绪'}
        
        if not self._context.session_id:
            return {'status': 'error', 'message': '未登录'}
        
        try:
            metadata = self._vault.retrieve_metadata(entry_id)
            key_name = metadata.name if metadata else None
            
            with self._isolation.isolated_operation('delete', entry_id):
                success = self._vault.delete(
                    entry_id, 
                    secure_delete=self.config.sandbox.secure_delete
                )
                
                if success:
                    self._access_control.delete_resource(entry_id)
                    self._context.operations_count += 1
                    
                    # 删除相关的授权记录
                    if key_name and self._key_proxy:
                        for grant_id in list(self._key_proxy._grants.keys()):
                            grant = self._key_proxy._grants[grant_id]
                            if grant.key_name == key_name:
                                del self._key_proxy._grants[grant_id]
                        self._key_proxy._save_grants()
                        self._logger.info(f"已删除密钥 '{key_name}' 的所有授权记录")
                    
                    self._logger.info(f"数据删除成功: {entry_id}")
                
                return {
                    'status': 'success' if success else 'error',
                    'message': '删除成功' if success else '删除失败'
                }
        except Exception as e:
            self._logger.error(f"数据删除失败: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def search_data(
        self, 
        query: Optional[str] = None,
        tags: Optional[List[str]] = None,
        content_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        搜索隐私数据
        """
        if self._state != AgentState.READY:
            return {'status': 'error', 'message': '智能体未就绪'}
        
        if not self._context.session_id:
            return {'status': 'error', 'message': '未登录'}
        
        try:
            results = self._vault.search(
                query=query,
                tags=tags,
                content_type=content_type
            )
            
            return {
                'status': 'success',
                'count': len(results),
                'results': [
                    {
                        'entry_id': r.entry_id,
                        'name': r.name,
                        'content_type': r.content_type,
                        'size': r.size,
                        'tags': r.tags,
                        'created_at': r.created_at
                    }
                    for r in results
                ]
            }
        except Exception as e:
            self._logger.error(f"数据搜索失败: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def rotate_keys(self) -> Dict[str, Any]:
        """
        轮换量子密钥
        """
        if self._state != AgentState.READY:
            return {'status': 'error', 'message': '智能体未就绪'}
        
        if not self._context.session_id:
            return {'status': 'error', 'message': '未登录'}
        
        try:
            rotation_result = self._crypto.rotate_keys()
            self._logger.info(f"密钥轮换完成: {rotation_result}")
            
            return {
                'status': 'success',
                'rotation': rotation_result
            }
        except Exception as e:
            self._logger.error(f"密钥轮换失败: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取智能体状态
        """
        return {
            'status': 'success',
            'agent_state': self._state.value,
            'agent_name': self.config.privacy_vault.name,
            'version': self.config.privacy_vault.version,
            'session_active': self._context.session_id is not None,
            'user_id': self._context.user_id,
            'operations_count': self._context.operations_count,
            'vault_stats': self._vault.get_stats() if self._vault else None,
            'key_stats': self._key_manager.get_key_stats() if self._key_manager else None
        }
    
    def get_audit_log(
        self, 
        since: Optional[float] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        获取审计日志
        """
        if self._state != AgentState.READY:
            return {'status': 'error', 'message': '智能体未就绪'}
        
        events = self._isolation.get_audit_trail(
            context_id=self._context.isolation_context_id,
            since=since
        )
        
        return {
            'status': 'success',
            'count': len(events[:limit]),
            'events': events[:limit]
        }
    
    def enable_mfa(self) -> Dict[str, Any]:
        """
        启用多因素认证
        """
        if not self._context.user_id:
            return {'status': 'error', 'message': '未登录'}
        
        secret, error = self._authenticator.enable_mfa(self._context.user_id)
        
        if error:
            return {'status': 'error', 'message': error}
        
        return {
            'status': 'success',
            'mfa_secret': secret,
            'message': '请使用TOTP应用扫描此密钥'
        }
    
    def backup_vault(self, backup_path: str) -> Dict[str, Any]:
        """
        备份存储库
        """
        if self._state != AgentState.READY:
            return {'status': 'error', 'message': '智能体未就绪'}
        
        success = self._vault.backup(Path(backup_path))
        
        return {
            'status': 'success' if success else 'error',
            'backup_path': backup_path
        }
    
    # ==================== 密钥代理服务 ====================
    
    def register_application(
        self,
        app_name: str,
        app_type: str = "service",
        permissions: Optional[List[str]] = None,
        public_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        注册应用/智能体，获取API密钥
        
        参数:
            app_name: 应用名称
            app_type: 应用类型 ('web', 'mobile', 'agent', 'service')
            permissions: 权限列表，如 ['key:read', 'key:use', 'key:sign']
            public_key: 应用的公钥（用于加密返回的密钥）
        
        返回:
            app_id: 应用ID
            api_key: API密钥（请妥善保管，只显示一次）
        """
        if self._state != AgentState.READY:
            return {'status': 'error', 'message': '智能体未就绪'}
        
        if not self._context.session_id:
            return {'status': 'error', 'message': '未登录'}
        
        app_id, api_key, app = self._key_proxy.register_application(
            app_name=app_name,
            app_type=app_type,
            permissions=permissions,
            public_key=public_key
        )
        
        self._logger.info(f"注册应用: {app_name} ({app_id})")
        
        return {
            'status': 'success',
            'app_id': app_id,
            'api_key': api_key,
            'message': '请妥善保管API密钥，此密钥只显示一次'
        }
    
    def grant_key_to_app(
        self,
        app_id: str,
        key_name: str,
        key_entry_id: str,
        access_type: str = "read",
        expires_in_hours: Optional[int] = None,
        max_usage: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        授权应用访问特定密钥
        
        参数:
            app_id: 应用ID
            key_name: 密钥名称
            key_entry_id: 密钥条目ID
            access_type: 访问类型 ('read', 'use', 'derive')
            expires_in_hours: 授权过期时间（小时）
            max_usage: 最大使用次数
        """
        if self._state != AgentState.READY:
            return {'status': 'error', 'message': '智能体未就绪'}
        
        if not self._context.session_id:
            return {'status': 'error', 'message': '未登录'}
        
        grant = self._key_proxy.grant_key_access(
            app_id=app_id,
            key_name=key_name,
            key_entry_id=key_entry_id,
            access_type=access_type,
            expires_in_hours=expires_in_hours,
            max_usage=max_usage
        )
        
        self._logger.info(f"授权应用 {app_id} 访问密钥 {key_name}")
        
        return {
            'status': 'success',
            'grant_id': grant.grant_id,
            'key_name': key_name,
            'access_type': access_type,
            'expires_at': grant.expires_at
        }
    
    def request_key_for_app(
        self,
        app_id: str,
        api_key: str,
        key_name: str,
        response_method: str = "encrypted"
    ) -> Dict[str, Any]:
        """
        应用请求密钥（供外部应用调用）
        
        参数:
            app_id: 应用ID
            api_key: API密钥
            key_name: 密钥名称
            response_method: 响应方式
                - 'encrypted': 返回加密的密钥
                - 'derived': 返回派生密钥
                - 'reference': 返回密钥引用
        
        返回:
            加密的密钥数据或派生密钥
        """
        if self._state != AgentState.READY:
            return {'status': 'error', 'message': '智能体未就绪'}
        
        return self._key_proxy.request_key(
            app_id=app_id,
            api_key=api_key,
            key_name=key_name,
            response_method=response_method
        )
    
    def use_key_for_app(
        self,
        app_id: str,
        api_key: str,
        key_name: str,
        operation: str,
        data: Optional[bytes] = None
    ) -> Dict[str, Any]:
        """
        应用使用密钥执行操作（不暴露原始密钥）
        
        参数:
            app_id: 应用ID
            api_key: API密钥
            key_name: 密钥名称
            operation: 操作类型 ('sign', 'encrypt', 'decrypt', 'verify')
            data: 要操作的数据
        
        返回:
            操作结果（签名、加密数据等）
        """
        if self._state != AgentState.READY:
            return {'status': 'error', 'message': '智能体未就绪'}
        
        return self._key_proxy.use_key(
            app_id=app_id,
            api_key=api_key,
            key_name=key_name,
            operation=operation,
            data=data
        )
    
    def list_applications(self) -> Dict[str, Any]:
        """
        列出所有注册的应用
        """
        if self._state != AgentState.READY:
            return {'status': 'error', 'message': '智能体未就绪'}
        
        if not self._context.session_id:
            return {'status': 'error', 'message': '未登录'}
        
        apps = []
        for app_id in self._key_proxy._applications:
            info = self._key_proxy.get_app_info(app_id)
            if info:
                # 获取该应用已授权的密钥列表
                granted_keys = []
                for grant_id, grant in self._key_proxy._grants.items():
                    if grant.app_id == app_id:
                        granted_keys.append({
                            'key_name': grant.key_name,
                            'access_type': grant.access_type,
                            'granted_at': grant.granted_at,
                            'expires_at': grant.expires_at,
                            'usage_count': grant.usage_count,
                            'max_usage': grant.max_usage
                        })
                info['granted_keys'] = granted_keys
                apps.append(info)
        
        return {
            'status': 'success',
            'count': len(apps),
            'applications': apps
        }
    
    def revoke_app_access(self, app_id: str) -> Dict[str, Any]:
        """
        撤销应用的所有访问权限
        """
        if self._state != AgentState.READY:
            return {'status': 'error', 'message': '智能体未就绪'}
        
        if not self._context.session_id:
            return {'status': 'error', 'message': '未登录'}
        
        success = self._key_proxy.revoke_app(app_id)
        
        return {
            'status': 'success' if success else 'error',
            'message': '应用权限已撤销' if success else '撤销失败'
        }
    
    def get_proxy_stats(self) -> Dict[str, Any]:
        """
        获取密钥代理服务统计
        """
        if self._state != AgentState.READY:
            return {'status': 'error', 'message': '智能体未就绪'}
        
        return {
            'status': 'success',
            'stats': self._key_proxy.get_stats()
        }
    
    def get_proxy_audit_log(self, app_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取密钥代理审计日志
        """
        if self._state != AgentState.READY:
            return {'status': 'error', 'message': '智能体未就绪'}
        
        return {
            'status': 'success',
            'logs': self._key_proxy.get_audit_log(app_id)
        }
    
    def get_settings(self) -> Dict[str, Any]:
        """
        获取系统设置
        """
        if self._state != AgentState.READY:
            return {'status': 'error', 'message': '智能体未就绪'}
        
        if not self._context.session_id:
            return {'status': 'error', 'message': '未登录'}
        
        settings_path = self.config.get_storage_path() / "settings.json"
        settings = {}
        
        if settings_path.exists():
            with open(settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
        
        return {
            'status': 'success',
            'settings': {
                'session_timeout_minutes': settings.get('session_timeout_minutes', self.config.auth.session_timeout_minutes),
                'encryption_method': settings.get('encryption_method', 'math_gamma'),
                'auto_rotate': settings.get('auto_rotate', False),
                'proxy_mode': settings.get('proxy_mode', True),
                'sensitive_confirm': settings.get('sensitive_confirm', True)
            }
        }
    
    def update_settings(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新系统设置
        """
        if self._state != AgentState.READY:
            return {'status': 'error', 'message': '智能体未就绪'}
        
        if not self._context.session_id:
            return {'status': 'error', 'message': '未登录'}
        
        settings_path = self.config.get_storage_path() / "settings.json"
        
        existing_settings = {}
        if settings_path.exists():
            with open(settings_path, 'r', encoding='utf-8') as f:
                existing_settings = json.load(f)
        
        for key, value in data.items():
            if key == 'session_timeout_minutes':
                self.config.auth.session_timeout_minutes = int(value)
            existing_settings[key] = value
        
        with open(settings_path, 'w', encoding='utf-8') as f:
            json.dump(existing_settings, f, indent=2)
        
        self._logger.info(f"设置已更新: {data}")
        
        return {
            'status': 'success',
            'message': '设置已保存',
            'settings': existing_settings
        }
    
    def set_encryption_method(self, method: str) -> Dict[str, Any]:
        """
        设置加密方法
        """
        if self._state != AgentState.READY:
            return {'status': 'error', 'message': '智能体未就绪'}
        
        if not self._context.session_id:
            return {'status': 'error', 'message': '未登录'}
        
        valid_methods = ['math_gamma', 'math_chaos', 'math_lattice', 'quantum_sim', 'aes256']
        if method not in valid_methods:
            return {'status': 'error', 'message': f'无效的加密方法: {method}'}
        
        settings_path = self.config.get_storage_path() / "settings.json"
        
        existing_settings = {}
        if settings_path.exists():
            with open(settings_path, 'r', encoding='utf-8') as f:
                existing_settings = json.load(f)
        
        existing_settings['encryption_method'] = method
        
        with open(settings_path, 'w', encoding='utf-8') as f:
            json.dump(existing_settings, f, indent=2)
        
        self._logger.info(f"加密方法已更改为: {method}")
        
        return {
            'status': 'success',
            'message': '加密方法已更改',
            'encryption_method': method
        }
    
    def shutdown(self) -> Dict[str, Any]:
        """
        关闭智能体
        """
        self._logger.info("智能体引擎关闭中...")
        
        if self._context.session_id:
            self.logout()
        
        if self._key_manager:
            expired = self._key_manager.cleanup_expired_keys()
            self._logger.info(f"清理了 {expired} 个过期密钥")
        
        self._state = AgentState.UNINITIALIZED
        self._logger.info("智能体引擎已关闭")
        
        return {'status': 'success', 'message': '智能体已关闭'}
