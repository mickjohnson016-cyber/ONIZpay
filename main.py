from fastapi import FastAPI, Request, HTTPException, status, APIRouter
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from urllib.parse import urlencode
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from dotenv import load_dotenv
import os
import database

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
LOCAL_ORIGINS = [
    "http://127.0.0.1:5506",
    "http://localhost:5506"
]
env_origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
ALLOWED_ORIGINS = [o for o in env_origins if o] + LOCAL_ORIGINS

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static folder
app.mount("/static", StaticFiles(directory="static"), name="static")

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "605810116247-8d87hifgj9a48lcn3q20u3lms7u9qtg4.apps.googleusercontent.com")
GOOGLE_REDIRECT_URI = "http://127.0.0.1:8000/auth/google/callback"

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

class LoginRequest(BaseModel):
    email: str
    password: str

class UserAuth(BaseModel):
    email: EmailStr
    password: str

async def get_user_by_email(email: str):
    db = database.get_db_connection()
    cursor = db.cursor()
    cursor.execute("SELECT id, email, password_hash FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    db.close()
    if row:
        from collections import namedtuple
        User = namedtuple("User", ["id", "email", "password"])
        return User(id=row["id"], email=row["email"], password=row["password_hash"])
    return None

@router.post("/login")
async def login(data: LoginRequest):
    user = await get_user_by_email(data.email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    if not database.verify_password(data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    return {
        "message": "Login successful",
        "user_id": user.id
    }

@app.get("/")
def root():
    return FileResponse("static/index.html")

@app.get("/index.html")
def index():
    return FileResponse("static/index.html")

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
    hashed_pwd = database.hash_password(data.password)
    
    # Store in SQLite
    cursor.execute("INSERT INTO users (email, password_hash) VALUES (?, ?)", (data.email, hashed_pwd))
    db.commit()
    db.close()
    
    return {"message": "Registration successful"}

app.include_router(router)

@app.get("/auth/google")
def google_login():
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent"
    }

    google_auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)

    return RedirectResponse(google_auth_url)

@app.get("/auth/google/callback")
async def google_callback(request: Request):
    code = request.query_params.get("code")

    if not code:
        return RedirectResponse(url="/login.html?error=no_code")

    # In a real application, exchange code for user info
    # For this implementation, we simulate a successful login redirect
    html_content = """
    <html>
        <body>
            <script>
                sessionStorage.setItem("isAuthenticated", "true");
                sessionStorage.setItem("userEmail", "google-user@onizpay.com");
                window.location.href = "/index.html";
            </script>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)
