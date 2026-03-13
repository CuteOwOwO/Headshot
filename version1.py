import cv2
import numpy as np

def generate_avatar(user_img_path, template_path, output_path):
    # 1. 讀取影像 (模板要包含 Alpha 通道)
    user_img = cv2.imread(user_img_path)
    template = cv2.imread(template_path, cv2.IMREAD_UNCHANGED) # 讀取透明度
    
    h, w = template.shape[:2]
    
    # 2. 將用戶照片縮放到模板大小 (或根據需求裁切)
    user_img = cv2.resize(user_img, (w, h))
    
    # 3. 分離 Alpha 通道作為遮罩
    b, g, r, a = cv2.split(template)
    alpha = a / 255.0  # 歸一化到 0~1
    
    # 4. 進行合成
    # 模板有顏色的地方用模板，透明的地方用照片
    for c in range(0, 3):
        user_img[:, :, c] = (alpha * template[:, :, c] + (1 - alpha) * user_img[:, :, c])
        
    # 5. 儲存結果
    cv2.imwrite(output_path, user_img)

# 使用範例
generate_avatar('head.jpg', 'background.png', 'result.jpg')