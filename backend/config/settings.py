import os
from pathlib import Path
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIST = BASE_DIR / "frontend_dist"

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "unsafe-local-key")
DEBUG = os.getenv("DJANGO_DEBUG", "False").lower() == "true"
ALLOWED_HOSTS = [h.strip() for h in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h.strip()]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "rest_framework.authtoken",
    "finance",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [FRONTEND_DIST] if FRONTEND_DIST.exists() else [],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB", "casa_yeison"),
        "USER": os.getenv("POSTGRES_USER", "casa_yeison"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", "casa_yeison_local"),
        "HOST": os.getenv("POSTGRES_HOST", "db"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
        "CONN_MAX_AGE": 60,
    }
}
if os.getenv("DATABASE_URL"):
    DATABASES["default"] = dj_database_url.config(
        default=os.getenv("DATABASE_URL"),
        conn_max_age=600,
        conn_health_checks=True,
    )

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "es-cr"
TIME_ZONE = "America/Costa_Rica"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [FRONTEND_DIST] if FRONTEND_DIST.exists() else []
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CORS_ALLOWED_ORIGINS = ["http://localhost:5186"]
CORS_ALLOWED_ORIGINS += [origin.strip() for origin in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",") if origin.strip()]
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",") if origin.strip()]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework.authentication.TokenAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_THROTTLE_RATES": {"pin_login": "8/minute", "receipt_scan": "20/hour"},
}

DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024

CELERY_BROKER_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.getenv("REDIS_URL", "redis://redis:6379/0")
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_BEAT_SCHEDULE = {
    "ensure-salaries-hourly": {
        "task": "finance.tasks.ensure_salaries_task",
        "schedule": 3600.0,
    },
    "daily-recommendations-at-noon": {
        "task": "finance.tasks.generate_daily_recommendations_task",
        "schedule": {"__type__": "crontab", "minute": "0", "hour": "12"},
    },
}

# Celery accepts a crontab instance, constructed here to keep the schedule explicit.
from celery.schedules import crontab
CELERY_BEAT_SCHEDULE["daily-recommendations-at-noon"]["schedule"] = crontab(minute=0, hour=12)

APP_PIN = os.getenv("APP_PIN", "2580")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5-20250929")

SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
WHITENOISE_MAX_AGE = 31536000 if not DEBUG else 0
