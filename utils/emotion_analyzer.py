from deepface import DeepFace
from config import Config

class EmotionAnalyzer:
    @staticmethod
    def analyze(img):
        """分析图像中的情绪"""
        try:
            result = DeepFace.analyze(
                img,
                actions=['emotion'],
                enforce_detection=True,
                detector_backend='opencv',
                align=True
            )
            emotion = result[0]['dominant_emotion']
            emotions = result[0]['emotion']
            
            # 将 float32 转换为 Python 原生 float
            emotions = {k: float(v) for k, v in emotions.items()}
            
            # 情绪映射
            detected_emotion = Config.EMOTION_MAP.get(emotion, '平静')
            
            return {
                'emotion': detected_emotion,
                'probabilities': emotions
            }
        except Exception as e:
            raise ValueError(f'情绪分析失败: {str(e)}') 