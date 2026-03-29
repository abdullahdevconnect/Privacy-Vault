/**
 * 隐私信息储存箱智能体 - Web UI JavaScript
 */

// ==================== 全局变量 ====================
const API_BASE = '';
let authToken = null;
let currentUser = null;

// ==================== 工具函数 ====================
function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icons = {
        success: 'fas fa-check-circle',
        error: 'fas fa-times-circle',
        warning: 'fas fa-exclamation-circle'
    };
    
    toast.innerHTML = `
        <i class="${icons[type]}"></i>
        <span class="toast-message">${message}</span>
    `;
    
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideIn 0.3s ease reverse';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function copyToClipboard(elementId) {
    const element = document.getElementById(elementId);
    const text = element.textContent;
    
    navigator.clipboard.writeText(text).then(() => {
        showToast('已复制到剪贴板', 'success');
    }).catch(() => {
        showToast('复制失败', 'error');
    });
}

function formatTime(timestamp) {
    const date = new Date(timestamp * 1000);
    return date.toLocaleString('zh-CN');
}

function formatDate(timestamp) {
    const date = new Date(timestamp * 1000);
    return date.toLocaleDateString('zh-CN');
}

// ==================== API调用 ====================
async function apiCall(endpoint, method = 'GET', data = null, requireAuth = true) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json'
        }
    };
    
    if (requireAuth && authToken) {
        options.headers['Authorization'] = `Bearer ${authToken}`;
    }
    
    if (data) {
        options.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, options);
        const result = await response.json();
        
        if (!response.ok) {
            const error = new Error(result.detail || result.message || '请求失败');
            error.data = result;
            throw error;
        }
        
        return result;
    } catch (error) {
        console.error('API调用错误:', error);
        throw error;
    }
}

// ==================== 登录相关 ====================
document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;
    const mfaCode = document.getElementById('login-mfa').value || null;
    
    try {
        const result = await apiCall('/api/auth/login', 'POST', {
            username,
            password,
            mfa_code: mfaCode
        }, false);
        
        if (result.status === 'success') {
            authToken = result.session_id;
            currentUser = {
                id: result.user_id,
                username: result.username,
                roles: result.roles
            };
            
            localStorage.setItem('authToken', authToken);
            localStorage.setItem('currentUser', JSON.stringify(currentUser));
            
            document.getElementById('current-username').textContent = currentUser.username;
            
            // 重置登录表单
            document.getElementById('login-form').reset();
            document.querySelector('.mfa-group').style.display = 'none';
            
            document.getElementById('login-page').classList.remove('active');
            document.getElementById('main-page').classList.add('active');
            
            showToast(`欢迎回来，${currentUser.username}！`, 'success');
            loadDashboard();
        }
    } catch (error) {
        const errorMsg = error.message || '';
        
        // 检查是否需要MFA验证码
        if (errorMsg.includes('MFA') || errorMsg.includes('验证码') || errorMsg.includes('mfa')) {
            document.querySelector('.mfa-group').style.display = 'flex';
            document.getElementById('login-mfa').focus();
            showToast('请输入手机认证器App生成的6位动态验证码', 'warning');
        } else {
            showToast(errorMsg, 'error');
        }
    }
});

// 注册
document.getElementById('register-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const username = document.getElementById('reg-username').value;
    const password = document.getElementById('reg-password').value;
    const passwordConfirm = document.getElementById('reg-password-confirm').value;
    const enableMfa = document.getElementById('reg-mfa').checked;
    
    if (password !== passwordConfirm) {
        showToast('两次输入的密码不一致', 'error');
        return;
    }
    
    // 密码强度检查
    if (password.length < 8) {
        showToast('密码至少需要8个字符', 'error');
        return;
    }
    
    try {
        const result = await apiCall('/api/auth/register', 'POST', {
            username,
            password,
            enable_mfa: enableMfa
        }, false);
        
        if (result.status === 'success') {
            // 重置表单
            document.getElementById('register-form').reset();
            // 关闭弹窗
            closeModal('register-modal');
            
            // 显示MFA密钥（如果启用了）
            if (result.mfa_secret) {
                // 显示MFA密钥弹窗
                const mfaModal = document.createElement('div');
                mfaModal.className = 'modal active';
                mfaModal.id = 'mfa-show-modal';
                mfaModal.innerHTML = `
                    <div class="modal-content modal-small">
                        <div class="modal-header">
                            <h2><i class="fas fa-key"></i> MFA密钥</h2>
                            <button class="close-btn" onclick="this.closest('.modal').remove()">&times;</button>
                        </div>
                        <div class="modal-body">
                            <p style="margin-bottom: 16px; color: var(--text-secondary);">
                                请使用手机认证器App（如Google Authenticator、Microsoft Authenticator）扫描下方密钥
                            </p>
                            <div class="mfa-setup" style="display: block;">
                                <div class="mfa-secret" style="font-size: 18px; letter-spacing: 2px; text-align: center; padding: 16px; background: var(--bg-secondary); border-radius: 8px; font-family: monospace;">
                                    ${result.mfa_secret}
                                </div>
                            </div>
                            <button class="btn btn-primary btn-block" style="margin-top: 16px;" onclick="navigator.clipboard.writeText('${result.mfa_secret}'); showToast('已复制MFA密钥', 'success');">
                                <i class="fas fa-copy"></i> 复制密钥
                            </button>
                            <div class="warning-box" style="margin-top: 16px;">
                                <i class="fas fa-exclamation-triangle"></i>
                                <p>请妥善保管此密钥，登录时需要输入认证器生成的6位动态验证码</p>
                            </div>
                        </div>
                    </div>
                `;
                document.body.appendChild(mfaModal);
            } else {
                showToast('注册成功！请登录', 'success');
            }
        }
    } catch (error) {
        showToast(error.message, 'error');
    }
});

