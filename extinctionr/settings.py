"""
Django settings for xrmass project.

Generated by 'django-admin startproject' using Django 2.1.7.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv(
    "SECRET_KEY", "msl&0^9j7r3#trf#c^4yja9ihj+1+@7wf9^)1-*v@42z*a2562"
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DEBUG", "true") == "true"

ALLOWED_HOSTS = [
    "www.xrboston.org",
    "xrboston.org",
    "test.xrboston.org",
    "localhost",
]

SITE_ID = 1

# Application definition

INSTALLED_APPS = [
    "dal",
    "dal_select2",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.sites.apps.SitesConfig",
    "django.contrib.staticfiles",
    "django.contrib.humanize.apps.HumanizeConfig",
    "django.contrib.redirects",
    # CRM stuff
    "simple_pagination",
    "compressor",
    "common.apps.CommonConfig",
    "accounts",
    "cases",
    "contacts",
    "emails",
    "leads",
    "opportunity",
    "planner",
    "phonenumber_field",
    "storages",
    "marketing",
    # end of CRM stuff
    "extinctionr.actions.apps.ActionsConfig",
    "extinctionr.info",
    "extinctionr.circles.apps.CircleConfig",
    "extinctionr.news",
    "extinctionr.vaquita",
    # Wagatil core packages.
    "wagtail.contrib.forms",
    "wagtail.contrib.redirects",
    "wagtail.contrib.modeladmin",
    "wagtail.contrib.settings",
    "wagtail.embeds",
    "wagtail.sites",
    "wagtail.users",
    "wagtail.snippets",
    "wagtail.documents",
    "wagtail.images",
    "wagtail.search",
    "wagtail.admin",
    "wagtail.core",
    "wagtailmarkdown",
    "modelcluster",
    # End of Wagtail.
    # Django SQL Explorer
    "explorer",
    # django wiki
    "django_nyt.apps.DjangoNytConfig",
    "mptt",
    "sekizai",
    "sorl.thumbnail",
    "wiki.apps.WikiConfig",
    "wiki.plugins.attachments.apps.AttachmentsConfig",
    "wiki.plugins.notifications.apps.NotificationsConfig",
    "wiki.plugins.images.apps.ImagesConfig",
    "wiki.plugins.macros.apps.MacrosConfig",
    "wiki.plugins.globalhistory.apps.GlobalHistoryConfig",
    "wiki.plugins.help.apps.HelpConfig",
    "markdownx",
    "todo",
    "taggit",
    # mailman
    "postorius",
    "django_mailman3",
    "django_gravatar",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.openid",
    # 'django_mailman3.lib.auth.fedora',
    # 'allauth.socialaccount.providers.github',
    # 'allauth.socialaccount.providers.gitlab',
    "allauth.socialaccount.providers.google",
    # 'allauth.socialaccount.providers.facebook',
    # 'allauth.socialaccount.providers.twitter',
    # 'allauth.socialaccount.providers.stackexchange',
    "django_apscheduler",
]

MIDDLEWARE = [
    "django.middleware.http.ConditionalGetMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    # 'django.middleware.csrf.CsrfViewMiddleware',
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.contrib.redirects.middleware.RedirectFallbackMiddleware",
    "extinctionr.middleware.redirect_middleware",
    "crum.CurrentRequestUserMiddleware",
    "postorius.middleware.PostoriusMiddleware",
    "wagtail.contrib.legacy.sitemiddleware.SiteMiddleware",
    "wagtail.contrib.redirects.middleware.RedirectMiddleware",
]
if DEBUG:
    try:
        import debug_toolbar

        INSTALLED_APPS += ["debug_toolbar"]
        MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]
    except ImportError:
        pass
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
    INSTALLED_APPS += ["wagtail.contrib.styleguide"]


INTERNAL_IPS = ["127.0.0.1"]

ROOT_URLCONF = "extinctionr.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "sekizai.context_processors.sekizai",  # for django-wiki
                "django_mailman3.context_processors.common",
                "postorius.context_processors.postorius",
                "extinctionr.circles.context_processors.signup",
            ],
            "libraries": {
                # Temp hack to fix CRM library. Django 3 removed staticfiles.
                "staticfiles": "django.templatetags.static"
            },
        },
    },
]

WSGI_APPLICATION = "extinctionr.wsgi.application"


# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
    },
    "readonly": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "US/Eastern"

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

STORAGE_TYPE = "normal"
STATICFILES_DIRS = (BASE_DIR + "/static",)

STATIC_ROOT = BASE_DIR + "/static_root/"

STATIC_URL = "/static/"
if DEBUG:
    MEDIA_URL = "/media/"
else:
    MEDIA_URL = "/static/media/"
MEDIA_ROOT = STATIC_ROOT + "media/"

COMPRESS_ENABLED = True
COMPRESS_ROOT = STATIC_ROOT

COMPRESS_CSS_FILTERS = [
    "compressor.filters.css_default.CssAbsoluteFilter",
    "extinctionr.utils.CSSMinFilter",
]

COMPRESS_REBUILD_TIMEOUT = 5400
COMPRESS_OUTPUT_DIR = "CACHE"
COMPRESS_URL = STATIC_URL

COMPRESS_PRECOMPILERS = (("text/x-scss", "django_libsass.SassCompiler"),)
COMPRESS_OFFLINE_CONTEXT = {
    "STATIC_URL": "STATIC_URL",
}

STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    "compressor.finders.CompressorFinder",
)

AUTH_USER_MODEL = "common.User"

LOGIN_REDIRECT_URL = "/"
LOGIN_URL = "login"
LOGOUT_URL = "logout"

GP_CLIENT_ID = os.getenv("GP_CLIENT_ID", False)
GP_CLIENT_SECRET = os.getenv("GP_CLIENT_SECRET", False)
ENABLE_GOOGLE_LOGIN = os.getenv("ENABLE_GOOGLE_LOGIN", False)

ADMIN_EMAIL = "webmaster@xrboston.org"
DEFAULT_FROM_EMAIL = "webmaster@xrboston.org"

PHONENUMBER_DEFAULT_REGION = "US"

CACHE_MIDDLEWARE_SECONDS = 1200

SECURE_PROXY_SSL_HEADER = ("HTTP_X_SCHEME", "https")
SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"

WIKI_CHECK_SLUG_URL_AVAILABLE = False

# django-todo settings
TODO_DEFAULT_LIST_SLUG = "tickets"
TODO_DEFAULT_ASSIGNEE = "johnb.xr@pm.me"
TODO_PUBLIC_SUBMIT_REDIRECT = "extinctionr.info:index"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
    },
    "formatters": {
        "django.server": {
            "()": "django.utils.log.ServerFormatter",
            "format": "[{server_time}] {message}",
            'style': '{',
        }
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "filters": ["require_debug_true"],
            "class": "logging.StreamHandler",
            "formatter": "django.server",
        },
        "console_debug_false": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "logging.StreamHandler",
            "formatter": "django.server",
        },
        "django.server": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "django.server",
        },
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "console_debug_false", "mail_admins"],
            "level": "INFO",
        },
        "django.server": {
            "handlers": ["django.server"],
            "level": "INFO",
            "propagate": False,
        },
        "extinctionr": {
            "handlers": ["console", "console_debug_false", "mail_admins"],
            "level": "INFO",
        },
    },
}

EXPLORER_CONNECTIONS = {"Default": "readonly"}
EXPLORER_DEFAULT_CONNECTION = "readonly"
EXPLORER_SCHEMA_INCLUDE_TABLE_PREFIXES = (
    "actions",
    "circles",
    "contacts",
    "common_user",
    "info",
    "marketing",
    "news",
    "taggit",
)

# Mailman API credentials
MAILMAN_REST_API_URL = "http://localhost:9001"
MAILMAN_REST_API_USER = "restadmin"
MAILMAN_REST_API_PASS = "restpass"
POSTORIUS_TEMPLATE_BASE_URL = "http://localhost:8000"


ADMINS = [("Webmaster", "webmaster@xrboston.org")]
SERVER_EMAIL = "webmaster@xrboston.org"
ACTION_RSVP_WHITELIST = []

# Wagtail settings
WAGTAIL_SITE_NAME = "XR Boston"
WAGTAILEMBEDS_RESPONSIVE_HTML = True
WAGTAILIMAGES_IMAGE_MODEL = "vaquita.CustomImage"
WAGTAIL_USER_EDIT_FORM = "extinctionr.vaquita.forms.CustomUserEditForm"
WAGTAIL_USER_CREATION_FORM = "extinctionr.vaquita.forms.CustomUserCreationForm"
WAGTAIL_USER_CUSTOM_FIELDS = ["username"]

AN_API_KEY = "Debug"
