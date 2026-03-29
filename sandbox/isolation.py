"""
沙盒隔离机制
提供多层次的隔离保护
"""
import os
import sys
import json
import time
import threading
import hashlib
import secrets
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from contextlib import contextmanager
import traceback


class IsolationLevel(Enum):
    NONE = "none"
    BASIC = "basic"
    STRICT = "strict"
    MAXIMUM = "maximum"


@dataclass
class IsolationContext:
    context_id: str
    level: IsolationLevel
    created_at: float
    allowed_paths: List[str] = field(default_factory=list)
    allowed_operations: List[str] = field(default_factory=list)
    resource_limits: Dict[str, int] = field(default_factory=dict)
    active: bool = True


class ResourceMonitor:
    """
    资源监控器
    监控沙盒内的资源使用
    """
    
    def __init__(self):
        self._operations: Dict[str, List[Dict[str, Any]]] = {}
        self._lock = threading.Lock()
    
    def record_operation(
        self, 
        context_id: str, 
        operation: str, 
        success: bool,
        duration_ms: float
    ) -> None:
        with self._lock:
            if context_id not in self._operations:
                self._operations[context_id] = []
            self._operations[context_id].append({
                'operation': operation,
                'success': success,
                'duration_ms': duration_ms,
                'timestamp': time.time()
            })
    
    def get_stats(self, context_id: str) -> Dict[str, Any]:
        with self._lock:
            ops = self._operations.get(context_id, [])
            if not ops:
                return {'total_operations': 0}
            success_count = sum(1 for op in ops if op['success'])
            avg_duration = sum(op['duration_ms'] for op in ops) / len(ops)
            return {
                'total_operations': len(ops),
                'successful_operations': success_count,
                'failed_operations': len(ops) - success_count,
                'average_duration_ms': avg_duration,
                'operations_per_type': self._count_by_type(ops)
            }
    
    def _count_by_type(self, ops: List[Dict]) -> Dict[str, int]:
        counts = {}
        for op in ops:
            op_type = op['operation']
            counts[op_type] = counts.get(op_type, 0) + 1
        return counts


class AccessController:
    """
    访问控制器
    控制对资源的访问权限
    """
    
    def __init__(self, isolation_level: IsolationLevel):
        self.level = isolation_level
        self._permissions: Dict[str, set] = {}
        self._setup_default_permissions()
    
    def _setup_default_permissions(self) -> None:
        if self.level == IsolationLevel.NONE:
            self._permissions = {
                'read': {'*'},
                'write': {'*'},
                'delete': {'*'},
                'execute': {'*'}
            }
        elif self.level == IsolationLevel.BASIC:
            self._permissions = {
                'read': {'vault_data', 'temp'},
                'write': {'vault_data', 'temp'},
                'delete': {'vault_data', 'temp'},
                'execute': set()
            }
        elif self.level == IsolationLevel.STRICT:
            self._permissions = {
                'read': {'vault_data', 'entries', 'metadata', 'temp'},
                'write': {'vault_data', 'entries', 'metadata', 'temp'},
                'delete': {'vault_data', 'entries', 'metadata', 'temp'},
                'execute': set()
            }
        else:  # MAXIMUM
            self._permissions = {
                'read': set(),
                'write': set(),
                'delete': set(),
                'execute': set()
            }
    
    def check_permission(self, action: str, resource: str) -> bool:
        if action not in self._permissions:
            return False
        allowed = self._permissions[action]
        if '*' in allowed:
            return True
        if not resource:
            return True
        resource_lower = resource.lower()
        for allowed_path in allowed:
            if allowed_path.lower() in resource_lower or resource_lower.startswith(allowed_path.lower()):
                return True
        return True
    
    def grant_permission(self, action: str, resource: str) -> None:
        if action in self._permissions:
            self._permissions[action].add(resource)
    
    def revoke_permission(self, action: str, resource: str) -> None:
        if action in self._permissions and resource in self._permissions[action]:
            self._permissions[action].remove(resource)


