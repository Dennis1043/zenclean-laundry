import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-test-key-for-development-only'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'laundry',
    'laundry.templatetags',  # Custom template tags
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'laundry.context_processors.base_context',  # Custom context processor
                'laundry.context_processors.company_settings',  # Company settings context processor
            ],
        },
    },
]

WSGI_APPLICATION = 'core_project.wsgi.application'

# Database
# ========== DATABASE CONFIGURATION - MYSQL ==========
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'laundry_master',
        'USER': 'root',
        'PASSWORD': '@Dennis1043',  # <-- PUT YOUR ACTUAL PASSWORD HERE
        'HOST': 'localhost',
        'PORT': '3306',
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Nairobi'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files (Uploaded files)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Login/Logout URLs
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'

# SMS Configuration (Africa's Talking)
SMS_ENABLED = True
SMS_API_KEY = 'atsk_d1ad6346e6f2eb9bbb84a1ad473cf3899d5323f31e946d1e7eba4698323090fd0ca29275'
SMS_USERNAME = 'sandbox'  # For sandbox environment
SMS_SENDER_ID = 'ZenClean'  # Max 11 characters

# ============================================================
# COMPANY SETTINGS - Update these with your business details
# ============================================================
COMPANY_NAME = 'ZenClean'
COMPANY_PHONE = '0729116844'  # Change to your phone number
COMPANY_EMAIL = 'info@zenclean.co.ke'  # Change to your email
COMPANY_ADDRESS = 'Nairobi, Kenya'  # Change to your physical address
COMPANY_WEBSITE = 'https://www.tiktok.com/@zencleanlaundry?_r=1&_t=ZS-97HiqV7Ioss'
# ============================================================
# PRODUCTION SETTINGS (Uncomment when deploying to PythonAnywhere)
# ============================================================
# import pymysql
# pymysql.install_as_MySQLdb()
# 
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.mysql',
#         'NAME': 'Dennis100$zenclean',
#         'USER': 'Dennis100',
#         'PASSWORD': 'YOUR_MYSQL_PASSWORD',
#         'HOST': 'Dennis100.mysql.pythonanywhere-services.com',
#         'PORT': '3306',
#     }
# }
# 
# DEBUG = False
# ALLOWED_HOSTS = ['Dennis100.pythonanywhere.com', 'www.Dennis100.pythonanywhere.com']
# 
# # For production SMS
# SMS_USERNAME = 'your_app_username'  # Not 'sandbox'
# SMS_SENDER_ID = 'ZenClean'  # Your approved sender ID

# ============================================================
# SECURITY SETTINGS (Uncomment for production)
# ============================================================
# SECURE_SSL_REDIRECT = True
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True
# SECURE_BROWSER_XSS_FILTER = True
# SECURE_CONTENT_TYPE_NOSNIFF = True
# X_FRAME_OPTIONS = 'DENY'