// 显示注册弹窗
document.getElementById('show-register-btn').addEventListener('click', () => {
    document.getElementById('register-modal').classList.add('active');
    // 重置表单
    document.getElementById('register-form').reset();
});

// 退出登录
document.getElementById('logout-btn').addEventListener('click', async () => {
    try {
        await apiCall('/api/auth/logout', 'POST');
    } catch (e) {}
    
    authToken = null;
    currentUser = null;
    localStorage.removeItem('authToken');
    localStorage.removeItem('currentUser');
    
    // 重置登录表单
    document.getElementById('login-form').reset();
    document.querySelector('.mfa-group').style.display = 'none';
    
    document.getElementById('main-page').classList.remove('active');
    document.getElementById('login-page').classList.add('active');
    
    showToast('已安全退出', 'success');
});

// ==================== 页面导航 ====================
document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', (e) => {
        e.preventDefault();
        
        const page = item.dataset.page;
        
        // 更新导航状态
        document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
        item.classList.add('active');
        
        // 切换内容区域
        document.querySelectorAll('.content-section').forEach(s => s.classList.remove('active'));
        document.getElementById(`${page}-section`).classList.add('active');
        
        // 更新标题
        const titles = {
            dashboard: '控制面板',
            keys: '密钥管理',
            apps: '应用授权',
            security: '安全设置',
            audit: '审计日志'
        };
        document.getElementById('page-title').textContent = titles[page];
        
        // 加载数据
        switch (page) {
            case 'dashboard':
                loadDashboard();
                break;
            case 'keys':
                loadKeys();
                break;
            case 'apps':
                loadApps();
                break;
            case 'security':
                loadSecuritySettings();
                break;
            case 'audit':
                loadAuditLog();
                break;
        }
    });
});

