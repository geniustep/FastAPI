from fastapi import FastAPI, HTTPException
import xmlrpc.client
import json
import logging
import time

# test Initialize FastAPI application
app = FastAPI(title="Odoo Webhook API", version="1.0", description="API for managing webhooks connected to Odoo")

# Odoo connection settings
ODOO_URL = "https://app.propanel.ma"
ODOO_DB = "zaka"
ODOO_USER = "zaka"
ODOO_PASSWORD = "zaka"

# Configure logging to store API logs
logging.basicConfig(filename="webhook.log", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Connect to Odoo using XML-RPC
try:
    common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common", allow_none=True, use_datetime=True)
    uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASSWORD, {})

    if not uid:
        logging.error("Failed to authenticate with Odoo. Check credentials.")
        raise Exception("Failed to authenticate with Odoo.")

    models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object", allow_none=True, use_datetime=True)
    logging.info("Successfully connected to Odoo.")

except Exception as e:
    logging.error(f"Error connecting to Odoo: {e}")
    raise Exception(f"Connection error with Odoo: {e}")

# Retry mechanism for handling Odoo connection failures
def retry_odoo_call(func, max_retries=3, delay=2):
    """Retry Odoo API calls in case of failure"""
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            logging.warning(f"Attempt {attempt + 1} failed: {e}")
            time.sleep(delay)
    raise HTTPException(status_code=500, detail="Failed to connect to Odoo after multiple attempts.")

# Root endpoint to check API status
@app.get("/", tags=["General"])
def root():
    """Root endpoint to check API health status"""
    return {"message": "Welcome to Odoo Webhook API", "status": "running"}

# Retrieve webhook data stored in Odoo
@app.get("/webhook/{model_name}", tags=["Webhook"])
def get_webhook_data(model_name: str):
    """Retrieve webhook data stored in Odoo for a specific model"""
    try:
        payload_key = f"webhook.payload.{model_name}"
        data = retry_odoo_call(lambda: models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                                                         'ir.config_parameter', 'get_param', [payload_key]))

        logging.info(f"Retrieved webhook data for {model_name}: {data}")

        if not data:
            return {"message": "No webhook data available", "status": "empty"}

        # Validate if the data is a valid JSON format
        try:
            data_list = json.loads(data)
        except json.JSONDecodeError:
            logging.error(f"Stored data for {model_name} is not valid JSON.")
            raise HTTPException(status_code=500, detail="Stored data is not in valid JSON format.")

        return {
            "message": "Webhook data retrieved successfully",
            "status": "success",
            "data": data_list
        }

    except Exception as e:
        logging.error(f"Error retrieving webhook data for {model_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {e}")

# Check for updates and retrieve record count from Odoo
@app.get("/webhook/check/{model_name}", tags=["Webhook"])
def check_webhook_updates(model_name: str):
    """Check if there are updates and get record count from Odoo"""
    try:
        payload_key = f"webhook.payload.{model_name}"
        data = retry_odoo_call(lambda: models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                                                         'ir.config_parameter', 'get_param', [payload_key]))

        has_updates = bool(data and isinstance(data, str) and json.loads(data))

        # Retrieve the total number of records from Odoo for the given model
        model_length = retry_odoo_call(lambda: models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                                                                 model_name, 'search_count', [[]]))

        return {
            "message": "Webhook check completed",
            "status": "success",
            "has_updates": has_updates,
            "model_length": model_length
        }

    except json.JSONDecodeError:
        logging.error(f"Stored data for {model_name} is not valid JSON.")
        raise HTTPException(status_code=500, detail="Stored data is not in valid JSON format.")

    except Exception as e:
        logging.error(f"Error checking webhook updates for {model_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {e}")

# Delete webhook data stored in Odoo
@app.delete("/webhook/delete/{model_name}", tags=["Webhook"])
def delete_webhook_data(model_name: str):
    """Delete webhook data stored in Odoo for a specific model"""
    try:
        payload_key = f"webhook.payload.{model_name}"

        # Set the parameter value to an empty list to clear the stored data
        success = retry_odoo_call(lambda: models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                                                            'ir.config_parameter', 'set_param',
                                                            [payload_key, json.dumps([])]))

        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete webhook data.")

        logging.info(f"Webhook data for {model_name} deleted successfully.")

        return {
            "message": "Webhook data deleted successfully",
            "status": "success"
        }

    except Exception as e:
        logging.error(f"Error deleting webhook data for {model_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {e}")
