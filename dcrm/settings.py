import os
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
load_dotenv()
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_FILE_PATH = os.path.join(BASE_DIR, 'data', '1819.csv')
# External DB path (optional). If not set, use project db.sqlite3
DB_PATH = os.environ.get('DB_PATH') or os.path.join(BASE_DIR, 'db.sqlite3')

def _env_bool(name: str, default: bool = False) -> bool:
    val = os.environ.get(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "y", "on"}

def _env_csv(name: str, default: list[str]) -> list[str]:
    val = os.environ.get(name)
    if not val:
        return default
    items = [x.strip() for x in val.split(",")]
    return [x for x in items if x]

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-jcxge@8cwms-4-$&qia^6p+^8-qwrsw7vey#0e6e326apg3mvo')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = _env_bool("DEBUG", True)

ALLOWED_HOSTS = _env_csv("ALLOWED_HOSTS", ["*"])

# CSRF / proxy (behind Traefik / HTTPS)
# Example:
#   CSRF_TRUSTED_ORIGINS=https://example.com,http://1.2.3.4:8088
CSRF_TRUSTED_ORIGINS = _env_csv("CSRF_TRUSTED_ORIGINS", [])

# If you terminate TLS at a reverse proxy and forward to Django via HTTP,
# enable this so Django knows the original scheme was HTTPS.
# (Traefik sets X-Forwarded-Proto by default.)
SECURE_PROXY_SSL_HEADER = (
    ("HTTP_X_FORWARDED_PROTO", "https") if _env_bool("SECURE_PROXY_SSL_HEADER", False) else None
)
USE_X_FORWARDED_HOST = _env_bool("USE_X_FORWARDED_HOST", False)

# Cookies over HTTPS (optional hardening)
CSRF_COOKIE_SECURE = _env_bool("CSRF_COOKIE_SECURE", default=False)
SESSION_COOKIE_SECURE = _env_bool("SESSION_COOKIE_SECURE", default=False)

# Workaround for some embedded browsers/webviews that send `Origin: null` on POST.
# This is OFF by default because it weakens CSRF protections.
CSRF_STRIP_NULL_ORIGIN = _env_bool("CSRF_STRIP_NULL_ORIGIN", default=False)

# Base URL of the site (used for generated links / copy-to-clipboard).
# Example: http://100.111.57.75:8088/
_site_url = (os.environ.get("SITE_URL") or "http://100.111.57.75:8088/").strip()
if _site_url and not _site_url.endswith("/"):
    _site_url += "/"
SITE_URL = _site_url
# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'website',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # Must be BEFORE CsrfViewMiddleware
    'dcrm.middleware.StripNullOriginMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'dcrm.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'dcrm.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': DB_PATH,
    }
}
# Password validation
# Валидаторы отключены - принимаются любые пароли
AUTH_PASSWORD_VALIDATORS = []

# Internationalization
LANGUAGE_CODE = 'ru'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]


MEDIA_URL = '/media/'  # URL для доступа к файлам
MEDIA_ROOT = os.environ.get('MEDIA_ROOT') or os.path.join(BASE_DIR, 'media')  # Локальный путь к файлам

# Telegram Bot Settings
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'