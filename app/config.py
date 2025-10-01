import os


class Config:
    def __call__(self):
        return self

    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    JSON_SORT_KEYS = False

    # SQLAlchemy / Postgres
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/student_crm"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT / Cookies
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret")
    JWT_TOKEN_LOCATION = ["cookies"]
    JWT_COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"
    JWT_COOKIE_SAMESITE = os.getenv("COOKIE_SAMESITE", "Lax")
    JWT_COOKIE_CSRF_PROTECT = True
    JWT_ACCESS_COOKIE_PATH = "/"
    JWT_REFRESH_COOKIE_PATH = "/api/auth/refresh"
    JWT_SESSION_COOKIE = True
    JWT_ACCESS_TOKEN_EXPIRES = 60 * 30  # 30 minutes
    JWT_REFRESH_TOKEN_EXPIRES = 60 * 60 * 24 * 7  # 7 days

    # Mail
    MAIL_SERVER = os.getenv("MAIL_SERVER", "localhost")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "25"))
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "false").lower() == "true"
    MAIL_USE_SSL = os.getenv("MAIL_USE_SSL", "false").lower() == "true"
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "no-reply@example.com")

    # Storage
    STORAGE_DIR = os.getenv("STORAGE_DIR", "/workspace/storage")

    # Crypto
    MASTER_ENCRYPTION_KEY_HEX = os.getenv("MASTER_ENCRYPTION_KEY_HEX")
    ACTIVE_ENCRYPTION_KEY_ID = os.getenv("ACTIVE_ENCRYPTION_KEY_ID", "default")

    # CORS
    CORS_SUPPORTS_CREDENTIALS = True
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")