// ==================== 加载数据 ====================
async function loadDashboard() {
    try {
        // 加载统计
        const status = await apiCall('/api/status');
        document.getElementById('stat-keys').textContent = status.vault_stats?.total_entries || 0;
        
        const proxyStats = await apiCall('/api/proxy/stats');
        document.getElementById('stat-apps').textContent = proxyStats.stats?.active_applications || 0;
        document.getElementById('stat-requests').textContent = proxyStats.stats?.requests_today || 0;
        
        // 加载最近活动
        const audit = await apiCall('/api/proxy/audit');
        const activityList = document.getElementById('recent-activity');
        
        if (audit.logs && audit.logs.length > 0) {
            activityList.innerHTML = audit.logs.slice(0, 5).map(log => `
                <div class="activity-item">
                    <i class="fas fa-key"></i>
                    <span>${log.key_name} - ${log.response_method}</span>
                    <small>${formatTime(log.requested_at)}</small>
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('加载仪表盘失败:', error);
    }
}

async function loadKeys() {
    try {
        const result = await apiCall('/api/data/list');
        const keysList = document.getElementById('keys-list');
        
        if (result.results && result.results.length > 0) {
            keysList.innerHTML = result.results.map(key => `
                <div class="key-card">
                    <div class="key-card-header">
                        <div class="key-type-icon">
                            <i class="fas fa-key"></i>
                        </div>
                        <div class="key-actions">
                            <button class="btn btn-icon btn-sm" onclick="viewKey('${key.entry_id}')" title="查看">
                                <i class="fas fa-eye"></i>
                            </button>
                            <button class="btn btn-icon btn-sm" onclick="deleteKey('${key.entry_id}')" title="删除">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                    <div class="key-name">${key.name}</div>
                    <div class="key-meta">
                        <span><i class="fas fa-calendar"></i> ${formatDate(key.created_at)}</span>
                        <span><i class="fas fa-file"></i> ${key.size} bytes</span>
                    </div>
                    <div class="key-tags">
                        ${(key.tags || []).map(tag => `<span class="tag">${tag}</span>`).join('')}
                    </div>
                </div>
            `).join('');
        } else {
            keysList.innerHTML = `
                <div class="empty-state" style="grid-column: 1/-1; text-align: center; padding: 60px; color: var(--text-muted);">
                    <i class="fas fa-inbox" style="font-size: 48px; margin-bottom: 16px;"></i>
                    <p>暂无密钥，点击上方按钮添加</p>
                </div>
            `;
        }
    } catch (error) {
        showToast('加载密钥列表失败: ' + error.message, 'error');
    }
}

async function loadApps() {
    try {
        const result = await apiCall('/api/proxy/apps');
        const appsList = document.getElementById('apps-list');
        
        if (result.applications && result.applications.length > 0) {
            appsList.innerHTML = result.applications.map(app => {
                // 构建已授权密钥列表
                let grantedKeysHtml = '';
                if (app.granted_keys && app.granted_keys.length > 0) {
                    grantedKeysHtml = `
                        <div class="granted-keys" style="margin-top: 8px; padding: 8px; background: var(--bg-tertiary); border-radius: 6px;">
                            <div style="font-size: 12px; color: var(--text-muted); margin-bottom: 4px;">
                                <i class="fas fa-key"></i> 已授权密钥:
                            </div>
                            ${app.granted_keys.map(key => `
                                <div class="granted-key-item" style="display: flex; justify-content: space-between; align-items: center; padding: 4px 0; font-size: 13px;">
                                    <span style="color: var(--primary);">${key.key_name}</span>
                                    <span style="color: var(--text-muted); font-size: 11px;">
                                        ${key.access_type === 'read' ? '读取' : '使用'}
                                        ${key.expires_at ? ' · ' + formatTime(key.expires_at) + '过期' : ''}
                                    </span>
                                </div>
                            `).join('')}
                        </div>
                    `;
                }
                
                return `
                    <div class="app-card">
                        <div class="app-icon">
                            <i class="fas fa-${app.app_type === 'agent' ? 'robot' : 'plug'}"></i>
                        </div>
                        <div class="app-info" style="flex: 1;">
                            <div class="app-name">${app.app_name}</div>
                            <div class="app-meta">
                                类型: ${app.app_type} | 
                                访问次数: ${app.access_count} |
                                ${app.active ? '<span style="color: #22c55e;">活跃</span>' : '<span style="color: #ef4444;">已禁用</span>'}
                            </div>
                            ${grantedKeysHtml}
                        </div>
                        <div class="app-actions">
                            <button class="btn btn-sm btn-secondary" onclick="showGrantModal('${app.app_id}')">
                                <i class="fas fa-key"></i> 授权
                            </button>
                            <button class="btn btn-sm btn-danger" onclick="revokeApp('${app.app_id}')">
                                <i class="fas fa-ban"></i> 撤销
                            </button>
                        </div>
                    </div>
                `;
            }).join('');
        } else {
            appsList.innerHTML = `
                <div class="empty-state" style="text-align: center; padding: 60px; color: var(--text-muted);">
                    <i class="fas fa-plug" style="font-size: 48px; margin-bottom: 16px;"></i>
                    <p>暂无注册应用</p>
                </div>
            `;
        }
    } catch (error) {
        showToast('加载应用列表失败: ' + error.message, 'error');
    }
}

async function loadAuditLog() {
    try {
        const result = await apiCall('/api/proxy/audit');
        const tbody = document.getElementById('audit-log-body');
        
        if (result.logs && result.logs.length > 0) {
            tbody.innerHTML = result.logs.map(log => `
                <tr>
                    <td>${formatTime(log.requested_at)}</td>
                    <td>${log.key_name}</td>
                    <td>${log.response_method}</td>
                    <td>
                        <span class="status-badge ${log.granted ? 'success' : 'failed'}">
                            <i class="fas fa-${log.granted ? 'check' : 'times'}"></i>
                            ${log.granted ? '成功' : '失败'}
                        </span>
                    </td>
                </tr>
            `).join('');
        } else {
            tbody.innerHTML = `
                <tr>
                    <td colspan="4" style="text-align: center; color: var(--text-muted);">
                        暂无日志记录
                    </td>
                </tr>
            `;
        }
    } catch (error) {
        showToast('加载审计日志失败: ' + error.message, 'error');
    }
}

// ==================== 密钥操作 ====================
function showAddKeyModal() {
    document.getElementById('add-key-modal').classList.add('active');
    // 重置表单
    document.getElementById('add-key-form').reset();
    document.getElementById('key-encrypt').checked = true;
    // 显示默认登录方式
    toggleLoginFields();
}

// 切换登录方式字段显示
function toggleLoginFields() {
    const loginType = document.getElementById('key-login-type').value;
    
    // 隐藏所有登录方式字段
    document.querySelectorAll('.login-type-fields').forEach(el => {
        el.style.display = 'none';
    });
    
    // 显示选中的登录方式字段
    const selectedFields = document.getElementById(`login-type-${loginType}`);
    if (selectedFields) {
        selectedFields.style.display = 'block';
    }
}

// 切换密码可见性
function togglePasswordVisibility(inputId) {
    const input = document.getElementById(inputId);
    const icon = input.nextElementSibling.querySelector('i');
    
    if (input.type === 'password') {
        input.type = 'text';
        icon.classList.remove('fa-eye');
        icon.classList.add('fa-eye-slash');
    } else {
        input.type = 'password';
        icon.classList.remove('fa-eye-slash');
        icon.classList.add('fa-eye');
    }
}

// 收集登录方式数据
function collectLoginData() {
    const loginType = document.getElementById('key-login-type').value;
    const data = { loginType: loginType };
    
    switch (loginType) {
        case 'password':
            data.username = document.getElementById('key-username').value.trim();
            data.password = document.getElementById('key-password').value;
            break;
            
        case 'phone_code':
            data.phone = document.getElementById('key-phone').value.trim();
            data.codeMethod = document.getElementById('key-code-method').value.trim();
            break;
            
        case 'email_code':
            data.email = document.getElementById('key-email').value.trim();
            data.codeMethod = document.getElementById('key-email-code-method').value.trim();
            break;
            
        case 'scan':
            data.scanMethod = document.getElementById('key-scan-method').value.trim();
            break;
            
        case 'third_party':
            data.thirdParty = document.getElementById('key-third-party').value;
            data.bindAccount = document.getElementById('key-bind-account').value.trim();
            data.loginMethod = document.getElementById('key-third-party-method').value.trim();
            break;
            
        case 'bank_card':
            data.cardNumber = document.getElementById('key-card-number').value.trim();
            data.cardHolder = document.getElementById('key-card-holder').value.trim();
            data.bankName = document.getElementById('key-bank-name').value.trim();
            data.cardPassword = document.getElementById('key-card-password').value;
            data.cvv = document.getElementById('key-card-cvv').value.trim();
            break;
            
        case 'api_key':
            data.apiKey = document.getElementById('key-api-key').value.trim();
            data.apiSecret = document.getElementById('key-api-secret').value.trim();
            data.apiEndpoint = document.getElementById('key-api-endpoint').value.trim();
            break;
            
        case 'other':
            data.account = document.getElementById('key-other-account').value.trim();
            data.password = document.getElementById('key-other-password').value.trim();
            break;
    }
    
    return data;
}

// 验证登录数据
function validateLoginData(data) {
    const loginType = data.loginType;
    
    switch (loginType) {
        case 'password':
            if (!data.username) return '请输入用户名/账号';
            if (!data.password) return '请输入密码';
            break;
            
        case 'phone_code':
            if (!data.phone) return '请输入手机号';
            break;
            
        case 'email_code':
            if (!data.email) return '请输入邮箱地址';
            break;
            
        case 'bank_card':
            if (!data.cardNumber) return '请输入银行卡号';
            break;
            
        case 'api_key':
            if (!data.apiKey) return '请输入API Key';
            break;
    }
    
    return null;
}

document.getElementById('add-key-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const name = document.getElementById('key-name').value.trim();
    const tagsStr = document.getElementById('key-tags').value;
    const notes = document.getElementById('key-notes').value.trim();
    const encrypt = document.getElementById('key-encrypt').checked;
    
    // 验证名称
    if (!name) {
        showToast('请输入密钥名称', 'error');
        return;
    }
    
    // 收集登录数据
    const loginData = collectLoginData();
    
    // 验证登录数据
    const validationError = validateLoginData(loginData);
    if (validationError) {
        showToast(validationError, 'error');
        return;
    }
    
    // 添加备注
    loginData.notes = notes;
    
    // 解析标签
    const tags = tagsStr ? tagsStr.split(/[,，]/).map(t => t.trim()).filter(t => t) : [];
    
    // 构建完整数据
    const fullData = JSON.stringify(loginData);
    
    try {
        showToast('正在加密保存...', 'warning');
        
        const result = await apiCall('/api/data/store', 'POST', {
            name: name,
            data: fullData,
            tags: tags,
            encrypt: encrypt
        });
        
        if (result.status === 'success') {
            showToast('密钥安全保存成功！', 'success');
            // 重置表单
            document.getElementById('add-key-form').reset();
            document.getElementById('key-encrypt').checked = true;
            toggleLoginFields();
            // 关闭弹窗
            closeModal('add-key-modal');
            // 刷新列表
            loadKeys();
            loadDashboard();
        }
    } catch (error) {
        showToast('保存失败: ' + error.message, 'error');
    }
});

async function viewKey(entryId) {
    try {
        const result = await apiCall('/api/data/retrieve', 'POST', { entry_id: entryId });
        
        if (result.status === 'success') {
            // 解析数据
            let keyData;
            try {
                keyData = JSON.parse(result.data);
            } catch {
                keyData = { loginType: 'password', password: result.data };
            }
            
            // 根据登录方式生成不同的显示内容
            let fieldsHtml = '';
            const loginType = keyData.loginType || 'password';
            
            // 登录方式标签
            const loginTypeLabels = {
                'password': '用户名+密码',
                'phone_code': '手机号+验证码',
                'email_code': '邮箱+验证码',
                'scan': '扫码登录',
                'third_party': '第三方登录',
                'bank_card': '银行卡',
                'api_key': 'API密钥',
                'other': '其他'
            };
            
            fieldsHtml += `
                <div class="form-group">
                    <label>登录方式</label>
                    <p style="color: var(--primary); font-weight: 500;">${loginTypeLabels[loginType] || loginType}</p>
                </div>
            `;
            
            switch (loginType) {
                case 'password':
                    if (keyData.username) {
                        fieldsHtml += createCopyField('用户名/账号', keyData.username);
                    }
                    if (keyData.password) {
                        fieldsHtml += createCopyField('密码', keyData.password, true);
                    }
                    break;
                    
                case 'phone_code':
                    if (keyData.phone) {
                        fieldsHtml += createCopyField('手机号', keyData.phone);
                    }
                    if (keyData.codeMethod) {
                        fieldsHtml += createInfoField('验证码获取方式', keyData.codeMethod);
                    }
                    break;
                    
                case 'email_code':
                    if (keyData.email) {
                        fieldsHtml += createCopyField('邮箱地址', keyData.email);
                    }
                    if (keyData.codeMethod) {
                        fieldsHtml += createInfoField('验证码获取方式', keyData.codeMethod);
                    }
                    break;
                    
                case 'scan':
                    if (keyData.scanMethod) {
                        fieldsHtml += createInfoField('扫码方式说明', keyData.scanMethod);
                    }
                    break;
                    
                case 'third_party':
                    if (keyData.thirdParty) {
                        const thirdPartyLabels = {
                            'wechat': '微信', 'qq': 'QQ', 'alipay': '支付宝',
                            'weibo': '微博', 'apple': 'Apple ID', 'google': 'Google', 'other': '其他'
                        };
                        fieldsHtml += createInfoField('第三方平台', thirdPartyLabels[keyData.thirdParty] || keyData.thirdParty);
                    }
                    if (keyData.bindAccount) {
                        fieldsHtml += createCopyField('绑定账号', keyData.bindAccount);
                    }
                    if (keyData.loginMethod) {
                        fieldsHtml += createInfoField('登录流程', keyData.loginMethod);
                    }
                    break;
                    
                case 'bank_card':
                    if (keyData.cardNumber) {
                        fieldsHtml += createCopyField('银行卡号', keyData.cardNumber);
                    }
                    if (keyData.cardHolder) {
                        fieldsHtml += createCopyField('持卡人', keyData.cardHolder);
                    }
                    if (keyData.bankName) {
                        fieldsHtml += createInfoField('银行名称', keyData.bankName);
                    }
                    if (keyData.cardPassword) {
                        fieldsHtml += createCopyField('密码', keyData.cardPassword, true);
                    }
                    if (keyData.cvv) {
                        fieldsHtml += createCopyField('CVV/有效期', keyData.cvv, true);
                    }
                    break;
                    
                case 'api_key':
                    if (keyData.apiKey) {
                        fieldsHtml += createCopyField('API Key', keyData.apiKey, true);
                    }
                    if (keyData.apiSecret) {
                        fieldsHtml += createCopyField('API Secret', keyData.apiSecret, true);
                    }
                    if (keyData.apiEndpoint) {
                        fieldsHtml += createCopyField('API端点', keyData.apiEndpoint);
                    }
                    break;
                    
                default:
                    if (keyData.account) {
                        fieldsHtml += createCopyField('账号', keyData.account);
                    }
                    if (keyData.password) {
                        fieldsHtml += createCopyField('密码', keyData.password, true);
                    }
            }
            
            // 备注
            if (keyData.notes) {
                fieldsHtml += createInfoField('备注', keyData.notes);
            }
            
            const modal = document.createElement('div');
            modal.className = 'modal active';
            modal.innerHTML = `
                <div class="modal-content">
                    <div class="modal-header">
                        <h2><i class="fas fa-eye"></i> 密钥详情</h2>
                        <button class="close-btn" onclick="this.closest('.modal').remove()">&times;</button>
                    </div>
                    <div class="modal-body">
                        ${fieldsHtml}
                    </div>
                </div>
            `;
            document.body.appendChild(modal);
        }
    } catch (error) {
        showToast('获取密钥失败: ' + error.message, 'error');
    }
}

// 创建可复制字段
function createCopyField(label, value, isSecret = false) {
    const escapedValue = value.replace(/`/g, '\\`').replace(/'/g, "\\'");
    return `
        <div class="form-group">
            <label>${label} ${isSecret ? '<i class="fas fa-lock" style="color: var(--warning);"></i>' : ''}</label>
            <div class="copy-field">
                <code style="word-break: break-all;">${value}</code>
                <button class="btn btn-icon copy-btn" onclick="navigator.clipboard.writeText(\`${escapedValue}\`); showToast('已复制${label}', 'success');">
                    <i class="fas fa-copy"></i>
                </button>
            </div>
        </div>
    `;
}

// 创建信息展示字段
function createInfoField(label, value) {
    return `
        <div class="form-group">
            <label>${label}</label>
            <p style="color: var(--text-secondary); font-size: 14px; white-space: pre-wrap;">${value}</p>
        </div>
    `;
}

async function deleteKey(entryId) {
    if (!confirm('确定要删除这个密钥吗？此操作不可恢复！')) {
        return;
    }
    
    try {
        const result = await apiCall('/api/data/delete', 'POST', { entry_id: entryId });
        
        if (result.status === 'success') {
            showToast('密钥已删除', 'success');
            loadKeys();
            loadDashboard();
        }
    } catch (error) {
        showToast('删除失败: ' + error.message, 'error');
    }
}

// ==================== 应用操作 ====================
function showRegisterAppModal() {
    document.getElementById('register-app-modal').classList.add('active');
    // 重置表单
    document.getElementById('register-app-form').reset();
    document.getElementById('perm-read').checked = true;
}

document.getElementById('register-app-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const appName = document.getElementById('app-name').value.trim();
    const appType = document.getElementById('app-type').value;
    const permissions = [];
    
    if (document.getElementById('perm-read').checked) permissions.push('key:read');
    if (document.getElementById('perm-use').checked) permissions.push('key:use');
    if (document.getElementById('perm-sign').checked) permissions.push('key:sign');
    
    if (!appName) {
        showToast('请输入应用名称', 'error');
        return;
    }
    
    try {
        const result = await apiCall('/api/proxy/register', 'POST', {
            app_name: appName,
            app_type: appType,
            permissions
        });
        
        if (result.status === 'success') {
            // 重置表单
            document.getElementById('register-app-form').reset();
            document.getElementById('perm-read').checked = true;
            // 关闭弹窗
            closeModal('register-app-modal');
            
            // 显示API密钥
            document.getElementById('display-app-id').textContent = result.app_id;
            document.getElementById('display-api-key').textContent = result.api_key;
            document.getElementById('api-key-modal').classList.add('active');
            
            loadApps();
            loadDashboard();
        }
    } catch (error) {
        showToast('注册失败: ' + error.message, 'error');
    }
});

function showGrantModal(appId) {
    document.getElementById('grant-app-id').value = appId;
    
    // 加载密钥列表到选择框
    apiCall('/api/data/list').then(result => {
        const select = document.getElementById('grant-key-select');
        if (result.results && result.results.length > 0) {
            select.innerHTML = result.results.map(key => 
                `<option value="${key.entry_id}" data-name="${key.name}">${key.name}</option>`
            ).join('');
        } else {
            select.innerHTML = '<option value="">暂无可授权的密钥</option>';
        }
    }).catch(err => {
        showToast('加载密钥列表失败', 'error');
    });
    
    document.getElementById('grant-modal').classList.add('active');
}

document.getElementById('grant-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const appId = document.getElementById('grant-app-id').value;
    const keySelect = document.getElementById('grant-key-select');
    const keyEntryId = keySelect.value;
    const keyName = keySelect.options[keySelect.selectedIndex].dataset.name;
    const accessType = document.getElementById('grant-access-type').value;
    const expiry = document.getElementById('grant-expiry').value;
    const maxUsage = document.getElementById('grant-max-usage').value;
    
    if (!keyEntryId) {
        showToast('请选择要授权的密钥', 'error');
        return;
    }
    
    try {
        const result = await apiCall('/api/proxy/grant', 'POST', {
            app_id: appId,
            key_name: keyName,
            key_entry_id: keyEntryId,
            access_type: accessType,
            expires_in_hours: expiry ? parseInt(expiry) : null,
            max_usage: maxUsage ? parseInt(maxUsage) : null
        });
        
        if (result.status === 'success') {
            showToast('授权成功！', 'success');
            document.getElementById('grant-form').reset();
            closeModal('grant-modal');
            loadApps();  // 刷新应用列表显示最新授权
        }
    } catch (error) {
        showToast('授权失败: ' + error.message, 'error');
    }
});

async function revokeApp(appId) {
    if (!confirm('确定要撤销此应用的所有权限吗？')) {
        return;
    }
    
    try {
        const result = await apiCall(`/api/proxy/apps/${appId}`, 'DELETE');
        
        if (result.status === 'success') {
            showToast('应用权限已撤销', 'success');
            loadApps();
            loadDashboard();
        }
    } catch (error) {
        showToast('撤销失败: ' + error.message, 'error');
    }
}

// ==================== 安全操作 ====================
async function rotateKeys() {
    if (!confirm('确定要轮换加密密钥吗？这会更新所有数据使用的加密密钥。\n\n注意：更改加密方法后，旧数据可能无法正确解密。')) {
        return;
    }
    
    try {
        showToast('正在轮换密钥...', 'warning');
        const result = await apiCall('/api/keys/rotate', 'POST');
        
        if (result.status === 'success') {
            showToast('密钥轮换成功！', 'success');
        }
    } catch (error) {
        showToast('轮换失败: ' + error.message, 'error');
    }
}

async function updateEncryptionMethod() {
    const method = document.getElementById('encryption-method').value;
    
    if (!confirm('确定要更改加密方法吗？\n\n注意：更改后新添加的数据会使用新方法，旧数据可能无法正确解密。')) {
        document.getElementById('encryption-method').value = currentEncryptionMethod;
        return;
    }
    
    try {
        const result = await apiCall('/api/encryption/method', 'POST', { method: method });
        
        if (result.status === 'success') {
            currentEncryptionMethod = method;
            showToast('加密方法已更改！', 'success');
            loadSecuritySettings();
        } else {
            showToast('更改失败: ' + result.message, 'error');
            document.getElementById('encryption-method').value = currentEncryptionMethod;
        }
    } catch (error) {
        showToast('更改失败: ' + error.message, 'error');
        document.getElementById('encryption-method').value = currentEncryptionMethod;
    }
}

async function loadSecuritySettings() {
    try {
        const result = await apiCall('/api/settings', 'GET');
        
        if (result.settings) {
            currentEncryptionMethod = result.settings.encryption_method || 'math_gamma';
            document.getElementById('encryption-method').value = currentEncryptionMethod;
            
            // 加载会话有效期设置
            const sessionTimeout = result.settings.session_timeout_minutes || 1440;
            const sessionSelect = document.getElementById('session-timeout');
            if (sessionSelect) {
                sessionSelect.value = sessionTimeout.toString();
            }
            
            const infoDiv = document.getElementById('encryption-info');
            const methodInfo = {
                'math_gamma': {
                    name: '伽马函数+梅森素数',
                    features: ['使用梅森素数进行模运算', '伽马函数扩展密钥空间', 'ChaCha20-Poly1305加密']
                },
                'math_chaos': {
                    name: '混沌映射加密',
                    features: ['Logistic混沌映射', 'Henon混沌映射', 'ChaCha20-Poly1305加密']
                },
                'math_lattice': {
                    name: '格基密码（抗量子）',
                    features: ['格基哈希', '抗量子攻击', 'ChaCha20-Poly1305加密']
                },
                'quantum_sim': {
                    name: '量子密码模拟（软件）',
                    features: ['BB84模拟', '量子态模拟', 'ChaCha20-Poly1305加密']
                },
                'aes256': {
                    name: 'AES-256-GCM',
                    features: ['NIST标准', '硬件加速', 'GCM认证加密']
                }
            };
            
            const info = methodInfo[currentEncryptionMethod] || methodInfo['math_gamma'];
            infoDiv.innerHTML = `
                <p><strong>当前方法：</strong>${info.name}</p>
                ${info.features.map(f => `<p>• ${f}</p>`).join('')}
            `;
        }
    } catch (error) {
        console.error('加载设置失败:', error);
    }
}

async function updateSessionTimeout() {
    const timeout = document.getElementById('session-timeout').value;
    
    try {
        const result = await apiCall('/api/settings', 'POST', {
            session_timeout_minutes: parseInt(timeout)
        });
        
        if (result.status === 'success') {
            showToast('会话有效期已更新！下次登录生效', 'success');
        }
    } catch (error) {
        showToast('更新失败: ' + error.message, 'error');
    }
}

let currentEncryptionMethod = 'math_gamma';

async function backupVault() {
    const path = prompt('请输入备份文件保存路径：', './backup_' + Date.now());
    if (!path) return;
    
    try {
        const result = await apiCall('/api/backup', 'POST', { backup_path: path });
        
        if (result.status === 'success') {
            showToast('备份成功！', 'success');
        }
    } catch (error) {
        showToast('备份失败: ' + error.message, 'error');
    }
}

// MFA开关
document.getElementById('mfa-toggle').addEventListener('change', async (e) => {
    if (e.target.checked) {
        try {
            const result = await apiCall('/api/auth/mfa/enable', 'POST');
            
            if (result.status === 'success') {
                document.getElementById('mfa-secret').textContent = result.mfa_secret;
                document.getElementById('mfa-setup').style.display = 'block';
                showToast('MFA已启用，请使用认证器应用绑定', 'success');
            }
        } catch (error) {
            e.target.checked = false;
            showToast('启用MFA失败: ' + error.message, 'error');
        }
    }
});

// ==================== 弹窗控制 ====================
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('active');
    }
}

