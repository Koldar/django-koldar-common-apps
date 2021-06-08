from django.contrib import admin
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from graphene_django.views import GraphQLView
from django_app_graphql.conf import settings

urlpatterns = [
# when graphiql is set to True, we will also provide a graphql frontend to ease the queries
    path(settings.GRAPHQL_SERVER_URL, csrf_exempt(GraphQLView.as_view(graphiql=settings.EXPOSE_GRAPHIQL)))
]
