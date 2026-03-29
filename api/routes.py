"""
REST API 路由
提供HTTP接口访问智能体功能
"""
import os
import json
import time
from typing import Optional, Dict, Any, List
from pathlib import Path

from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.agent_engine import AgentEngine, AgentState


class UserRegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    roles: Optional[List[str]] = None
    enable_mfa: bool = False


class UserLoginRequest(BaseModel):
    username: str
    password: str
    mfa_code: Optional[str] = None


class DataStoreRequest(BaseModel):
    name: str
    data: Any
    tags: Optional[List[str]] = None
    encrypt: bool = True


class DataRetrieveRequest(BaseModel):
    entry_id: Optional[str] = None
    name: Optional[str] = None


class DataDeleteRequest(BaseModel):
    entry_id: str


class SearchRequest(BaseModel):
    query: Optional[str] = None
    tags: Optional[List[str]] = None
    content_type: Optional[str] = None


class BackupRequest(BaseModel):
    backup_path: str


_agent: Optional[AgentEngine] = None


def get_agent() -> AgentEngine:
    global _agent
    if _agent is None:
        _agent = AgentEngine()
        _agent.initialize()
    return _agent


def get_session_user(
    authorization: Optional[str] = Header(None),
    agent: AgentEngine = Depends(get_agent)
) -> Dict[str, Any]:
    if not authorization:
        raise HTTPException(status_code=401, detail="未提供认证信息")
    
    if authorization.startswith("Bearer "):
        session_id = authorization[7:]
    else:
        session_id = authorization
    
    session, user = agent._authenticator.validate_session(session_id)
    
    if not session or not user:
        raise HTTPException(status_code=401, detail="会话无效或已过期")
    
    return {
        'session_id': session.session_id,
        'user_id': user.user_id,
        'username': user.username,
        'roles': user.roles
    }


