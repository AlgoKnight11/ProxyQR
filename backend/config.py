import os

SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key-proxyqr-change-in-production-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 24 hours

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./attendance.db")

# Dynamic QR code rotation window in seconds
QR_ROTATION_INTERVAL_SECONDS = 15
# Grace period in seconds to account for network lag during student scan submission
QR_GRACE_PERIOD_SECONDS = 5