// 使用事件委托处理关闭按钮（支持动态创建的弹窗）
document.addEventListener('click', (e) => {
    const target = e.target;
    
    // 检查是否点击了关闭按钮或其子元素
    if (target.classList.contains('close-btn') || 
        target.closest('.close-btn') ||
        target.textContent === '×') {
        
        e.preventDefault();
        e.stopPropagation();
        
        const modal = target.closest('.modal');
        if (modal) {
            modal.classList.remove('active');
        }
        return;
    }
    
    // 点击背景关闭
    if (target.classList.contains('modal') && target.id) {
        target.classList.remove('active');
    }
}, true);  // 使用捕获阶段确保先处理

// ==================== 密码强度检测 ====================
document.getElementById('reg-password').addEventListener('input', (e) => {
    const password = e.target.value;
    const bar = document.querySelector('.strength-bar');
    const text = document.querySelector('.strength-text');
    
    let strength = 0;
    if (password.length >= 8) strength++;
    if (/[a-z]/.test(password)) strength++;
    if (/[A-Z]/.test(password)) strength++;
    if (/[0-9]/.test(password)) strength++;
    if (/[^a-zA-Z0-9]/.test(password)) strength++;
    
    const colors = ['#ef4444', '#f59e0b', '#eab308', '#22c55e', '#10b981'];
    const texts = ['很弱', '弱', '中等', '强', '很强'];
    
    bar.style.width = `${strength * 20}%`;
    bar.style.background = colors[strength - 1] || '#334155';
    text.textContent = texts[strength - 1] || '密码强度';
});

