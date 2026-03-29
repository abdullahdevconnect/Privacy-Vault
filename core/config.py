"""
配置管理模块
"""
import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class QuantumCryptoConfig(BaseModel):
    algorithm: str = "kyber"
    key_size: int = 256
    qkd_simulation: bool = True
    entropy_source: str = "system"


class SandboxConfig(BaseModel):
    storage_path: str = "./vault_data"
    max_storage_gb: int = 10
    auto_encrypt: bool = True
    secure_delete: bool = True
    isolation_level: str = "strict"


class AuthConfig(BaseModel):
    multi_factor: bool = True
    session_timeout_minutes: int = 1440  # 24小时
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15
    biometric_enabled: bool = False


class APIConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = 8443
    ssl_enabled: bool = True
    cors_origins: list = Field(default_factory=lambda: ["http://localhost:3000"])


class LoggingConfig(BaseModel):
    level: str = "INFO"
    file: str = "./logs/vault.log"
    max_size_mb: int = 100
    backup_count: int = 5


class PrivacyVaultConfig(BaseModel):
    name: str = "PrivacyVaultAgent"
    version: str = "1.0.0"
    description: str = "量子密码保护的隐私信息储存箱智能体"


class Config:
    _instance: Optional['Config'] = None
    _config_path: str = "config.yaml"
    
    def __new__(cls) -> 'Config':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._raw_config: Dict[str, Any] = {}
        self.privacy_vault: PrivacyVaultConfig = PrivacyVaultConfig()
        self.quantum_crypto: QuantumCryptoConfig = QuantumCryptoConfig()
        self.sandbox: SandboxConfig = SandboxConfig()
        self.auth: AuthConfig = AuthConfig()
        self.api: APIConfig = APIConfig()
        self.logging: LoggingConfig = LoggingConfig()
        self.load_config()
    
    def load_config(self, config_path: Optional[str] = None) -> None:
        if config_path:
            self._config_path = config_path
        
        path = Path(self._config_path)
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                self._raw_config = yaml.safe_load(f) or {}
        
        if 'privacy_vault' in self._raw_config:
            self.privacy_vault = PrivacyVaultConfig(**self._raw_config['privacy_vault'])
        if 'quantum_crypto' in self._raw_config:
            self.quantum_crypto = QuantumCryptoConfig(**self._raw_config['quantum_crypto'])
        if 'sandbox' in self._raw_config:
            self.sandbox = SandboxConfig(**self._raw_config['sandbox'])
        if 'auth' in self._raw_config:
            self.auth = AuthConfig(**self._raw_config['auth'])
        if 'api' in self._raw_config:
            self.api = APIConfig(**self._raw_config['api'])
        if 'logging' in self._raw_config:
            self.logging = LoggingConfig(**self._raw_config['logging'])
    
    def get_storage_path(self) -> Path:
        return Path(self.sandbox.storage_path).resolve()
    
    def ensure_directories(self) -> None:
        self.get_storage_path().mkdir(parents=True, exist_ok=True)
        Path(self.logging.file).parent.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_instance(cls) -> 'Config':
        return cls()
