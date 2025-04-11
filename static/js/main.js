class FaceAuth {
    constructor() {
        this.initializeElements();
        this.setupEventListeners();
        this.startVideo();
    }

    initializeElements() {
        this.video = document.getElementById('video');
        
        // 登录页面元素
        this.detectButton = document.getElementById('detect-face');
        this.blinkText = document.getElementById('blink-text');
        this.registerForm = document.getElementById('registerForm');
        this.username = document.getElementById('username');
        this.confirmRegister = document.getElementById('confirmRegister');
        
        // 仪表板页面元素
        this.captureButton = document.querySelector('.capture-btn');
        this.userListTab = document.querySelector('[data-tab="user-list"]');
        
        // 初始化计数器
        this.blinkCount = 0;
        this.maxDetectionAttempts = 50;
        this.detectionAttempts = 0;
    }

    setupEventListeners() {
        // 登录页面事件
        if (this.detectButton) {
            this.detectButton.addEventListener('click', () => this.detectFace());
        }
        
        // 仪表板页面事件
        if (this.captureButton) {
            this.captureButton.addEventListener('click', () => this.captureEmotion());
        }
        if (this.userListTab) {
            this.userListTab.addEventListener('click', () => this.updateUserList());
        }

        // 添加导航切换功能
        const navLinks = document.querySelectorAll('.sidebar nav a');
        if (navLinks.length > 0) {
            navLinks.forEach(link => {
                link.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.switchTab(link.getAttribute('data-tab'));
                });
            });

            // 初始化时更新用户列表
            this.updateUserList();
        }
    }

    async startVideo() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ video: true });
            if (this.video) {
                this.video.srcObject = stream;
            }
        } catch (err) {
            console.error('摄像头访问错误:', err);
            if (this.blinkText) {
                this.blinkText.textContent = '无法访问摄像头，请确保已授予权限';
            }
        }
    }

    detectFace() {
        if (!this.video || !this.video.videoWidth) {
            alert('请确保摄像头已开启');
            return;
        }

        this.blinkText.textContent = '请眨眼...';
        this.detectBlink();
    }

    detectBlink() {
        if (this.detectionAttempts >= this.maxDetectionAttempts) {
            this.blinkText.textContent = '未检测到眨眼，请重试';
            this.detectionAttempts = 0;
            return;
        }

        const canvas = document.createElement('canvas');
        canvas.width = this.video.videoWidth;
        canvas.height = this.video.videoHeight;
        
        const context = canvas.getContext('2d');
        context.drawImage(this.video, 0, 0, canvas.width, canvas.height);
        
        const imageData = canvas.toDataURL('image/jpeg');

        fetch('/detect_action', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                image: imageData
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                this.blinkCount++;
                this.blinkText.textContent = `检测到眨眼 ${this.blinkCount} 次`;
                
                if (this.blinkCount >= 2) {
                    this.checkFace();
                    return;
                }
            } else {
                this.blinkText.textContent = data.message || '请眨眼';
            }
            
            this.detectionAttempts++;
            setTimeout(() => this.detectBlink(), 100);
        })
        .catch(error => {
            console.error('检测错误:', error);
            this.blinkText.textContent = '检测出错，请重试';
        });
    }

    checkFace() {
        const canvas = document.createElement('canvas');
        canvas.width = this.video.videoWidth;
        canvas.height = this.video.videoHeight;
        
        const context = canvas.getContext('2d');
        context.drawImage(this.video, 0, 0, canvas.width, canvas.height);
        
        const imageData = canvas.toDataURL('image/jpeg');

        this.blinkText.textContent = '正在验证...';

        fetch('/check_face', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                image: imageData
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success' && data.data && data.data.exists) {
                window.location.href = '/dashboard';
            } else {
                this.blinkText.textContent = data.message || '验证失败，请重试';
                this.blinkCount = 0;
                this.detectionAttempts = 0;
            }
        })
        .catch(error => {
            console.error('验证错误:', error);
            this.blinkText.textContent = '验证出错，请重试';
            this.blinkCount = 0;
            this.detectionAttempts = 0;
        });
    }

    captureEmotion() {
        if (!this.video || !this.video.videoWidth) {
            Swal.fire({
                title: '错误',
                text: '摄像头未就绪，请稍后再试',
                icon: 'error',
                confirmButtonText: '确定'
            });
            return;
        }

        Swal.fire({
            title: '处理中...',
            text: '正在分析情绪，请稍候',
            allowOutsideClick: false,
            allowEscapeKey: false,
            showConfirmButton: false,
            didOpen: () => {
                Swal.showLoading();
            }
        });

        const canvas = document.createElement('canvas');
        canvas.width = this.video.videoWidth;
        canvas.height = this.video.videoHeight;
        
        const context = canvas.getContext('2d');
        context.drawImage(this.video, 0, 0, canvas.width, canvas.height);
        
        const imageData = canvas.toDataURL('image/jpeg');

        fetch('/record_emotion', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                image: imageData
            })
        })
        .then(response => response.json())
        .then(data => {
            Swal.close();
            
            if (data.status === 'success') {
                Swal.fire({
                    title: '记录成功！',
                    html: `
                        <div style="margin: 20px 0;">
                            <p style="font-size: 1.2em;">检测到的情绪：</p>
                            <p style="font-size: 1.5em; color: #4CAF50; margin: 10px 0;">
                                ${data.emotion}
                            </p>
                        </div>
                    `,
                    icon: 'success',
                    confirmButtonText: '确定',
                    confirmButtonColor: '#4CAF50'
                }).then(() => {
                    this.updateUserList();
                });
            } else {
                Swal.fire({
                    title: '记录失败',
                    text: data.message || '未知错误',
                    icon: 'error',
                    confirmButtonText: '确定'
                });
            }
        })
        .catch(error => {
            console.error('请求错误:', error);
            Swal.close();
            Swal.fire({
                title: '发生错误',
                text: error.toString(),
                icon: 'error',
                confirmButtonText: '确定'
            });
        });
    }

    updateUserList() {
        fetch('/get_user_list')
        .then(response => response.json())
        .then(data => {
            const userList = document.getElementById('user-list');
            if (userList) {
                userList.innerHTML = '';
                if (data && data.length > 0) {
                    data.forEach(user => {
                        const row = document.createElement('tr');
                        const createdAt = user.created_at || '暂无';
                        row.innerHTML = `
                            <td>${user.username || ''}</td>
                            <td>${user.latest_emotion || '暂无'}</td>
                            <td>${createdAt}</td>
                        `;
                        userList.appendChild(row);
                    });
                } else {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td colspan="3" style="text-align: center;">暂无记录</td>
                    `;
                    userList.appendChild(row);
                }
            }
        })
        .catch(error => {
            console.error('更新用户列表失败:', error);
            const userList = document.getElementById('user-list');
            if (userList) {
                userList.innerHTML = `
                    <tr>
                        <td colspan="3" style="text-align: center; color: red;">
                            加载失败，请刷新页面重试
                        </td>
                    </tr>
                `;
            }
        });
    }

    // 添加切换标签页的方法
    switchTab(tabId) {
        // 更新导航链接状态
        document.querySelectorAll('.sidebar nav a').forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('data-tab') === tabId) {
                link.classList.add('active');
            }
        });

        // 更新内容区域显示
        document.querySelectorAll('.content-section').forEach(section => {
            section.classList.remove('active');
        });
        const targetSection = document.getElementById(`${tabId}-section`);
        if (targetSection) {
            targetSection.classList.add('active');
        }

        // 根据标签页执行相应的操作
        if (tabId === 'user-list') {
            this.updateUserList();
        } else if (tabId === 'emotion-analysis') {
            this.updateEmotionChart();
        }
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    new FaceAuth();
});