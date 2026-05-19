import asyncio
import os
import cv2
import numpy as np
import onnxruntime as ort
from pyrogram.enums import ChatMemberStatus
from AnnieXMedia import app
from AnnieXMedia.misc import SUDOERS

# تحميل نموذج الفحص محلياً
# تأكد من تحميل ملف nsfw_detector.onnx ووضعه في نفس مسار البوت
MODEL_PATH = "nsfw_detector.onnx"
session = ort.InferenceSession(MODEL_PATH)

async def has_permission(chat_id: int, user_id: int):
    if user_id in SUDOERS:
        return True
    try:
        member = await app.get_chat_member(chat_id, user_id)
        if member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return True
    except:
        return False
    return False

def _run_local_scan(image_path: str) -> bool:
    """المنطق البرمجي لفحص الصورة محلياً"""
    try:
        img = cv2.imread(image_path)
        img = cv2.resize(img, (224, 224))
        img = img.astype(np.float32) / 255.0
        img = np.expand_dims(img, axis=0)
        
        input_name = session.get_inputs()[0].name
        results = session.run(None, {input_name: img})
        
        # القيمة الأولى في النتائج تمثل نسبة الإباحية في النموذج الشهير
        porn_score = results[0][0][0]
        return porn_score > 0.7
    except Exception as e:
        print(f"Local Scan Error: {e}")
        return False

async def check_porn_api(file_path: str):
    """تغليف دالة الفحص المحلى لتتوافق مع طبيعة البوت غير المتزامنة"""
    return await asyncio.to_thread(_run_local_scan, file_path)

async def scan_video_frames(video_path: str):
    """تحليل لقطات الفيديو محلياً بدون أي API"""
    is_detected = False
    try:
        cam = cv2.VideoCapture(video_path)
        total_frames = int(cam.get(cv2.CAP_PROP_FRAME_COUNT))
        
        if total_frames > 0:
            check_points = [0.1, 0.5, 0.9]
            for point in check_points:
                frame_id = int(total_frames * point)
                cam.set(cv2.CAP_PROP_POS_FRAMES, frame_id)
                ret, frame = cam.read()
                if ret:
                    temp_frame = f"{video_path}_check.jpg"
                    cv2.imwrite(temp_frame, frame)
                    
                    if await check_porn_api(temp_frame):
                        is_detected = True
                        if os.path.exists(temp_frame): os.remove(temp_frame)
                        break 
                    
                    if os.path.exists(temp_frame):
                        os.remove(temp_frame)
        cam.release()
    except Exception as e:
        print(f"Video Frame Scan Error: {e}")
    return is_detected

async def force_delete(chat_id: int, current_id: int, limit: int):
    msg_ids = list(range(current_id, max(0, current_id - limit), -1))
    chunks = [msg_ids[i:i + 100] for i in range(0, len(msg_ids), 100)]
    await asyncio.gather(*[app.delete_messages(chat_id, chunk) for chunk in chunks], return_exceptions=True)
    return len(msg_ids)
