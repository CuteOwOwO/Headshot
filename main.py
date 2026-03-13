from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
import cv2
import numpy as np

app = FastAPI()

def process_image(user_bytes, template_bytes, offset_x: int, offset_y: int, target_width: int):
    # 1. 讀取圖片
    user_img = cv2.imdecode(np.frombuffer(user_bytes, np.uint8), cv2.IMREAD_COLOR)
    template = cv2.imdecode(np.frombuffer(template_bytes, np.uint8), cv2.IMREAD_UNCHANGED)
    
    uh, uw = user_img.shape[:2]
    th, tw = template.shape[:2]
    
    # 2. 將模板縮放到前端指定的大小 (維持比例)
    scale = target_width / tw
    new_tw, new_th = int(tw * scale), int(th * scale)
    template_resized = cv2.resize(template, (new_tw, new_th))
    
    # 3. 準備一塊畫布 (大小等於縮放後的模板)
    # 為了避免超出邊界的背景變成黑色，這裡填滿白色背景 (255, 255, 255)
    cropped_user = np.full((new_th, new_tw, 3), 255, dtype=np.uint8)
    
    # 4. 安全計算交集範圍 (防呆：防止使用者把模板拖移到照片外面)
    u_x1, u_y1 = 0, 0
    u_x2, u_y2 = uw, uh
    
    t_x1, t_y1 = offset_x, offset_y
    t_x2, t_y2 = offset_x + new_tw, offset_y + new_th
    
    # 找出兩者的重疊區塊
    i_x1 = max(u_x1, t_x1)
    i_y1 = max(u_y1, t_y1)
    i_x2 = min(u_x2, t_x2)
    i_y2 = min(u_y2, t_y2)
    
    # 如果有重疊，才把照片對應的區域貼到畫布上
    if i_x1 < i_x2 and i_y1 < i_y2:
        valid_user_part = user_img[i_y1:i_y2, i_x1:i_x2]
        
        # 計算在畫布上的相對位置
        c_x1 = i_x1 - t_x1
        c_y1 = i_y1 - t_y1
        c_x2 = c_x1 + (i_x2 - i_x1)
        c_y2 = c_y1 + (i_y2 - i_y1)
        
        cropped_user[c_y1:c_y2, c_x1:c_x2] = valid_user_part

    # 5. Alpha 合成
    b, g, r, a = cv2.split(template_resized)
    alpha = a / 255.0
    
    result = np.zeros((new_th, new_tw, 3), dtype=np.uint8)
    for c in range(3):
        result[:, :, c] = (alpha * template_resized[:, :, c] + (1 - alpha) * cropped_user[:, :, c])
        
    _, encoded_img = cv2.imencode('.jpg', result)
    return encoded_img.tobytes()

@app.post("/api/generate")
async def generate_avatar(
    user_photo: UploadFile = File(...), 
    template: UploadFile = File(...),
    offset_x: int = Form(...),
    offset_y: int = Form(...),
    target_width: int = Form(...)
):
    user_bytes = await user_photo.read()
    template_bytes = await template.read()
    
    result_bytes = process_image(user_bytes, template_bytes, offset_x, offset_y, target_width)
    return Response(content=result_bytes, media_type="image/jpeg")

app.mount("/", StaticFiles(directory="static", html=True), name="static")