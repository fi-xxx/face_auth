from flask import Flask, render_template, request, jsonify, session, send_from_directory, redirect, url_for
from datetime import datetime
from functools import wraps
import base64
import os
import numpy as np

from config import Config
from utils.image_processor import ImageProcessor
from utils.emotion_analyzer import EmotionAnalyzer
from utils.database import Database
from utils.face_recognition import FaceRecognition
from utils.emotion_utils import get_emotion_color, calculate_emotion_variation

def eye_aspect_ratio(eye):
    """计算眼睛纵横比(EAR)"""
    try:
        # 确保坐标点是 numpy 数组
        eye = np.array(eye)
        
        # 计算垂直方向上的欧氏距离
        A = np.linalg.norm(eye[1] - eye[5])
        B = np.linalg.norm(eye[2] - eye[4])
        
        # 计算水平方向上的欧氏距离
        C = np.linalg.norm(eye[0] - eye[3])
        
        # 计算眼睛纵横比
        ear = (A + B) / (2.0 * C)
        return ear
    except Exception as e:
        print(f"计算眼睛纵横比时出错: {str(e)}")
        return 0.0

# 初始化 Flask 应用
app = Flask(__name__, 
            static_folder=Config.STATIC_FOLDER,
            static_url_path=Config.STATIC_URL_PATH)
app.secret_key = Config.SECRET_KEY

