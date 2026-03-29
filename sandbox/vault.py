"""
加密存储库实现
提供安全的数据存储和检索
"""
import os
import json
import secrets
import hashlib
import time
import shutil
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
import base64
import uuid


@dataclass
class VaultMetadata:
    entry_id: str
    name: str
    content_type: str
    size: int
    created_at: float
    updated_at: float
    tags: List[str] = field(default_factory=list)
    checksum: str = ""
    encrypted: bool = True
    version: int = 1
    custom_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VaultMetadata':
        return cls(**data)


@dataclass
class VaultEntry:
    metadata: VaultMetadata
    encrypted_data: Optional[bytes] = None
    data_path: Optional[Path] = None
    
    def is_loaded(self) -> bool:
        return self.encrypted_data is not None


class Vault:
    """
    加密存储库
    提供安全的数据存储、检索和管理功能
    """
    
    def __init__(self, storage_path: Path, crypto_provider=None):
        self.storage_path = Path(storage_path)
        self.crypto = crypto_provider
        self._entries: Dict[str, VaultEntry] = {}
        self._index: Dict[str, str] = {}
        self._initialized = False
    
    def initialize(self) -> Dict[str, Any]:
        self.storage_path.mkdir(parents=True, exist_ok=True)
        (self.storage_path / "entries").mkdir(exist_ok=True)
        (self.storage_path / "metadata").mkdir(exist_ok=True)
        (self.storage_path / "temp").mkdir(exist_ok=True)
        self._load_index()
        self._initialized = True
        return {
            'status': 'initialized',
            'storage_path': str(self.storage_path),
            'entries_count': len(self._entries)
        }
    
    def _generate_entry_id(self) -> str:
        return f"entry_{uuid.uuid4().hex[:16]}_{int(time.time() * 1000)}"
    
    def _load_index(self) -> None:
        index_file = self.storage_path / "index.json"
        if index_file.exists():
            with open(index_file, 'r', encoding='utf-8') as f:
                self._index = json.load(f)
            for entry_id, name in self._index.items():
                metadata_path = self.storage_path / "metadata" / f"{entry_id}.json"
                if metadata_path.exists():
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        metadata = VaultMetadata.from_dict(json.load(f))
                    self._entries[entry_id] = VaultEntry(
                        metadata=metadata,
                        data_path=self.storage_path / "entries" / f"{entry_id}.dat"
                    )
    
    def _save_index(self) -> None:
        index_file = self.storage_path / "index.json"
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(self._index, f, indent=2)
    
    def _save_metadata(self, entry: VaultEntry) -> None:
        metadata_path = self.storage_path / "metadata" / f"{entry.metadata.entry_id}.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(entry.metadata.to_dict(), f, indent=2)
    
    def _compute_checksum(self, data: bytes) -> str:
        return hashlib.sha3_256(data).hexdigest()
    
    def store(
        self, 
        name: str, 
        data: Union[bytes, str, Dict[str, Any]], 
        content_type: str = "application/octet-stream",
        tags: Optional[List[str]] = None,
        encrypt: bool = True,
        custom_metadata: Optional[Dict[str, Any]] = None
    ) -> VaultEntry:
        if not self._initialized:
            raise RuntimeError("Vault未初始化")
        if isinstance(data, str):
            data = data.encode('utf-8')
        elif isinstance(data, dict):
            data = json.dumps(data).encode('utf-8')
            content_type = "application/json"
        entry_id = self._generate_entry_id()
        checksum = self._compute_checksum(data)
        encrypted_data = data
        if encrypt and self.crypto:
            encrypted_package = self.crypto.encrypt_data(data)
            encrypted_data = json.dumps({
                k: base64.b64encode(v).decode() if isinstance(v, bytes) else v
                for k, v in encrypted_package.items()
            }).encode('utf-8')
        now = time.time()
        metadata = VaultMetadata(
            entry_id=entry_id,
            name=name,
            content_type=content_type,
            size=len(data),
            created_at=now,
            updated_at=now,
            tags=tags or [],
            checksum=checksum,
            encrypted=encrypt,
            custom_metadata=custom_metadata or {}
        )
        entry = VaultEntry(
            metadata=metadata,
            encrypted_data=encrypted_data,
            data_path=self.storage_path / "entries" / f"{entry_id}.dat"
        )
        with open(entry.data_path, 'wb') as f:
            f.write(encrypted_data)
        self._entries[entry_id] = entry
        self._index[entry_id] = name
        self._save_index()
        self._save_metadata(entry)
        entry.encrypted_data = None
        return entry
    
    def retrieve(
        self, 
        entry_id: Optional[str] = None, 
        name: Optional[str] = None
    ) -> Optional[bytes]:
        if not self._initialized:
            raise RuntimeError("Vault未初始化")
        entry = None
        if entry_id:
            entry = self._entries.get(entry_id)
        elif name:
            for e in self._entries.values():
                if e.metadata.name == name:
                    entry = e
                    break
        if not entry:
            return None
        with open(entry.data_path, 'rb') as f:
            encrypted_data = f.read()
        if entry.metadata.encrypted and self.crypto:
            try:
                encrypted_package = json.loads(encrypted_data.decode('utf-8'))
                encrypted_package = {
                    k: base64.b64decode(v) if isinstance(v, str) else v
                    for k, v in encrypted_package.items()
                }
                return self.crypto.decrypt_data(encrypted_package)
            except Exception as e:
                import traceback
                print(f"解密失败: {type(e).__name__}: {e}")
                traceback.print_exc()
                raise
        return encrypted_data
    
    def retrieve_metadata(self, entry_id: str) -> Optional[VaultMetadata]:
        entry = self._entries.get(entry_id)
        return entry.metadata if entry else None
    
    def update(
        self, 
        entry_id: str, 
        data: Union[bytes, str, Dict[str, Any]],
        tags: Optional[List[str]] = None,
        custom_metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[VaultEntry]:
        entry = self._entries.get(entry_id)
        if not entry:
            return None
        if isinstance(data, str):
            data = data.encode('utf-8')
        elif isinstance(data, dict):
            data = json.dumps(data).encode('utf-8')
        checksum = self._compute_checksum(data)
        encrypted_data = data
        if entry.metadata.encrypted and self.crypto:
            encrypted_package = self.crypto.encrypt_data(data)
            encrypted_data = json.dumps({
                k: base64.b64encode(v).decode() if isinstance(v, bytes) else v
                for k, v in encrypted_package.items()
            }).encode('utf-8')
        with open(entry.data_path, 'wb') as f:
            f.write(encrypted_data)
        entry.metadata.size = len(data)
        entry.metadata.updated_at = time.time()
        entry.metadata.checksum = checksum
        entry.metadata.version += 1
        if tags is not None:
            entry.metadata.tags = tags
        if custom_metadata is not None:
            entry.metadata.custom_metadata.update(custom_metadata)
        self._save_metadata(entry)
        return entry
    
    def delete(self, entry_id: str, secure_delete: bool = True) -> bool:
        entry = self._entries.get(entry_id)
        if not entry:
            return False
        if secure_delete and entry.data_path.exists():
            file_size = entry.data_path.stat().st_size
            with open(entry.data_path, 'wb') as f:
                for _ in range(3):
                    f.seek(0)
                    f.write(secrets.token_bytes(file_size))
            entry.data_path.unlink()
        metadata_path = self.storage_path / "metadata" / f"{entry_id}.json"
        if metadata_path.exists():
            metadata_path.unlink()
        del self._entries[entry_id]
        if entry_id in self._index:
            del self._index[entry_id]
        self._save_index()
        return True
    
    def search(
        self, 
        query: Optional[str] = None, 
        tags: Optional[List[str]] = None,
        content_type: Optional[str] = None
    ) -> List[VaultMetadata]:
        results = []
        for entry in self._entries.values():
            match = True
            if query:
                query_lower = query.lower()
                if query_lower not in entry.metadata.name.lower():
                    if not any(
                        query_lower in str(v).lower() 
                        for v in entry.metadata.custom_metadata.values()
                    ):
                        match = False
            if tags and match:
                if not all(tag in entry.metadata.tags for tag in tags):
                    match = False
            if content_type and match:
                if not entry.metadata.content_type.startswith(content_type):
                    match = False
            if match:
                results.append(entry.metadata)
        return results
    
    def list_all(self) -> List[VaultMetadata]:
        return [entry.metadata for entry in self._entries.values()]
    
    def get_stats(self) -> Dict[str, Any]:
        total_size = sum(e.metadata.size for e in self._entries.values())
        encrypted_count = sum(1 for e in self._entries.values() if e.metadata.encrypted)
        return {
            'total_entries': len(self._entries),
            'total_size_bytes': total_size,
            'encrypted_entries': encrypted_count,
            'storage_path': str(self.storage_path)
        }
    
    def export_entry(self, entry_id: str, export_path: Path) -> bool:
        data = self.retrieve(entry_id)
        if data is None:
            return False
        with open(export_path, 'wb') as f:
            f.write(data)
        return True
    
    def import_file(
        self, 
        file_path: Path, 
        name: Optional[str] = None,
        tags: Optional[List[str]] = None,
        encrypt: bool = True
    ) -> Optional[VaultEntry]:
        if not file_path.exists():
            return None
        with open(file_path, 'rb') as f:
            data = f.read()
        entry_name = name or file_path.name
        content_type = self._guess_content_type(file_path)
        return self.store(
            name=entry_name,
            data=data,
            content_type=content_type,
            tags=tags,
            encrypt=encrypt
        )
    
    def _guess_content_type(self, file_path: Path) -> str:
        suffix = file_path.suffix.lower()
        content_types = {
            '.txt': 'text/plain',
            '.json': 'application/json',
            '.pdf': 'application/pdf',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.key': 'application/x-pem-key',
            '.pem': 'application/x-pem-file',
            '.xml': 'application/xml',
            '.zip': 'application/zip'
        }
        return content_types.get(suffix, 'application/octet-stream')
    
    def backup(self, backup_path: Path) -> bool:
        try:
            if backup_path.exists():
                shutil.rmtree(backup_path)
            shutil.copytree(self.storage_path, backup_path)
            return True
        except Exception as e:
            print(f"备份失败: {e}")
            return False
    
    def restore(self, backup_path: Path) -> bool:
        try:
            if not backup_path.exists():
                return False
            if self.storage_path.exists():
                shutil.rmtree(self.storage_path)
            shutil.copytree(backup_path, self.storage_path)
            self._load_index()
            return True
        except Exception as e:
            print(f"恢复失败: {e}")
            return False
