"""
隐私信息储存箱智能体使用示例
演示如何通过Python代码使用智能体的各项功能
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.agent_engine import AgentEngine


def example_basic_usage():
    """
    基本使用示例
    """
    print("=" * 60)
    print("示例1: 基本使用流程")
    print("=" * 60)
    
    agent = AgentEngine()
    
    init_result = agent.initialize()
    print(f"初始化结果: {init_result['status']}")
    
    register_result = agent.register_user(
        username="alice",
        password="SecurePass@123",
        roles=["user"],
        enable_mfa=False
    )
    print(f"用户注册: {register_result}")
    
    login_result = agent.login("alice", "SecurePass@123")
    print(f"用户登录: {login_result['status']}")
    
    if login_result['status'] == 'success':
        store_result = agent.store_data(
            name="我的密码",
            data="my_secret_password_123",
            tags=["密码", "重要"],
            encrypt=True
        )
        print(f"存储数据: {store_result}")
        
        retrieve_result = agent.retrieve_data(name="我的密码")
        print(f"检索数据: {retrieve_result}")
        
        agent.logout()
    
    agent.shutdown()


def example_store_sensitive_info():
    """
    存储敏感信息示例
    """
    print("\n" + "=" * 60)
    print("示例2: 存储各类敏感信息")
    print("=" * 60)
    
    agent = AgentEngine()
    agent.initialize()
    agent.register_user("bob", "Bob@456")
    agent.login("bob", "Bob@456")
    
    bank_card = {
        "card_type": "信用卡",
        "number": "6222 **** **** 8888",
        "cvv": "***",
        "expiry": "12/2028",
        "bank": "中国银行"
    }
    agent.store_data("银行卡信息", bank_card, tags=["金融", "银行卡"])
    
    id_card = {
        "type": "身份证",
        "number": "110************1234",
        "name": "张三",
        "issue_date": "2020-01-01"
    }
    agent.store_data("身份证信息", id_card, tags=["证件", "重要"])
    
    wifi_password = {
        "ssid": "MyHomeWiFi",
        "password": "w1f1_p@ssw0rd",
        "security": "WPA3"
    }
    agent.store_data("家庭WiFi", wifi_password, tags=["网络", "密码"])
    
    crypto_wallet = {
        "type": "比特币钱包",
        "address": "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
        "seed_phrase": "word1 word2 word3 ... word12"
    }
    agent.store_data("加密货币钱包", crypto_wallet, tags=["金融", "加密货币"])
    
    search_result = agent.search_data(tags=["金融"])
    print(f"\n金融相关数据: {search_result['count']} 条")
    for item in search_result['results']:
        print(f"  - {item['name']}")
    
    agent.logout()
    agent.shutdown()


def example_quantum_crypto():
    """
    量子密码功能示例
    """
    print("\n" + "=" * 60)
    print("示例3: 量子密码功能")
    print("=" * 60)
    
    agent = AgentEngine()
    init_result = agent.initialize()
    
    print(f"\nQKD状态: {init_result['crypto']['qkd_stats']}")
    print(f"密钥哈希: {init_result['crypto']['master_key_hash']}")
    
    agent.register_user("crypto_user", "Crypto@789")
    agent.login("crypto_user", "Crypto@789")
    
    agent.store_data("测试数据", "这是一条测试数据")
    
    print("\n执行密钥轮换...")
    rotate_result = agent.rotate_keys()
    print(f"轮换结果: {rotate_result}")
    
    retrieve_result = agent.retrieve_data(name="测试数据")
    print(f"轮换后数据检索: {retrieve_result['status']}")
    
    agent.logout()
    agent.shutdown()


def example_access_control():
    """
    访问控制示例
    """
    print("\n" + "=" * 60)
    print("示例4: 访问控制和角色管理")
    print("=" * 60)
    
    agent = AgentEngine()
    agent.initialize()
    
    agent.register_user("admin_user", "Admin@123", roles=["admin"])
    agent.register_user("viewer_user", "Viewer@123", roles=["viewer"])
    
    agent.login("admin_user", "Admin@123")
    agent.store_data("管理员数据", "只有管理员能看到", tags=["机密"])
    agent.logout()
    
    agent.login("viewer_user", "Viewer@123")
    search_result = agent.search_data()
    print(f"viewer用户可见数据: {search_result['count']} 条")
    agent.logout()
    
    agent.shutdown()


def example_audit_logging():
    """
    审计日志示例
    """
    print("\n" + "=" * 60)
    print("示例5: 审计日志")
    print("=" * 60)
    
    agent = AgentEngine()
    agent.initialize()
    
    agent.register_user("audit_user", "Audit@123")
    agent.login("audit_user", "Audit@123")
    
    for i in range(3):
        agent.store_data(f"数据_{i}", f"内容_{i}")
    
    audit_result = agent.get_audit_log()
    print(f"\n审计日志条数: {audit_result['count']}")
    
    event_types = {}
    for event in audit_result['events']:
        et = event['event_type']
        event_types[et] = event_types.get(et, 0) + 1
    
    print("事件统计:")
    for et, count in event_types.items():
        print(f"  - {et}: {count} 次")
    
    agent.logout()
    agent.shutdown()


def example_api_usage():
    """
    API使用示例 (需要先启动API服务)
    """
    print("\n" + "=" * 60)
    print("示例6: 通过API使用智能体")
    print("=" * 60)
    
    import requests
    import json
    
    base_url = "http://127.0.0.1:8443"
    
    try:
        response = requests.get(f"{base_url}/")
        print(f"API状态: {response.json()}")
        
        register_data = {
            "username": "api_user",
            "password": "ApiUser@123",
            "roles": ["user"],
            "enable_mfa": False
        }
        response = requests.post(
            f"{base_url}/api/auth/register",
            json=register_data
        )
        print(f"注册结果: {response.json()}")
        
        login_data = {
            "username": "api_user",
            "password": "ApiUser@123"
        }
        response = requests.post(
            f"{base_url}/api/auth/login",
            json=login_data
        )
        login_result = response.json()
        print(f"登录结果: {login_result}")
        
        if login_result['status'] == 'success':
            token = login_result['session_id']
            headers = {"Authorization": f"Bearer {token}"}
            
            store_data = {
                "name": "API存储的数据",
                "data": {"key": "value"},
                "tags": ["api", "test"],
                "encrypt": True
            }
            response = requests.post(
                f"{base_url}/api/data/store",
                json=store_data,
                headers=headers
            )
            print(f"存储结果: {response.json()}")
            
            response = requests.post(
                f"{base_url}/api/auth/logout",
                headers=headers
            )
            print(f"登出结果: {response.json()}")
    
    except requests.exceptions.ConnectionError:
        print("无法连接到API服务，请先运行: python main.py --mode api")


if __name__ == "__main__":
    print("\n隐私信息储存箱智能体 - 使用示例\n")
    
    example_basic_usage()
    example_store_sensitive_info()
    example_quantum_crypto()
    example_access_control()
    example_audit_logging()
    
    print("\n" + "=" * 60)
    print("所有示例执行完成!")
    print("=" * 60)
