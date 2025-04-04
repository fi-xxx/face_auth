from flask import Flask, render_template, request, jsonify, session, send_from_directory
import mysql.connector
import face_recognition
import cv2
import numpy as np
import os
from datetime import datetime
import base64

app = Flask(__name__, 
            static_folder=os.path.abspath('static'),
            static_url_path='/static'
           )
app.secret_key = 'your-secret-key'  # 用于session加密

# MySQL配置
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '1234',
    'database': 'face_auth'
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(255) NOT NULL,
            face_encoding TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    cursor.close()
    conn.close()

def eye_aspect_ratio(eye):
    # 计算眼睛纵横比
    A = np.linalg.norm(np.array(eye[1]) - np.array(eye[5]))
    B = np.linalg.norm(np.array(eye[2]) - np.array(eye[4]))
    C = np.linalg.norm(np.array(eye[0]) - np.array(eye[3]))
    ear = (A + B) / (2.0 * C)
    return ear

@app.route('/')
def index():
    print("当前工作目录:", os.getcwd())
    print("静态文件目录:", app.static_folder)
    print("模板目录:", app.template_folder)
    return render_template('index.html')

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

@app.route('/detect_action', methods=['POST'])
def detect_action():
    try:
        image_data = request.json['image']
        
        # 解码图像
        image_data = base64.b64decode(image_data.split(',')[1])
        nparr = np.frombuffer(image_data, np.uint8)
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
        
        if ear < 0.2:  # 眨眼阈值
            return jsonify({'detected': True, 'message': '检测到眨眼'})
        
        return jsonify({'detected': False, 'message': '请眨眼'})
        
    except Exception as e:
        return jsonify({'detected': False, 'message': str(e)})

@app.route('/register', methods=['POST'])
def register():
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
        if img.shape[0] < 200 or img.shape[1] < 200:
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
            if distance < 0.4:  # 使用相同的严格阈值
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
            'username': username
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

def calculate_face_distance(known_face_encoding, face_encoding_to_check):
    face_distance = face_recognition.face_distance([known_face_encoding], face_encoding_to_check)
    return face_distance[0]

@app.route('/check_face', methods=['POST'])
def check_face():
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
            # 计算人脸距离
            distance = calculate_face_distance(stored_encoding, face_encoding)
            
            # 使用更严格的匹配条件
            if distance < min_distance:
                min_distance = distance
                matched_user = user
        
        # 设置更严格的阈值
        if min_distance < 0.4:  # 降低这个值会提高识别严格度
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
            matches = face_recognition.compare_faces([stored_encoding], face_encoding, tolerance=0.6)
            if matches[0]:
                session['user_id'] = user[0]
                cursor.close()
                conn.close()
                return jsonify({
                    'success': True,
                    'message': '登录成功',
                    'username': user[1]
                })
        
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'message': '用户不存在'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

if __name__ == '__main__':
    init_db()
    app.run(debug=True) 