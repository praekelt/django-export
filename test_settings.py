DEBUG = True

DATABASE_ENGINE = 'sqlite3'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

SECRET_KEY = '123'

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.admin',
    'django.contrib.contenttypes',
    'object_tools',
    'export'
]

ROOT_URLCONF = 'object_tools.tests.urls'
STATIC_URL = '/static/'
