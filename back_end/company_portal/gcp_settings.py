import os
from .settings import *
from .settings import BASE_DIR

ALLOWED_HOSTS = ['api.archr.se']

FRONTEND_URL = "https://portal.archr.se"

# CORS - allows your frontend to talk to backend
CORS_ALLOWED_ORIGINS = ['https://portal.archr.se']

# CSRF - basic protection
CSRF_TRUSTED_ORIGINS = [
    'https://api.archr.se',  # Backend
    'https://portal.archr.se',  # Frontend
]
CSRF_COOKIE_DOMAIN = ".archr.se"
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_SAMESITE = 'None'

SESSION_COOKIE_SAMESITE = 'None'

DEBUG = False
SECRET_KEY = os.environ.get('SECRET_KEY')
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Cloud SQL MySQL Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST', '/cloudsql/portal-score:europe-west1:archr-mysql'),
        'PORT': '',
        'OPTIONS': {
            'ssl_mode': 'REQUIRED',
            'charset': 'utf8mb4',
        },
    }
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',  # Only show important stuff
    },
}