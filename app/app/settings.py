from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

TELEGRAM_LISTENER_WEBSOCKET = os.getenv('TELEGRAM_LISTENER_WEBSOCKET')
TELEGRAM_LISTENER_TOKEN = os.getenv('TELEGRAM_LISTENER_TOKEN')
TELEGRAM_API_TOKEN = os.getenv('TELEGRAM_API_TOKEN')
TELEGRAM_DEBUG_API_TOKEN = os.getenv('TELEGRAM_DEBUG_API_TOKEN')

BINANCE_ENDPOINT = os.getenv('BINANCE_ENDPOINT')
BINANCE_PRIVATE_STREAM = os.getenv('BINANCE_PRIVATE_STREAM')
BINANCE_KEEP_ALIVE_PERIOD = int(os.getenv('BINANCE_KEEP_ALIVE_PERIOD'))

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_DOMAIN = os.getenv('AWS_DOMAIN')
AWS_BUCKET_NAME = os.getenv('AWS_BUCKET_NAME')

BROKER_HOST = os.getenv('BROKER_HOST')
BROKER_PASS = os.getenv('BROKER_PASS')


INSTALLED_APPS = (
    'django.contrib.contenttypes',
    'django.contrib.auth',
    # Local apps
    'core.apps.CoreConfig'
)


WSGI_APPLICATION = 'app.wsgi.application'


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "HOST": os.getenv("DB_HOST"),
        "NAME": os.getenv("DB_NAME"),
        "USER": os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PASS")
    }
}

BROKER_URI = f'redis://:{BROKER_PASS}@{BROKER_HOST}:6379/0'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': BROKER_URI,
    }
}


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False
}


CELERY_BROKER_URL = BROKER_URI
CELERY_RESULT_BACKEND = BROKER_URI
CELERY_TIMEZONE = 'Asia/Tehran'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60

AUTH_USER_MODEL = 'core.User'

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Tehran'

USE_I18N = True

USE_L10N = True

USE_TZ = True


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

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
