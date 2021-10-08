# from datetime import timedelta
# from typing import Iterable, Any, Dict, List
#
# from django_koldar_utils.django_toolbox.ApplicationProperty import ApplicationProperty
# from django_koldar_utils.sections.AbstractDjangoSection import AbstractDjangoSection
#
#
# class GraphQLSection(AbstractDjangoSection):
#
#     def setup(self):
#         pass
#
#     def get_section_setup_dependencies(self) -> Iterable[str]:
#         return [".*"]
#
#     def is_exposing_http_endpoint(self) -> bool:
#         return True
#
#     def get_configuration_dictionary_name(self) -> str:
#         return "GRAPHQL_SECTION"
#
#     def get_properties_declaration(self) -> Dict[str, ApplicationProperty]:
#         return {}
#
#     def update_middlewares(self, middlewares: List[str]) -> List[str]:
#         return middlewares
#
#     def get_variables_to_add_in_project_settings(self, base_dir: str) -> Dict[str, Any]:
#         return dict(
#             GRAPHENE={
#                 "SCHEMA": "graphql_section.schema.schema",
#                 'SCHEMA_OUTPUT': 'graphql-schema.json',
#                 'SCHEMA_INDENT': 2,
#                 'MIDDLEWARE': [
#                     "graphql_jwt.middleware.JSONWebTokenMiddleware",
#                     "graphql_section.middleware.GraphQLStackTraceInErrorMiddleware",
#                 ],
#             },
#             GRAPHENE_DJANGO_EXTRAS={
#                 'DEFAULT_PAGINATION_CLASS': 'graphene_django_extras.paginations.LimitOffsetGraphqlPagination',
#                 'DEFAULT_PAGE_SIZE': 20,
#                 'MAX_PAGE_SIZE': 50,
#                 'CACHE_ACTIVE': True,
#                 'CACHE_TIMEOUT': 300  # seconds
#             },
#             # see https://django-graphql-jwt.domake.io/en/latest/refresh_token.html
#             GRAPHQL_JWT={
#                 # This configures graphql-jwt to add "token" input at each request to be authenticated
#                 'JWT_ALLOW_ARGUMENT': True,
#                 'JWT_ARGUMENT_NAME': "token",
#                 'JWT_VERIFY_EXPIRATION': True,
#                 'JWT_EXPIRATION_DELTA': timedelta(minutes=30),
#                 'JWT_ALGORITHM': "HS256",
#                 'JWT_REFRESH_EXPIRATION_DELTA': timedelta(days=7),
#                 'JWT_AUTH_HEADER_PREFIX': "Bearer",
#             }
#         )
#
#     def get_route_prefix(self) -> str:
#         return "graphql"
#
#     def depends_on_app(self) -> Iterable[str]:
#         return [
#             'graphene_django',
#             'django_filters',
#         ]
#
#     def get_authentication_backends(self) -> Iterable[str]:
#         return [
#             "graphql_jwt.backends.JSONWebTokenBackend",
#             "django.contrib.auth.backends.ModelBackend"
#         ]
#
#
