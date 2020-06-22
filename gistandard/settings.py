

import os
import sys
#git 测试
# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, 'apps'))
sys.path.insert(0, os.path.join(BASE_DIR, 'extra_apps'))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '#i334a-(y5e9=$ket!!)x4&pow&r#x8kqxtrj&n)!x=57n8)#%'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

# Application definition

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',  # 跨域
    'apps.users.apps.UsersConfig',
    'apps.rbac.apps.RbacConfig',
    'apps.system.apps.SystemConfig',
    'apps.adm.apps.AdmConfig',
    'apps.personal.apps.PersonalConfig',
    'apps.bulletin.apps.BulletinConfig',
    'apps.oilWear.apps.OilwearConfig',
    'apps.assess.apps.AssessConfig',
    'apps.worklog.apps.WorklogConfig',
    'apps.exam.apps.ExamConfig',
    'xadmin',
    'crispy_forms',
    'django.contrib',

]

AUTH_USER_MODEL = 'users.UserProfile'

AUTHENTICATION_BACKENDS = (
    'users.views_user.UserBackend',
)

# 中间层
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # 跨域
    'apps.users.middleware.MenuMiddleware',
    'apps.rbac.middleware.RbacMiddleware',
]

ROOT_URLCONF = 'gistandard.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')]
        ,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',   # 表示文件文档   {{ MEDIA_URL }}路由有效
            ],
        },
    },
]

WSGI_APPLICATION = 'gistandard.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases
#
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.mysql',
#         'NAME': 'ygerp',
#         'HOST': 'localhost',
#         'USER': 'root',
#         'PASSWORD': '123456',
#     }
# }
# 本地模仿阿里云数据库
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.mysql',
#         'NAME': 'yun_oa',
#         'HOST': 'localhost',
#         'USER': 'root',
#         'PASSWORD': '123456',
#     }
# }


# 正式服
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'yun_oa',
        'HOST': 'localhost',
        'USER': 'root',
        'PASSWORD': 'ygdl12345!@#$%',
    }
}
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.mysql',
#         'NAME': 'yun_oa',
#         'HOST': '192.168.1.104',
#         'USER': 'root',
#         'PASSWORD': 'Ygkj123456.',
#     }
# }

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.mysql',
#         'NAME': 'yun_oa',
#         'HOST': 'localhost',
#         'USER': 'root',
#         'PASSWORD': '123',
#     }
# }

# 阿里云
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.mysql',
#         'NAME': 'ygerp',
#         'HOST': '39.98.164.227',
#         'USER': 'yunmysql',
#         'PASSWORD': 'ygdl12345!@#$%',
#         'PORT': '9001',
#     }
# }
# 
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
#     }
# }

# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'zh-hans'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_L10N = True

USE_TZ = False

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

STATIC_URL = '/static/'

STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

MEDIA_URL = '/media/'

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

LOGIN_URL = '/login/'

# URL white list
SAFE_URL = [r'^/$',
            '/login/',
            '/logout',
            '/index/',
            '/media/',
            '/xadmin/',
            ]

# session timeout

SESSION_COOKIE_AGE = 60 * 30
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_SAVE_EVERY_REQUEST = True

# mail server
EMAIL_HOST = "mail.sandbox.com"
EMAIL_PORT = 587
EMAIL_HOST_USER = "test@sandbox.com"
EMAIL_HOST_PASSWORD = "1234@abcd.com"
EMAIL_USE_TLS = True
EMAIL_FROM = "test@sandbox.com"

# CORS
# 跨域增加忽略
CORS_ALLOW_CREDENTIALS = True
CORS_ORIGIN_ALLOW_ALL = True
CORS_ORIGIN_WHITELIST = ()

CORS_ALLOW_METHODS = (
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
    'VIEW',
)

CORS_ALLOW_HEADERS = (
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
)
