# 人脸识别登录系统 (Face Authentication System)

这是一个基于 Flask 和 face_recognition 的人脸识别登录系统，支持人脸识别、活体检测和自动注册功能。

## 功能特点

- 实时摄像头人脸捕捉
- 人脸识别自动登录
- 新用户自动注册
- 眨眼活体检测
- 基于 MySQL 的用户数据存储

## 系统要求

- Python 3.8+
- MySQL 5.7+
- Windows/Linux/MacOS
- 摄像头设备

## 安装步骤

### 1. 克隆项目
```bash
git clone [项目地址]
cd face-auth-flask
```

### 2. 创建并配置 MySQL 数据库
```sql
CREATE DATABASE face_auth;
USE face_auth;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    face_encoding TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3. 安装依赖

建议先创建虚拟环境：
```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
.\venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

安装依赖包：
```bash
# 更新 pip
python -m pip install --upgrade pip

# 安装依赖
pip install -r requirements.txt
```

### 4. 配置数据库连接

在 `app.py` 中修改数据库配置：
```python
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'xxxx',  # 修改为您的数据库密码
    'database': 'face_auth'
}
```

## 运行应用

1. 确保虚拟环境已激活
2. 运行应用：
```bash
python app.py
```
3. 在浏览器中访问：`http://localhost:5000`

## 使用流程

1. 首次使用：
   - 点击"开始识别"
   - 完成眨眼活体检测
   - 系统识别为新用户，提示输入姓名
   - 输入姓名后完成注册

2. 后续使用：
   - 点击"开始识别"
   - 完成眨眼活体检测
   - 系统自动识别并登录

## 项目结构
