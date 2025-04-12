import mysql.connector
from contextlib import contextmanager
from config import Config

class Database:
    @staticmethod
    @contextmanager
    def get_connection():
        """获取数据库连接"""
        conn = mysql.connector.connect(**Config.DB_CONFIG)
        try:
            yield conn
        finally:
            conn.close()

    @staticmethod
    def init_tables():
        """初始化数据库表"""
        with Database.get_connection() as conn:
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

    @staticmethod
    def save_emotion(user_id, emotion, created_at):
        """保存情绪记录"""
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO emotions (user_id, emotion, created_at) VALUES (%s, %s, %s)",
                (user_id, emotion, created_at)
            )
            conn.commit()

    @staticmethod
    def get_user_list():
        """获取用户列表"""
        with Database.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT 
                    u.username,
                    e.emotion as latest_emotion,
                    DATE_FORMAT(e.created_at, '%Y-%m-%d %H:%i:%s') as emotion_time
                FROM users u
                LEFT JOIN (
                    SELECT user_id, emotion, created_at,
                        ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY created_at DESC) as rn
                    FROM emotions
                ) e ON u.id = e.user_id AND e.rn = 1
                ORDER BY e.created_at DESC
            """)
            return cursor.fetchall()

    @staticmethod
    def search_users(query):
        """搜索用户"""
        with Database.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
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
            """, (f'%{query}%',))
            return cursor.fetchall()

    @staticmethod
    def get_emotion_history(user_id, days):
        """获取情绪历史数据"""
        with Database.get_connection() as conn:
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
            ''', (user_id, days))
            records = cursor.fetchall()
            
            # 获取统计信息
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
            ''', (user_id, days, user_id, days))
            
            stats = cursor.fetchone()
            return records, stats 