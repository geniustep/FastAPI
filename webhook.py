import json
import logging
import xmlrpc.client
from fastapi import APIRouter, HTTPException, Request
from config import ODOO_URL, ODOO_DB, logger
import requests

# إنشاء الراوتر الخاص بالويب هوك
webhook_router = APIRouter()

# الاتصال بـ Odoo عبر XML-RPC
def connect_to_odoo():
    """إنشاء اتصال مع Odoo باستخدام XML-RPC"""
    try:
        logger.info("Connecting to Odoo...")
        common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common")
        uid = common.authenticate(ODOO_DB, "admin", "admin_password", {})

        if not uid:
            logger.error("Authentication with Odoo failed. Check credentials.")
            return None, None

        models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object")
        logger.info(f"Successfully connected to Odoo with UID: {uid}")

        return uid, models
    except Exception as e:
        logger.error(f"Error connecting to Odoo: {e}")
        return None, None

uid, models = connect_to_odoo()

@webhook_router.get("/webhook/{model_name}", tags=["Webhook"])
def get_webhook_data(model_name: str, request: Request):
    """استرجاع بيانات Webhook المخزنة في `ir.config_parameter` لأي موديل"""
    try:
        # التحقق من `session_id` في `cookies`
        session_id = request.cookies.get("session_id")

        if not session_id:
            raise HTTPException(status_code=401, detail="Missing authentication session_id")

        # تمرير `session_id` في `headers`
        headers = {"Cookie": f"session_id={session_id}"}

        # تحديد الـ key بناءً على `model_name`
        payload_key = f"webhook.payload.{model_name}"
        
        # إرسال طلب لاسترجاع البيانات من Odoo
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "model": "ir.config_parameter",
                "method": "get_param",
                "args": [payload_key],
                "kwargs": {}
            }
        }

        response = requests.post(f"{ODOO_URL}/web/dataset/call_kw", json=payload, headers=headers)

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to retrieve webhook data from Odoo")

        result = response.json().get("result", "")

        # تحويل النص إلى JSON
        try:
            webhook_data = json.loads(result) if result else []
        except json.JSONDecodeError:
            webhook_data = []

        return {
            "message": f"Webhook data for {model_name} retrieved successfully",
            "status": "success",
            "data": webhook_data
        }

    except Exception as e:
        logger.error(f"Error retrieving webhook data for {model_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {e}")
    


@webhook_router.get("/webhook/check/{model_name}", tags=["Webhook"])
def check_webhook_updates(model_name: str, request: Request):
    """التحقق من وجود تحديثات وعدد السجلات في Odoo"""
    try:
        session_id = request.cookies.get("session_id")
        if not session_id:
            raise HTTPException(status_code=401, detail="Missing authentication session_id")

        headers = {"Cookie": f"session_id={session_id}"}
        payload_key = f"webhook.payload.{model_name}"

        # 🔍 استرجاع البيانات المخزنة من `ir.config_parameter`
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "model": "ir.config_parameter",
                "method": "get_param",
                "args": [payload_key],
                "kwargs": {}
            }
        }

        response = requests.post(f"{ODOO_URL}/web/dataset/call_kw", json=payload, headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to retrieve webhook data")

        data = response.json().get("result", "")
        has_updates = bool(data and isinstance(data, str) and json.loads(data))  # تحقق مما إذا كان هناك بيانات مخزنة

        # 🔢 استرجاع عدد السجلات في الموديل
        count_payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "model": model_name,
                "method": "search_count",
                "args": [[]],
                "kwargs": {}
            }
        }

        count_response = requests.post(f"{ODOO_URL}/web/dataset/call_kw", json=count_payload, headers=headers)
        if count_response.status_code != 200:
            raise HTTPException(status_code=count_response.status_code, detail="Failed to retrieve model count")

        model_length = count_response.json().get("result", 0)

        return {
            "message": "Webhook check completed",
            "status": "success",
            "has_updates": has_updates,
            "model_length": model_length
        }

    except json.JSONDecodeError:
        logger.error(f"Stored data for {model_name} is not valid JSON.")
        raise HTTPException(status_code=500, detail="Stored data is not in valid JSON format.")

    except Exception as e:
        logger.error(f"Error checking webhook updates for {model_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {e}")


@webhook_router.delete("/webhook/delete/{model_name}", tags=["Webhook"])
def delete_webhook_data(model_name: str, request: Request):
    """حذف بيانات الـ Webhook المخزنة في Odoo لموديل معين"""
    try:
        session_id = request.cookies.get("session_id")
        if not session_id:
            raise HTTPException(status_code=401, detail="Missing authentication session_id")

        headers = {"Cookie": f"session_id={session_id}"}
        payload_key = f"webhook.payload.{model_name}"

        # 🗑️ تعيين البيانات إلى قائمة فارغة لمسحها
        delete_payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "model": "ir.config_parameter",
                "method": "set_param",
                "args": [payload_key, json.dumps([])],
                "kwargs": {}
            }
        }

        delete_response = requests.post(f"{ODOO_URL}/web/dataset/call_kw", json=delete_payload, headers=headers)
        if delete_response.status_code != 200:
            raise HTTPException(status_code=delete_response.status_code, detail="Failed to delete webhook data")

        logger.info(f"Webhook data for {model_name} deleted successfully.")

        return {
            "message": "Webhook data deleted successfully",
            "status": "success"
        }

    except Exception as e:
        logger.error(f"Error deleting webhook data for {model_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {e}")
