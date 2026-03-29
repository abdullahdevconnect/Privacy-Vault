#!/usr/bin/env python3
"""
隐私信息储存箱智能体 - 主入口
Privacy Vault Agent - Main Entry Point

使用方法:
    1. 命令行模式: python main.py --mode cli
    2. API服务模式: python main.py --mode api --port 8443
    3. 交互模式: python main.py --mode interactive
"""

import os
import sys
import argparse
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.agent_engine import AgentEngine
from core.config import Config


def print_banner():
    banner = """
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║     ██████╗ ██████╗ ███████╗ █████╗ ████████╗██╗██╗   ██╗   ║
    ║    ██╔════╝ ██╔══██╗██╔════╝██╔══██╗╚══██╔══╝██║██║   ██║   ║
    ║    ██║      ██████╔╝███████╗███████║   ██║   ██║██║   ██║   ║
    ║    ██║      ██╔══██╗╚════██║██╔══██║   ██║   ██║██║   ██║   ║
    ║    ╚██████╗ ██║  ██║███████║██║  ██║   ██║   ██║╚██████╔╝   ║
    ║     ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝   ╚═╝   ╚═╝ ╚═════╝    ║
    ║                                                               ║
    ║            Privacy Vault Agent - 量子密码保护                 ║
    ║                    Version 1.0.0                              ║
    ╚═══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def run_cli_mode(config_path: str = None):
    """
    命令行模式 - 执行单个命令
    """
    print_banner()
    print("\n[CLI模式] 初始化智能体...")
    
    agent = AgentEngine(config_path)
    result = agent.initialize()
    
    if result['status'] != 'success':
        print(f"初始化失败: {result}")
        return 1
    
    print(f"初始化成功: {result}")
    print("\n可用命令:")
    print("  register <username> <password>  - 注册用户")
    print("  login <username> <password>     - 登录")
    print("  store <name> <data>             - 存储数据")
    print("  retrieve <name>                 - 检索数据")
    print("  list                            - 列出所有数据")
    print("  status                          - 查看状态")
    print("  exit                            - 退出")
    
    while True:
        try:
            cmd_input = input("\n> ").strip().split()
            if not cmd_input:
                continue
            
            cmd = cmd_input[0].lower()
            args = cmd_input[1:]
            
            if cmd == 'exit' or cmd == 'quit':
                agent.shutdown()
                print("再见!")
                break
            
            elif cmd == 'status':
                status = agent.get_status()
                print(f"\n状态: {status}")
            
            elif cmd == 'register':
                if len(args) < 2:
                    print("用法: register <username> <password>")
                    continue
                result = agent.register_user(args[0], args[1])
                print(f"注册结果: {result}")
            
            elif cmd == 'login':
                if len(args) < 2:
                    print("用法: login <username> <password>")
                    continue
                result = agent.login(args[0], args[1])
                print(f"登录结果: {result}")
            
            elif cmd == 'store':
                if len(args) < 2:
                    print("用法: store <name> <data>")
                    continue
                result = agent.store_data(args[0], ' '.join(args[1:]))
                print(f"存储结果: {result}")
            
            elif cmd == 'retrieve':
                if len(args) < 1:
                    print("用法: retrieve <name>")
                    continue
                result = agent.retrieve_data(name=args[0])
                print(f"检索结果: {result}")
            
            elif cmd == 'list':
                result = agent.search_data()
                print(f"\n数据列表 ({result['count']} 条):")
                for item in result.get('results', []):
                    print(f"  - {item['name']} ({item['size']} bytes)")
            
            elif cmd == 'delete':
                if len(args) < 1:
                    print("用法: delete <entry_id>")
                    continue
                result = agent.delete_data(args[0])
                print(f"删除结果: {result}")
            
            elif cmd == 'rotate':
                result = agent.rotate_keys()
                print(f"密钥轮换结果: {result}")
            
            else:
                print(f"未知命令: {cmd}")
        
        except KeyboardInterrupt:
            print("\n\n正在退出...")
            agent.shutdown()
            break
        except Exception as e:
            print(f"错误: {e}")
    
    return 0


def run_api_mode(config_path: str = None, host: str = "127.0.0.1", port: int = 8443):
    """
    API服务模式 - 启动REST API服务器
    """
    print_banner()
    print(f"\n[API模式] 启动服务器...")
    print(f"地址: http://{host}:{port}")
    print(f"API文档: http://{host}:{port}/docs")
    
    import uvicorn
    from api.routes import create_app
    
    app = create_app(config_path)
    uvicorn.run(app, host=host, port=port)


def run_interactive_mode(config_path: str = None):
    """
    交互模式 - 提供交互式演示
    """
    print_banner()
    print("\n[交互模式] 启动隐私信息储存箱智能体演示...\n")
    
    agent = AgentEngine(config_path)
    result = agent.initialize()
    
    if result['status'] != 'success':
        print(f"初始化失败: {result}")
        return 1
    
    print("=" * 60)
    print("智能体初始化成功!")
    print("=" * 60)
    print(f"\n量子密码状态:")
    print(f"  - 密钥哈希: {result['crypto']['master_key_hash']}")
    print(f"  - QKD状态: {'检测到窃听' if result['crypto']['qkd_stats']['eve_detected'] else '安全'}")
    print(f"  - 错误率: {result['crypto']['qkd_stats']['error_rate']:.2%}")
    
    print("\n" + "=" * 60)
    print("演示1: 用户注册和登录")
    print("=" * 60)
    
    register_result = agent.register_user(
        username="demo_user",
        password="Demo@123456",
        roles=["user"],
        enable_mfa=False
    )
    print(f"\n注册结果: {register_result}")
    
    login_result = agent.login("demo_user", "Demo@123456")
    print(f"登录结果: {login_result}")
    
    print("\n" + "=" * 60)
    print("演示2: 存储隐私数据")
    print("=" * 60)
    
    sensitive_data = {
        "type": "credit_card",
        "number": "****-****-****-1234",
        "holder": "张三",
        "expiry": "12/2028"
    }
    
    store_result = agent.store_data(
        name="我的银行卡信息",
        data=sensitive_data,
        tags=["金融", "重要"],
        encrypt=True
    )
    print(f"\n存储结果: {store_result}")
    
    print("\n" + "=" * 60)
    print("演示3: 检索隐私数据")
    print("=" * 60)
    
    retrieve_result = agent.retrieve_data(name="我的银行卡信息")
    print(f"\n检索结果: {retrieve_result}")
    
    print("\n" + "=" * 60)
    print("演示4: 搜索数据")
    print("=" * 60)
    
    search_result = agent.search_data(tags=["金融"])
    print(f"\n搜索结果: {search_result}")
    
    print("\n" + "=" * 60)
    print("演示5: 查看审计日志")
    print("=" * 60)
    
    audit_result = agent.get_audit_log()
    print(f"\n审计日志条数: {audit_result['count']}")
    for event in audit_result['events'][:3]:
        print(f"  - {event['event_type']}: {event['success']}")
    
    print("\n" + "=" * 60)
    print("演示6: 密钥轮换")
    print("=" * 60)
    
    rotate_result = agent.rotate_keys()
    print(f"\n密钥轮换结果: {rotate_result}")
    
    print("\n" + "=" * 60)
    print("演示完成!")
    print("=" * 60)
    
    agent.shutdown()
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="隐私信息储存箱智能体 - Privacy Vault Agent"
    )
    parser.add_argument(
        '--mode', '-m',
        choices=['cli', 'api', 'interactive'],
        default='interactive',
        help='运行模式: cli(命令行), api(API服务), interactive(交互演示)'
    )
    parser.add_argument(
        '--config', '-c',
        default='config.yaml',
        help='配置文件路径'
    )
    parser.add_argument(
        '--host',
        default='127.0.0.1',
        help='API服务监听地址'
    )
    parser.add_argument(
        '--port', '-p',
        type=int,
        default=8443,
        help='API服务监听端口'
    )
    
    args = parser.parse_args()
    
    if args.mode == 'cli':
        return run_cli_mode(args.config)
    elif args.mode == 'api':
        return run_api_mode(args.config, args.host, args.port)
    else:
        return run_interactive_mode(args.config)


if __name__ == "__main__":
    sys.exit(main())
