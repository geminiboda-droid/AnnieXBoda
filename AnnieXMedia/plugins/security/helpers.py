# Authored By Certified Coders © 2026
# Security Module: Intelligence Helpers
# Logic: Local AI Media Scanning (ONNX), Permissions, & Concurrent Deletion

import asyncio
import os
import urllib.request
import cv2
import numpy as np
import onnxruntime as ort
from pyrogram.enums import ChatMemberStatus
from AnnieXMedia import app
from AnnieXMedia.misc import SUDOERS

# --- إعدادات المحرك الأمني ---
MODEL_PATH = "nsfw_detector.onnx"
MODEL_URL = "https://github.com/GantMan/nsfw_model/releases/download/1.2.0/nsfw_detector.onnx"

# تحميل النموذج تلقائياً إذا لم يكن موجوداً
if not os.path.exists(MODEL_PATH):
    print("Downloading NSFW Detection Model...")
    try:
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
        print("Model downloaded successfully.")
    except Exception as e:
        print(f"Model download failed: {e}")

# إعدادات جلسة ONNX لاستغلال 8 أنوية
sess_options = ort.SessionOptions()
sess_options.intra_op_num_threads = 8
sess_options.execution_mode = ort.ExecutionMode.ORT_PARALLEL
sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

# تحميل الجلسة
try:
    session = ort.InferenceSession(MODEL_PATH, sess_options=sess_options, providers=['CPUExecutionProvider'])
except Exception as e:
    print(f"Error initializing ONNX session: {e}")
    session = None

async def has_permission(chat_id: int, user_id: int):
    """التحقق من صلاحيات المستخدم"""
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
    """معالجة وفحص الصورة محلياً باستخدام النموذج"""
    if session is None:
        return False
    try:
        img = cv2.imread(image_path)
        if img is None: return False
        
        # تجهيز الصورة (تغيير الأبعاد والتطبيع)
        img = cv2.resize(img, (224, 224))
        img = img.astype(np.float32) / 255.0
        img = np.expand_dims(img, axis=0)
        
        input_name = session.get_inputs()[0].name
        results = session.run(None, {input_name: img})
        
        # التنبؤ (القيمة الثانية في المصفوفة هي غالباً نسبة الإباحية)
        score = results[0][0][1] 
        return score > 0.7
    except Exception as e:
        print(f"Local Scan Error: {e}")
        return False

async def check_porn_local(file_path: str):
    """تغليف دالة الفحص المحلى لتعمل بشكل غير متزامن"""
    return await asyncio.to_thread(_run_local_scan, file_path)

async def scan_video_frames(video_path: str):
    """تحليل لقطات الفيديو محلياً"""
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
                    
                    if await check_porn_local(temp_frame):
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
    """مسح جماعي سريع للرسائل باستخدام التوازي"""
    msg_ids = list(range(current_id, max(0, current_id - limit), -1))
    chunks = [msg_ids[i:i + 100] for i in range(0, len(msg_ids), 100)]
    
    await asyncio.gather(
        *[app.delete_messages(chat_id, chunk) for chunk in chunks], 
        return_exceptions=True
    )
    return len(msg_ids)
