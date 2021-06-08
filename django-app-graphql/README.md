# Introduction

Django app that expose a graphql schema as well as a graphiql interface.

# install

```
pip install django-app-graphql
```

# Configuration

in `INSTALLED_APPS` you need to add:

```
'graphene_django',
'django_filters',
```

After all your apps you need to use this app:

```
'django_app_graphql',
```

The app needs to be deploy for last because otherwise it cannot detect all the Django models and their types.
You also need to configure the authentication proces. Hence you need t add "AUTHENTICATION_BACKENDS" in the `settings.py`:

```
AUTHENTICATION_BACKENDS = [
    "graphql_jwt.backends.JSONWebTokenBackend",
    "django.contrib.auth.backends.ModelBackend"
]
```

After that, you need to properly configure the graphene, graphenedjango-extras and graphene-jwt. Add all these in your `settings.py`:

```
GRAPHENE={
    "SCHEMA": "django_app_graphql.schema.schema",
    'SCHEMA_OUTPUT': 'graphql-schema.json',
    'SCHEMA_INDENT': 2,
    'MIDDLEWARE': [
        "graphql_jwt.middleware.JSONWebTokenMiddleware",
        "django_app_graphql.middleware.GraphQLStackTraceInErrorMiddleware",
    ],
}

GRAPHENE_DJANGO_EXTRAS = {
    'DEFAULT_PAGINATION_CLASS': 'graphene_django_extras.paginations.LimitOffsetGraphqlPagination',
    'DEFAULT_PAGE_SIZE': 20,
    'MAX_PAGE_SIZE': 50,
    'CACHE_ACTIVE': True,
    'CACHE_TIMEOUT': 300  # seconds
}

# see https://django-graphql-jwt.domake.io/en/latest/refresh_token.html
GRAPHQL_JWT = {
    # This configures graphql-jwt to add "token" input at each request to be authenticated
    'JWT_ALLOW_ARGUMENT': True,
    'JWT_ARGUMENT_NAME': "token",
    'JWT_VERIFY_EXPIRATION': True,
    'JWT_EXPIRATION_DELTA': timedelta(minutes=30),
    'JWT_ALGORITHM': "HS256",
    'JWT_REFRESH_EXPIRATION_DELTA': timedelta(days=7),
    'JWT_AUTH_HEADER_PREFIX': "Bearer",
}
```

Finally you can configure this app, for instance:

```
DJANGO_APP_GRAPHQL = {
    "EXPOSE_GRAPHIQL": True,
    "GRAPHQL_SERVER_URL": ""
}
```


# Update new version (only for developers)

```
pmakeup update-version-patch build upload-to-pypi
```