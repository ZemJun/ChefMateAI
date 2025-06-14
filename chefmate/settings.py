# ChefMateAI\chefmate\settings.py

from pathlib import Path
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

# ALLOWED_HOSTS 从 .env 读取，并解析成列表
# default 值用于当 .env 中没有这个变量时
ALLOWED_HOSTS_str = config('ALLOWED_HOSTS', default='127.0.0.1,localhost')
ALLOWED_HOSTS = [host.strip() for host in ALLOWED_HOSTS_str.split(',')]

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # My Apps
    'django_extensions',
    'users.apps.UsersConfig',
    'recipes.apps.RecipesConfig', # 新增 recipes 应用

    # Third Party Apps
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist', # 如果需要支持token吊销/刷新后旧token失效
    'corsheaders',
    'drf_yasg',
]

AUTH_USER_MODEL = 'users.User'

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    'corsheaders.middleware.CorsMiddleware', 
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "chefmate.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug", # 建议加上 debug context processor
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "chefmate.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': config('DB_ENGINE', default='django.db.backends.postgresql'),
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432', cast=int),
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "zh-hans"

TIME_ZONE = "Asia/Shanghai"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = "static/"

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    # 默认的认证方式
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    # 默认的权限策略
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    # 默认的分页设置
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    
    # 默认的渲染器
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    
    # vvvvvvvvvvvvvvvvvvvv 这是需要修改的地方 vvvvvvvvvvvvvvvvvvvv
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',          # 继续支持 JSON 数据
        'rest_framework.parsers.FormParser',          # 支持 application/x-www-form-urlencoded
        'rest_framework.parsers.MultiPartParser'      # <--- 核心：添加这个来支持 multipart/form-data (文件上传)
    ]
    # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
}

from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=120),      # Access Token 的有效期 (例如: 120 分钟)
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),        # Refresh Token 的有效期 (例如: 1 天)
    'ROTATE_REFRESH_TOKENS': True,                      # 每次使用 Refresh Token 刷新 Access Token 时，是否也返回一个新的 Refresh Token
    'BLACKLIST_AFTER_ROTATION': True,                   # 如果 ROTATE_REFRESH_TOKENS 为 True, 是否将旧的 Refresh Token 加入黑名单
                                                        # (需要 INSTALLED_APPS 中有 'rest_framework_simplejwt.token_blacklist')
    'UPDATE_LAST_LOGIN': True,                         # 登录（获取token）时是否更新 Django User 模型的 last_login 字段

    'ALGORITHM': 'HS256',                               # JWT 签名算法
    'SIGNING_KEY': SECRET_KEY,                          # 用于签名的密钥，直接使用 Django 的 SECRET_KEY
    'VERIFYING_KEY': None,                              # 用于验证签名的公钥 (如果使用非对称算法如RS256)
    'AUDIENCE': None,                                   # JWT 的受众
    'ISSUER': None,                                     # JWT 的签发者
    'JWK_URL': None,                                    # JSON Web Key Set URL
    'LEEWAY': 0,                                        # 允许的时间偏差 (秒)

    'AUTH_HEADER_TYPES': ('Bearer',),                   # HTTP 请求头中用于传递 Token 的认证方案 (例如: "Authorization: Bearer <token>")
                                                        # 也可设为 ('JWT',)，则为 "Authorization: JWT <token>"
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',           # 存储 Token 的 HTTP 请求头的名称
    'USER_ID_FIELD': 'id',                              # User 模型中用作用户标识的字段名 (通常是 'id')
    'USER_ID_CLAIM': 'user_id',                         # JWT payload 中代表用户ID的声明 (claim) 的名称
    
    # 自定义用户认证规则
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',), # Access Token 使用的类
    'TOKEN_TYPE_CLAIM': 'token_type',                   # JWT payload 中代表 Token 类型的声明的名称
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser', # 用于从 Token 中重建用户的类

    'JTI_CLAIM': 'jti',                                 # JWT ID (jti) 声明的名称, 用于唯一标识 Token

    # 滑动窗口 Token (Sliding Tokens) - 如果需要 token 自动续期，可以启用
    # 'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    # 'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    # 'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

CORS_ALLOW_ALL_ORIGINS = True # <--- 在开发环境下为了方便测试，允许所有来源