# 装饰器
def login_required(f):
    """登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# 统一的响应格式
def make_response(success=True, message='', data=None):
    return jsonify({
        'status': 'success' if success else 'error',
        'message': message,
        **(({'data': data} if data else {}))
    })

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
        img = ImageProcessor.decode_base64_image(image_data)
        
        # 获取人脸关键点
        landmarks = FaceRecognition.get_face_landmarks(img)
        if not landmarks:
            return make_response(False, '未检测到人脸特征点')
        
        # 检测眨眼
        left_eye = landmarks.get('left_eye')
        right_eye = landmarks.get('right_eye')
        
        if not left_eye or not right_eye:
            return make_response(False, '未检测到眼睛特征点')
        
        # 计算眼睛纵横比
        left_ear = eye_aspect_ratio(left_eye)
        right_ear = eye_aspect_ratio(right_eye)
        ear = (left_ear + right_ear) / 2
        
        # 眨眼阈值
        EYE_AR_THRESH = 0.22
        
        if ear < EYE_AR_THRESH:
            print(f"检测到眨眼 - EAR: {ear}")
            return make_response(True, '检测到眨眼', {'ear': ear})
        
        print(f"未检测到眨眼 - EAR: {ear}")
        return make_response(False, '请眨眼', {'ear': ear})
        
    except Exception as e:
        print(f"眨眼检测错误: {str(e)}")
        return make_response(False, str(e))

@app.route('/register', methods=['POST'])
def register():
    """注册路由"""
    try:
        image_data = request.json['image']
        username = request.json.get('username', '').strip()
        
        if not username:
            return make_response(False, '请输入姓名')
        
        # 解码图像
        img = ImageProcessor.decode_base64_image(image_data)
        
        # 检测人脸
        FaceRecognition.detect_face(img)
            
        # 检查图像质量
        ImageProcessor.check_image_quality(img)
            
        # 获取人脸编码
        face_encoding = FaceRecognition.get_face_encoding(img)
        
        # 检查是否与现有用户太相似
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT face_encoding FROM users')
            existing_users = cursor.fetchall()
            
            for existing_user in existing_users:
                stored_encoding = np.frombuffer(base64.b64decode(existing_user[0]), dtype=np.float64)
                if FaceRecognition.check_face_similarity(face_encoding, stored_encoding):
                    return make_response(False, '已存在相似用户，请重试')
            
            # 保存用户信息
            face_encoding_str = base64.b64encode(face_encoding).decode('utf-8')
            cursor.execute(
                'INSERT INTO users (username, face_encoding) VALUES (%s, %s)',
                (username, face_encoding_str)
            )
            conn.commit()
            session['user_id'] = cursor.lastrowid
        
        return make_response(True, '注册成功', {
            'username': username,
            'redirect': url_for('dashboard')
        })
        
    except Exception as e:
        return make_response(False, str(e))

@app.route('/check_face', methods=['POST'])
def check_face():
    """人脸验证路由"""
    try:
        # 1. 获取并验证图片数据
        data = request.get_json()
        if not data or 'image' not in data:
            return make_response(False, '未收到图片数据')
        
        try:
            # 2. 解码和处理图片
            img = ImageProcessor.decode_base64_image(data['image'])
            if img is None:
                return make_response(False, '图片解码失败')
            
            # 3. 检查图片质量
            ImageProcessor.check_image_quality(img)
            
            # 4. 获取人脸特征
            face_encoding = FaceRecognition.get_face_encoding(img)
            
            # 5. 从数据库获取所有用户
            with Database.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute('SELECT id, username, face_encoding FROM users')
                users = cursor.fetchall()
                
                # 6. 首先用严格阈值检查用户是否存在
                for user in users:
                    stored_encoding = np.frombuffer(base64.b64decode(user['face_encoding']), dtype=np.float64)
                    distance = FaceRecognition.calculate_face_distance(stored_encoding, face_encoding)
                    
                    # 如果找到匹配用户，使用宽松阈值进行最终验证
                    if distance < Config.FACE_RECOGNITION['face_distance_threshold']:
                        # 使用宽松阈值进行最终验证
                        if distance < Config.FACE_RECOGNITION['login_tolerance']:
                            session['user_id'] = user['id']
                            return make_response(True, '验证成功', {
                                'exists': True,
                                'username': user['username']
                            })
                        else:
                            return make_response(False, '人脸特征不匹配，请重试')
                
                # 如果没有找到匹配用户
                return make_response(False, '未找到匹配用户，请先注册')
                
        except ValueError as ve:
            print(f"人脸检测失败: {str(ve)}")
            return make_response(False, '未能检测到人脸，请调整姿势或光线')
            
        except Exception as e:
            print(f"处理图片数据时出错: {str(e)}")
            return make_response(False, f'处理图片时发生错误: {str(e)}')
            
    except Exception as e:
        print(f"请求处理错误: {str(e)}")
        return make_response(False, f'验证失败: {str(e)}')

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return make_response(True, '已退出登录')

@app.route('/record_emotion', methods=['POST'])
@login_required
def record_emotion():
    """情绪记录路由"""
    try:
        # 1. 获取并验证图片数据
        data = request.get_json()
        if not data or 'image' not in data:
            return make_response(False, '未收到图片数据')
        
        try:
            # 2. 解码和处理图片
            img = ImageProcessor.decode_base64_image(data['image'])
            if img is None:
                return make_response(False, '图片解码失败')

            # 3. 检测人脸
            FaceRecognition.detect_face(img)
            
            # 4. 检查图像质量
            ImageProcessor.check_image_quality(img)
            
            # 5. 调整图像大小
            img = ImageProcessor.resize_image(img)
            
            # 6. 分析情绪
            result = EmotionAnalyzer.analyze(img)
            
            # 7. 记录到数据库
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            Database.save_emotion(session['user_id'], result['emotion'], current_time)

            # 8. 返回结果
            return make_response(
                True,
                f'情绪 {result["emotion"]} 已记录',
                {
                    'emotion': result['emotion'],
                    'details': {
                        'probabilities': result['probabilities'],
                        'timestamp': current_time
                    }
                }
            )
            
        except ValueError as ve:
            print(f"人脸检测失败: {str(ve)}")
            return make_response(False, '未能检测到人脸，请调整姿势或光线')
            
        except Exception as e:
            print(f"处理图片数据时出错: {str(e)}")
            return make_response(False, f'处理图片时发生错误: {str(e)}')
            
    except Exception as e:
        print(f"请求处理错误: {str(e)}")
        return make_response(False, f'记录情绪时发生错误: {str(e)}')

@app.route('/search_users', methods=['GET'])
def search_users():
    try:
        search_query = request.args.get('query', '').strip()
        users = Database.search_users(search_query)
        return make_response(True, '搜索成功', {'users': users})
        
    except Exception as e:
        print(f"搜索错误: {str(e)}")
        return make_response(False, str(e))

@app.route('/get_emotion_history', methods=['GET'])
@login_required
def get_emotion_history():
    """获取情绪历史数据"""
    try:
        days = int(request.args.get('days', 7))
        records, stats = Database.get_emotion_history(session['user_id'], days)
        
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
        
        return make_response(True, '获取成功', {
            'labels': dates,
            'datasets': datasets,
            'stats': {
                'mainEmotion': stats['main_emotion'] or '-',
                'emotionVariation': f"{variation:.1f}",
                'recordCount': stats['total_records']
            }
        })
        
    except Exception as e:
        print(f"获取情绪历史数据错误: {str(e)}")
        return make_response(False, str(e))

@app.route('/get_user_list')
def get_user_list():
    try:
        users = Database.get_user_list()
        return make_response(True, '获取成功', users)
        
    except Exception as e:
        print(f"获取用户列表失败: {str(e)}")
        return make_response(False, str(e))

@app.route('/dashboard')
@login_required
def dashboard():
    """仪表板路由"""
    try:
        with Database.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute('SELECT username FROM users WHERE id = %s', (session['user_id'],))
            user = cursor.fetchone()
            
        if not user:
            return redirect(url_for('index'))
            
        return render_template('dashboard.html', current_user=user['username'])
        
    except Exception as e:
        print(f"获取用户信息失败: {str(e)}")
        return redirect(url_for('index'))

if __name__ == '__main__':
    Database.init_tables()
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