class FaceAuth {
    constructor() {
        this.video = document.getElementById('video');
        this.canvas = document.getElementById('canvas');
        this.captureButton = document.getElementById('capture');
        this.statusDiv = document.getElementById('status');
        this.usernameInput = document.getElementById('username');
        this.registerForm = document.getElementById('registerForm');
        this.confirmRegisterButton = document.getElementById('confirmRegister');
        this.liveDetection = document.getElementById('liveDetection');
        this.detectionInstruction = document.getElementById('detectionInstruction');
        
        this.tempFaceData = null;
        this.isDetecting = false;
        this.isNewUser = false;
        
        this.setupCanvas();
        this.setupEventListeners();
    }
    
    setupCanvas() {
        this.canvas.width = 640;
        this.canvas.height = 480;
    }
    
    setupEventListeners() {
        this.captureButton.addEventListener('click', () => this.startRecognition());
        this.confirmRegisterButton.addEventListener('click', () => this.register());
        this.usernameInput.addEventListener('input', () => {
            this.confirmRegisterButton.disabled = !this.usernameInput.value.trim();
        });
    }
    
    async setupCamera() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ video: true });
            this.video.srcObject = stream;
            this.captureButton.disabled = false;
        } catch (err) {
            this.showError('无法访问摄像头: ' + err.message);
        }
    }

    async startRecognition() {
        this.captureButton.disabled = true;
        this.showLoading('正在识别...');
        
        // 捕获图像
        const context = this.canvas.getContext('2d');
        context.drawImage(this.video, 0, 0, this.canvas.width, this.canvas.height);
        const imageData = this.canvas.toDataURL('image/jpeg');
        this.tempFaceData = imageData;
        
        try {
            const response = await fetch('/check_face', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ image: imageData })
            });
            
            const result = await response.json();
            
            if (!result.success) {
                this.showError(result.message);
                this.captureButton.disabled = false;
                return;
            }
            
            // 存储用户状态和信息
            this.isNewUser = !result.exists;
            if (result.exists) {
                this.existingUsername = result.username;
            }
            
            // 开始活体检测
            this.startLiveDetection();
            
        } catch (err) {
            this.showError('识别出错: ' + err.message);
            this.captureButton.disabled = false;
        }
    }

    async startLiveDetection() {
        this.isDetecting = true;
        this.liveDetection.style.display = 'block';
        this.captureButton.style.display = 'none';
        this.detectionInstruction.textContent = '请眨眨眼';
        this.detectBlink();
    }

    async detectBlink() {
        const context = this.canvas.getContext('2d');
        let detectionAttempts = 0;
        const maxAttempts = 100;
        let lastEar = 1.0;  // 添加上一次的 EAR 值
        let blinkDetected = false;  // 添加眨眼检测标志
        
        const detect = async () => {
            if (!this.isDetecting || detectionAttempts >= maxAttempts) {
                this.showError('检测超时，请重试');
                this.resetDetection();
                return;
            }
            
            context.drawImage(this.video, 0, 0, this.canvas.width, this.canvas.height);
            const imageData = this.canvas.toDataURL('image/jpeg');
            
            try {
                const response = await fetch('/detect_action', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ image: imageData })
                });
                
                const result = await response.json();
                console.log('眨眼检测结果:', result);
                
                // 检查是否是有效的眨眼动作（需要先睁眼再闭眼）
                if (result.ear && lastEar) {
                    const earDiff = lastEar - result.ear;
                    if (earDiff > 0.1 && result.ear < 0.19) {  // 眨眼的条件更严格
                        blinkDetected = true;
                    }
                }
                
                if (blinkDetected) {
                    console.log('检测到有效的眨眼动作');
                    this.onLiveDetectionSuccess();
                    return;
                }
                
                lastEar = result.ear;  // 更新上一次的 EAR 值
                detectionAttempts++;
                requestAnimationFrame(detect);
                
            } catch (err) {
                console.error('眨眼检测错误:', err);
                this.showError('检测出错: ' + err.message);
                this.resetDetection();
            }
        };
        
        detect();
    }

    async onLiveDetectionSuccess() {
        this.liveDetection.style.display = 'none';
        
        if (this.isNewUser) {
            // 新用户，显示注册表单
            this.showNewUserForm();
        } else {
            // 已存在用户，直接登录
            await this.loginExistingUser();
        }
    }

    async loginExistingUser() {
        this.showLoading('正在登录...');
        
        try {
            const response = await fetch('/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    image: this.tempFaceData
                })
            });
            
            const result = await response.json();
            if (result.success) {
                this.showSuccess(`登录成功，欢迎 ${result.username}！`);
                // 添加重定向
                if (result.redirect) {
                    window.location.href = result.redirect;
                }
            } else {
                this.showError(result.message);
                this.resetDetection();
            }
        } catch (err) {
            this.showError('登录失败: ' + err.message);
            this.resetDetection();
        }
    }

    resetDetection() {
        this.isDetecting = false;
        this.liveDetection.style.display = 'none';
        this.captureButton.style.display = 'block';
        this.captureButton.disabled = false;
    }

    showNewUserForm() {
        this.registerForm.style.display = 'block';
        this.captureButton.style.display = 'none';
        this.showStatus('新用户，请输入您的姓名进行注册');
        this.confirmRegisterButton.disabled = true;
    }

    async register() {
        const username = this.usernameInput.value.trim();
        if (!username) {
            this.showError('请输入姓名');
            return;
        }

        this.confirmRegisterButton.disabled = true;
        this.showLoading('正在注册...');

        try {
            const response = await fetch('/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    image: this.tempFaceData,
                    username: username
                })
            });
            
            const result = await response.json();
            if (result.success) {
                this.showSuccess(`注册成功，欢迎 ${username}！`);
                // 添加重定向
                window.location.href = '/dashboard';
            } else {
                this.showError(result.message);
                this.confirmRegisterButton.disabled = false;
            }
        } catch (err) {
            this.showError('注册失败: ' + err.message);
            this.confirmRegisterButton.disabled = false;
        }
    }

    showStatus(message) {
        this.statusDiv.textContent = message;
        this.statusDiv.className = '';
    }

    showLoading(message) {
        this.statusDiv.textContent = message;
        this.statusDiv.className = 'loading';
    }
    
    showError(message) {
        this.statusDiv.textContent = message;
        this.statusDiv.className = 'error';
    }
    
    showSuccess(message) {
        this.statusDiv.textContent = message;
        this.statusDiv.className = 'success';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const faceAuth = new FaceAuth();
    faceAuth.setupCamera();
});