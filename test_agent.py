"""
测试脚本 - 验证智能体功能
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.agent_engine import AgentEngine

def test_agent():
    print("=" * 60)
    print("测试隐私信息储存箱智能体")
    print("=" * 60)
    
    # 初始化
    print("\n1. 初始化智能体...")
    agent = AgentEngine()
    result = agent.initialize()
    print(f"   初始化结果: {result['status']}")
    
    # 注册用户
    print("\n2. 注册测试用户...")
    result = agent.register_user("testuser", "Test@123456")
    print(f"   注册结果: {result}")
    
    # 登录
    print("\n3. 用户登录...")
    result = agent.login("testuser", "Test@123456")
    print(f"   登录结果: {result}")
    
    if result['status'] == 'success':
        # 存储数据
        print("\n4. 存储测试数据...")
        result = agent.store_data(
            name="测试密码",
            data="这是测试密码内容123",
            tags=["测试", "密码"],
            encrypt=True
        )
        print(f"   存储结果: {result}")
        
        if result['status'] == 'success':
            # 检索数据
            print("\n5. 检索数据...")
            result = agent.retrieve_data(name="测试密码")
            print(f"   检索结果: {result}")
        
        # 登出
        print("\n6. 用户登出...")
        result = agent.logout()
        print(f"   登出结果: {result}")
    
    # 关闭
    print("\n7. 关闭智能体...")
    agent.shutdown()
    print("   完成!")
    
    print("\n" + "=" * 60)
    print("用户数据存储位置: ./vault_data/auth/")
    print("=" * 60)

if __name__ == "__main__":
    test_agent()
