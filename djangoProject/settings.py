# just to recommit
from pathlib import Path
import pymysql
from decouple import config, Csv
import os
pymysql.install_as_MySQLdb()
from corsheaders.defaults import default_headers

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# # Quick-start development settings - unsuitable for production
SECRET_KEY = 'Linka2024!' 

DEBUG = True  # Keep this True during development, set to False in production

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '137.184.141.237', 'backend',
    'backend:8000', 'linka_backend_1']

MEDIA_ROOT = '/tmp/'

FILE_UPLOAD_TEMP_DIR = '/tmp/'

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'login_service',
    'file_processor',
    'rest_framework',
    'dashboards',
    'django_extensions',
    'sslserver',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'djangoProject.middleware.custom_middleware.SecurePartitionedCookieMiddleware',

]

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://localhost:3000",
    "http://127.0.0.1:3000",
    "https://127.0.0.1:3000",
]

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'cache-control',
]

ROOT_URLCONF = 'djangoProject.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # Specify template directories if needed
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

WSGI_APPLICATION = 'djangoProject.wsgi.application'

# Database configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'linka_database',
        'USER': 'developer',
        'PASSWORD': 'Linka2024!',
        # for local only
        'HOST': config('DATABASE_NAME', default='mysql'),
        #'HOST': 'mysql',  
        'PORT': '3306',      
    }
}

# Password validation (can be simplified or removed during development)
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},  # Set a minimum length requirement
]
AUTH_USER_MODEL = 'login_service.BaseUser' 

# Internationalization and time zone
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/deployments/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'deployments'),
]


# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = '/verify-account/' 
# Session configuration 
SESSION_ENGINE = 'django.contrib.sessions.backends.db' 
SESSION_COOKIE_NAME = 'sessionid' 
SESSION_COOKIE_SECURE = False # True for local, False for development
SESSION_COOKIE_HTTPONLY = False 
SESSION_COOKIE_SAMESITE = 'None'
SESSION_COOKIE_AGE = 1209600  # 2 weeks in seconds

# Disable CSRF
CSRF_COOKIE_SECURE = True# True for local, False for development
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'None'
