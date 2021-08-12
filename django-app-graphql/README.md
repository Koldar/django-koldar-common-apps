# Introduction

Django app that expose a graphql schema as well as a graphiql interface.

# User

## Installation

```
pip install django-app-graphql
```

## Configuration

in `INSTALLED_APPS` you need to add:

```
'graphene_django',
'django_filters',
```

**After all your apps you need to use this app** (this is important otherwise some models won't be detected at all!):

```
'django_app_graphql',
```

The first thing you need to do is determine if you want your graphql server setupped 
using `graphene` or using `ariadne`. In settings, write:

```
DJANGOAPPGRAPHQL = dict(
    BACKENDTYPE="ariadne/graphene"
)
```

and select either *ariadne* or *graphene*.

Finally, in `urls.py` of the entire project add the following line:

```
urlpatterns = [
    ...
    path("graphqls/", include("django_app_graphql.urls")),
    ...
]
```


### You have chosen graphene

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
GRAPHENE = dict(
    SCHEMA" = "django_app_graphql.graphene.schema.SCHEMA",
    SCHEMA_OUTPUT = 'graphql-schema.json',
    SCHEMA_INDENT = 2,
    MIDDLEWARE = [
        "graphql_jwt.middleware.JSONWebTokenMiddleware",
        "django_app_graphql.middleware.GraphQLStackTraceInErrorMiddleware",
    ],
)

GRAPHENE_DJANGO_EXTRAS = dict(
    DEFAULT_PAGINATION_CLASS = 'graphene_django_extras.paginations.LimitOffsetGraphqlPagination',
    DEFAULT_PAGE_SIZE = 20,
    MAX_PAGE_SIZE = 50,
    CACHE_ACTIVE = True,
    CACHE_TIMEOUT = 300  # seconds
)

# see https://django-graphql-jwt.domake.io/en/latest/refresh_token.html
GRAPHQL_JWT = dict(
    # This configures graphql-jwt to add "token" input at each request to be authenticated
    JWT_ALLOW_ARGUMENT = True,
    JWT_ARGUMENT_NAME = "token",
    JWT_VERIFY_EXPIRATION = True,
    JWT_EXPIRATION_DELTA = timedelta(minutes=30),
    JWT_ALGORITHM = "HS256",
    JWT_REFRESH_EXPIRATION_DELTA = timedelta(days=7),
    JWT_AUTH_HEADER_PREFIX = "Bearer",
)
```

### You have chosen ariadne

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

Ariadne is in unstable development (I don't know if it will ever be supported)

### Generic tweaks

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
# Developer

# Update new version (only for developers)

You can use `setuptools` and `twine`:

```
python setup.py update_version_patch bdist_wheel
twine upload dist/*
```

Or you can use `pmakeup`

```
pmakeup update-version-patch build upload-to-pypi
```