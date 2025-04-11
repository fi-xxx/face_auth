class DashboardManager {
    constructor() {
        // DOM 元素
        this.video = document.getElementById('video');
        this.captureBtn = document.getElementById('captureBtn');
        this.emotionResult = document.getElementById('emotionResult');
        this.userSearch = document.getElementById('userSearch');
        this.timeRange = document.getElementById('timeRange');
        this.chartType = document.getElementById('chartType');
        this.logoutBtn = document.getElementById('logoutBtn');
        this.emotionChart = null;

        // 初始化
        this.initializeEventListeners();
        this.updateUserList();
    }

    initializeEventListeners() {
        // 导航菜单点击事件
        document.querySelectorAll('.sidebar-menu li').forEach(item => {
            item.addEventListener('click', () => {
                const section = item.getAttribute('data-section');
                this.showSection(section);
            });
        });

        // 退出按钮事件
        if (this.logoutBtn) {
            this.logoutBtn.addEventListener('click', () => this.logout());
        }

        // 捕获表情按钮事件
        if (this.captureBtn) {
            this.captureBtn.addEventListener('click', () => {
                if (!this.video || !this.video.videoWidth) {
                    this.showAlert('错误', '摄像头未就绪，请稍后再试', 'error');
                    return;
                }
                this.captureEmotion();
            });
        }
        
        // 搜索事件监听
        if (this.userSearch) {
            this.userSearch.addEventListener('input', this.debounce((e) => {
                this.searchUsers(e.target.value);
            }, 300));
        }
        
        // 图表相关事件监听
        if (this.timeRange) {
            this.timeRange.addEventListener('change', () => this.updateEmotionChart());
        }
        if (this.chartType) {
            this.chartType.addEventListener('change', () => this.updateEmotionChart());
        }
    }

    // 统一的提示框方法
    showAlert(title, text, icon = 'info', options = {}) {
        return Swal.fire({
            title,
            text,
            icon,
            confirmButtonText: '确定',
            ...options
        });
    }

    // 统一的加载提示方法
    showLoading(text = '处理中...') {
        return Swal.fire({
            title: text,
            allowOutsideClick: false,
            allowEscapeKey: false,
            showConfirmButton: false,
            didOpen: () => {
                Swal.showLoading();
            }
        });
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
        try {
            // 显示加载提示
            this.showLoading('正在分析情绪，请稍候');

            // 捕获图像
            const canvas = document.createElement('canvas');
            canvas.width = this.video.videoWidth;
            canvas.height = this.video.videoHeight;
            canvas.getContext('2d').drawImage(this.video, 0, 0);
            const imageData = canvas.toDataURL('image/jpeg');
            
            // 发送请求
            const response = await fetch('/record_emotion', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image: imageData })
            });
            
            const result = await response.json();
            Swal.close();

            if (result.status === 'success' && result.data) {
                // 显示成功结果
                await this.showAlert('检测完成！', '', 'success', {
                    html: `
                        <div style="margin: 20px 0;">
                            <p style="font-size: 1.2em;">检测到的情绪：</p>
                            <p style="font-size: 1.5em; color: #4CAF50; margin: 10px 0;">
                                ${result.data.emotion}
                            </p>
                        </div>
                    `,
                    confirmButtonColor: '#4CAF50'
                });
                
                // 更新用户列表
                this.updateUserList();
            } else {
                // 显示错误信息
                await this.showAlert('检测失败', result.message || '未知错误', 'error');
            }
        } catch (err) {
            console.error('请求失败:', err);
            Swal.close();
            await this.showAlert('发生错误', err.message, 'error');
        }
    }

    // 显示情绪结果
    showEmotionResult(message, success = true) {
        this.emotionResult.textContent = message;
        this.emotionResult.style.display = 'block';
        this.emotionResult.className = `emotion-result ${success ? 'success' : 'error'}`;
    }

    // 搜索用户
    async searchUsers(query) {
        try {
            const response = await fetch(`/search_users?query=${encodeURIComponent(query)}`);
            const data = await response.json();
            if (data.status === 'success' && data.data) {
                this.updateUsersTable(data.data);
            } else {
                this.showAlert('搜索失败', data.message || '未知错误', 'error');
            }
        } catch (err) {
            console.error('搜索失败:', err);
            this.showAlert('搜索失败', err.message, 'error');
        }
    }

    // 更新用户表格
    updateUsersTable(users) {
        const tbody = document.getElementById('user-list');
        if (!tbody) return;
        
        tbody.innerHTML = '';
        if (users && users.length > 0) {
            users.forEach(user => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${this.escapeHtml(user.username)}</td>
                    <td>
                        <span class="emotion-badge ${user.latest_emotion || 'neutral'}">
                            ${user.latest_emotion || '暂无记录'}
                        </span>
                    </td>
                    <td>${user.emotion_time || '暂无记录'}</td>
                `;
                tbody.appendChild(tr);
            });
        } else {
            const tr = document.createElement('tr');
            tr.innerHTML = '<td colspan="3" class="text-center">暂无数据</td>';
            tbody.appendChild(tr);
        }
    }

    // 更新情绪图表
    async updateEmotionChart() {
        try {
            const days = this.timeRange.value;
            const response = await fetch(`/get_emotion_history?days=${days}`);
            const data = await response.json();
            
            if (data.status === 'success' && data.data) {
                this.renderChart(data.data);
                if (data.data.stats) {
                    this.updateStats(data.data.stats);
                }
            } else {
                this.showAlert('获取数据失败', data.message || '未知错误', 'error');
            }
        } catch (err) {
            console.error('获取图表数据失败:', err);
            this.showAlert('获取数据失败', err.message, 'error');
        }
    }

    // 渲染图表
    renderChart(data) {
        const ctx = document.getElementById('emotionChart').getContext('2d');
        
        if (this.emotionChart) {
            this.emotionChart.destroy();
        }
        
        this.emotionChart = new Chart(ctx, {
            type: this.chartType.value,
            data: {
                labels: data.labels,
                datasets: data.datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    // 更新统计信息
    updateStats(stats) {
        document.getElementById('mainEmotion').textContent = stats.mainEmotion;
        document.getElementById('emotionVariation').textContent = stats.emotionVariation;
        document.getElementById('recordCount').textContent = stats.recordCount;
    }

    // 切换显示部分
    showSection(section) {
        // 更新内容区域
        document.querySelectorAll('.content-section').forEach(el => {
            el.classList.remove('active');
        });
        const targetSection = document.getElementById(`${section}-section`);
        if (targetSection) {
            targetSection.classList.add('active');
        }
        
        // 更新导航菜单激活状态
        document.querySelectorAll('.sidebar-menu li').forEach(el => {
            el.classList.remove('active');
        });
        const menuItem = document.querySelector(`.sidebar-menu li[data-section="${section}"]`);
        if (menuItem) {
            menuItem.classList.add('active');
        }

        // 根据不同部分执行相应的初始化
        if (section === 'emotion') {
            this.setupCamera();
        } else if (section === 'analysis') {
            this.updateEmotionChart();
        } else if (section === 'users') {
            this.updateUserList();
        }
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

    // 工具方法
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

    escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    showError(message) {
        Swal.fire({
            title: '错误',
            text: message,
            icon: 'error',
            confirmButtonText: '确定'
        });
    }

    // 更新用户列表
    async updateUserList() {
        try {
            const response = await fetch('/get_user_list');
            const data = await response.json();
            
            if (data.status === 'success' && data.data) {
                this.updateUsersTable(data.data);
            } else {
                this.showAlert('获取用户列表失败', data.message || '未知错误', 'error');
            }
        } catch (err) {
            console.error('更新用户列表失败:', err);
            this.showAlert('更新用户列表失败', err.message, 'error');
        }
    }
}

// 确保在 DOM 加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new DashboardManager();
}); 