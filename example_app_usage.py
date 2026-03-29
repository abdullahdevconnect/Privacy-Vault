"""
其他应用（如OpenClaw）使用隐私储存箱智能体的完整示例

工作流程:
1. 用户在隐私储存箱中注册应用，获取app_id和api_key
2. 用户授权该应用访问特定密钥
3. 应用使用app_id和api_key请求密钥
4. 隐私储存箱验证后返回加密的密钥数据
"""

import requests
import json
import base64


class PrivacyVaultClient:
    """
    隐私储存箱客户端
    供其他应用（如OpenClaw）使用
    """
    
    def __init__(self, vault_url: str = "http://127.0.0.1:8443"):
        self.vault_url = vault_url
        self.app_id = None
        self.api_key = None
    
    def set_credentials(self, app_id: str, api_key: str) -> None:
        """
        设置应用凭据
        这些凭据由用户在隐私储存箱中注册应用后获得
        """
        self.app_id = app_id
        self.api_key = api_key
    
    def request_key(self, key_name: str) -> dict:
        """
        请求密钥
        
        参数:
            key_name: 密钥名称（如"华为账号"、"微信密码"）
        
        返回:
            {
                'status': 'success',
                'data': {...},  # 密钥数据
                'login_type': 'password' | 'phone_code' | ...
            }
        """
        if not self.app_id or not self.api_key:
            return {'status': 'error', 'message': '未设置应用凭据'}
        
        response = requests.post(
            f"{self.vault_url}/api/proxy/request-key",
            json={
                "app_id": self.app_id,
                "api_key": self.api_key,
                "key_name": key_name,
                "response_method": "encrypted"
            }
        )
        
        result = response.json()
        
        if result.get('status') == 'success':
            # 解析密钥数据
            data = result.get('data', '')
            if data:
                try:
                    # 数据是base64编码的JSON
                    decoded = base64.b64decode(data).decode('utf-8')
                    key_data = json.loads(decoded)
                    return {
                        'status': 'success',
                        'key_data': key_data,
                        'login_type': key_data.get('login_type', 'password')
                    }
                except Exception as e:
                    return {
                        'status': 'success',
                        'raw_data': data,
                        'error': f'解析失败: {e}'
                    }
        
        return result
    
    def get_password(self, key_name: str) -> tuple:
        """
        获取用户名和密码（便捷方法）
        
        返回: (username, password) 或 (None, None)
        """
        result = self.request_key(key_name)
        
        if result.get('status') != 'success':
            return None, None
        
        key_data = result.get('key_data', {})
        login_type = key_data.get('login_type', 'password')
        
        if login_type == 'password':
            return key_data.get('username'), key_data.get('password')
        elif login_type == 'phone_code':
            return key_data.get('phone'), None  # 手机号登录无固定密码
        elif login_type == 'bank_card':
            return key_data.get('cardNumber'), key_data.get('cardPassword')
        else:
            return key_data.get('account'), key_data.get('password')
    
    def get_phone_login_info(self, key_name: str) -> dict:
        """
        获取手机号登录信息
        
        返回: {'phone': '...', 'code_method': '...'}
        """
        result = self.request_key(key_name)
        
        if result.get('status') != 'success':
            return {}
        
        key_data = result.get('key_data', {})
        
        return {
            'phone': key_data.get('phone', ''),
            'code_method': key_data.get('codeMethod', ''),
            'login_type': 'phone_code'
        }
    
    def get_bank_card_info(self, key_name: str) -> dict:
        """
        获取银行卡信息
        
        返回: {'card_number': '...', 'holder': '...', ...}
        """
        result = self.request_key(key_name)
        
        if result.get('status') != 'success':
            return {}
        
        key_data = result.get('key_data', {})
        
        return {
            'card_number': key_data.get('cardNumber', ''),
            'card_holder': key_data.get('cardHolder', ''),
            'bank_name': key_data.get('bankName', ''),
            'password': key_data.get('cardPassword', ''),
            'cvv': key_data.get('cvv', '')
        }
    
    def use_key_for_operation(
        self,
        key_name: str,
        operation: str,
        data: bytes = None
    ) -> dict:
        """
        使用密钥执行操作（不获取原始密钥）
        
        操作类型:
        - sign: 使用密钥签名数据
        - encrypt: 使用密钥加密数据
        - decrypt: 使用密钥解密数据
        
        这样可以避免密钥泄露给应用
        """
        if not self.app_id or not self.api_key:
            return {'status': 'error', 'message': '未设置应用凭据'}
        
        request_data = {
            "app_id": self.app_id,
            "api_key": self.api_key,
            "key_name": key_name,
            "operation": operation
        }
        
        if data:
            request_data["data"] = base64.b64encode(data).decode()
        
        response = requests.post(
            f"{self.vault_url}/api/proxy/use-key",
            json=request_data
        )
        
        return response.json()


# ==================== 使用示例 ====================

