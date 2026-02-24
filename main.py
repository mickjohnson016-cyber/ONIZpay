from fastapi import FastAPI, Request, HTTPException, status, APIRouter, Form
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from urllib.parse import urlencode
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from dotenv import load_dotenv
import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import database
import uuid
from datetime import datetime

load_dotenv()

DEBUG = os.getenv("DEBUG", "False").lower() == "true"
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY not found in environment variables")

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")

LOCAL_ORIGINS = [
    "http://127.0.0.1:5506",
    "http://localhost:5506"
]
env_origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
ALLOWED_ORIGINS = [o for o in env_origins if o] + LOCAL_ORIGINS

app = FastAPI(debug=DEBUG)

# ═════════════════════════════════
# SECURITY MIDDLEWARE (Production Hardening)
# ═════════════════════════════════

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-XSS-Protection"] = "1; mode=block" # SECURE_BROWSER_XSS_FILTER
        response.headers["X-Content-Type-Options"] = "nosniff" # SECURE_CONTENT_TYPE_NOSNIFF
        response.headers["X-Frame-Options"] = "DENY" # X_FRAME_OPTIONS
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=ALLOWED_HOSTS)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    SessionMiddleware, 
    secret_key=SECRET_KEY,
    https_only=not DEBUG, # Use HTTPS secure flag in production
    same_site="lax",
    max_age=3600 # 1 hour session
)

# Mount static folder
app.mount("/static", StaticFiles(directory="static"), name="static")

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_REDIRECT_URI = "http://127.0.0.1:8000/auth/google/callback"

templates = Jinja2Templates(directory="templates")

router = APIRouter()
# Consolidating hashing logic in database.py
# pwd_context moved/stored there for consistency.

def get_current_user(request: Request):
    return request.session.get("user")

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserAuth(BaseModel):
    email: EmailStr
    password: str
    full_name: str = None

async def get_user_by_email(email: str):
    db = database.get_db_connection()
    cursor = db.cursor()
    cursor.execute("SELECT id, email, full_name, password_hash, role FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    db.close()
    if row:
        from collections import namedtuple
        User = namedtuple("User", ["id", "email", "full_name", "hashed_password", "role"])
        return User(
            id=row["id"], 
            email=row["email"], 
            full_name=row["full_name"], 
            hashed_password=row["password_hash"],
            role=row["role"]
        )
    return None

@app.post("/login")
async def login(request: Request, email: str = Form(...), password: str = Form(...)):
    try:
        db_user = await get_user_by_email(email)

        if not db_user or not database.verify_password(password, db_user.hashed_password):
            return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid email or password"})

        # STORE SESSION
        request.session["user"] = {
            "name": db_user.full_name,
            "email": db_user.email,
            "id": db_user.id,
            "role": db_user.role or "user"
        }

        # Successful login redirect
        return RedirectResponse("/", status_code=303)
    except Exception as e:
        # Structured logging instead of raw prints
        logging.error(f"Authentication Failure: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during authentication")

@app.get("/auth/me")
def get_auth_me(request: Request):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401)
    return user

@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)

@app.get("/", response_class=HTMLResponse)
@app.get("/index.html", response_class=HTMLResponse)
async def home(request: Request):
    user = get_current_user(request)
    return templates.TemplateResponse("index.html", {"request": request, "user": user})

@app.get("/contact")
@app.get("/contact.html")
async def contact(request: Request, success: str = None):
    user = request.session.get("user")
    return templates.TemplateResponse(
        "contact.html",
        {"request": request, "user": user, "success": success}
    )

@app.post("/contact")
async def submit_contact(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    subject: str = Form(...),
    message: str = Form(...)
):
    ticket_id = "OINZ-" + uuid.uuid4().hex[:8].upper()
    
    # Store in DB
    db = database.get_db_connection()
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO contact_messages (ticket_id, full_name, email, subject, message)
        VALUES (?, ?, ?, ?, ?)
    """, (ticket_id, full_name, email, subject, message))
    db.commit()
    db.close()

    # SECTION 4 — CONNECT EMAIL TO CONTACT FLOW
    try:
        from services.notification_service import send_contact_email
        ticket_data = {
            "ticket_id": ticket_id,
            "full_name": full_name,
            "email": email,
            "subject": subject,
            "message": message
        }
        send_contact_email(ticket_data)
    except Exception as e:
        print(f"Notification error: {e}")

    return RedirectResponse(f"/contact?success={ticket_id}", status_code=303)

@app.get("/demo.html")
async def demo(request: Request):
    user = get_current_user(request)
    return templates.TemplateResponse("demo.html", {"request": request, "user": user})

@app.get("/privacy.html")
async def privacy(request: Request):
    user = get_current_user(request)
    return templates.TemplateResponse("privacy.html", {"request": request, "user": user})

@app.get("/terms.html")
async def terms(request: Request):
    user = get_current_user(request)
    return templates.TemplateResponse("terms.html", {"request": request, "user": user})

@app.get("/login.html")
async def login_page(request: Request):
    user = get_current_user(request)
    return templates.TemplateResponse("login.html", {"request": request, "user": user})

@app.get("/register.html")
async def register_page(request: Request):
    user = get_current_user(request)
    return templates.TemplateResponse("register.html", {"request": request, "user": user})

@app.get("/oinz.html")
async def oinz_page(request: Request):
    user = get_current_user(request)
    return templates.TemplateResponse("oinz.html", {"request": request, "user": user})

@app.get("/admin/tickets")
async def admin_tickets(request: Request):
    user = request.session.get("user")
    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Forbidden: Admin access required")
    
    db = database.get_db_connection()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM contact_messages ORDER BY created_at DESC")
    tickets = cursor.fetchall()
    db.close()
    
    # We'll use a simple HTML response for now as requested for Section 5
    return templates.TemplateResponse("admin_tickets.html", {"request": request, "user": user, "tickets": tickets})

@app.get("/health")
def health():
    return JSONResponse(content={"health": "ok"})

@app.post("/register")
def register(data: UserAuth):
    db = database.get_db_connection()
    cursor = db.cursor()
    
    # Reject if email already exists
    cursor.execute("SELECT id FROM users WHERE email = ?", (data.email,))
    if cursor.fetchone():
        db.close()
        raise HTTPException(status_code=400, detail="Email already exists")
    
    # Hash password before storing
    hashed_password = database.hash_password(data.password)
    
    # Store in SQLite
    cursor.execute("INSERT INTO users (email, full_name, password_hash) VALUES (?, ?, ?)", (data.email, data.full_name, hashed_password))
    db.commit()
    db.close()
    
    return {"message": "Registration successful"}

app.include_router(router)

@app.get("/auth/google/login")
async def google_login():

    google_auth_url = "https://accounts.google.com/o/oauth2/v2/auth"

    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": "http://127.0.0.1:8000/auth/google/callback",
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
    }

    return RedirectResponse(f"{google_auth_url}?{urlencode(params)}")

@app.get("/auth/google/callback")
async def google_callback(request: Request):
    # In a simulated environment, we create a structured session 
    # matching the production requirements of Section 1
    google_name = "Oinz User" # Simulation Placeholder
    google_email = "user@example.com"
    google_id = 999
    google_role = "user" # Default role for new Google logins

    # Store structured session object as requested
    request.session["user"] = {
        "id": google_id,
        "name": google_name,
        "email": google_email,
        "role": google_role
    }

    return RedirectResponse(url="/", status_code=303)
