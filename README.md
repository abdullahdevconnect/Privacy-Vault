# 隐私信息储存箱

一个安全、本地运行的密钥管理智能体，可与OpenClaw等AI智能体搭配使用，解决AI应用访问敏感信息的安全问题。

## 特性

- **本地运行** - 所有数据存储在本地，不上传云端
- **多种加密** - 支持伽马函数+梅森素数、混沌映射、格基密码、AES-256等多种加密方式
- **细粒度授权** - 可控制应用访问权限、有效期、使用次数
- **代理操作** - 应用可使用密钥签名/加密，但不暴露密钥本身
- **审计日志** - 完整记录所有访问操作
- **多种登录方式** - 支持密码、手机验证码、银行卡、API密钥等

## 快速开始

### 环境要求

- Python 3.9+
- Windows/Linux/macOS

### 安装

```bash
# 克隆仓库
git clone https://github.com/your-username/privacy-vault.git
cd privacy-vault

# 安装依赖
pip install -r requirements.txt

# 启动服务
python main.py --mode api --port 8443
```

### 访问Web界面

打开浏览器访问：http://127.0.0.1:8443/ui

## 使用指南

### 1. 注册账户

首次使用需要注册账户，设置强密码并可选启用多因素认证(MFA)。

### 2. 添加密钥

支持多种密钥类型：
- 用户名+密码
- 手机号+验证码
- 邮箱+验证码
- 扫码登录
- 第三方登录
- 银行卡
- API密钥

### 3. 注册应用

为OpenClaw等应用注册访问凭据：
1. 进入"应用授权"页面
2. 点击"注册应用"
3. 输入应用名称和权限
4. 获取app_id和api_key

### 4. 授权访问

为应用授权访问特定密钥：
1. 点击应用卡片上的"授权"按钮
2. 选择要授权的密钥
3. 设置访问类型和有效期
4. 确认授权

### 5. 应用集成

在OpenClaw中配置：

```python
from example_app_usage import PrivacyVaultClient

client = PrivacyVaultClient("http://127.0.0.1:8443")
client.set_credentials("app_xxx", "sk_xxx")

# 获取密钥
result = client.request_key("华为账号")

# 代理操作（不暴露密钥）
signature = client.sign_data("我的密钥", b"要签名的数据")
```

## 安全特性

### 加密方法

| 方法 | 说明 | 安全级别 |
|------|------|---------|
| 伽马函数+梅森素数 | 数学函数扩展密钥空间 | 高 |
| 混沌映射加密 | Logistic+Henon混沌映射 | 高 |
| 格基密码 | 抗量子计算攻击 | 很高 |
| 量子密码模拟 | BB84协议模拟 | 很高 |
| AES-256-GCM | NIST标准 | 高 |

### 代理操作模式

应用可以使用密钥执行操作，但不获取密钥本身：

```
应用请求签名 → 隐私储存箱使用密钥签名 → 返回签名结果
（应用从未看到密钥）
```

### 真实量子密钥（可选）

如需使用真实量子密钥，需要以下设备：
- ID Quantique Clavis系列（瑞士）- 约$50,000+
- QuantumCTek QKD系统（中国）- 约¥30万+
- Toshiba QKD系统（日本）- 约$100,000+

## 项目结构

```
privacy-vault/
├── api/              # API路由
├── auth/             # 认证授权
├── core/             # 核心引擎
├── crypto/           # 加密模块
├── sandbox/          # 沙盒隔离
├── static/           # Web UI
├── main.py           # 入口文件
├── requirements.txt  # 依赖
└── README.md         # 说明文档
```

## API文档

### 认证

```bash
# 注册
POST /api/auth/register
{
    "username": "user",
    "password": "password123",
    "enable_mfa": true
}

# 登录
POST /api/auth/login
{
    "username": "user",
    "password": "password123",
    "mfa_code": "123456"
}
```

### 密钥管理

```bash
# 存储密钥
POST /api/data/store
{
    "name": "华为账号",
    "data": "{\"phone\":\"13800138000\"}",
    "encrypt": true
}

# 获取密钥
POST /api/data/retrieve
{
    "entry_id": "entry_xxx"
}

# 删除密钥
POST /api/data/delete
{
    "entry_id": "entry_xxx"
}
```

### 应用授权

```bash
# 注册应用
POST /api/proxy/apps
{
    "app_name": "OpenClaw",
    "app_type": "agent",
    "permissions": ["key:read", "key:use"]
}

# 授权密钥
POST /api/proxy/grant
{
    "app_id": "app_xxx",
    "key_name": "华为账号",
    "access_type": "read"
}

# 请求密钥
POST /api/proxy/request-key
{
    "app_id": "app_xxx",
    "api_key": "sk_xxx",
    "key_name": "华为账号"
}
```

## 与OpenClaw搭配使用

OpenClaw是一个AI智能体，但它存在安全问题：密钥散落各处、无访问控制、无审计追踪。

隐私储存箱解决了这些问题：

| 问题 | 解决方案 |
|------|---------|
| 密钥散落 | 集中管理 |
| 明文存储 | 强加密存储 |
| 无访问控制 | 细粒度授权 |
| 无审计 | 完整日志 |
| AI直接获取密钥 | 代理操作模式 |

## 开发

```bash
# 运行测试
python test_agent.py

# 检查代码
python check_project.py
```

## 贡献

欢迎提交Issue和Pull Request！

## 许可证

MIT License

## 作者

Privacy Vault Team

## 致谢

感谢所有贡献者和用户的支持！
