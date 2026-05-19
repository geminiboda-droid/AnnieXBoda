# Authored By Certified Coders © 2026
# Security Module: Database Manager
# Optimized to reuse AnnieXMedia Core Mongo Connection

from typing import Dict, Any
from AnnieXMedia.core.mongo import mongodb

# --- تعريف مجموعات الحماية (Collections) ---
# سيتم إنشاء هذه المجموعات تلقائياً داخل نفس قاعدة بيانات السورس
db_locks = mongodb.protection_locks
db_warns = mongodb.protection_warns

# ==========================================
# دالات جلب وتحديث الأقفال (النظام الديناميكي الجديد)
# ==========================================

async def get_lock_settings(chat_id: int) -> Dict[str, Any]:
    """جلب إعدادات الأقفال الديناميكية للمجموعة"""
    try:
        doc = await db_locks.find_one({"chat_id": chat_id})
        return doc.get("settings", {}) if doc else {}
    except Exception as e:
        print(f"Error getting lock settings: {e}")
        return {}

async def set_lock_settings(chat_id: int, key: str, settings: dict = None):
    """
    حفظ أو مسح إعدادات قفل معين
    إذا كان settings يساوي None، سيتم حذف القفل (فتحه)
    وإلا سيتم تخزين قاموس العقوبة (نوع العقوبة، عدد التحذيرات، الوقت)
    """
    try:
        current_settings = await get_lock_settings(chat_id)
        
        if settings is None:
            # المشرف قام بـ "فتح" القفل (حذفه من الداتا)
            if key in current_settings:
                del current_settings[key]
        else:
            # تحديث أو إضافة القفل بالعقوبة الجديدة
            current_settings[key] = settings
            
        await db_locks.update_one(
            {"chat_id": chat_id}, 
            {"$set": {"settings": current_settings}}, 
            upsert=True
        )
    except Exception as e:
        print(f"Error setting lock settings: {e}")

# ==========================================
# دالات نظام التحذيرات (Warnings)
# ==========================================

async def get_current_warns(chat_id: int, user_id: int) -> int:
    """جلب عدد تحذيرات المستخدم الحالي"""
    try:
        doc = await db_warns.find_one({"chat_id": chat_id})
        if doc and "users" in doc:
            return doc["users"].get(str(user_id), 0)
        return 0
    except Exception as e:
        print(f"Error getting warns: {e}")
        return 0

async def update_user_warns(chat_id: int, user_id: int, count: int):
    """تحديث سجل تحذيرات المستخدم"""
    try:
        await db_warns.update_one(
            {"chat_id": chat_id}, 
            {"$set": {f"users.{user_id}": count}}, 
            upsert=True
        )
    except Exception as e:
        print(f"Error updating warns: {e}")

# ==========================================
# دوال التوافق (للأوامر العامة القديمة إن وجدت)
# ==========================================

async def get_warn_limit(chat_id: int) -> int:
    """جلب ليمت التحذيرات للمجموعة (للتوافق مع الأوامر العامة)"""
    try:
        doc = await db_warns.find_one({"chat_id": chat_id})
        return doc.get("limit", 3) if doc else 3
    except:
        return 3

async def set_warn_limit_db(chat_id: int, limit: int):
    """تعديل ليمت التحذيرات (للتوافق مع أمر 'تحذيرات')"""
    try:
        await db_warns.update_one(
            {"chat_id": chat_id}, 
            {"$set": {"limit": limit}}, 
            upsert=True
        )
    except:
        pass