// ==================== 搜索功能 ====================
document.getElementById('key-search').addEventListener('input', (e) => {
    const query = e.target.value.toLowerCase();
    document.querySelectorAll('.key-card').forEach(card => {
        const name = card.querySelector('.key-name').textContent.toLowerCase();
        card.style.display = name.includes(query) ? '' : 'none';
    });
});

document.getElementById('app-search').addEventListener('input', (e) => {
    const query = e.target.value.toLowerCase();
    document.querySelectorAll('.app-card').forEach(card => {
        const name = card.querySelector('.app-name').textContent.toLowerCase();
        card.style.display = name.includes(query) ? '' : 'none';
    });
});

// ==================== 初始化 ====================
document.addEventListener('DOMContentLoaded', () => {
    // 检查登录状态
    const savedToken = localStorage.getItem('authToken');
    const savedUser = localStorage.getItem('currentUser');
    
    if (savedToken && savedUser) {
        authToken = savedToken;
        currentUser = JSON.parse(savedUser);
        
        document.getElementById('current-username').textContent = currentUser.username;
        document.getElementById('login-page').classList.remove('active');
        document.getElementById('main-page').classList.add('active');
        
        loadDashboard();
    }
});

// 导出函数供HTML使用
window.showAddKeyModal = showAddKeyModal;
window.showRegisterAppModal = showRegisterAppModal;
window.showGrantModal = showGrantModal;
window.viewKey = viewKey;
window.deleteKey = deleteKey;
window.revokeApp = revokeApp;
window.rotateKeys = rotateKeys;
window.backupVault = backupVault;
window.copyToClipboard = copyToClipboard;
window.closeModal = closeModal;
window.toggleLoginFields = toggleLoginFields;
window.togglePasswordVisibility = togglePasswordVisibility;
window.updateSessionTimeout = updateSessionTimeout;
