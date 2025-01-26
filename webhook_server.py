# from fastapi import FastAPI, HTTPException, Request
# import xmlrpc.client
# import json
# import logging
# import time
# from logging.handlers import RotatingFileHandler


# # test Initialize FastAPI application
# app = FastAPI(title="Odoo Webhook API", version="1.0", description="API for managing webhooks connected to Odoo")

# # Configure logging to store API logs
# # Initialize FastAPI application
# app = FastAPI(title="Odoo Webhook API", version="1.0", description="API for managing webhooks connected to Odoo")

# # Odoo connection settings
# ODOO_URL = "https://app.propanel.ma"
# ODOO_DB = "zaka"

# # Configure logging
# log_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

# # Create handlers
# console_handler = logging.StreamHandler()
# console_handler.setFormatter(log_formatter)

# webhook_file_handler = RotatingFileHandler("webhook.log", maxBytes=1048576, backupCount=3)
# webhook_file_handler.setFormatter(log_formatter)

# auth_file_handler = RotatingFileHandler("auth.log", maxBytes=1048576, backupCount=3)
# auth_file_handler.setFormatter(log_formatter)

# # Get the root logger
# logger = logging.getLogger()
# logger.setLevel(logging.INFO)

# # Add handlers to logger
# logger.addHandler(console_handler)
# logger.addHandler(webhook_file_handler)
# logger.addHandler(auth_file_handler)


# @app.post("/login", tags=["Authentication"])
# def login(request_data: dict):
#     """Authenticate user with Odoo and return session cookie"""
#     try:
#         username = request_data.get("username")
#         password = request_data.get("password")
#         if not username or not password:
#             raise HTTPException(status_code=400, detail="Username and password are required")

#         # Connect to Odoo
#         common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common", allow_none=True, use_datetime=True)
#         uid = common.authenticate(ODOO_DB, username, password, {})

#         if not uid:
#             raise HTTPException(status_code=401, detail="Invalid credentials")

#         # Generate session cookie (Odoo's default behavior)
#         session_id = f"session_id={uid}"

#         logging.info(f"User {username} authenticated successfully")

#         return {
#             "message": "Login successful",
#             "status": "success",
#             "session_id": session_id
#         }

#     except Exception as e:
#         logging.error(f"Login error: {e}")
#         raise HTTPException(status_code=500, detail="Internal server error")


# def connect_to_odoo():
#     """Establish connection with Odoo using XML-RPC"""
#     try:
#         logging.info("Connecting to Odoo...")
#         common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common", allow_none=True, use_datetime=True)
#         return common
#     except Exception as e:
#         logging.error(f"Error connecting to Odoo: {e}")
#         return None

# common = connect_to_odoo()

# def retry_odoo_call(func, max_retries=3, delay=2):
#     """Retry Odoo API calls and reconnect if necessary"""
#     for attempt in range(max_retries):
#         try:
#             return func()
#         except Exception as e:
#             logging.warning(f"Attempt {attempt + 1} failed: {e}")
#             time.sleep(delay)
#     raise HTTPException(status_code=500, detail="Failed to connect to Odoo after multiple attempts.")

# @app.get("/webhook/{model_name}", tags=["Webhook"])
# def get_webhook_data(model_name: str, request: Request):
#     """Retrieve webhook data stored in Odoo for a specific model"""
#     try:
#         cookies = request.headers.get("cookie")
#         if not cookies:
#             raise HTTPException(status_code=401, detail="Missing authentication cookies")

#         payload_key = f"webhook.payload.{model_name}"
#         data = retry_odoo_call(lambda: common.execute_kw(ODOO_DB, cookies, 'ir.config_parameter', 'get_param', [payload_key]))

#         if not data:
#             return {"message": "No webhook data available", "status": "empty"}

#         try:
#             data_list = json.loads(data)
#         except json.JSONDecodeError:
#             raise HTTPException(status_code=500, detail="Stored data is not in valid JSON format.")

