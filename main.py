from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
import cv2
import numpy as np

app = FastAPI()

MAX_FILE_SIZE = 20 * 1024 * 1024  # 設定最大限制為 20 MB

def process_image(user_img, template, offset_x: int, offset_y: int, target_width: int):
    # 圖片已經在外面解碼與檢查過了，直接拿來用
    uh, uw = user_img.shape[:2]
    th, tw = template.shape[:2]
    
    # 將模板縮放到前端指定的大小 (維持比例)
    scale = target_width / tw
    new_tw, new_th = int(tw * scale), int(th * scale)
    template_resized = cv2.resize(template, (new_tw, new_th))
    
    # 準備畫布 (填滿白色背景)
    cropped_user = np.full((new_th, new_tw, 3), 255, dtype=np.uint8)
    
    # 安全計算交集範圍
    u_x1, u_y1 = 0, 0
    u_x2, u_y2 = uw, uh
    
    t_x1, t_y1 = offset_x, offset_y
    t_x2, t_y2 = offset_x + new_tw, offset_y + new_th
    
    i_x1 = max(u_x1, t_x1)
    i_y1 = max(u_y1, t_y1)
    i_x2 = min(u_x2, t_x2)
    i_y2 = min(u_y2, t_y2)
    
    if i_x1 < i_x2 and i_y1 < i_y2:
        valid_user_part = user_img[i_y1:i_y2, i_x1:i_x2]
        c_x1 = i_x1 - t_x1
        c_y1 = i_y1 - t_y1
        c_x2 = c_x1 + (i_x2 - i_x1)
        c_y2 = c_y1 + (i_y2 - i_y1)
        cropped_user[c_y1:c_y2, c_x1:c_x2] = valid_user_part

    # Alpha 合成
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
    
    # 限制檔案大小 (超過 20MB 直接拒絕)
    if len(user_bytes) > MAX_FILE_SIZE or len(template_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="檔案太大了啦！")
    
    # 檢查是否為合法圖片
    user_img = cv2.imdecode(np.frombuffer(user_bytes, np.uint8), cv2.IMREAD_COLOR)
    template_img = cv2.imdecode(np.frombuffer(template_bytes, np.uint8), cv2.IMREAD_UNCHANGED)
    
    if user_img is None or template_img is None:
        raise HTTPException(status_code=400, detail="這好像不是正常的圖片檔喔！")
        
    # 確保模板有透明度 (Alpha Channel)
    if template_img.shape[2] != 4:
        raise HTTPException(status_code=400, detail="模板圖片必須是帶有透明背景的 PNG 檔！")
    
    result_bytes = process_image(user_img, template_img, offset_x, offset_y, target_width)
    return Response(content=result_bytes, media_type="image/jpeg")

app.mount("/", StaticFiles(directory="static", html=True), name="static")