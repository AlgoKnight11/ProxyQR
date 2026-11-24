import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse

from backend.database import engine, Base
from backend.routers import auth, courses, sessions, attendance

# Create all tables in SQLite/PostgreSQL
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ProxyQR - Real-Time Dynamic Attendance Management System",
    description="Automated, secure, dynamic QR code attendance system for universities.",
    version="1.0.0"
)

# Configure CORS - allows Netlify deployments and mobile network clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow Netlify and all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(auth.router)
app.include_router(courses.router)
app.include_router(sessions.router)
app.include_router(attendance.router)

# Mount static files
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_dir):
    # Mount at /static for backward compatibility with explicit /static paths
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

@app.get("/")
def root():
    return RedirectResponse(url="/login.html")

# Also mount frontend at root for direct Netlify-parity URLs (e.g. /login.html)
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend_root")


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "ProxyQR Backend API"}
