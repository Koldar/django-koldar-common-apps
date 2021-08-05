import abc
import json
import re
from typing import Dict, Tuple, Callable, Union

import jmespath
from django.core.handlers.wsgi import WSGIRequest
from graphene_django.utils.testing import GraphQLTestCase


class GraphQLRequestInfo(object):
    """
    A class that syntethzie the graphql call the developer wants to test
    """

    def __init__(self, graphql_query: str, graphql_operation_name: str = None, input_data: Dict[str, any] = None, headers: Dict[str, any] = None, graphql_variables: Dict[str, any] = None):
        self.query = graphql_query
        self.operation_name = graphql_operation_name
        self.input_data = input_data
        self.graphql_variables = graphql_variables
        self.headers = headers


class GraphQLResponseInfo(object):
    """
    A class that synthetizes the rerequest-response the program has performed with a graphql server
    """

    def __init__(self, request: GraphQLRequestInfo, response: WSGIRequest, content: Dict[str, any]):
        self.request = request
        self.response = response
        self.content = content


GraphQLAssertionConstraint = Callable[[GraphQLResponseInfo], Tuple[bool, str]]
"""
A constraint of assert_graphql_response_satisfy

:param 1: gaphql request parameters
:param 2: gaphql response
:param 3: graphql json decoded response
:return: tuple where first value is a boolean that is set if the constraint was satisfied, false otherwise; seocnd parameter
    is a string that is used to transmit error to the developer i the constraint was not satisfied
"""


