import face_recognition
import numpy as np
from config import Config

class FaceRecognition:
    @staticmethod
    def detect_face(img):
        """检测人脸"""
        face_locations = face_recognition.face_locations(img)
        if not face_locations:
            raise ValueError('未检测到人脸')
        return face_locations

    @staticmethod
    def get_face_encoding(img):
        """获取人脸编码"""
        face_encodings = face_recognition.face_encodings(img)
        if not face_encodings:
            raise ValueError('未检测到人脸特征')
        return face_encodings[0]

    @staticmethod
    def calculate_face_distance(known_face_encoding, face_encoding_to_check):
        """计算人脸距离"""
        return face_recognition.face_distance([known_face_encoding], face_encoding_to_check)[0]

    @staticmethod
    def check_face_similarity(face_encoding, stored_encoding):
        """检查人脸相似度"""
        distance = FaceRecognition.calculate_face_distance(stored_encoding, face_encoding)
        return distance < Config.FACE_RECOGNITION['face_distance_threshold']

    @staticmethod
    def get_face_landmarks(img):
        """获取人脸关键点"""
        landmarks = face_recognition.face_landmarks(img)
        if not landmarks:
            raise ValueError('未检测到人脸特征点')
        return landmarks[0] 