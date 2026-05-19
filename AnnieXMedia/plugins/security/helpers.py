# Authored By Certified Coders © 2026
# Security Module: Intelligence Helpers
# Logic: Local AI Media Scanning (NudeNet), Permissions, & Concurrent Deletion

import asyncio
import os
import cv2
from pyrogram.enums import ChatMemberStatus
from AnnieXMedia import app
from AnnieXMedia.misc import SUDOERS

# استدعاء مكتبة الذكاء الاصطناعي الحديثة
from nudenet import NudeDetector

# تهيئة المحرك (سيقوم بتحميل الموديل من مصادره الموثوقة تلقائياً في أول تشغيل فقط)
detector = NudeDetector()

# الأجزاء التي يعتبرها البوت إباحية صريحة (تمنع الحذف الخاطئ للصور العادية)
UNSAFE_LABELS = [
    "EXPOSED_GENITALIA",
    "EXPOSED_ANUS",
    "EXPOSED_BREAST_F",
    "EXPOSED_BUTTOCKS"
]

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
    """معالجة وفحص الصورة محلياً باستخدام NudeNet"""
    try:
        # المكتبة تقوم بضبط الأبعاد والفحص واستخراج النتائج تلقائياً
        detections = detector.detect(image_path)
        
        for detection in detections:
            # إذا وجدت المكتبة أي جزء محظور بنسبة تأكد أعلى من 65%، تعتبر الصورة إباحية
            if detection['class'] in UNSAFE_LABELS and detection['score'] > 0.65:
                return True
                
        return False
    except Exception as e:
        print(f"Local Scan Error: {e}")
        return False

async def check_porn_api(file_path: str):
    """تغليف دالة الفحص المحلى لتعمل بشكل غير متزامن مع Pyrogram"""
    return await asyncio.to_thread(_run_local_scan, file_path)

async def scan_video_frames(video_path: str):
    """تحليل لقطات الفيديو محلياً"""
    is_detected = False
    try:
        cam = cv2.VideoCapture(video_path)
        total_frames = int(cam.get(cv2.CAP_PROP_FRAME_COUNT))
        
        if total_frames > 0:
            # فحص ثلاث لقطات مختلفة من الفيديو
            check_points = [0.1, 0.5, 0.9]
            for point in check_points:
                frame_id = int(total_frames * point)
                cam.set(cv2.CAP_PROP_POS_FRAMES, frame_id)
                ret, frame = cam.read()
                if ret:
                    temp_frame = f"{video_path}_check_{int(point*100)}.jpg"
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
    """مسح جماعي سريع للرسائل باستخدام التوازي"""
    msg_ids = list(range(current_id, max(0, current_id - limit), -1))
    chunks = [msg_ids[i:i + 100] for i in range(0, len(msg_ids), 100)]
    
    await asyncio.gather(
        *[app.delete_messages(chat_id, chunk) for chunk in chunks], 
        return_exceptions=True
    )
    return len(msg_ids)
