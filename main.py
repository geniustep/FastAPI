from fastapi import FastAPI
from auth import auth_router
from webhook import webhook_router

# Initialize FastAPI application
app = FastAPI(title="Odoo Webhook API", version="1.0", description="API for managing webhooks connected to Odoo")

# Include routers
app.include_router(auth_router)
app.include_router(webhook_router)

# Root endpoint to check API status
@app.get("/", tags=["General"])
def root():
    """Root endpoint to check API health status"""
    return {"message": "Welcome to Odoo Webhook API", "status": "running"}

