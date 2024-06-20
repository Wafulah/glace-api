# settings.py

from pathlib import Path
from os import getenv
from dotenv import load_dotenv
import datetime
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv()

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = getenv('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['glace-api-vhkd.onrender.com', 'localhost', '127.0.0.1']

# Application definition
INSTALLED_APPS = [
    'rest_framework',
    'corsheaders',
    'api',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'oidc_provider',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    

]


ROOT_URLCONF = 'config.urls'

# Add DRF settings
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_jwt.authentication.JSONWebTokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
}

JWT_AUTH = {
    'JWT_EXPIRATION_DELTA': datetime.timedelta(days=7),
    'JWT_ALLOW_REFRESH': True,
}

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'config.wsgi.application'

CORS_ORIGIN_WHITELIST = ['http://localhost:3000','https://glace-store.vercel.app']



# Database
DATABASES = {
  'default': {
    'ENGINE': 'django.db.backends.postgresql',
    'NAME': getenv('PGDATABASE'),
    'USER': getenv('PGUSER'),
    'PASSWORD': getenv('PGPASSWORD'),
    'HOST': getenv('PGHOST'),
    'PORT': getenv('PGPORT', 5432),
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

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

SITE_ID = 1

# Custom settings
LOGIN_REDIRECT_URL = 'https://glace-store.vercel.app'
# LOGIN_URL will be set in urls.py

# OIDC Provider settings
OIDC_USERINFO_ENDPOINT = 'https://openidconnect.googleapis.com/v1/userinfo'
OIDC_AUTHORIZATION_ENDPOINT = 'https://accounts.google.com/o/oauth2/auth'
OIDC_TOKEN_ENDPOINT = 'https://oauth2.googleapis.com/token'
OIDC_CLIENT_ID = getenv('OIDC_CLIENT_ID')
OIDC_CLIENT_SECRET = getenv('OIDC_CLIENT_SECRET')
OIDC_ENDPOINT_DECORATOR = 'oidc_provider.decorators.protected_resource'

OIDC_PROVIDERS = {
    'google': {
        'issuer': 'https://accounts.google.com',
        'client_id': OIDC_CLIENT_ID,
        'client_secret': OIDC_CLIENT_SECRET,
        'redirect_uris': ['https://glace-api-vhkd.onrender.com/api/openid/callback'],
        'scopes': ['openid', 'email', 'profile'],
    }
}
