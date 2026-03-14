import cv2
import numpy as np
import os
import glob

def generate_avatar(user_img_path, template_path, output_path):
    # 讀取影像
    user_img = cv2.imread(user_img_path)
    template = cv2.imread(template_path, cv2.IMREAD_UNCHANGED)
    
    # 確保圖片都有成功讀取
    if user_img is None or template is None:
        print(f"錯誤：無法讀取圖片 {user_img_path} 或模板")
        return
        
    th, tw = template.shape[:2]
    uh, uw = user_img.shape[:2]
    
    # 計算縮放比例：取寬度或高度縮放比例較大者，確保照片能完全填滿模板
    scale = max(tw / uw, th / uh)
    new_w, new_h = int(uw * scale), int(uh * scale)
    
    # 將用戶照片等比例縮放
    resized_user = cv2.resize(user_img, (new_w, new_h))
    
    # 置中裁切 
    x = (new_w - tw) // 2
    y = (new_h - th) // 2
    
    
    cropped_user = resized_user[y:y+th, x:x+tw]
    
    # 分離 Alpha 通道作為遮罩
    b, g, r, a = cv2.split(template)
    alpha = a / 255.0  
    
    # 4進行合成
    for c in range(0, 3):
        cropped_user[:, :, c] = (alpha * template[:, :, c] + (1 - alpha) * cropped_user[:, :, c])
        
    # 儲存結果
    cv2.imwrite(output_path, cropped_user)

# --- 單張測試 ---
# generate_avatar('head.jpg', 'background.png', 'result.jpg')

# --- 批次處理資料夾範例 ---
def process_folder(input_folder, template_path, output_folder):
    # 確保輸出資料夾存在
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        
    # 抓取資料夾內所有 jpg 和 png 照片 (可依需求增加副檔名)
    image_paths = glob.glob(os.path.join(input_folder, "*.[jJ][pP][gG]")) + \
                  glob.glob(os.path.join(input_folder, "*.[pP][nN][gG]"))
                  
    for img_path in image_paths:
        filename = os.path.basename(img_path)
        out_path = os.path.join(output_folder, filename)
        
        print(f"處理中: {filename}...")
        generate_avatar(img_path, template_path, out_path)
        
    print("批次處理完成！")

# 使用範例：把 input_photos 資料夾裡的照片全部轉換，存到 output_photos
# process_folder('input_photos', 'background.png', 'output_photos')