def create_app(config_path: Optional[str] = None) -> FastAPI:
    app = FastAPI(
        title="Privacy Vault Agent API",
        description="量子密码保护的隐私信息储存箱智能体API",
        version="1.0.0"
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    static_dir = Path(__file__).parent.parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    
    global _agent
    _agent = AgentEngine(config_path)
    
    @app.on_event("startup")
    async def startup_event():
        _agent.initialize()
    
    @app.on_event("shutdown")
    async def shutdown_event():
        _agent.shutdown()
    
    @app.get("/")
    async def root():
        return {
            "name": "Privacy Vault Agent",
            "version": "1.0.0",
            "description": "量子密码保护的隐私信息储存箱智能体",
            "ui": "/ui",
            "docs": "/docs",
            "endpoints": {
                "auth": ["/api/auth/register", "/api/auth/login", "/api/auth/logout"],
                "data": ["/api/data/store", "/api/data/retrieve", "/api/data/delete", "/api/data/search"],
                "proxy": ["/api/proxy/register", "/api/proxy/grant", "/api/proxy/request-key"],
                "system": ["/api/status", "/api/keys/rotate", "/api/audit"]
            }
        }
    
    @app.get("/ui")
    @app.get("/ui/{path:path}")
    async def serve_ui(path: str = ""):
        static_dir = Path(__file__).parent.parent / "static"
        index_file = static_dir / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return {"error": "UI not found"}
    
    @app.get("/api/status")
    async def get_status(agent: AgentEngine = Depends(get_agent)):
        return agent.get_status()
    
    @app.post("/api/auth/register")
    async def register(
        request: UserRegisterRequest,
        agent: AgentEngine = Depends(get_agent)
    ):
        result = agent.register_user(
            username=request.username,
            password=request.password,
            roles=request.roles,
            enable_mfa=request.enable_mfa
        )
        if result['status'] == 'error':
            raise HTTPException(status_code=400, detail=result['message'])
        return result
    
    @app.post("/api/auth/login")
    async def login(
        request: UserLoginRequest,
        http_request: Request,
        agent: AgentEngine = Depends(get_agent)
    ):
        result = agent.login(
            username=request.username,
            password=request.password,
            mfa_code=request.mfa_code,
            ip_address=http_request.client.host if http_request.client else None
        )
        if result['status'] == 'error':
            raise HTTPException(status_code=401, detail=result['message'])
        return result
    
    @app.post("/api/auth/logout")
    async def logout(
        agent: AgentEngine = Depends(get_agent),
        user_info: Dict = Depends(get_session_user)
    ):
        return agent.logout()
    
    @app.post("/api/auth/mfa/enable")
    async def enable_mfa(
        agent: AgentEngine = Depends(get_agent),
        user_info: Dict = Depends(get_session_user)
    ):
        result = agent.enable_mfa()
        if result['status'] == 'error':
            raise HTTPException(status_code=400, detail=result['message'])
        return result
    
    @app.post("/api/data/store")
    async def store_data(
        request: DataStoreRequest,
        agent: AgentEngine = Depends(get_agent),
        user_info: Dict = Depends(get_session_user)
    ):
        result = agent.store_data(
            name=request.name,
            data=request.data,
            tags=request.tags,
            encrypt=request.encrypt
        )
        if result['status'] == 'error':
            raise HTTPException(status_code=400, detail=result['message'])
        return result
    
    @app.post("/api/data/retrieve")
    async def retrieve_data(
        request: DataRetrieveRequest,
        agent: AgentEngine = Depends(get_agent),
        user_info: Dict = Depends(get_session_user)
    ):
        result = agent.retrieve_data(
            entry_id=request.entry_id,
            name=request.name
        )
        if result['status'] == 'error':
            raise HTTPException(status_code=404, detail=result['message'])
        return result
    
    @app.post("/api/data/delete")
    async def delete_data(
        request: DataDeleteRequest,
        agent: AgentEngine = Depends(get_agent),
        user_info: Dict = Depends(get_session_user)
    ):
        result = agent.delete_data(request.entry_id)
        if result['status'] == 'error':
            raise HTTPException(status_code=400, detail=result['message'])
        return result
    
    @app.post("/api/data/search")
    async def search_data(
        request: SearchRequest,
        agent: AgentEngine = Depends(get_agent),
        user_info: Dict = Depends(get_session_user)
    ):
        result = agent.search_data(
            query=request.query,
            tags=request.tags,
            content_type=request.content_type
        )
        return result
    
    @app.get("/api/data/list")
    async def list_data(
        agent: AgentEngine = Depends(get_agent),
        user_info: Dict = Depends(get_session_user)
    ):
        result = agent.search_data()
        return result
    
    @app.post("/api/keys/rotate")
    async def rotate_keys(
        agent: AgentEngine = Depends(get_agent),
        user_info: Dict = Depends(get_session_user)
    ):
        result = agent.rotate_keys()
        if result['status'] == 'error':
            raise HTTPException(status_code=400, detail=result['message'])
        return result
    
    @app.get("/api/audit")
    async def get_audit_log(
        since: Optional[float] = None,
        limit: int = 100,
        agent: AgentEngine = Depends(get_agent),
        user_info: Dict = Depends(get_session_user)
    ):
        result = agent.get_audit_log(since=since, limit=limit)
        return result
    
    @app.post("/api/backup")
    async def backup_vault(
        request: BackupRequest,
        agent: AgentEngine = Depends(get_agent),
        user_info: Dict = Depends(get_session_user)
    ):
        result = agent.backup_vault(request.backup_path)
        return result
    
    # ==================== 密钥代理服务API ====================
    
    class AppRegisterRequest(BaseModel):
        app_name: str
        app_type: str = "service"
        permissions: Optional[List[str]] = None
        public_key: Optional[str] = None
    
    class GrantKeyRequest(BaseModel):
        app_id: str
        key_name: str
        key_entry_id: str
        access_type: str = "read"
        expires_in_hours: Optional[int] = None
        max_usage: Optional[int] = None
    
    class KeyRequestRequest(BaseModel):
        app_id: str
        api_key: str
        key_name: str
        response_method: str = "encrypted"
    
    class KeyUseRequest(BaseModel):
        app_id: str
        api_key: str
        key_name: str
        operation: str
        data: Optional[str] = None
    
    @app.post("/api/proxy/register")
    async def register_application(
        request: AppRegisterRequest,
        agent: AgentEngine = Depends(get_agent),
        user_info: Dict = Depends(get_session_user)
    ):
        result = agent.register_application(
            app_name=request.app_name,
            app_type=request.app_type,
            permissions=request.permissions,
            public_key=request.public_key
        )
        if result['status'] == 'error':
            raise HTTPException(status_code=400, detail=result['message'])
        return result
    
    @app.post("/api/proxy/grant")
    async def grant_key(
        request: GrantKeyRequest,
        agent: AgentEngine = Depends(get_agent),
        user_info: Dict = Depends(get_session_user)
    ):
        result = agent.grant_key_to_app(
            app_id=request.app_id,
            key_name=request.key_name,
            key_entry_id=request.key_entry_id,
            access_type=request.access_type,
            expires_in_hours=request.expires_in_hours,
            max_usage=request.max_usage
        )
        if result['status'] == 'error':
            raise HTTPException(status_code=400, detail=result['message'])
        return result
    
    @app.post("/api/proxy/request-key")
    async def request_key(
        request: KeyRequestRequest,
        agent: AgentEngine = Depends(get_agent)
    ):
        result = agent.request_key_for_app(
            app_id=request.app_id,
            api_key=request.api_key,
            key_name=request.key_name,
            response_method=request.response_method
        )
        if result['status'] == 'error':
            raise HTTPException(status_code=403, detail=result['message'])
        return result
    
    @app.post("/api/proxy/use-key")
    async def use_key(
        request: KeyUseRequest,
        agent: AgentEngine = Depends(get_agent)
    ):
        data_bytes = request.data.encode() if request.data else None
        result = agent.use_key_for_app(
            app_id=request.app_id,
            api_key=request.api_key,
            key_name=request.key_name,
            operation=request.operation,
            data=data_bytes
        )
        if result['status'] == 'error':
            raise HTTPException(status_code=403, detail=result['message'])
        return result
    
    @app.get("/api/proxy/apps")
    async def list_apps(
        agent: AgentEngine = Depends(get_agent),
        user_info: Dict = Depends(get_session_user)
    ):
        return agent.list_applications()
    
    @app.delete("/api/proxy/apps/{app_id}")
    async def revoke_app(
        app_id: str,
        agent: AgentEngine = Depends(get_agent),
        user_info: Dict = Depends(get_session_user)
    ):
        result = agent.revoke_app_access(app_id)
        return result
    
    @app.get("/api/settings")
    async def get_settings(
        agent: AgentEngine = Depends(get_agent),
        user_info: Dict = Depends(get_session_user)
    ):
        return agent.get_settings()
    
    @app.post("/api/settings")
    async def update_settings(
        request: Request,
        agent: AgentEngine = Depends(get_agent),
        user_info: Dict = Depends(get_session_user)
    ):
        data = await request.json()
        return agent.update_settings(data)
    
    @app.post("/api/encryption/method")
    async def set_encryption_method(
        request: Request,
        agent: AgentEngine = Depends(get_agent),
        user_info: Dict = Depends(get_session_user)
    ):
        data = await request.json()
        method = data.get('method', 'math_gamma')
        return agent.set_encryption_method(method)
    
    @app.get("/api/proxy/stats")
    async def proxy_stats(
        agent: AgentEngine = Depends(get_agent),
        user_info: Dict = Depends(get_session_user)
    ):
        return agent.get_proxy_stats()
    
    @app.get("/api/proxy/audit")
    async def proxy_audit(
        app_id: Optional[str] = None,
        agent: AgentEngine = Depends(get_agent),
        user_info: Dict = Depends(get_session_user)
    ):
        return agent.get_proxy_audit_log(app_id)
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": str(exc),
                "timestamp": time.time()
            }
        )
    
    return app


app = create_app()
