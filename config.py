import logging
from logging.handlers import RotatingFileHandler

# Odoo connection settings
ODOO_URL = "https://app.propanel.ma"
ODOO_DB = ""

# Configure logging
log_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

# Create handlers
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)

webhook_file_handler = RotatingFileHandler("webhook.log", maxBytes=1048576, backupCount=3)
webhook_file_handler.setFormatter(log_formatter)

auth_file_handler = RotatingFileHandler("auth.log", maxBytes=1048576, backupCount=3)
auth_file_handler.setFormatter(log_formatter)

# Get the root logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Add handlers to logger
logger.addHandler(console_handler)
logger.addHandler(webhook_file_handler)
logger.addHandler(auth_file_handler)
