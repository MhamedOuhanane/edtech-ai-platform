"""Configuration principale du projet Django."""

from datetime import timedelta
from pathlib import Path
from urllib.parse import urlparse
import os

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - fallback si python-dotenv n'est pas installé.
    load_dotenv = None


# Chargement des variables d'environnement depuis le fichier .env.
BASE_DIR = Path(__file__).resolve().parent.parent
if load_dotenv is not None:
    load_dotenv(BASE_DIR / ".env")
else:
    env_file = BASE_DIR / ".env"
    if env_file.exists():
        for raw_line in env_file.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


# Paramètres de base du projet.
SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-change-me")
DEBUG = os.getenv("DEBUG", "True").lower() == "true"
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "*").split(",")


# Applications installées: noyau Django, API, authentification JWT et apps métier.
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "accounts",
    "documents",
    "chat",
    "quiz",
]


# Middleware, avec la gestion CORS placée avant CommonMiddleware.
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Base PostgreSQL alimentée par DATABASE_URL.
def _parse_database_url(database_url: str) -> dict:
    parsed_url = urlparse(database_url)
    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": parsed_url.path.lstrip("/") or "",
        "USER": parsed_url.username or "",
        "PASSWORD": parsed_url.password or "",
        "HOST": parsed_url.hostname or "",
        "PORT": parsed_url.port or "",
    }


DATABASES = {
    "default": _parse_database_url(
        os.getenv("DATABASE_URL", "postgres://postgres:postgres@localhost:5432/edtech_ai_platform")
    )
}


# Validations de mot de passe Django.
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Personnalisation de l'utilisateur principal.
AUTH_USER_MODEL = "accounts.User"


# Internationalisation.
LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# API REST: authentification JWT par défaut.
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
}


# Configuration Simple JWT: access 1 jour, refresh 7 jours.
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": False,
}


# CORS en développement: tout est autorisé.
CORS_ALLOW_ALL_ORIGINS = True


# Fichiers statiques et médias.
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


# Clé primaire automatique pour les nouveaux modèles.
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
