from flask import Flask, render_template, request, jsonify, session, send_from_directory, redirect, url_for
import mysql.connector
import face_recognition  # 用于人脸识别登录
import cv2              # 用于图像处理和情绪检测
import numpy as np      # 用于数组操作
import os              # 用于文件路径操作
from datetime import datetime  # 用于时间戳
import base64          # 用于图像编码解码
from functools import wraps  # 用于装饰器
from deepface import DeepFace
from PIL import Image
import io

# 配置部分
class Config:
    """应用配置类"""
    SECRET_KEY = 'your-secret-key'
    STATIC_FOLDER = os.path.abspath('static')
    STATIC_URL_PATH = '/static'
    
    # 数据库配置
    DB_CONFIG = {
        'host': 'localhost',
        'user': 'root',
        'password': '1234',
        'database': 'face_auth'
    }
    
    # 人脸识别配置
    FACE_RECOGNITION = {
        'min_quality_width': 200,
        'min_quality_height': 200,
        'face_distance_threshold': 0.4,
        'login_tolerance': 0.6
    }
    
    # 情绪检测配置
    EMOTION_DETECTION = {
        'std_threshold': 45,
        'high_std_threshold': 60,
        'brightness_threshold': 130
    }

# 初始化 Flask 应用
app = Flask(__name__, 
            static_folder=Config.STATIC_FOLDER,
            static_url_path=Config.STATIC_URL_PATH)
app.secret_key = Config.SECRET_KEY

# 数据库操作
def get_db_connection():
    """创建数据库连接"""
    return mysql.connector.connect(**Config.DB_CONFIG)

def init_db():
    """初始化数据库表"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 创建用户表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(255) NOT NULL,
            face_encoding TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 创建情绪表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS emotions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            emotion VARCHAR(50) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    conn.commit()
    cursor.close()
    conn.close()

# 工具函数
def eye_aspect_ratio(eye):
    """计算眼睛纵横比"""
    try:
        # 将关键点转换为numpy数组
        eye_points = np.array(eye)
        
        # 计算垂直方向的距离
        A = np.linalg.norm(eye_points[1] - eye_points[5])
        B = np.linalg.norm(eye_points[2] - eye_points[4])
        
        # 计算水平方向的距离
        C = np.linalg.norm(eye_points[0] - eye_points[3])
        
        # 计算纵横比
        ear = (A + B) / (2.0 * C)
        
        print(f"眼睛关键点: {eye}")
        print(f"垂直距离 A: {A}, B: {B}")
        print(f"水平距离 C: {C}")
        print(f"纵横比 EAR: {ear}")
        
        return ear
    except Exception as e:
        print(f"计算眼睛纵横比错误: {str(e)}")
        return 0.3  # 返回一个默认值

def calculate_face_distance(known_face_encoding, face_encoding_to_check):
    """计算人脸距离"""
    return face_recognition.face_distance([known_face_encoding], face_encoding_to_check)[0]

def detect_emotion(img_data):
    """
    使用 DeepFace 预训练模型进行情绪识别
    
    参数:
        img_data: 图片数据
    返回:
        emotion: 检测到的情绪
    """
    try:
        # 将图片数据转换为 PIL Image
        img = Image.open(io.BytesIO(img_data))
        img = np.array(img)
        
        # 使用 DeepFace 进行情绪分析
        result = DeepFace.analyze(
            img, 
            actions=['emotion'],
            enforce_detection=False  # 如果人脸检测失败，不抛出异常
        )
        
        # 获取情绪结果
        emotion = result[0]['dominant_emotion']
        
        # 将英文情绪映射为中文
        emotion_map = {
            'happy': '开心',
            'sad': '伤心',
            'angry': '愤怒',
            'fear': '恐惧',
            'surprise': '惊讶',
            'neutral': '平静',
            'disgust': '厌恶'
        }
        
        return emotion_map.get(emotion, '平静')
        
    except Exception as e:
        print(f"情绪检测错误: {str(e)}")
        return '平静'  # 发生错误时返回默认情绪

# 装饰器
def login_required(f):
    """登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# 路由处理
