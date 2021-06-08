import os
import unittest
from typing import Any

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server_project.settings")
import django
django.setup()


from graphene.test import Client
from graphql_section import schema


class AbstractGraphQLTest(unittest.TestCase):

    graphql_client: Client = None

    @classmethod
    def setUpClass(cls) -> None:
        pass

    def setUp(self) -> None:
        self.graphql_client = Client(schema=schema.schema)

    def _check_query(self, query, context):
        query = f"""
        query {{
            {query}
        }}
        """
        executed = self.graphql_client.execute(query, context=context)
        assert 'data' in executed, "GraphQL output should return 'data', but this call did not."
        assert 'errors' not in executed, f"Got graphQL errors: {executed}"
        assert executed['data'] is not None, f"data paylaod is None. Output={executed}"
        return executed['data']

    def assert_query_data_equal(self, query, expected, context=None):
        output = self._check_query(query, context)
        assert output == expected

    def assert_query_data_contains_key(self, query: str, key: str, context=None):
        output = self._check_query(query, context)
        assert key in output

    def assert_query_data_key_value(self, query:str, key: str, value: Any, context=None):
        output = self._check_query(query, context)

        assert key in output
        assert output[key] is not None
        assert output[key] == value




# Create your tests here.