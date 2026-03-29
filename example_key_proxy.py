"""
隐私信息储存箱智能体 - 完整使用示例
展示如何将智能体作为密钥代理服务使用

场景:
1. 用户将所有密钥存入智能体
2. 注册其他应用/智能体
3. 授权应用访问特定密钥
4. 应用请求密钥或使用密钥执行操作
"""

import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.agent_engine import AgentEngine


def example_key_proxy_workflow():
    """
    完整的密钥代理服务工作流程示例
    """
    print("=" * 70)
    print("隐私信息储存箱智能体 - 密钥代理服务示例")
    print("=" * 70)
    
    # ==================== 步骤1: 初始化智能体 ====================
    print("\n【步骤1】初始化智能体...")
    
    agent = AgentEngine()
    init_result = agent.initialize()
    print(f"  初始化状态: {init_result['status']}")
    print(f"  量子密码模式: {init_result['crypto']['mode']}")
    
    # ==================== 步骤2: 用户注册和登录 ====================
    print("\n【步骤2】用户注册和登录...")
    
    register_result = agent.register_user(
        username="key_owner",
        password="Owner@123456",
        roles=["admin"]
    )
    print(f"  用户注册: {register_result['status']}")
    
    login_result = agent.login("key_owner", "Owner@123456")
    print(f"  用户登录: {login_result['status']}")
    
    # ==================== 步骤3: 存储各类密钥 ====================
    print("\n【步骤3】存储各类密钥到智能体...")
    
    # 存储银行密码
    bank_result = agent.store_data(
        name="招商银行密码",
        data="MyBank@Password123",
        tags=["银行", "密码", "金融"],
        encrypt=True
    )
    print(f"  存储银行密码: {bank_result['status']}")
    
    # 存储API密钥
    api_key_result = agent.store_data(
        name="OpenAI_API_Key",
        data="sk-proj-xxxxxxxxxxxxxxxxxxxxxxxx",
        tags=["API", "OpenAI", "AI服务"],
        encrypt=True
    )
    print(f"  存储API密钥: {api_key_result['status']}")
    
    # 存储数据库密码
    db_result = agent.store_data(
        name="MySQL生产库密码",
        data={
            "host": "192.168.1.100",
            "port": 3306,
            "username": "admin",
            "password": "Db@SecurePass123"
        },
        tags=["数据库", "MySQL", "生产环境"],
        encrypt=True
    )
    print(f"  存储数据库密码: {db_result['status']}")
    
    # 存储SSH私钥
    ssh_key = """-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA0Z3VS5JJcds3xfn/ygWyF8PbnGy0AHB7mSrORbsXxHNHYtML
...
-----END RSA PRIVATE KEY-----"""
    ssh_result = agent.store_data(
        name="服务器SSH私钥",
        data=ssh_key,
        tags=["SSH", "服务器", "私钥"],
        encrypt=True
    )
    print(f"  存储SSH私钥: {ssh_result['status']}")
    
    # ==================== 步骤4: 注册应用/智能体 ====================
    print("\n【步骤4】注册需要访问密钥的应用...")
    
    # 注册一个AI助手应用
    ai_app_result = agent.register_application(
        app_name="AI助手应用",
        app_type="agent",
        permissions=["key:read", "key:use"],
        public_key=None  # 可选：提供应用的公钥用于加密返回的密钥
    )
    print(f"  注册AI助手应用: {ai_app_result['status']}")
    print(f"  应用ID: {ai_app_result['app_id']}")
    print(f"  API密钥: {ai_app_result['api_key'][:20]}...")  # 只显示前20个字符
    
    # 注册一个Web服务
    web_app_result = agent.register_application(
        app_name="Web后端服务",
        app_type="service",
        permissions=["key:read"],
        public_key=None
    )
    print(f"  注册Web服务: {web_app_result['status']}")
    print(f"  应用ID: {web_app_result['app_id']}")
    
    # ==================== 步骤5: 授权应用访问密钥 ====================
    print("\n【步骤5】授权应用访问特定密钥...")
    
    # 授权AI助手访问OpenAI API密钥
    grant_result = agent.grant_key_to_app(
        app_id=ai_app_result['app_id'],
        key_name="OpenAI_API_Key",
        key_entry_id=api_key_result['entry_id'],
        access_type="read",
        expires_in_hours=24,  # 24小时后过期
        max_usage=100  # 最多使用100次
    )
    print(f"  授权AI助手访问OpenAI密钥: {grant_result['status']}")
    
    # 授权Web服务访问数据库密码
    grant_result2 = agent.grant_key_to_app(
        app_id=web_app_result['app_id'],
        key_name="MySQL生产库密码",
        key_entry_id=db_result['entry_id'],
        access_type="read",
        expires_in_hours=168  # 7天
    )
    print(f"  授权Web服务访问数据库密码: {grant_result2['status']}")
    
    # ==================== 步骤6: 应用请求密钥 ====================
    print("\n【步骤6】应用请求密钥（模拟外部应用调用）...")
    
    # AI助手请求OpenAI API密钥
    key_request = agent.request_key_for_app(
        app_id=ai_app_result['app_id'],
        api_key=ai_app_result['api_key'],
        key_name="OpenAI_API_Key",
        response_method="encrypted"  # 返回加密的密钥
    )
    print(f"  AI助手请求密钥: {key_request['status']}")
    if key_request['status'] == 'success':
        print(f"  响应方式: {key_request['response_method']}")
        print(f"  密钥数据已加密返回")
    
    # ==================== 步骤7: 应用使用密钥执行操作（不暴露原始密钥） ====================
    print("\n【步骤7】应用使用密钥执行操作（不暴露原始密钥）...")
    
    # 使用密钥签名数据
    sign_result = agent.use_key_for_app(
        app_id=ai_app_result['app_id'],
        api_key=ai_app_result['api_key'],
        key_name="OpenAI_API_Key",
        operation="sign",
        data=b"important data to sign"
    )
    print(f"  签名操作: {sign_result['status']}")
    if sign_result['status'] == 'success':
        print(f"  签名算法: {sign_result['algorithm']}")
        print(f"  签名结果: {sign_result['signature'][:30]}...")
    
    # 使用密钥加密数据
    encrypt_result = agent.use_key_for_app(
        app_id=ai_app_result['app_id'],
        api_key=ai_app_result['api_key'],
        key_name="OpenAI_API_Key",
        operation="encrypt",
        data=b"sensitive data to encrypt"
    )
    print(f"  加密操作: {encrypt_result['status']}")
    if encrypt_result['status'] == 'success':
        print(f"  加密算法: {encrypt_result['algorithm']}")
    
    # ==================== 步骤8: 查看审计日志 ====================
    print("\n【步骤8】查看密钥访问审计日志...")
    
    audit_result = agent.get_proxy_audit_log()
    print(f"  审计日志条数: {len(audit_result['logs'])}")
    for log in audit_result['logs'][:3]:
        print(f"  - {log['key_name']}: {log['response_method']} @ {log['requested_at']:.0f}")
    
    # ==================== 步骤9: 查看统计信息 ====================
    print("\n【步骤9】查看密钥代理服务统计...")
    
    stats = agent.get_proxy_stats()
    print(f"  注册应用数: {stats['stats']['total_applications']}")
    print(f"  活跃应用数: {stats['stats']['active_applications']}")
    print(f"  授权总数: {stats['stats']['total_grants']}")
    print(f"  今日请求数: {stats['stats']['requests_today']}")
    
    # ==================== 步骤10: 清理 ====================
    print("\n【步骤10】清理和关闭...")
    
    agent.logout()
    agent.shutdown()
    print("  智能体已关闭")
    
    print("\n" + "=" * 70)
    print("示例完成！")
    print("=" * 70)


