import requests
from fastapi import APIRouter, HTTPException, Request, Response
from config import ODOO_URL, ODOO_DB, logger

# Create Router for authentication
auth_router = APIRouter()

@auth_router.post("/login", tags=["Authentication"])
def login(request_data: dict, response: Response):
    """Authenticate user with Odoo and return session cookie"""
    try:
        username = request_data.get("username")
        password = request_data.get("password")
        if not username or not password:
            raise HTTPException(status_code=400, detail="Username and password are required")

        # Prepare Odoo authentication payload
        payload = {
            "jsonrpc": "2.0",
            "params": {
                "db": ODOO_DB,
                "login": username,
                "password": password
            }
        }

        # Send request to Odoo's authentication endpoint
        odoo_response = requests.post(f"{ODOO_URL}/web/session/authenticate", json=payload)

        if odoo_response.status_code != 200:
            raise HTTPException(status_code=odoo_response.status_code, detail="Failed to connect to Odoo")

        result = odoo_response.json()

        # Check if authentication was successful
        if "result" not in result or not result["result"].get("uid"):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Extract session ID from cookies
        session_id = odoo_response.cookies.get("session_id")

        if not session_id:
            raise HTTPException(status_code=500, detail="Failed to retrieve session ID")

        logger.info(f"User {username} authenticated successfully with session {session_id}")

        # Set session_id in response cookie
        response.set_cookie(key="session_id", value=session_id, httponly=True, path="/", max_age=604800, samesite="Lax")

        return {
            "message": "Login successful",
            "status": "success",
            "session_id": session_id
        }

    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