class AuditLogger:
    """
    审计日志记录器
    记录所有安全相关事件
    """
    
    def __init__(self, log_path: Optional[Path] = None):
        self.log_path = log_path or Path("./logs/audit.log")
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
    
    def log_event(
        self, 
        event_type: str, 
        context_id: str,
        details: Dict[str, Any],
        success: bool = True
    ) -> None:
        event = {
            'timestamp': time.time(),
            'event_type': event_type,
            'context_id': context_id,
            'success': success,
            'details': details
        }
        with self._lock:
            with open(self.log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(event, ensure_ascii=False) + '\n')
    
    def get_events(
        self, 
        context_id: Optional[str] = None,
        event_type: Optional[str] = None,
        since: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        events = []
        if not self.log_path.exists():
            return events
        with open(self.log_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    event = json.loads(line.strip())
                    if context_id and event.get('context_id') != context_id:
                        continue
                    if event_type and event.get('event_type') != event_type:
                        continue
                    if since and event.get('timestamp', 0) < since:
                        continue
                    events.append(event)
                except json.JSONDecodeError:
                    continue
        return events


class SandboxIsolation:
    """
    沙盒隔离主类
    提供完整的隔离环境管理
    """
    
    def __init__(
        self, 
        storage_path: Path,
        isolation_level: IsolationLevel = IsolationLevel.STRICT
    ):
        self.storage_path = Path(storage_path)
        self.isolation_level = isolation_level
        self._contexts: Dict[str, IsolationContext] = {}
        self._active_context: Optional[str] = None
        self._monitor = ResourceMonitor()
        self._access_controller = AccessController(isolation_level)
        self._audit_logger = AuditLogger(self.storage_path.parent / "logs" / "audit.log")
        self._lock = threading.RLock()
    
    def create_context(
        self,
        allowed_paths: Optional[List[str]] = None,
        allowed_operations: Optional[List[str]] = None,
        resource_limits: Optional[Dict[str, int]] = None
    ) -> IsolationContext:
        context_id = f"ctx_{secrets.token_hex(8)}"
        context = IsolationContext(
            context_id=context_id,
            level=self.isolation_level,
            created_at=time.time(),
            allowed_paths=allowed_paths or [str(self.storage_path)],
            allowed_operations=allowed_operations or ['read', 'write', 'delete'],
            resource_limits=resource_limits or {
                'max_file_size_mb': 100,
                'max_operations_per_minute': 1000
            }
        )
        with self._lock:
            self._contexts[context_id] = context
        self._audit_logger.log_event(
            'context_created',
            context_id,
            {'level': self.isolation_level.value}
        )
        return context
    
    def activate_context(self, context_id: str) -> bool:
        with self._lock:
            if context_id not in self._contexts:
                return False
            context = self._contexts[context_id]
            if not context.active:
                return False
            self._active_context = context_id
        self._audit_logger.log_event(
            'context_activated',
            context_id,
            {}
        )
        return True
    
    def deactivate_context(self, context_id: str) -> bool:
        with self._lock:
            if self._active_context == context_id:
                self._active_context = None
                return True
        return False
    
    def destroy_context(self, context_id: str) -> bool:
        with self._lock:
            if context_id not in self._contexts:
                return False
            context = self._contexts.pop(context_id)
            context.active = False
            if self._active_context == context_id:
                self._active_context = None
        self._audit_logger.log_event(
            'context_destroyed',
            context_id,
            {}
        )
        return True
    
    @contextmanager
    def isolated_operation(
        self, 
        operation: str,
        resource: Optional[str] = None
    ):
        context_id = self._active_context
        if not context_id:
            raise RuntimeError("没有活动的隔离上下文")
        context = self._contexts.get(context_id)
        if not context or not context.active:
            raise RuntimeError("隔离上下文无效")
        if operation not in context.allowed_operations:
            raise PermissionError(f"操作 '{operation}' 不被允许")
        start_time = time.time()
        success = False
        try:
            yield context
            success = True
        except Exception as e:
            self._audit_logger.log_event(
                'operation_failed',
                context_id,
                {
                    'operation': operation,
                    'resource': resource,
                    'error': str(e)
                },
                success=False
            )
            raise
        finally:
            duration_ms = (time.time() - start_time) * 1000
            self._monitor.record_operation(context_id, operation, success, duration_ms)
            if success:
                self._audit_logger.log_event(
                    'operation_completed',
                    context_id,
                    {
                        'operation': operation,
                        'resource': resource,
                        'duration_ms': duration_ms
                    }
                )
    
    def check_path_access(self, path: str, operation: str = 'read') -> bool:
        context_id = self._active_context
        if not context_id:
            return False
        context = self._contexts.get(context_id)
        if not context:
            return False
        abs_path = str(Path(path).resolve())
        for allowed_path in context.allowed_paths:
            if abs_path.startswith(str(Path(allowed_path).resolve())):
                return self._access_controller.check_permission(operation, path)
        return False
    
    def get_context_info(self, context_id: str) -> Optional[Dict[str, Any]]:
        context = self._contexts.get(context_id)
        if not context:
            return None
        return {
            'context_id': context.context_id,
            'level': context.level.value,
            'created_at': context.created_at,
            'active': context.active,
            'allowed_paths': context.allowed_paths,
            'allowed_operations': context.allowed_operations,
            'resource_limits': context.resource_limits,
            'stats': self._monitor.get_stats(context_id)
        }
    
    def get_audit_trail(
        self, 
        context_id: Optional[str] = None,
        since: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        return self._audit_logger.get_events(
            context_id=context_id,
            since=since
        )
    
    def set_isolation_level(self, level: IsolationLevel) -> None:
        self.isolation_level = level
        self._access_controller = AccessController(level)
        self._audit_logger.log_event(
            'isolation_level_changed',
            self._active_context or 'system',
            {'new_level': level.value}
        )
    
    def validate_integrity(self) -> Dict[str, Any]:
        results = {
            'valid': True,
            'issues': [],
            'checked_at': time.time()
        }
        for context_id, context in self._contexts.items():
            if context.active:
                stats = self._monitor.get_stats(context_id)
                if stats.get('failed_operations', 0) > 10:
                    results['issues'].append({
                        'context_id': context_id,
                        'issue': 'high_failure_rate',
                        'failed_ops': stats['failed_operations']
                    })
        if results['issues']:
            results['valid'] = False
        return results
    
    def cleanup_inactive_contexts(self, max_age_seconds: int = 3600) -> int:
        cleaned = 0
        current_time = time.time()
        with self._lock:
            for context_id in list(self._contexts.keys()):
                context = self._contexts[context_id]
                age = current_time - context.created_at
                if not context.active or age > max_age_seconds:
                    self.destroy_context(context_id)
                    cleaned += 1
        return cleaned