def example_api_usage():
    """
    通过HTTP API使用智能体的示例
    """
    print("\n" + "=" * 70)
    print("通过HTTP API使用智能体示例")
    print("=" * 70)
    
    code = '''
import requests
import json

BASE_URL = "http://127.0.0.1:8443"

# 1. 用户登录
login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
    "username": "key_owner",
    "password": "Owner@123456"
})
token = login_resp.json()['session_id']
headers = {"Authorization": f"Bearer {token}"}

# 2. 存储密钥
store_resp = requests.post(f"{BASE_URL}/api/data/store", 
    headers=headers,
    json={
        "name": "我的API密钥",
        "data": "sk-xxxxx",
        "tags": ["API"],
        "encrypt": True
    }
)
entry_id = store_resp.json()['entry_id']

# 3. 注册应用
app_resp = requests.post(f"{BASE_URL}/api/proxy/register",
    headers=headers,
    json={
        "app_name": "我的应用",
        "app_type": "service",
        "permissions": ["key:read"]
    }
)
app_id = app_resp.json()['app_id']
api_key = app_resp.json()['api_key']

# 4. 授权应用访问密钥
grant_resp = requests.post(f"{BASE_URL}/api/proxy/grant",
    headers=headers,
    json={
        "app_id": app_id,
        "key_name": "我的API密钥",
        "key_entry_id": entry_id,
        "access_type": "read"
    }
)

# 5. 应用请求密钥（无需用户登录）
key_resp = requests.post(f"{BASE_URL}/api/proxy/request-key",
    json={
        "app_id": app_id,
        "api_key": api_key,
        "key_name": "我的API密钥",
        "response_method": "encrypted"
    }
)
print(f"获取密钥: {key_resp.json()}")
'''
    print(code)


def example_other_agent_integration():
    """
    其他智能体集成示例
    """
    print("\n" + "=" * 70)
    print("其他智能体集成示例")
    print("=" * 70)
    
    code = '''
# 其他智能体（如OpenClaw等）可以这样使用隐私信息储存箱智能体

class OtherAgent:
    def __init__(self, app_id: str, api_key: str, vault_url: str):
        self.app_id = app_id
        self.api_key = api_key
        self.vault_url = vault_url
    
    def get_password(self, key_name: str) -> str:
        """从隐私储存箱获取密码"""
        import requests
        resp = requests.post(f"{self.vault_url}/api/proxy/request-key", json={
            "app_id": self.app_id,
            "api_key": self.api_key,
            "key_name": key_name,
            "response_method": "encrypted"
        })
        if resp.json()['status'] == 'success':
            # 解密获取密码
            return self._decrypt(resp.json()['data'])
        return None
    
    def sign_data(self, key_name: str, data: bytes) -> str:
        """使用密钥签名数据（不暴露原始密钥）"""
        import requests
        resp = requests.post(f"{self.vault_url}/api/proxy/use-key", json={
            "app_id": self.app_id,
            "api_key": self.api_key,
            "key_name": key_name,
            "operation": "sign",
            "data": data.decode()
        })
        return resp.json().get('signature')

# 使用示例
agent = OtherAgent(
    app_id="app_xxxxx",
    api_key="sk_xxxxx",
    vault_url="http://127.0.0.1:8443"
)

# 获取银行密码
bank_password = agent.get_password("招商银行密码")

# 使用密钥签名
signature = agent.sign_data("OpenAI_API_Key", b"重要数据")
'''
    print(code)


if __name__ == "__main__":
    example_key_proxy_workflow()
    example_api_usage()
    example_other_agent_integration()
