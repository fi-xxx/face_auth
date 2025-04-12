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