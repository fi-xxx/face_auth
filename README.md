# 人脸识别登录系统

基于 Flask 和 face_recognition 的人脸识别登录系统，支持人脸识别、活体检测和情绪识别功能。

## 功能特点

- 🎥 实时摄像头人脸捕捉
- 🔐 人脸识别自动登录
- 👤 新用户自动注册
- 👁️ 眨眼活体检测
- 😊 情绪识别功能
- 🔍 用户搜索功能
- 📊 用户管理面板
- 🎨 响应式界面设计

## 系统要求

- Python 3.8+
- MySQL 5.7+
- 摄像头设备
- Windows/Linux/MacOS

## 安装步骤

### 1. 克隆项目

```bash
git clone [https://github.com/fi-xxx/face_auth.git]
cd face-auth-flask
```

### 2. 创建虚拟环境

```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

### 3. 安装依赖

```bash
# 更新pip
python -m pip install --upgrade pip

# 安装依赖包
pip install -r requirements.txt
```

### 4. 配置数据库

```sql
CREATE DATABASE face_auth;
USE face_auth;

-- 用户表
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    face_encoding TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 情绪记录表
CREATE TABLE emotions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    emotion VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### 5. 配置环境变量

创建 `.env` 文件：

```env
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your-secret-key
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your-password
DB_NAME=face_auth
```

## 运行应用

1. 确保虚拟环境已激活
2. 运行应用：
```bash
python ./app.py
```
3. 访问 `https://localhost:5000`

## 使用说明

### 首次使用（注册）

1. 点击"开始识别"
2. 完成眨眼活体检测
3. 输入用户名完成注册
4. 自动跳转到控制面板

### 后续使用（登录）

1. 点击"开始识别"
2. 完成眨眼活体检测
3. 自动识别并登录
4. 进入控制面板

### 控制面板功能

1. 用户管理
   - 查看所有用户
   - 搜索用户
   - 查看用户情绪记录

2. 情绪记录
   - 实时捕获表情
   - 自动识别情绪
   - 记录情绪历史

## 项目结构
