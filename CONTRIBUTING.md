# 贡献指南

感谢你对隐私信息储存箱项目的关注！

## 如何贡献

### 报告问题

如果你发现了bug或有功能建议，请：
1. 在GitHub Issues中搜索是否已有相关问题
2. 如果没有，创建新的Issue，详细描述问题或建议

### 提交代码

1. Fork本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建Pull Request

### 代码规范

- Python代码遵循PEP 8规范
- 使用有意义的变量名和函数名
- 添加必要的注释和文档字符串
- 编写单元测试

### 安全问题

如果你发现了安全漏洞，请**不要**在公开的Issue中报告。请发送邮件到安全团队。

## 开发环境设置

```bash
# 克隆仓库
git clone https://github.com/your-username/privacy-vault.git
cd privacy-vault

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 运行测试
python test_agent.py
```

## 项目结构

```
privacy-vault/
├── api/              # API路由
├── auth/             # 认证授权
├── core/             # 核心引擎
├── crypto/           # 加密模块
├── sandbox/          # 沙盒隔离
├── static/           # Web UI
├── tests/            # 测试文件
├── main.py           # 入口文件
└── requirements.txt  # 依赖
```

## 许可证

提交代码即表示你同意你的代码将以MIT许可证发布。
