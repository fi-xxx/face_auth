class DashboardManager {
    constructor() {
        this.video = document.getElementById('video');
        this.canvas = document.getElementById('canvas');
        this.captureBtn = document.getElementById('capture-btn');
        this.emotionResult = document.getElementById('emotion-result');
        this.searchInput = document.getElementById('searchUser');
        
        this.initializeEventListeners();
    }
    
    initializeEventListeners() {
        // 捕获表情按钮事件
        if (this.captureBtn) {
            this.captureBtn.addEventListener('click', () => this.captureEmotion());
        }
        
        // 搜索事件监听
        if (this.searchInput) {
            this.searchInput.addEventListener('input', this.debounce((e) => {
                this.searchUsers(e.target.value);
            }, 300));
        }
    }
    
    // 防抖函数
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    // 搜索用户
    async searchUsers(query) {
        try {
            const response = await fetch(`/search_users?query=${encodeURIComponent(query)}`);
            const data = await response.json();
            
            if (data.status === 'success') {
                this.updateUsersTable(data.users);
            } else {
                console.error('搜索失败:', data.message);
            }
        } catch (error) {
            console.error('搜索请求失败:', error);
        }
    }
    
    // 更新用户表格
    updateUsersTable(users) {
        const tbody = document.querySelector('.users-table tbody');
        if (!tbody) return;
        
        tbody.innerHTML = '';
        
        users.forEach(user => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${this.escapeHtml(user.username)}</td>
                <td>
                    <span class="emotion-badge ${user.latest_emotion ? user.latest_emotion.toLowerCase() : 'neutral'}">
                        ${user.latest_emotion || '暂无记录'}
                    </span>
                </td>
                <td>${user.emotion_time || '暂无记录'}</td>
            `;
            tbody.appendChild(tr);
        });
    }
    
    // HTML转义函数
    escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
    
    // 切换内容区域
    showSection(section) {
        document.querySelectorAll('.content-section').forEach(el => el.classList.remove('active'));
        document.querySelectorAll('.sidebar-menu li').forEach(el => el.classList.remove('active'));
        
        document.getElementById(`${section}-section`).classList.add('active');
        document.querySelector(`.sidebar-menu li[onclick="dashboard.showSection('${section}')"]`).classList.add('active');
        
        if (section === 'emotion') {
            this.setupCamera();
        }
    }
    
    // 设置摄像头
    async setupCamera() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ video: true });
            this.video.srcObject = stream;
        } catch (err) {
            console.error('摄像头访问失败:', err);
            this.showError('无法访问摄像头');
        }
    }
    
    // 捕获表情
    async captureEmotion() {
        this.canvas.width = this.video.videoWidth;
        this.canvas.height = this.video.videoHeight;
        this.canvas.getContext('2d').drawImage(this.video, 0, 0);
        
        const imageData = this.canvas.toDataURL('image/jpeg');
        
        try {
            const response = await fetch('/record_emotion', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ image: imageData })
            });
            
            const result = await response.json();
            if (result.success) {
                this.showEmotionResult(`当前情绪: ${result.emotion}`);
                location.reload();
            } else {
                this.showError(`情绪检测失败: ${result.message}`);
            }
        } catch (err) {
            console.error('请求失败:', err);
            this.showError(`发生错误: ${err.message}`);
        }
    }
    
    // 显示情绪结果
    showEmotionResult(message) {
        this.emotionResult.textContent = message;
        this.emotionResult.style.display = 'block';
        this.emotionResult.className = 'emotion-result success';
    }
    
    // 显示错误信息
    showError(message) {
        this.emotionResult.textContent = message;
        this.emotionResult.style.display = 'block';
        this.emotionResult.className = 'emotion-result error';
    }
    
    // 退出登录
    async logout() {
        try {
            const response = await fetch('/logout', {
                method: 'POST'
            });
            
            if (response.ok) {
                window.location.href = '/';
            } else {
                this.showError('退出失败');
            }
        } catch (err) {
            console.error('退出请求失败:', err);
            this.showError('退出失败: ' + err.message);
        }
    }
}

// 初始化仪表盘管理器
let dashboard;
document.addEventListener('DOMContentLoaded', () => {
    dashboard = new DashboardManager();
}); 