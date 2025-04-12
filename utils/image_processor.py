import cv2
import numpy as np
import base64
from config import Config

class ImageProcessor:
    @staticmethod
    def decode_base64_image(base64_string):
        """解码base64图像数据"""
        try:
            if ',' in base64_string:
                base64_string = base64_string.split(',')[1]
            image_bytes = base64.b64decode(base64_string)
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                raise ValueError('图片解码失败')
            return img
        except Exception as e:
            raise ValueError(f'图片处理失败: {str(e)}')

    @staticmethod
    def check_image_quality(img):
        """检查图像质量"""
        if img.shape[0] < Config.FACE_RECOGNITION['min_quality_width'] or \
           img.shape[1] < Config.FACE_RECOGNITION['min_quality_height']:
            raise ValueError('图像质量太低，请调整距离')
        return True

    @staticmethod
    def resize_image(img, target_size=224):
        """调整图像大小并保持宽高比"""
        height, width = img.shape[:2]
        max_dim = max(height, width)
        scale = target_size / max_dim
        new_height, new_width = int(height * scale), int(width * scale)
        return cv2.resize(img, (new_width, new_height)) 