/**
 * 用户认证模块
 * 登录、注册、Token 管理
 */

// ==================== 登录/登出 ====================

function showLoginModal() {
    document.getElementById('loginModal').style.display = 'flex';
    switchAuthTab('login');
}

function closeLoginModal() {
    document.getElementById('loginModal').style.display = 'none';
    document.getElementById('loginError').textContent = '';
    document.getElementById('registerError').textContent = '';
}

function switchAuthTab(tab) {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    if (tab === 'login') {
        document.querySelector('.tab-btn:first-child').classList.add('active');
        document.getElementById('loginForm').style.display = 'flex';
        document.getElementById('registerForm').style.display = 'none';
    } else {
        document.querySelector('.tab-btn:last-child').classList.add('active');
        document.getElementById('loginForm').style.display = 'none';
        document.getElementById('registerForm').style.display = 'flex';
    }
}

async function login() {
    const username = document.getElementById('loginUsername').value.trim();
    const password = document.getElementById('loginPassword').value.trim();
    const errorEl = document.getElementById('loginError');

    if (!username || !password) {
        errorEl.textContent = '请输入用户名和密码';
        return;
    }

    try {
        const result = await apiLogin({ username, password });
        if (result.code === 200) {
            localStorage.setItem('token', result.data.access_token);
            localStorage.setItem('user', JSON.stringify(result.data.user));
            updateUserUI(result.data.user);
            closeLoginModal();
            showTip('登录成功！', 'success');
        } else {
            errorEl.textContent = result.msg || '登录失败';
        }
    } catch (e) {
        errorEl.textContent = '网络错误，请检查后端服务';
    }
}

async function register() {
    const username = document.getElementById('regUsername').value.trim();
    const password = document.getElementById('regPassword').value.trim();
    const nickname = document.getElementById('regNickname').value.trim();
    const email = document.getElementById('regEmail').value.trim();
    const errorEl = document.getElementById('registerError');

    if (!username || !password) {
        errorEl.textContent = '用户名和密码为必填项';
        return;
    }
    if (username.length < 3) {
        errorEl.textContent = '用户名至少3个字符';
        return;
    }
    if (password.length < 6) {
        errorEl.textContent = '密码至少6个字符';
        return;
    }

    try {
        const result = await apiRegister({ username, password, nickname, email });
        if (result.code === 200) {
            showTip('注册成功，请登录！', 'success');
            switchAuthTab('login');
            document.getElementById('loginUsername').value = username;
        } else {
            errorEl.textContent = result.msg || '注册失败';
        }
    } catch (e) {
        errorEl.textContent = '网络错误，请检查后端服务';
    }
}

function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    document.getElementById('userInfo').style.display = 'none';
    document.getElementById('loginBtn').style.display = 'inline-block';
    document.getElementById('adminNavBtn').style.display = 'none';
    if (currentModule === 'admin') switchModule('map');
    showTip('已退出登录', 'info');
}

function updateUserUI(user) {
    document.getElementById('loginBtn').style.display = 'none';
    document.getElementById('userInfo').style.display = 'flex';
    document.getElementById('userNickname').textContent = user.nickname || user.username;
    // 显示管理按钮
    document.getElementById('adminNavBtn').style.display = 'inline-block';
}

// ==================== 初始化认证状态 ====================

function initAuth() {
    const token = getToken();
    if (token) {
        const userStr = localStorage.getItem('user');
        if (userStr) {
            try {
                const user = JSON.parse(userStr);
                updateUserUI(user);
            } catch (e) {
                localStorage.removeItem('token');
                localStorage.removeItem('user');
            }
        }
    }
}
