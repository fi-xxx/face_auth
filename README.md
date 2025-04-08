# 人脸识别情绪分析系统

基于 Flask 和深度学习的人脸识别登录系统，集成了人脸识别、活体检测和情绪分析功能。

## 功能特点

### 核心功能
- 🎥 实时摄像头人脸捕捉
- 🔐 人脸识别自动登录
- 👤 新用户自动注册
- 👁️ 眨眼活体检测
- 😊 情绪识别与分析

### 用户界面
- 📊 情绪趋势分析图表
- 🔍 用户搜索功能
- 📱 响应式界面设计
- 🎨 美观的数据可视化

### 技术特性
- 🤖 DeepFace 情绪识别模型
- 🧬 face_recognition 人脸特征提取
- 👀 基于 EAR 的眨眼检测
- 📈 实时数据统计分析

## 系统要求

- Python 3.8+
- MySQL 5.7+
- 摄像头设备
- Windows/Linux/MacOS
- 4GB+ RAM（用于深度学习模型）

## 使用的深度学习模型

1. **人脸识别模型**
   - 使用 face_recognition 库
   - 基于 dlib 的深度学习模型
   - 人脸特征点检测和编码

2. **情绪识别模型**
   - 使用 DeepFace 框架
   - 支持 7 种基础情绪识别
   - 实时情绪分析

3. **活体检测**
   - 基于面部特征点的眨眼检测
   - EAR（Eye Aspect Ratio）算法
   - 防伪验证机制

## 安装步骤

### 1. 克隆项目

```bash
git clone [repository-url]
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

## 使用说明

### 首次使用（注册）
1. 访问系统首页
2. 点击"开始识别"
3. 完成眨眼活体检测
4. 输入用户名完成注册
5. 自动跳转到控制面板

### 日常使用（登录）
1. 访问系统首页
2. 点击"开始识别"
3. 完成眨眼活体检测
4. 自动识别并登录
5. 进入控制面板

### 情绪记录
1. 进入"情绪记录"页面
2. 点击"捕获表情"按钮
3. 系统自动分析并记录情绪
4. 查看情绪分析结果

### 数据分析
1. 进入"情绪分析"页面
2. 选择时间范围
3. 查看情绪趋势图表
4. 分析情绪变化统计

## 技术架构

### 前端技术
- HTML5 / CSS3
- JavaScript (ES6+)
- Chart.js 图表库
- WebRTC 摄像头接入

### 后端技术
- Flask Web 框架
- MySQL 数据库
- face_recognition 人脸识别
- DeepFace 情绪分析
- OpenCV 图像处理

## 注意事项

1. 确保摄像头正常工作
2. 保持适当的光照条件
3. 正面面对摄像头
4. 建议使用 Chrome 浏览器
5. 首次加载可能较慢（模型加载）

## 常见问题

1. **无法检测到人脸**
   - 检查光线条件
   - 调整与摄像头的距离
   - 确保面部正对摄像头

2. **眨眼检测不响应**
   - 确保眨眼动作明显
   - 检查网络连接状态
   - 调整浏览器权限设置

3. **情绪识别不准确**
   - 保持表情自然
   - 确保光线充足
   - 避免剧烈头部移动

## 维护者

[您的名字/组织]

## 许可证

MIT License

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

## 联系方式

- 作者：[fixxx]
- 邮箱：[ys_fixxx@163.com]
- GitHub：[https://github.com/fi-xxx]
