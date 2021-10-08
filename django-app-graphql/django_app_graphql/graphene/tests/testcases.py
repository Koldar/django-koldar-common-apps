import abc

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import LiveServerTestCase, TestCase
from graphene_file_upload.django.testing import GraphQLFileUploadTestMixin

from django_app_graphql.graphene.tests.AbstractGraphQLTestMixin import AbstractGraphQLTestMixin, RealGraphQLClientMixIn, \
    GrapheneClientTestMixIn


class AbstractGraphQLDjangoTestCase(GrapheneClientTestMixIn, AbstractGraphQLTestMixin, TestCase, abc.ABC):
    """
    Graphql testclass to derive in order to test graphql.
    We use django Client graphql implementation
    """
    pass


class AbstractGraphQLDjangoStaticLiveServerTestCase(GrapheneClientTestMixIn, AbstractGraphQLTestMixin, StaticLiveServerTestCase, abc.ABC):
    """
    We use django live server to test. We use a fake graphql client to query the server
    """
    pass


class AbstractGraphQLRealTestCase(RealGraphQLClientMixIn, AbstractGraphQLTestMixin, TestCase, abc.ABC):
    """
    Graphql testclass to derive in order to test graphql
    We use a real http connection to perform graphql queries
    """
    pass


class AbstractGraphQLRealStaticLiveServerTestCase(RealGraphQLClientMixIn, AbstractGraphQLTestMixin, StaticLiveServerTestCase, abc.ABC):
    """
    We use django live server to test. We use a fake graphql client to query the server
    We use a real http connection to perform graphql queries
    """
    pass