def example_openclaw_integration():
    """
    OpenClaw智能体集成示例
    """
    print("=" * 60)
    print("OpenClaw智能体使用隐私储存箱示例")
    print("=" * 60)
    
    # 1. 初始化客户端
    client = PrivacyVaultClient("http://127.0.0.1:8443")
    
    # 2. 设置凭据（这些由用户在隐私储存箱中注册后提供）
    # 用户操作：
    # - 登录隐私储存箱Web界面
    # - 进入"应用授权"页面
    # - 点击"注册应用"
    # - 输入应用名称"OpenClaw"
    # - 获得app_id和api_key
    client.set_credentials(
        app_id="app_xxxxxxxx",  # 用户提供的应用ID
        api_key="sk_xxxxxxxx"   # 用户提供的API密钥
    )
    
    # 3. 用户还需要在隐私储存箱中授权OpenClaw访问特定密钥
    # 用户操作：
    # - 在"应用授权"页面找到"OpenClaw"
    # - 点击"授权"
    # - 选择要授权的密钥（如"华为账号"）
    # - 设置访问类型和有效期
    
    # 4. OpenClaw请求密钥
    print("\n请求华为账号密钥...")
    result = client.request_key("华为账号")
    
    if result.get('status') == 'success':
        key_data = result.get('key_data', {})
        login_type = key_data.get('login_type')
        
        print(f"登录方式: {login_type}")
        
        if login_type == 'phone_code':
            print(f"手机号: {key_data.get('phone')}")
            print(f"验证码获取方式: {key_data.get('codeMethod')}")
            print("\n使用流程:")
            print("1. 打开华为登录页面")
            print("2. 输入手机号:", key_data.get('phone'))
            print("3. 点击获取验证码")
            print("4. 等待短信验证码")
            print("5. 输入验证码完成登录")
        
        elif login_type == 'password':
            print(f"用户名: {key_data.get('username')}")
            print(f"密码: {key_data.get('password')}")
    else:
        print(f"获取失败: {result.get('message')}")
    
    # 5. 使用便捷方法获取密码
    print("\n获取微信账号密码...")
    username, password = client.get_password("微信密码")
    if username:
        print(f"用户名: {username}")
        print(f"密码: {password}")
    
    # 6. 安全操作（不暴露密钥）
    print("\n使用密钥签名数据（不获取原始密钥）...")
    sign_result = client.use_key_for_operation(
        key_name="API密钥",
        operation="sign",
        data=b"important data to sign"
    )
    if sign_result.get('status') == 'success':
        print(f"签名结果: {sign_result.get('signature')[:30]}...")


def example_api_direct_usage():
    """
    直接API调用示例
    """
    print("\n" + "=" * 60)
    print("直接API调用示例")
    print("=" * 60)
    
    code = '''
import requests
import json
import base64

VAULT_URL = "http://127.0.0.1:8443"

# 步骤1: 用户在Web界面注册应用后获得这些凭据
APP_ID = "app_xxxxxxxx"
API_KEY = "sk_xxxxxxxx"

# 步骤2: 请求密钥
response = requests.post(f"{VAULT_URL}/api/proxy/request-key", json={
    "app_id": APP_ID,
    "api_key": API_KEY,
    "key_name": "华为账号",
    "response_method": "encrypted"
})

result = response.json()

if result["status"] == "success":
    # 解析密钥数据
    data_base64 = result["data"]
    data_json = base64.b64decode(data_base64).decode()
    key_data = json.loads(data_json)
    
    print(f"登录方式: {key_data.get('login_type')}")
    print(f"手机号: {key_data.get('phone')}")
    print(f"验证码获取方式: {key_data.get('codeMethod')}")
else:
    print(f"错误: {result['message']}")
'''
    print(code)


def example_security_best_practices():
    """
    安全最佳实践
    """
    print("\n" + "=" * 60)
    print("安全最佳实践")
    print("=" * 60)
    
    print("""
1. 凭据管理
   - app_id和api_key应该安全存储（不要硬编码）
   - 建议使用环境变量或配置文件
   - 定期轮换API密钥

2. 权限最小化
   - 只请求必要的权限（如只读）
   - 设置授权过期时间
   - 限制访问次数

3. 安全操作
   - 优先使用use_key_for_operation而不是直接获取密钥
   - 这样密钥不会暴露给应用

4. 审计监控
   - 定期检查审计日志
   - 发现异常访问立即撤销授权

5. 示例配置
   ```python
   # config.py
   import os
   
   VAULT_CONFIG = {
       'url': os.environ.get('VAULT_URL', 'http://127.0.0.1:8443'),
       'app_id': os.environ.get('VAULT_APP_ID'),
       'api_key': os.environ.get('VAULT_API_KEY')
   }
   ```
""")


if __name__ == "__main__":
    example_openclaw_integration()
    example_api_direct_usage()
    example_security_best_practices()