#         return {
#             "message": "Webhook data retrieved successfully",
#             "status": "success",
#             "data": data_list
#         }
#     except Exception as e:
#         logging.error(f"Error retrieving webhook data for {model_name}: {e}")
#         raise HTTPException(status_code=500, detail=f"Error: {e}")

# # Root endpoint to check API status
# @app.get("/", tags=["General"])
# def root():
#     """Root endpoint to check API health status"""
#     return {"message": "Welcome to Odoo Webhook API", "status": "running"}

# # Retrieve webhook data stored in Odoo
# @app.get("/webhook/{model_name}", tags=["Webhook"])
# def get_webhook_data(model_name: str, request: Request):
#     """Retrieve webhook data stored in Odoo for a specific model"""
#     cookies = request.headers.get("cookie")
#     if not cookies:
#             raise HTTPException(status_code=401, detail="Missing authentication cookies")
#     try:
#         payload_key = f"webhook.payload.{model_name}"
#         data = retry_odoo_call(lambda: models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
#                                                          'ir.config_parameter', 'get_param', [payload_key]))

#         logging.info(f"Retrieved webhook data for {model_name}: {data}")

#         if not data:
#             return {"message": "No webhook data available", "status": "empty"}

#         # Validate if the data is a valid JSON format
#         try:
#             data_list = json.loads(data)
#         except json.JSONDecodeError:
#             logging.error(f"Stored data for {model_name} is not valid JSON.")
#             raise HTTPException(status_code=500, detail="Stored data is not in valid JSON format.")

#         return {
#             "message": "Webhook data retrieved successfully",
#             "status": "success",
#             "data": data_list
#         }

#     except Exception as e:
#         logging.error(f"Error retrieving webhook data for {model_name}: {e}")
#         raise HTTPException(status_code=500, detail=f"Error: {e}")

# # Check for updates and retrieve record count from Odoo
# @app.get("/webhook/check/{model_name}", tags=["Webhook"])
# def check_webhook_updates(model_name: str):
#     """Check if there are updates and get record count from Odoo"""
#     try:
#         payload_key = f"webhook.payload.{model_name}"
#         data = retry_odoo_call(lambda: models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
#                                                          'ir.config_parameter', 'get_param', [payload_key]))

#         has_updates = bool(data and isinstance(data, str) and json.loads(data))

#         # Retrieve the total number of records from Odoo for the given model
#         model_length = retry_odoo_call(lambda: models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
#                                                                  model_name, 'search_count', [[]]))

#         return {
#             "message": "Webhook check completed",
#             "status": "success",
#             "has_updates": has_updates,
#             "model_length": model_length
#         }

#     except json.JSONDecodeError:
#         logging.error(f"Stored data for {model_name} is not valid JSON.")
#         raise HTTPException(status_code=500, detail="Stored data is not in valid JSON format.")

#     except Exception as e:
#         logging.error(f"Error checking webhook updates for {model_name}: {e}")
#         raise HTTPException(status_code=500, detail=f"Error: {e}")

# # Delete webhook data stored in Odoo
# @app.delete("/webhook/delete/{model_name}", tags=["Webhook"])
# def delete_webhook_data(model_name: str):
#     """Delete webhook data stored in Odoo for a specific model"""
#     try:
#         payload_key = f"webhook.payload.{model_name}"

#         # Set the parameter value to an empty list to clear the stored data
#         success = retry_odoo_call(lambda: models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
#                                                             'ir.config_parameter', 'set_param',
#                                                             [payload_key, json.dumps([])]))

#         if not success:
#             raise HTTPException(status_code=500, detail="Failed to delete webhook data.")

#         logging.info(f"Webhook data for {model_name} deleted successfully.")

#         return {
#             "message": "Webhook data deleted successfully",
#             "status": "success"
#         }

#     except Exception as e:
#         logging.error(f"Error deleting webhook data for {model_name}: {e}")
#         raise HTTPException(status_code=500, detail=f"Error: {e}")
