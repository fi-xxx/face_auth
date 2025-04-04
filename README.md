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

## 技术栈

- 后端：Flask + MySQL
- 人脸识别：face_recognition + OpenCV
- 前端：HTML5 + CSS3 + JavaScript
- 数据库：MySQL

## 安全特性

- 眨眼活体检测防止照片攻击
- 人脸编码安全存储
- 会话管理和认证
- SQL注入防护
- XSS防护
- CSRF防护

## 开发者指南

### 代码规范

- Python代码遵循PEP 8规范
- JavaScript代码遵循ESLint规范
- CSS采用BEM命名规范

### 测试

```bash
# 运行测试
pytest tests/
```

### 代码格式化

```bash
# Python代码格式化
black .

# 代码检查
flake8
```

## 常见问题

1. 摄像头访问失败
   - 检查浏览器摄像头权限
   - 确认摄像头未被其他程序占用

2. 人脸识别不准确
   - 调整光线条件
   - 确保人脸正对摄像头
   - 调整与摄像头的距离

3. 数据库连接错误
   - 检查数据库配置
   - 确认MySQL服务运行状态

## 更新日志

### v1.0.0 (2024-04-04)
- 初始版本发布
- 基础人脸识别功能
- 眨眼活体检测
- 情绪识别功能
- 用户管理面板

## 贡献指南

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

没有，啊哈哈

## 联系方式

- 作者：[fixxx]
- 邮箱：[ys_fixxx@163.com]
- GitHub：[https://github.com/fi-xxx]
