"""
密钥管理模块
管理量子密钥的生命周期
"""
import os
import json
import secrets
import hashlib
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
import base64


@dataclass
class QuantumKey:
    key_id: str
    key_data: bytes
    algorithm: str = "quantum_hybrid"
    created_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None
    usage_count: int = 0
    max_usage: int = 10000
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at
    
    def is_exhausted(self) -> bool:
        return self.usage_count >= self.max_usage
    
    def is_valid(self) -> bool:
        return not self.is_expired() and not self.is_exhausted()
    
    def increment_usage(self) -> None:
        self.usage_count += 1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'key_id': self.key_id,
            'key_data': base64.b64encode(self.key_data).decode(),
            'algorithm': self.algorithm,
            'created_at': self.created_at,
            'expires_at': self.expires_at,
            'usage_count': self.usage_count,
            'max_usage': self.max_usage,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QuantumKey':
        return cls(
            key_id=data['key_id'],
            key_data=base64.b64decode(data['key_data']),
            algorithm=data.get('algorithm', 'quantum_hybrid'),
            created_at=data['created_at'],
            expires_at=data.get('expires_at'),
            usage_count=data.get('usage_count', 0),
            max_usage=data.get('max_usage', 10000),
            metadata=data.get('metadata', {})
        )


class KeyManager:
    """
    量子密钥管理器
    负责密钥的生成、存储、轮换和销毁
    """
    
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path("./vault_data/keys")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._keys: Dict[str, QuantumKey] = {}
        self._key_index: Dict[str, str] = {}
        self._rotation_policy = {
            'max_age_hours': 24 * 7,
            'max_usage': 10000,
            'auto_rotate': True
        }
    
    def generate_key_id(self) -> str:
        timestamp = int(time.time() * 1000)
        random_part = secrets.token_hex(8)
        return f"qk_{timestamp}_{random_part}"
    
    def create_key(
        self, 
        key_data: bytes, 
        algorithm: str = "quantum_hybrid",
        ttl_hours: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> QuantumKey:
        key_id = self.generate_key_id()
        expires_at = None
        if ttl_hours:
            expires_at = time.time() + (ttl_hours * 3600)
        elif self._rotation_policy['auto_rotate']:
            expires_at = time.time() + (self._rotation_policy['max_age_hours'] * 3600)
        
        key = QuantumKey(
            key_id=key_id,
            key_data=key_data,
            algorithm=algorithm,
            expires_at=expires_at,
            max_usage=self._rotation_policy['max_usage'],
            metadata=metadata or {}
        )
        self._keys[key_id] = key
        self._persist_key(key)
        return key
    
    def get_key(self, key_id: str) -> Optional[QuantumKey]:
        key = self._keys.get(key_id)
        if key and key.is_valid():
            key.increment_usage()
            return key
        elif key:
            self._handle_invalid_key(key_id)
        return None
    
    def get_active_key(self) -> Optional[QuantumKey]:
        for key_id, key in self._keys.items():
            if key.is_valid():
                key.increment_usage()
                return key
        return None
    
    def rotate_key(self, old_key_id: str, new_key_data: bytes) -> Optional[QuantumKey]:
        old_key = self._keys.get(old_key_id)
        if not old_key:
            return None
        new_key = self.create_key(
            key_data=new_key_data,
            algorithm=old_key.algorithm,
            metadata={'rotated_from': old_key_id, **old_key.metadata}
        )
        self.revoke_key(old_key_id)
        return new_key
    
    def revoke_key(self, key_id: str) -> bool:
        if key_id not in self._keys:
            return False
        key = self._keys.pop(key_id)
        self._secure_delete_key_file(key_id)
        return True
    
    def list_keys(self, include_invalid: bool = False) -> List[Dict[str, Any]]:
        keys_info = []
        for key_id, key in self._keys.items():
            if include_invalid or key.is_valid():
                keys_info.append({
                    'key_id': key.key_id,
                    'algorithm': key.algorithm,
                    'created_at': datetime.fromtimestamp(key.created_at).isoformat(),
                    'expires_at': datetime.fromtimestamp(key.expires_at).isoformat() if key.expires_at else None,
                    'usage_count': key.usage_count,
                    'is_valid': key.is_valid()
                })
        return keys_info
    
    def cleanup_expired_keys(self) -> int:
        expired_count = 0
        for key_id in list(self._keys.keys()):
            key = self._keys[key_id]
            if not key.is_valid():
                self.revoke_key(key_id)
                expired_count += 1
        return expired_count
    
    def set_rotation_policy(
        self, 
        max_age_hours: Optional[int] = None,
        max_usage: Optional[int] = None,
        auto_rotate: Optional[bool] = None
    ) -> None:
        if max_age_hours is not None:
            self._rotation_policy['max_age_hours'] = max_age_hours
        if max_usage is not None:
            self._rotation_policy['max_usage'] = max_usage
        if auto_rotate is not None:
            self._rotation_policy['auto_rotate'] = auto_rotate
    
    def _persist_key(self, key: QuantumKey) -> None:
        key_file = self.storage_path / f"{key.key_id}.key"
        encrypted_data = self._encrypt_key_storage(key.to_dict())
        with open(key_file, 'w') as f:
            json.dump(encrypted_data, f)
    
    def _encrypt_key_storage(self, data: Dict[str, Any]) -> Dict[str, Any]:
        protected = {
            'protected': True,
            'data_hash': hashlib.sha256(
                json.dumps(data, sort_keys=True).encode()
            ).hexdigest()
        }
        protected['payload'] = base64.b64encode(
            json.dumps(data).encode()
        ).decode()
        return protected
    
    def _decrypt_key_storage(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if not data.get('protected'):
            return data
        payload = base64.b64decode(data['payload']).decode()
        return json.loads(payload)
    
    def _handle_invalid_key(self, key_id: str) -> None:
        key = self._keys.get(key_id)
        if key:
            if key.is_expired():
                print(f"密钥 {key_id} 已过期")
            elif key.is_exhausted():
                print(f"密钥 {key_id} 使用次数已达上限")
    
    def _secure_delete_key_file(self, key_id: str) -> None:
        key_file = self.storage_path / f"{key_id}.key"
        if key_file.exists():
            file_size = key_file.stat().st_size
            with open(key_file, 'wb') as f:
                f.write(secrets.token_bytes(file_size))
            key_file.unlink()
    
    def load_keys(self) -> int:
        loaded_count = 0
        for key_file in self.storage_path.glob("*.key"):
            try:
                with open(key_file, 'r') as f:
                    data = json.load(f)
                decrypted_data = self._decrypt_key_storage(data)
                key = QuantumKey.from_dict(decrypted_data)
                self._keys[key.key_id] = key
                loaded_count += 1
            except Exception as e:
                print(f"加载密钥文件 {key_file} 失败: {e}")
        return loaded_count
    
    def get_key_stats(self) -> Dict[str, Any]:
        total_keys = len(self._keys)
        valid_keys = sum(1 for k in self._keys.values() if k.is_valid())
        expired_keys = sum(1 for k in self._keys.values() if k.is_expired())
        exhausted_keys = sum(1 for k in self._keys.values() if k.is_exhausted())
        
        return {
            'total_keys': total_keys,
            'valid_keys': valid_keys,
            'expired_keys': expired_keys,
            'exhausted_keys': exhausted_keys,
            'rotation_policy': self._rotation_policy
        }
