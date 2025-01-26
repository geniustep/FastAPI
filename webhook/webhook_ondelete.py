model_name = record._name
operation = "deleted"
payload_key = f"webhook.payload.{model_name}"
id = "{}-{}-{}".format(record.id, env.context.get("uid", 0), int(time.time()))

# ✅ جلب البيانات المخزنة مسبقًا
existing_data = env["ir.config_parameter"].sudo().get_param(payload_key)

# ✅ تحويل البيانات إلى قائمة JSON
if existing_data:
    try:
        existing_data = json.loads(existing_data) if existing_data.startswith("[") else []
    except Exception:
        existing_data = []
else:
    existing_data = []

# ✅ التأكد من أن existing_data هو قائمة
if not isinstance(existing_data, list):
    existing_data = []

# ✅ إزالة جميع الإدخالات السابقة لنفس `record_id`
existing_data = [entry for entry in existing_data if entry.get("record_id") != record.id]

# ✅ إضافة الإدخال الجديد مع `deleted`
new_entry = {"id": id, "model_name": model_name, "record_id": record.id, "operation": operation}
existing_data.append(new_entry)

# ✅ حفظ القائمة المحدثة في `ir.config_parameter`
try:
    env["ir.config_parameter"].sudo().set_param(payload_key, json.dumps(existing_data))
except Exception as e:
    env["ir.logging"].sudo().create({
        "name": "Webhook Delete Error",
        "type": "server",
        "level": "error",
        "message": f"Error storing webhook delete event: {str(e)}",
        "path": "webhook",
        "func": "delete_webhook",
        "line": "0",
        "user_id": env.user.id,
    })
