"""
敏感操作确认模块
当应用请求敏感密钥时，需要用户确认

工作流程:
1. 应用请求密钥
2. 系统判断是否为敏感密钥
3. 如果敏感，发送确认请求给用户
4. 用户在Web界面或手机确认
5. 确认后才返回密钥
"""
import time
import secrets
import json
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from enum import Enum


class ConfirmationStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass
class ConfirmationRequest:
    """确认请求"""
    request_id: str
    app_id: str
    app_name: str
    key_name: str
    operation: str
    reason: str
    created_at: float
    expires_at: float
    status: ConfirmationStatus = ConfirmationStatus.PENDING
    user_response: Optional[str] = None
    responded_at: Optional[float] = None


class SensitiveOperationManager:
    """
    敏感操作管理器
    
    管理:
    - 敏感密钥标记
    - 确认请求队列
    - 用户响应处理
    - 通知发送
    """
    
    def __init__(self, storage_path: Path):
        self.storage_path = Path(storage_path)
        self.requests_path = self.storage_path / "confirmation_requests.json"
        self.sensitive_keys_path = self.storage_path / "sensitive_keys.json"
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self._pending_requests: Dict[str, ConfirmationRequest] = {}
        self._sensitive_keys: Dict[str, Dict] = {}
        
        self._load_data()
    
    def _load_data(self) -> None:
        if self.requests_path.exists():
            with open(self.requests_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for req_id, req_data in data.items():
                req_data['status'] = ConfirmationStatus(req_data['status'])
                self._pending_requests[req_id] = ConfirmationRequest(**req_data)
        
        if self.sensitive_keys_path.exists():
            with open(self.sensitive_keys_path, 'r', encoding='utf-8') as f:
                self._sensitive_keys = json.load(f)
    
    def _save_requests(self) -> None:
        data = {}
        for req_id, req in self._pending_requests.items():
            req_dict = {
                'request_id': req.request_id,
                'app_id': req.app_id,
                'app_name': req.app_name,
                'key_name': req.key_name,
                'operation': req.operation,
                'reason': req.reason,
                'created_at': req.created_at,
                'expires_at': req.expires_at,
                'status': req.status.value,
                'user_response': req.user_response,
                'responded_at': req.responded_at
            }
            data[req_id] = req_dict
        
        with open(self.requests_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def mark_key_sensitive(
        self,
        key_name: str,
        sensitivity_level: str = "high",
        require_confirmation: bool = True,
        auto_approve_after: Optional[int] = None
    ) -> None:
        """
        标记密钥为敏感
        
        参数:
            key_name: 密钥名称
            sensitivity_level: 敏感级别 (low, medium, high, critical)
            require_confirmation: 是否需要用户确认
            auto_approve_after: 多少秒后自动批准（None表示不自动批准）
        """
        self._sensitive_keys[key_name] = {
            'sensitivity_level': sensitivity_level,
            'require_confirmation': require_confirmation,
            'auto_approve_after': auto_approve_after
        }
        
        with open(self.sensitive_keys_path, 'w', encoding='utf-8') as f:
            json.dump(self._sensitive_keys, f, indent=2, ensure_ascii=False)
    
    def is_key_sensitive(self, key_name: str) -> bool:
        """检查密钥是否被标记为敏感"""
        return key_name in self._sensitive_keys
    
    def requires_confirmation(self, key_name: str, operation: str) -> bool:
        """
        检查是否需要用户确认
        
        读取操作通常需要确认
        使用操作（签名、加密）可能不需要
        """
        if key_name not in self._sensitive_keys:
            return False
        
        key_config = self._sensitive_keys[key_name]
        
        if not key_config.get('require_confirmation', True):
            return False
        
        if operation == 'read':
            return True
        elif operation in ['sign', 'encrypt', 'decrypt']:
            return key_config.get('sensitivity_level') in ['high', 'critical']
        
        return True
    
    def create_confirmation_request(
        self,
        app_id: str,
        app_name: str,
        key_name: str,
        operation: str,
        reason: str = "",
        expires_in_seconds: int = 300
    ) -> ConfirmationRequest:
        """
        创建确认请求
        
        返回请求对象，等待用户响应
        """
        request_id = f"confirm_{secrets.token_hex(8)}"
        now = time.time()
        
        request = ConfirmationRequest(
            request_id=request_id,
            app_id=app_id,
            app_name=app_name,
            key_name=key_name,
            operation=operation,
            reason=reason,
            created_at=now,
            expires_at=now + expires_in_seconds
        )
        
        self._pending_requests[request_id] = request
        self._save_requests()
        
        return request
    
    def get_pending_requests(self) -> List[ConfirmationRequest]:
        """获取所有待处理的确认请求"""
        now = time.time()
        pending = []
        
        for req in self._pending_requests.values():
            if req.status == ConfirmationStatus.PENDING:
                if now > req.expires_at:
                    req.status = ConfirmationStatus.EXPIRED
                else:
                    pending.append(req)
        
        self._save_requests()
        return pending
    
    def approve_request(self, request_id: str, user_response: str = "approved") -> bool:
        """用户批准请求"""
        if request_id not in self._pending_requests:
            return False
        
        request = self._pending_requests[request_id]
        
        if request.status != ConfirmationStatus.PENDING:
            return False
        
        if time.time() > request.expires_at:
            request.status = ConfirmationStatus.EXPIRED
            self._save_requests()
            return False
        
        request.status = ConfirmationStatus.APPROVED
        request.user_response = user_response
        request.responded_at = time.time()
        
        self._save_requests()
        return True
    
    def reject_request(self, request_id: str, user_response: str = "rejected") -> bool:
        """用户拒绝请求"""
        if request_id not in self._pending_requests:
            return False
        
        request = self._pending_requests[request_id]
        
        if request.status != ConfirmationStatus.PENDING:
            return False
        
        request.status = ConfirmationStatus.REJECTED
        request.user_response = user_response
        request.responded_at = time.time()
        
        self._save_requests()
        return True
    
    def check_request_status(self, request_id: str) -> Optional[ConfirmationStatus]:
        """检查请求状态"""
        if request_id not in self._pending_requests:
            return None
        
        request = self._pending_requests[request_id]
        
        if request.status == ConfirmationStatus.PENDING:
            if time.time() > request.expires_at:
                request.status = ConfirmationStatus.EXPIRED
                self._save_requests()
        
        return request.status
    
    def wait_for_confirmation(
        self,
        request_id: str,
        timeout: int = 300,
        poll_interval: float = 1.0
    ) -> ConfirmationStatus:
        """
        等待用户确认
        
        阻塞等待直到用户响应或超时
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.check_request_status(request_id)
            
            if status in [
                ConfirmationStatus.APPROVED,
                ConfirmationStatus.REJECTED,
                ConfirmationStatus.EXPIRED
            ]:
                return status
            
            time.sleep(poll_interval)
        
        return ConfirmationStatus.EXPIRED
    
    def get_request(self, request_id: str) -> Optional[ConfirmationRequest]:
        """获取请求详情"""
        return self._pending_requests.get(request_id)
    
    def cleanup_expired(self) -> int:
        """清理过期的请求"""
        now = time.time()
        expired_count = 0
        
        for req in list(self._pending_requests.values()):
            if req.status == ConfirmationStatus.PENDING and now > req.expires_at:
                req.status = ConfirmationStatus.EXPIRED
                expired_count += 1
        
        self._save_requests()
        return expired_count
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = {
            'total_requests': len(self._pending_requests),
            'pending': 0,
            'approved': 0,
            'rejected': 0,
            'expired': 0,
            'sensitive_keys': len(self._sensitive_keys)
        }
        
        for req in self._pending_requests.values():
            if req.status == ConfirmationStatus.PENDING:
                stats['pending'] += 1
            elif req.status == ConfirmationStatus.APPROVED:
                stats['approved'] += 1
            elif req.status == ConfirmationStatus.REJECTED:
                stats['rejected'] += 1
            elif req.status == ConfirmationStatus.EXPIRED:
                stats['expired'] += 1
        
        return stats