@app.route('/')
def index():
    """首页路由"""
    return render_template('index.html')

@app.route('/static/<path:filename>')
def serve_static(filename):
    """静态文件服务"""
    return send_from_directory(app.static_folder, filename)

@app.route('/detect_action', methods=['POST'])
def detect_action():
    """眨眼检测路由"""
    try:
        image_data = request.json['image']
        nparr = np.frombuffer(base64.b64decode(image_data.split(',')[1]), np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # 获取人脸关键点
        face_landmarks = face_recognition.face_landmarks(img)
        if not face_landmarks:
            return jsonify({'detected': False, 'message': '未检测到人脸特征点'})
        
        landmarks = face_landmarks[0]
        
        # 检测眨眼
        left_eye = landmarks['left_eye']
        right_eye = landmarks['right_eye']
        
        # 计算眼睛纵横比
        left_ear = eye_aspect_ratio(left_eye)
        right_ear = eye_aspect_ratio(right_eye)
        ear = (left_ear + right_ear) / 2
        
        # 调整眨眼阈值，使其更严格
        EYE_AR_THRESH = 0.19  # 降低阈值，使其更难触发
        
        if ear < EYE_AR_THRESH:
            print(f"检测到眨眼 - EAR: {ear}")
            return jsonify({
                'detected': True, 
                'message': '检测到眨眼',
                'ear': ear
            })
        
        print(f"未检测到眨眼 - EAR: {ear}")
        return jsonify({
            'detected': False, 
            'message': '请眨眼',
            'ear': ear
        })
        
    except Exception as e:
        print(f"眨眼检测错误: {str(e)}")
        return jsonify({'detected': False, 'message': str(e)})

@app.route('/register', methods=['POST'])
def register():
    """注册路由"""
    try:
        image_data = request.json['image']
        username = request.json.get('username', '').strip()
        
        if not username:
            return jsonify({'success': False, 'message': '请输入姓名'})
        
        # 解码图像
        image_data = base64.b64decode(image_data.split(',')[1])
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # 检测人脸
        face_locations = face_recognition.face_locations(img)
        if not face_locations:
            return jsonify({'success': False, 'message': '未检测到人脸'})
            
        # 检查图像质量
        if img.shape[0] < Config.FACE_RECOGNITION['min_quality_width'] or \
           img.shape[1] < Config.FACE_RECOGNITION['min_quality_height']:
            return jsonify({'success': False, 'message': '图像质量太低，请调整距离'})
            
        # 获取人脸编码
        face_encoding = face_recognition.face_encodings(img)[0]
        
        # 检查是否与现有用户太相似
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT face_encoding FROM users')
        existing_users = cursor.fetchall()
        
        for existing_user in existing_users:
            stored_encoding = np.frombuffer(base64.b64decode(existing_user[0]), dtype=np.float64)
            distance = calculate_face_distance(stored_encoding, face_encoding)
            if distance < Config.FACE_RECOGNITION['face_distance_threshold']:
                cursor.close()
                conn.close()
                return jsonify({'success': False, 'message': '已存在相似用户，请重试'})
        
        # 保存用户信息
        face_encoding_str = base64.b64encode(face_encoding).decode('utf-8')
        cursor.execute(
            'INSERT INTO users (username, face_encoding) VALUES (%s, %s)',
            (username, face_encoding_str)
        )
        conn.commit()
        session['user_id'] = cursor.lastrowid
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': '注册成功',
            'username': username,
            'redirect': url_for('dashboard')
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/check_face', methods=['POST'])
def check_face():
    """检查人脸是否存在"""
    try:
        image_data = request.json['image']
        
        # 解码图像
        image_data = base64.b64decode(image_data.split(',')[1])
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # 检测人脸
        face_locations = face_recognition.face_locations(img)
        if not face_locations:
            return jsonify({'success': False, 'message': '未检测到人脸'})
        
        # 获取人脸编码
        face_encoding = face_recognition.face_encodings(img)[0]
        
        # 检查是否已存在相似用户
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, face_encoding FROM users')
        users = cursor.fetchall()
        
        min_distance = float('inf')
        matched_user = None
        
        for user in users:
            stored_encoding = np.frombuffer(base64.b64decode(user[2]), dtype=np.float64)
            distance = calculate_face_distance(stored_encoding, face_encoding)
            
            if distance < min_distance:
                min_distance = distance
                matched_user = user
        
        if min_distance < Config.FACE_RECOGNITION['face_distance_threshold']:
            session['user_id'] = matched_user[0]
            cursor.close()
            conn.close()
            return jsonify({
                'success': True,
                'exists': True,
                'username': matched_user[1]
            })
        
        cursor.close()
        conn.close()
        return jsonify({
            'success': True,
            'exists': False
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/login', methods=['POST'])
def login():
    """登录路由"""
    try:
        image_data = request.json['image']
        
        # 解码图像
        image_data = base64.b64decode(image_data.split(',')[1])
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # 获取人脸编码
        face_encoding = face_recognition.face_encodings(img)[0]
        
        # 查找匹配用户
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, face_encoding FROM users')
        users = cursor.fetchall()
        
        for user in users:
            stored_encoding = np.frombuffer(base64.b64decode(user[2]), dtype=np.float64)
            matches = face_recognition.compare_faces(
                [stored_encoding], 
                face_encoding, 
                tolerance=Config.FACE_RECOGNITION['login_tolerance']
            )
            if matches[0]:
                session['user_id'] = user[0]
                cursor.close()
                conn.close()
                return jsonify({
                    'success': True,
                    'message': '登录成功',
                    'username': user[1],
                    'redirect': url_for('dashboard')
                })
        
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'message': '用户不存在'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# 添加新的路由
@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # 获取当前用户信息
    cursor.execute('SELECT username FROM users WHERE id = %s', (session['user_id'],))
    current_user = cursor.fetchone()['username']
    
    # 获取所有用户及其最新情绪
    cursor.execute('''
        SELECT 
            u.id,
            u.username,
            e.emotion as latest_emotion,
            e.created_at as emotion_time
        FROM users u
        LEFT JOIN (
            SELECT user_id, emotion, created_at,
                   ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY created_at DESC) as rn
            FROM emotions
        ) e ON u.id = e.user_id AND e.rn = 1
        ORDER BY u.created_at DESC
    ''')
    users = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('dashboard.html', current_user=current_user, users=users)

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

# 情绪记录路由
@app.route('/record_emotion', methods=['POST'])
def record_emotion():
    try:
        if 'user_id' not in session:
            return jsonify({'status': 'error', 'message': '请先登录'})
        
        # 获取 JSON 数据
        data = request.get_json()
        if not data or 'image' not in data:
            return jsonify({'status': 'error', 'message': '未收到图片数据'})
        
        try:
            # 解码 base64 图片数据
            image_data = data['image'].split(',')[1]
            image_bytes = base64.b64decode(image_data)
            
            # 转换为 OpenCV 格式
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                return jsonify({'status': 'error', 'message': '图片解码失败'})
            
            # 使用 DeepFace 进行情绪分析
            result = DeepFace.analyze(
                img, 
                actions=['emotion'],
                enforce_detection=False
            )
            
            emotion = result[0]['dominant_emotion']
            emotion_map = {
                'happy': '开心',
                'sad': '伤心',
                'angry': '愤怒',
                'fear': '恐惧',
                'surprise': '惊讶',
                'neutral': '平静',
                'disgust': '厌恶'
            }
            detected_emotion = emotion_map.get(emotion, '平静')
            
            # 记录到数据库
            conn = get_db_connection()
            cursor = conn.cursor()
            
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 修改 SQL 语句，使用正确的列名
            cursor.execute(
                "INSERT INTO emotions (user_id, emotion, created_at) VALUES (%s, %s, %s)",
                (session['user_id'], detected_emotion, current_time)
            )
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return jsonify({
                'status': 'success',
                'emotion': detected_emotion,
                'message': f'情绪 {detected_emotion} 已记录'
            })
            
        except Exception as e:
            print(f"处理图片数据时出错: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': f'处理图片时发生错误: {str(e)}'
            })
            
    except Exception as e:
        print(f"处理请求时发生错误: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'记录情绪时发生错误: {str(e)}'
        })

@app.route('/search_users', methods=['GET'])
def search_users():
    try:
        # 获取搜索关键词
        search_query = request.args.get('query', '').strip()
        
        # 连接数据库
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 构建SQL查询
        sql = """
        SELECT 
            u.username,
            e.emotion as latest_emotion,
            e.created_at as emotion_time
        FROM users u
        LEFT JOIN (
            SELECT user_id, emotion, created_at,
                   ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY created_at DESC) as rn
            FROM emotions
        ) e ON u.id = e.user_id AND e.rn = 1
        WHERE u.username LIKE %s
        ORDER BY e.created_at DESC
        """
        
        # 执行查询
        cursor.execute(sql, (f'%{search_query}%',))
        users = cursor.fetchall()
        
        # 处理时间格式
        for user in users:
            if user['emotion_time']:
                user['emotion_time'] = user['emotion_time'].strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'users': users
        })
        
    except Exception as e:
        print(f"搜索错误: {str(e)}")  # 添加错误日志
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/get_emotion_history', methods=['GET'])
@login_required
def get_emotion_history():
    """获取情绪历史数据"""
    try:
        days = int(request.args.get('days', 7))
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 获取指定天数的情绪记录
        cursor.execute('''
            SELECT 
                DATE(created_at) as date,
                emotion,
                COUNT(*) as count
            FROM emotions
            WHERE user_id = %s
            AND created_at >= DATE_SUB(CURRENT_DATE, INTERVAL %s DAY)
            GROUP BY DATE(created_at), emotion
            ORDER BY date
        ''', (session['user_id'], days))
        
        records = cursor.fetchall()
        
        # 获取统计信息 - 修改为使用子查询获取主要情绪
        cursor.execute('''
            SELECT 
                COUNT(*) as total_records,
                COUNT(DISTINCT DATE(created_at)) as total_days,
                (
                    SELECT emotion
                    FROM (
                        SELECT emotion, COUNT(*) as emotion_count
                        FROM emotions
                        WHERE user_id = %s
                        AND created_at >= DATE_SUB(CURRENT_DATE, INTERVAL %s DAY)
                        GROUP BY emotion
                        ORDER BY emotion_count DESC
                        LIMIT 1
                    ) as most_common
                ) as main_emotion
            FROM emotions
            WHERE user_id = %s
            AND created_at >= DATE_SUB(CURRENT_DATE, INTERVAL %s DAY)
        ''', (session['user_id'], days, session['user_id'], days))
        
        stats = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        # 处理数据格式
        dates = sorted(list(set(record['date'].strftime('%Y-%m-%d') for record in records)))
        emotions = sorted(list(set(record['emotion'] for record in records)))
        
        # 构建数据集
        datasets = []
        for emotion in emotions:
            data = []
            for date in dates:
                count = 0
                for record in records:
                    if record['date'].strftime('%Y-%m-%d') == date and record['emotion'] == emotion:
                        count = record['count']
                        break
                data.append(count)
            
            datasets.append({
                'label': emotion,
                'data': data,
                'borderColor': get_emotion_color(emotion),
                'backgroundColor': get_emotion_color(emotion, 0.2)
            })
        
        # 计算情绪波动指数
        variation = calculate_emotion_variation(records) if records else 0
        
        return jsonify({
            'success': True,
            'data': {
                'labels': dates,
                'datasets': datasets,
                'stats': {
                    'mainEmotion': stats['main_emotion'] or '-',
                    'emotionVariation': f"{variation:.1f}",
                    'recordCount': stats['total_records']
                }
            }
        })
        
    except Exception as e:
        print(f"获取情绪历史数据错误: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

def get_emotion_color(emotion, alpha=1):
    """获取情绪对应的颜色"""
    colors = {
        '开心': f'rgba(46, 204, 113, {alpha})',     # 更鲜艳的绿色
        '伤心': f'rgba(231, 76, 60, {alpha})',      # 更鲜艳的红色
        '愤怒': f'rgba(230, 126, 34, {alpha})',     # 更鲜艳的橙色
        '平静': f'rgba(52, 152, 219, {alpha})',     # 更鲜艳的蓝色
        '惊讶': f'rgba(155, 89, 182, {alpha})',     # 更鲜艳的紫色
        '疲惫': f'rgba(149, 165, 166, {alpha})'     # 更深的灰色
    }
    return colors.get(emotion, f'rgba(189, 195, 199, {alpha})')

def calculate_emotion_variation(records):
    """计算情绪波动指数"""
    if not records:
        return 0
        
    # 将情绪转换为数值
    emotion_values = {
        '开心': 1,
        '平静': 0,
        '惊讶': 0.5,
        '伤心': -1,
        '愤怒': -0.8,
        '疲惫': -0.3
    }
    
    # 计算情绪变化的标准差
    values = [emotion_values.get(record['emotion'], 0) * record['count'] for record in records]
    if not values:
        return 0
        
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    return (variance ** 0.5) * 100  # 转换为0-100的分数

@app.route('/get_user_list')
def get_user_list():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 修改 SQL 查询，获取最新的情绪记录
        cursor.execute("""
            SELECT 
                u.username,
                e.emotion as latest_emotion,
                DATE_FORMAT(e.created_at, '%Y-%m-%d %H:%i:%s') as created_at
            FROM users u
            LEFT JOIN (
                SELECT user_id, emotion, created_at,
                    ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY created_at DESC) as rn
                FROM emotions
            ) e ON u.id = e.user_id AND e.rn = 1
            ORDER BY e.created_at DESC
        """)
        
        users = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify(users)
        
    except Exception as e:
        print(f"获取用户列表失败: {str(e)}")
        return jsonify([])

@app.route('/get_emotion_stats')
def get_emotion_stats():
    try:
        if 'user_id' not in session:
            return jsonify({'status': 'error', 'message': '请先登录'})
            
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 获取用户最近的情绪统计
        cursor.execute("""
            SELECT 
                emotion,
                COUNT(*) as count,
                DATE(created_at) as date
            FROM emotions
            WHERE user_id = %s
            AND created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            GROUP BY emotion, DATE(created_at)
            ORDER BY date
        """, (session['user_id'],))
        
        stats = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify({
            'labels': list(set(stat['date'].strftime('%Y-%m-%d') for stat in stats)),
            'datasets': [
                {
                    'label': emotion,
                    'data': [stat['count'] for stat in stats if stat['emotion'] == emotion]
                }
                for emotion in set(stat['emotion'] for stat in stats)
            ]
        })
        
    except Exception as e:
        print(f"获取情绪统计失败: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    init_db()
    print("加载证书中...", os.path.exists(r"D:\openSSL\cert.pem"))
    app.run(
        host='0.0.0.0',
        port=5001,
        debug=True,
        ssl_context=(
            r"D:\openSSL\cert.pem",  # 你的证书路径
            r"D:\openSSL\key.pem"    # 你的私钥路径
        )
    )