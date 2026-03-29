"""
基于角色的访问控制(RBAC)模块
"""
import json
import time
import secrets
from typing import Optional, Dict, Any, List, Set
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class Permission(Enum):
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"
    EXPORT = "export"
    IMPORT = "import"
    SHARE = "share"


@dataclass
class Resource:
    resource_id: str
    resource_type: str
    name: str
    owner_id: str
    created_at: float
    permissions: Dict[str, List[str]] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'resource_id': self.resource_id,
            'resource_type': self.resource_type,
            'name': self.name,
            'owner_id': self.owner_id,
            'created_at': self.created_at,
            'permissions': self.permissions,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Resource':
        return cls(**data)


@dataclass
class Role:
    role_id: str
    name: str
    description: str
    permissions: Set[str] = field(default_factory=set)
    inherits_from: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    
    def has_permission(self, permission: str) -> bool:
        return permission in self.permissions
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'role_id': self.role_id,
            'name': self.name,
            'description': self.description,
            'permissions': list(self.permissions),
            'inherits_from': self.inherits_from,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Role':
        data['permissions'] = set(data.get('permissions', []))
        return cls(**data)


class AccessControlManager:
    """
    访问控制管理器
    实现基于角色的访问控制(RBAC)
    """
    
    DEFAULT_ROLES = {
        'admin': {
            'permissions': ['read', 'write', 'delete', 'admin', 'export', 'import', 'share'],
            'description': '管理员角色，拥有所有权限'
        },
        'user': {
            'permissions': ['read', 'write', 'export'],
            'description': '普通用户角色'
        },
        'viewer': {
            'permissions': ['read'],
            'description': '只读用户角色'
        },
        'auditor': {
            'permissions': ['read', 'export'],
            'description': '审计员角色'
        }
    }
    
    def __init__(self, storage_path: Path):
        self.storage_path = Path(storage_path)
        self.roles_path = self.storage_path / "roles.json"
        self.resources_path = self.storage_path / "resources.json"
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self._roles: Dict[str, Role] = {}
        self._resources: Dict[str, Resource] = {}
        self._user_roles: Dict[str, Set[str]] = {}
        
        self._load_data()
        self._ensure_default_roles()
    
    def _load_data(self) -> None:
        if self.roles_path.exists():
            with open(self.roles_path, 'r', encoding='utf-8') as f:
                roles_data = json.load(f)
            self._roles = {
                rid: Role.from_dict(data) for rid, data in roles_data.items()
            }
        if self.resources_path.exists():
            with open(self.resources_path, 'r', encoding='utf-8') as f:
                resources_data = json.load(f)
            self._resources = {
                rid: Resource.from_dict(data) for rid, data in resources_data.items()
            }
    
    def _save_roles(self) -> None:
        with open(self.roles_path, 'w', encoding='utf-8') as f:
            json.dump(
                {rid: role.to_dict() for rid, role in self._roles.items()},
                f, indent=2
            )
    
    def _save_resources(self) -> None:
        with open(self.resources_path, 'w', encoding='utf-8') as f:
            json.dump(
                {rid: res.to_dict() for rid, res in self._resources.items()},
                f, indent=2
            )
    
    def _ensure_default_roles(self) -> None:
        for role_name, role_config in self.DEFAULT_ROLES.items():
            if role_name not in self._roles:
                self.create_role(
                    name=role_name,
                    description=role_config['description'],
                    permissions=role_config['permissions']
                )
    
    def create_role(
        self, 
        name: str, 
        description: str = "",
        permissions: Optional[List[str]] = None,
        inherits_from: Optional[str] = None
    ) -> Role:
        role_id = f"role_{secrets.token_hex(8)}"
        role = Role(
            role_id=role_id,
            name=name,
            description=description,
            permissions=set(permissions or []),
            inherits_from=inherits_from
        )
        if inherits_from and inherits_from in self._roles:
            parent_permissions = self._roles[inherits_from].permissions
            role.permissions.update(parent_permissions)
        self._roles[role_id] = role
        self._save_roles()
        return role
    
    def get_role(self, role_id: str) -> Optional[Role]:
        return self._roles.get(role_id)
    
    def get_role_by_name(self, name: str) -> Optional[Role]:
        for role in self._roles.values():
            if role.name == name:
                return role
        return None
    
    def update_role(
        self, 
        role_id: str, 
        permissions: Optional[List[str]] = None,
        description: Optional[str] = None
    ) -> Optional[Role]:
        role = self._roles.get(role_id)
        if not role:
            return None
        if permissions is not None:
            role.permissions = set(permissions)
        if description is not None:
            role.description = description
        self._save_roles()
        return role
    
    def delete_role(self, role_id: str) -> bool:
        if role_id not in self._roles:
            return False
        for user_roles in self._user_roles.values():
            user_roles.discard(role_id)
        del self._roles[role_id]
        self._save_roles()
        return True
    
    def assign_role_to_user(self, user_id: str, role_name: str) -> bool:
        role = self.get_role_by_name(role_name)
        if not role:
            return False
        if user_id not in self._user_roles:
            self._user_roles[user_id] = set()
        self._user_roles[user_id].add(role.role_id)
        return True
    
    def revoke_role_from_user(self, user_id: str, role_name: str) -> bool:
        role = self.get_role_by_name(role_name)
        if not role or user_id not in self._user_roles:
            return False
        self._user_roles[user_id].discard(role.role_id)
        return True
    
    def get_user_roles(self, user_id: str) -> List[Role]:
        role_ids = self._user_roles.get(user_id, set())
        return [self._roles[rid] for rid in role_ids if rid in self._roles]
    
    def get_user_permissions(self, user_id: str) -> Set[str]:
        permissions = set()
        for role in self.get_user_roles(user_id):
            permissions.update(role.permissions)
        return permissions
    
    def check_permission(
        self, 
        user_id: str, 
        permission: str,
        resource_id: Optional[str] = None
    ) -> bool:
        user_permissions = self.get_user_permissions(user_id)
        if 'admin' in user_permissions:
            return True
        if permission in user_permissions:
            if resource_id:
                resource = self._resources.get(resource_id)
                if resource:
                    if user_id == resource.owner_id:
                        return True
                    user_allowed = resource.permissions.get(user_id, [])
                    if permission in user_allowed:
                        return True
                    for role in self.get_user_roles(user_id):
                        if role.name in resource.permissions:
                            if permission in resource.permissions[role.name]:
                                return True
                    return False
            return True
        return False
    
    def create_resource(
        self,
        resource_type: str,
        name: str,
        owner_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Resource:
        resource_id = f"res_{secrets.token_hex(8)}"
        resource = Resource(
            resource_id=resource_id,
            resource_type=resource_type,
            name=name,
            owner_id=owner_id,
            created_at=time.time(),
            metadata=metadata or {}
        )
        self._resources[resource_id] = resource
        self._save_resources()
        return resource
    
    def get_resource(self, resource_id: str) -> Optional[Resource]:
        return self._resources.get(resource_id)
    
    def grant_resource_permission(
        self,
        resource_id: str,
        target: str,
        permission: str
    ) -> bool:
        resource = self._resources.get(resource_id)
        if not resource:
            return False
        if target not in resource.permissions:
            resource.permissions[target] = []
        if permission not in resource.permissions[target]:
            resource.permissions[target].append(permission)
        self._save_resources()
        return True
    
    def revoke_resource_permission(
        self,
        resource_id: str,
        target: str,
        permission: str
    ) -> bool:
        resource = self._resources.get(resource_id)
        if not resource or target not in resource.permissions:
            return False
        if permission in resource.permissions[target]:
            resource.permissions[target].remove(permission)
        self._save_resources()
        return True
    
    def delete_resource(self, resource_id: str) -> bool:
        if resource_id in self._resources:
            del self._resources[resource_id]
            self._save_resources()
            return True
        return False
    
    def list_user_resources(
        self, 
        user_id: str,
        resource_type: Optional[str] = None
    ) -> List[Resource]:
        resources = []
        for resource in self._resources.values():
            if resource.owner_id == user_id:
                if resource_type is None or resource.resource_type == resource_type:
                    resources.append(resource)
            elif user_id in resource.permissions:
                if resource_type is None or resource.resource_type == resource_type:
                    resources.append(resource)
        return resources
    
    def list_all_roles(self) -> List[Role]:
        return list(self._roles.values())
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            'total_roles': len(self._roles),
            'total_resources': len(self._resources),
            'users_with_roles': len(self._user_roles)
        }
