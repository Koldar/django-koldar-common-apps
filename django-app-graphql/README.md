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

**After all your apps you need to use this app** (this is important otherwise some models won't be detected at all!):

```
'django_app_graphql',
```

The first thing you need to do is determine if you want your grpahql server setupped using `graphene` or uysing `ariadne`.
In settings, write:

```
DJANGO_APP_GRAPHQL = {
    "BACKEND_TYPE": "ariadne|graphene"
}
```

and select either *ariadne* or *graphene*.

## You have chosen graphene

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
    "SCHEMA": "django_app_graphql.graphene.schema.schema",
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

## You have chosen ariadne

In `settings.py` add:

```
INSTALLED_APPS = [
    ...
    "ariadne.contrib.django",
]
```

Add templates (otherwise the playground won't work):

```
TEMPLATES = [
    {
        ...,
        'APP_DIRS': True,
        ...
    },
]
```

## Generic tweaks

Finally you can configure this app, for instance:

```
DJANGO_APP_GRAPHQL = {
    "BACKEND_TYPE": "graphene",
    "EXPOSE_GRAPHIQL": True,
    "GRAPHQL_SERVER_URL": "",
    "ENABLE_GRAPHQL_FEDERATION": True,
    "SAVE_GRAPHQL_SCHEMA": "output/schema.graphql"
}
```


# Update new version (only for developers)

```
pmakeup update-version-patch build upload-to-pypi
```