class AbstractGraphQLTest(GraphQLTestCase, abc.ABC):
    """
    A class allowing you to tst graphql queries
    """

    def perform_graphql_query(self, graphql_query_info: Union[GraphQLRequestInfo, str]) -> GraphQLResponseInfo:
        """
        Generally perform a query to the graphql endpoint

        :param graphql_query_info: either a full structure describing the request we want to make or a graphql query string (query nd mutation included)
        """
        if isinstance(graphql_query_info, str):
            graphql_query_info = GraphQLRequestInfo(
                graphql_query=graphql_query_info,
            )
        response = self.query(
            query=graphql_query_info.query,
            operation_name=graphql_query_info.operation_name,
            input_data=graphql_query_info.input_data,
            variables=graphql_query_info.graphql_variables,
            headers=graphql_query_info.headers,
        )
        # load the reponse as a json
        content = json.loads(response.content)
        return GraphQLResponseInfo(graphql_query_info, response, content)

    def perform_simple_query(self, query_body: str) -> GraphQLResponseInfo:
        """
        perform a graphql query that needs only to send a simple query body (included query{).

        :param query_body:
        """
        return self.perform_graphql_query(GraphQLRequestInfo(
            graphql_query=str(query_body)
        ))

    def perform_simple_mutation(self, mutation_body: str) -> GraphQLResponseInfo:
        return self.perform_graphql_query(GraphQLRequestInfo(
            graphql_query=str(mutation_body)
        ))

    def assert_graphql_response_satisfy(self, graphql_response: GraphQLResponseInfo, constraint: GraphQLAssertionConstraint, check_success: bool = True):
        satisfied, error_message = constraint(graphql_response)
        if check_success:
            self.assert_graphql_response_noerrors(graphql_response)
        if not satisfied:
            raise AssertionError(f"Error: {error_message}\nQuery:{graphql_response.request.query}\nVariables:{graphql_response.request.graphql_variables}")

    def assert_graphql_response_noerrors(self, graphql_response: GraphQLResponseInfo):
        """
        Ensure that the graphql response you got from the graphql test client is a successful one (at least on HTTP level)

        :param graphql_response: object genrated by perform_graphql_query
        :raise AssertionError: if the check fails
        """
        super().assertResponseNoErrors(graphql_response.response, f"graphql {graphql_response.request} did not return successfully!")

    def assert_json_path_satisfies(self, graphql_response: GraphQLResponseInfo, criterion: GraphQLAssertionConstraint):
        """
        Ensure that the json body you got by parsing a graphql successful response you got from the graphql test client
         satisfies a specific constraint. Nothing is said about the constraint

        :param graphql_response: object genrated by perform_graphql_query
        :param criterion: the criterion the json body needs to satisfy.
        :raise AssertionError: if the check fails
        """
        satisfied, error_message = criterion(graphql_response)
        if not satisfied:
            return satisfied, f"json body check failure. {error_message}"
        else:
            return True, None

    def assert_json_path_exists(self, graphql_response: GraphQLResponseInfo, path: str):
        """
        Ensure that the json body you got by parsing a graphql successful response you got from the graphql test client
        specifies a specific path. e.g., 'foo.bar' is present in {'foo': {'bar': 5}} while 'foo.baz' is not

        :param graphql_response: object genrated by perform_graphql_query
        :param path: a JSON path in the graphql response
        :raise AssertionError: if the check fails
        :see: https://jmespath.org/
        """
        def criterion(aresponse: GraphQLResponseInfo) -> Tuple[bool, str]:
            return jmespath.search(path, aresponse.content) is not None, f"path {path} does not exist in response!"

        self.assert_json_path_satisfies(graphql_response, criterion)

    def assert_json_path_is_absent(self, graphql_response: GraphQLResponseInfo, path: str):
        """
        Ensure that the json body you got by parsing a graphql successful response you got from the graphql test client
        does not specify a specific path. e.g., 'foo.bar' is present in {'foo': {'bar': 5}} while 'foo.baz' is not

        :param graphql_response: object genrated by perform_graphql_query
        :param path: a JSON path in the graphql response
        :raise AssertionError: if the check fails
        :see: https://jmespath.org/
        """
        def criterion(aresponse: GraphQLResponseInfo) -> Tuple[bool, str]:
            return jmespath.search(path, aresponse.content) is None, f"path {path} exists in the response"

        self.assert_json_path_satisfies(graphql_response, criterion)

    def assert_json_path_equals_to(self, graphql_response: GraphQLResponseInfo, path: str, expected_value: any):
        """
        Ensure that the json body you got by parsing a graphql successful response you got from the graphql test client
        associates a value from a specific is equaal to an expected one.
         e.g., 'foo.bar' is expected to be 5 and in the json we have {'foo': {'bar': 5}}

        :param graphql_response: object genrated by perform_graphql_query
        :param path: a JSON path in the graphql response
        :param expected_value: expected value associated to the path
        :raise AssertionError: if the check fails
        :see: https://jmespath.org/
        """
        def criterion(aresponse: GraphQLResponseInfo) -> Tuple[bool, str]:
            actual = jmespath.search(path, aresponse.content)
            return actual == expected_value, f"in path {path}: actual == expected failed: {actual} != {expected_value}"

        self.assert_json_path_satisfies(graphql_response, criterion)

    def assert_json_path_not_equals_to(self, graphql_response: GraphQLResponseInfo, path: str, expected_value: any):
        def criterion(aresponse: GraphQLResponseInfo) -> Tuple[bool, str]:
            actual = jmespath.search(path, aresponse.content)
            return actual != expected_value, f"in path {path}: actual != expected failed: {actual} == {expected_value}"

        self.assert_json_path_satisfies(graphql_response, criterion)

    def assert_json_path_greater_than_to(self, graphql_response: GraphQLResponseInfo, path: str, expected_value: any):
        def criterion(aresponse: GraphQLResponseInfo) -> Tuple[bool, str]:
            actual = jmespath.search(path, aresponse.content)
            return actual > expected_value, f"in path {path}: actual > expected failed: {actual} <= {expected_value}"

        self.assert_json_path_satisfies(graphql_response, criterion)

    def assert_json_path_less_than_to(self, graphql_response: GraphQLResponseInfo, path: str, expected_value: any):
        def criterion(aresponse: GraphQLResponseInfo) -> Tuple[bool, str]:
            actual = jmespath.search(path, aresponse.content)
            return actual < expected_value, f"in path {path}: actual < expected failed: {actual} >= {expected_value}"

        self.assert_json_path_satisfies(graphql_response, criterion)

    def assert_json_path_greater_or_equal_to(self, graphql_response: GraphQLResponseInfo, path: str, expected_value: any):
        def criterion(aresponse: GraphQLResponseInfo) -> Tuple[bool, str]:
            actual = jmespath.search(path, aresponse.content)
            return actual >= expected_value, f"in path {path}: actual >= expected failed: {actual} < {expected_value}"

        self.assert_json_path_satisfies(graphql_response, criterion)

    def assert_json_path_less_than_or_equals_to(self, graphql_response: GraphQLResponseInfo, path: str, expected_value: any):
        def criterion(aresponse: GraphQLResponseInfo) -> Tuple[bool, str]:
            actual = jmespath.search(path, aresponse.content)
            return actual <= expected_value, f"in path {path}: actual <= expected failed: {actual} > {expected_value}"

        self.assert_json_path_satisfies(graphql_response, criterion)

    def assert_json_path_str_equals_to(self, graphql_response: GraphQLResponseInfo, path: str, expected_value: any):
        def criterion(aresponse: GraphQLResponseInfo) -> Tuple[bool, str]:
            actual = str(jmespath.search(path, aresponse.content))
            return actual == str(expected_value), f"in path {path}: str(actual) == str(expected) failed: {actual} != {expected_value}"

        self.assert_json_path_satisfies(graphql_response, criterion)

    def assert_json_path_str_not_equals_to(self, graphql_response: GraphQLResponseInfo, path: str, expected_value: any):
        def criterion(aresponse: GraphQLResponseInfo) -> Tuple[bool, str]:
            actual = str(jmespath.search(path, aresponse.content))
            return actual != str(expected_value), f"in path {path}: str(actual) != str(expected) failed: {actual} == {expected_value}"

        self.assert_json_path_satisfies(graphql_response, criterion)

    def assert_json_path_str_longer_than(self, graphql_response: GraphQLResponseInfo, path: str, minimum_length: int = None, maximum_length: int = None, min_included: bool = True, max_included: bool = False):
        def criterion(aresponse: GraphQLResponseInfo) -> Tuple[bool, str]:
            nonlocal minimum_length, maximum_length
            actual = str(jmespath.search(path, aresponse.content))
            actual_length = len(actual)
            if minimum_length is not None:
                if not min_included:
                    minimum_length += 1
                if actual_length < minimum_length:
                    return False, f"in path {path}: expected string needed to be at least {minimum_length} long (included), but it was {actual_length}"
            if maximum_length is not None:
                if not max_included:
                    maximum_length -= 1
                if actual_length > maximum_length:
                    return False, f"in path {path}: expected string needed to be at most {maximum_length} long (included), but it was {actual_length}"

        self.assert_json_path_satisfies(graphql_response, criterion)

    def assert_json_path_str_contains_substring(self, graphql_response: GraphQLResponseInfo, path: str, expected_substring: str):
        def criterion(aresponse: GraphQLResponseInfo) -> Tuple[bool, str]:
            actual = str(jmespath.search(path, aresponse.content))
            return str(expected_substring) in actual, f"in path {path}: expected in actual failed: {expected_substring} not in {actual}"

        self.assert_json_path_satisfies(graphql_response, criterion)

    def assert_json_path_str_match_regex(self, graphql_response: GraphQLResponseInfo, path: str, expected_regex: str):
        def criterion(aresponse: GraphQLResponseInfo) -> Tuple[bool, str]:
            actual = str(jmespath.search(path, aresponse.content))
            m = re.match(expected_regex, actual)
            return m is not None, f"in path {path} string {actual} does not WHOLLY satisfy the regex {expected_regex}"

        self.assert_json_path_satisfies(graphql_response, criterion)

    def assert_json_path_str_search_regex(self, graphql_response: GraphQLResponseInfo, path: str, expected_regex: str):
        def criterion(aresponse: GraphQLResponseInfo) -> Tuple[bool, str]:
            actual = str(jmespath.search(path, aresponse.content))
            m = re.search(expected_regex, actual)
            return m is not None, f"in path {path} string {actual} does not even partially satisfy the regex {expected_regex}"

        self.assert_json_path_satisfies(graphql_response, criterion)