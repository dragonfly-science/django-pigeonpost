DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '/tmp/pigeonpost',
    }
}


# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)
TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.request",
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.transaction.TransactionMiddleware',
)


INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.admin',
    'django.contrib.markup',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.sitemaps',
    #'django.contrib.staticfiles',
    'pigeonpost',
    'pigeonpost_example',
    'django_coverage',
)

SECRET_KEY = '959684cb7a188abc25b9a504db03fbe3'

SITE_ID = 1

ROOT_URLCONF = 'pigeonpost.urls'


# Testing settings for django coverage
COVERAGE_REPORT_HTML_OUTPUT_DIR = 'htmlcov'
COVERAGE_TEST_RUNNER = 'django_coverage.coverage_runner.CoverageRunner'
COVERAGE_USE_CACHE = True
