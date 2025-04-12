import os

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

    # 情绪映射配置
    EMOTION_MAP = {
        'happy': '开心',
        'sad': '伤心',
        'angry': '愤怒',
        'fear': '恐惧',
        'surprise': '惊讶',
        'neutral': '平静',
        'disgust': '厌恶'
    } 