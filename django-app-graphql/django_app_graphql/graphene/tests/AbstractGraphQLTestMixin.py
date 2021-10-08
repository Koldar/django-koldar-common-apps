import abc
import json
import operator
import os
import re
import sys
from typing import Dict, Tuple, Callable, Union, List, Optional

import jmespath
from django.conf import settings
from django.core.handlers.wsgi import WSGIRequest

# from graphene.test import Client
from gql.transport.exceptions import TransportQueryError
from graphene_django.tests.test_utils import client_query
from graphene_django.utils.testing import GraphQLTestCase, graphql_query
from graphene_file_upload.django.testing import GraphQLFileUploadTestMixin, file_graphql_query

import gql
from gql.client import AsyncClientSession
from gql import Client as GQLClient
from graphql import DocumentNode
from gql.transport.async_transport import AsyncTransport

import logging

LOG = logging.getLogger(__name__)


class FileToUpload(object):
    """
    Declarative way of a file to upload
    """

    def __init__(self, filepath: str, file_variable_name: str, encoding: str = "utf8", name: str = None,
                 content_type: str = None):
        self.filepath = filepath
        self.encoding = encoding
        self.name = name or os.path.basename(self.filepath)
        self.content_type = content_type or "text/plain"
        self.file_variable_name = file_variable_name
        """
        the name of the graphql endpoint accepting this file 
        """


class GraphQLRequestInfo(object):
    """
    A class that syntethzie the graphql call the developer wants to test
    """

    def __init__(self, graphql_query: str, graphql_operation_name: str = None, input_data: Dict[str, any] = None,
                 headers: Dict[str, any] = None, graphql_variables: Dict[str, any] = None,
                 files: List[FileToUpload] = None):
        self.query = graphql_query
        self.operation_name = graphql_operation_name
        self.input_data = input_data
        self.graphql_variables = graphql_variables
        self.headers = headers
        self.files = files


class GraphQLResponseInfo(object):
    """
    A class that synthetizes the rerequest-response the program has performed with a graphql server
    """

    def __init__(self, request: GraphQLRequestInfo, response: WSGIRequest, content: Dict[str, any], response_status_code: int):
        self.request = request
        self.response = response
        self.content = content
        self.response_status_code = response_status_code

    def query_content(self, path: str) -> any:
        """
        Query the content in a generic way
        :param path:
        :return:
        """
        result = jmespath.search(path, self.content)
        return result

    def get_only_int(self, path: str):
        """
        perform a jmes query on the body. Then, check that there is only one from the response
        :param path: path to investigate
        :return: the only integer found or an exception if multiple or none are found
        """
        result = jmespath.search(path, self.content)
        if isinstance(result, list):
            raise ValueError(f"should have fetched one integer, but got {result}")
        if result is None:
            raise ValueError(f"should have been one integer. Got none of them!")
        return int(result)

    def get_first_int(self, path: str):
        result = jmespath.search(path, self.content)
        if isinstance(result, list):
            val = int(result[0])
        else:
            val = int(result)
        return val

    def get_only_string(self, path: str):
        """
        perform a jmes query on the body. Then, check that there is only one from the response
        :param path: path to investigate
        :return: the only string found or an exception if multiple or none are found
        """
        result = jmespath.search(path, self.content)
        if isinstance(result, list):
            raise ValueError(f"should have fetched one string, but got {result}")
        if result is None:
            raise ValueError(f"should have been one string. Got none of them!")
        return str(result)

    def get_first_string(self, path: str):
        result = jmespath.search(path, self.content)
        if isinstance(result, list):
            val = str(result[0])
        else:
            val = str(result)
        return val

    def get_only_bool(self, path: str):
        """
        perform a jmes query on the body. Then, check that there is only one from the response
        :param path: path to investigate
        :return: the only bool found or an exception if multiple or none are found
        """
        result = jmespath.search(path, self.content)
        if isinstance(result, list):
            raise ValueError(f"should have fetched one boolean, but got {result}")
        if result is None:
            raise ValueError(f"should have been one boolean. Got none of them!")
        return bool(result)

    def get_first_bool(self, path: str):

        result = jmespath.search(path, self.content)
        if isinstance(result, list):
            val = bool(result[0])
        else:
            val = bool(result)
        return val


GraphQLAssertionConstraint = Callable[[GraphQLResponseInfo], Tuple[bool, str]]
"""
A constraint of assert_graphql_response_satisfy

:param 1: gaphql request parameters
:param 2: gaphql response
:param 3: graphql json decoded response
:return: tuple where first value is a boolean that is set if the constraint was satisfied, false otherwise; seocnd parameter
    is a string that is used to transmit error to the developer i the constraint was not satisfied
"""


class AbstractGraphQLTestMixin(GraphQLFileUploadTestMixin, abc.ABC):
    """
    A class allowing you to tst graphql queries
    """

    def graphql_url(self) -> str:
        """
        Url of the graphql server to contact. Be **sure** it exists. By default it goes to GRAPHQL_URL, if existent.
        optheriwse, it returns graphql.
        :return:
        """
        return getattr(type(self), "GRAPHQL_URL", "/graphql/")

    def graphql_client_timeout(self) -> Optional[int]:
        """
        Number of seconds to wait for the response of a grpahql server before giving it up
        :return: If none there will be no timeout
        """
        return None

    @abc.abstractmethod
    def perform_authentication(self, **kwargs) -> any:
        """
        A method that is used in the tests to perform authentication of a client. Returns whatever you want.
        Requires you to input something that resembles credentials (e.g., username and password). We never call it,
        it's a convenience methdo for you,. If you don't plan tyo use authentication in your tests, set it to whateve you want
        """
        pass

    @abc.abstractmethod
    def _setup_graphql_client(self, graphql_url: str) -> any:
        """
        setup a the object that will be use to actually perform graphql queries to the server.
        The function will be called the first time we needed to contact the grpahql server. So you can use this function
        to setup the graphql client

        :param graphql_url: url part used to contact the graphql server
        :return: any object which have the following method: post
        """
        pass

    @abc.abstractmethod
    def _graphql_query(self,
                       query: str,
                       graphql_url: str,
                       client: any,
                       files: List[FileToUpload],
                       operation_name: str = None,
                       input_data: Dict[str, any] = None,
                       variables: Dict[str, any] = None,
                       headers: Dict[str, any] = None,

                       ):
        """
        Actually perform the graphql query. Override this method if you need to customize the graphql test client.
        Override this function to customize how the client (setupped in _setup_graphql_client) behaves when sending
        data to the graphql server. By default this function assumes the test client is graphene-django.unit.testing.Client

        Copied from graphene-django.unit.testing

        :param query: GraphQL query to run
        :param operation_name: If the query is a mutation or named query, you must
            supply the op_name.  For annon queries ("{ ... }"),
            should be None (default).
        :param input_data: If provided, the $input variable in GraphQL will be set
            to this value. If both ``input_data`` and ``variables``,
            are provided, the ``input`` field in the ``variables``
            dict will be overwritten with this value.
        :param variables: If provided, the "variables" field in GraphQL will be
            set to this value.
        :param headers: If provided, the headers in POST request to GRAPHQL_URL
            will be set to this value.
        :param client: Test client
        :param graphql_url: URL to graphql endpoint.
        :returns: Response object from client
        """
        pass

    @abc.abstractmethod
    def _load_json_body_from_response(self, response: any) -> Dict[str, any]:
        """
        Fetch the graphql json response from the client. The default assume the usage of graphen-django.utils.testing.Client

        :param response: response from the client used to connect to the graphql server
        """
        pass

    @abc.abstractmethod
    def _prepare_url(self, query: str, graphql_url: str) -> str:
        """
        Function that is used to prepare the url passed by the developer before feeding it in the graphql client.
        This can be useful because sometimes you need to set a whole url, som other times only a url endpoint.

        :param query: query involved
        :param graphql_url: url to prepare
        :return: url prepared
        """
        pass

    @abc.abstractmethod
    def _fetch_response_status_code_from_response(self, response: any) -> int:
        """
        Fetch the HTTP status code from the grpahql response
        """
        pass

    def perform_graphql_query(self, graphql_query_info: Union[GraphQLRequestInfo, str]) -> GraphQLResponseInfo:
        """
        Generally perform a query to the graphql endpoint.

        If the file variable is not None, we expect the graphql to have as many variables as there are files.
        Each variable name **has to be** one specified by graphql_query_info.files.file_variable_name.

        :param graphql_query_info: either a full structure describing the request we want to make or a graphql query string (query nd mutation included)
        """
        if isinstance(graphql_query_info, str):
            graphql_query_info = GraphQLRequestInfo(
                graphql_query=graphql_query_info,
            )

        url = self.graphql_url()
        url = self._prepare_url(graphql_query_info.query, url)

        if self.client is None:
            self.client = self._setup_graphql_client(graphql_url=url)

        if graphql_query_info.files is None:
            files = []
        else:
            files = graphql_query_info.files

        response = self._graphql_query(
            query=graphql_query_info.query,
            operation_name=graphql_query_info.operation_name,
            input_data=graphql_query_info.input_data,
            variables=graphql_query_info.graphql_variables,
            headers=graphql_query_info.headers,
            graphql_url=url,
            client=self.client,
            files=files,
        )

        # load the reponse as a json
        content = self._load_json_body_from_response(response)
        status_code = self._fetch_response_status_code_from_response(response)
        return GraphQLResponseInfo(graphql_query_info, response, content, status_code)

    def perform_simple_upload_mutation(self, query: str, upload_filepath: str, upload_filepath_name: str = "test_file",
                                       content_type: str = "text/plain", upload_file_variable_name: str = "file",
                                       encoding: str = "utf-8"):
        """
        Contact an upload mutation and upload a single file
        :param query: graphql endpoint to contact
        :param upload_filepath: filepath of the file to upload
        :param upload_filepath_name: name of the file to upload. if missing, it is test_file
        :param content_type: type of the file to upload. If missing, it is text/plain
        :param upload_file_variable_name: name of the argument associated to the file
        :param encoding: encoding of the file to upload. Default to utf8
        :return: output of the graphql query
        """
        graphql_query_info = GraphQLRequestInfo(
            graphql_query=query,
            files=[
                FileToUpload(
                    filepath=upload_filepath,
                    name=upload_filepath_name,
                    file_variable_name=upload_file_variable_name,
                    encoding=encoding,
                    content_type=content_type,
                )
            ]
        )
        return self.perform_graphql_query(graphql_query_info)

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

    def assert_graphql_response_satisfy(self, graphql_response: GraphQLResponseInfo,
                                        constraint: GraphQLAssertionConstraint, check_success: bool = True):
        satisfied, error_message = constraint(graphql_response)
        if check_success:
            self.assert_graphql_response_noerrors(graphql_response)
        if not satisfied:
            raise AssertionError(f"""Error: {error_message}
                Query:{graphql_response.request.query}
                Variables:{graphql_response.request.graphql_variables}""")

    def assert_graphql_response_noerrors(self, graphql_response: GraphQLResponseInfo):
        """
        Ensure that the graphql response you got from the graphql test client is a successful one (at least on HTTP level)

        :param graphql_response: object genrated by perform_graphql_query
        :raise AssertionError: if the check fails
        """
        try:
            errors = list(map(lambda error: error["message"], graphql_response.content["errors"]))
        except Exception:
            errors = ["Could not analyze graphql error section. Please try to directly invoke the request"]

        errors = '\n'.join(errors)
        self.assertEqual(graphql_response.response_status_code, 200,
                         f"""The graphql query HTTP status is not 200! Errors were:\n{errors}""")
        # ensure errors are not present (or errors are presents but it is empty
        if "errors" in list(graphql_response.content.keys()):
            errors = graphql_response.content["errors"]
            if errors is None:
                pass
            elif len(graphql_response.content["errors"]) == 0:
                pass
            else:
                s = '\n'.join(map(str, graphql_response.content['errors']))
                raise AssertionError(f"Errors are present in the response: \n{s}")

    def assert_graphql_response_error(self, graphql_response: GraphQLResponseInfo, expected_error_substring: str):
        """
        Ensure that the error section of graphql has at least one error whose string contains the given substring

        :param graphql_response: reponse to inspect
        :param expected_error_substring: subsrting of the error to consider
        """

        def check(aresponse: GraphQLResponseInfo) -> Tuple[bool, str]:
            if "errors" not in aresponse.content:
                return False, "response was successful, but we expected to have errors"

            for error_data in aresponse.content["errors"]:
                if expected_error_substring in str(error_data["message"]):
                    return True, ""
            return False, f"no errors were found s.t. contains substring \"{expected_error_substring}\".\nErrors were: {aresponse.content['errors']}"

        self.assert_graphql_response_satisfy(graphql_response, constraint=check, check_success=False)

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

    def assert_json_path_of_type(self, graphql_response: GraphQLResponseInfo, path: str,
                                 allowed_type: Union[type, List[type]]):
        """

        :param graphql_response: object genrated by perform_graphql_query
        :param path: a JSON path in the graphql response
        :param allowed_type:either a single type or a list of types the value associated to the path may have
        :raise AssertionError: if the data is not valid
        :see: https://jmespath.org/
        """

        def criterion(aresponse: GraphQLResponseInfo) -> Tuple[bool, str]:
            nonlocal allowed_type
            if not isinstance(allowed_type, list):
                allowed_type = [allowed_type]
            actual = jmespath.search(path, aresponse.content)
            return type(
                actual) in allowed_type, f"in path {path}: actual was of type {type(actual)} but only {', '.join(map(lambda x: x.__name__, allowed_type))} are allowed!"

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

    def assert_json_path_greater_or_equal_to(self, graphql_response: GraphQLResponseInfo, path: str,
                                             expected_value: any):
        def criterion(aresponse: GraphQLResponseInfo) -> Tuple[bool, str]:
            actual = jmespath.search(path, aresponse.content)
            return actual >= expected_value, f"in path {path}: actual >= expected failed: {actual} < {expected_value}"

        self.assert_json_path_satisfies(graphql_response, criterion)

    def assert_json_path_less_than_or_equals_to(self, graphql_response: GraphQLResponseInfo, path: str,
                                                expected_value: any):
        def criterion(aresponse: GraphQLResponseInfo) -> Tuple[bool, str]:
            actual = jmespath.search(path, aresponse.content)
            return actual <= expected_value, f"in path {path}: actual <= expected failed: {actual} > {expected_value}"

        self.assert_json_path_satisfies(graphql_response, criterion)

    def assert_json_path_str_equals_to(self, graphql_response: GraphQLResponseInfo, path: str, expected_value: any):
        def criterion(aresponse: GraphQLResponseInfo) -> Tuple[bool, str]:
            actual = str(jmespath.search(path, aresponse.content))
            return actual == str(
                expected_value), f"in path {path}: str(actual) == str(expected) failed: {actual} != {expected_value}"

        self.assert_json_path_satisfies(graphql_response, criterion)

    def assert_json_path_str_not_equals_to(self, graphql_response: GraphQLResponseInfo, path: str, expected_value: any):
        def criterion(aresponse: GraphQLResponseInfo) -> Tuple[bool, str]:
            actual = str(jmespath.search(path, aresponse.content))
            return actual != str(
                expected_value), f"in path {path}: str(actual) != str(expected) failed: {actual} == {expected_value}"

        self.assert_json_path_satisfies(graphql_response, criterion)

    def assert_json_path_str_longer_than(self, graphql_response: GraphQLResponseInfo, path: str,
                                         minimum_length: int = None, maximum_length: int = None,
                                         min_included: bool = True, max_included: bool = False):
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
            return True, ""

        self.assert_json_path_satisfies(graphql_response, criterion)

    def assert_json_path_str_contains_substring(self, graphql_response: GraphQLResponseInfo, path: str,
                                                expected_substring: str):
        def criterion(aresponse: GraphQLResponseInfo) -> Tuple[bool, str]:
            actual = str(jmespath.search(path, aresponse.content))
            return str(
                expected_substring) in actual, f"in path {path}: expected in actual failed: {expected_substring} not in {actual}"

        self.assert_json_path_satisfies(graphql_response, criterion)

    def assert_json_path_str_does_not_contain_substring(self, graphql_response: GraphQLResponseInfo, path: str,
                                                        expected_substring: str):
        def criterion(aresponse: GraphQLResponseInfo) -> Tuple[bool, str]:
            actual = str(jmespath.search(path, aresponse.content))
            return str(
                expected_substring) not in actual, f"in path {path}: expected is indeed in actual, but we needed not to: {expected_substring} not in {actual}"

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

    def assert_json_path_obj_dynamic_method(self, graphql_response: GraphQLResponseInfo, path: str, method_name: str,
                                            args: List[any], kwargs: Dict[str, any], expected_result: any,
                                            comparison_function: Callable[[any, any], any] = None):
        """
        Use this assertion to test the output of a instance method of the return value generated by jmespath path.

        .. ::code-block::
            assert_json_path_obj_dynamic_method(response, "foo.bar", "__len__", [], {}, 5)

        In the previous method, we expect the item to be an object tha thas the instance method "__len__", with not further arguments.
        We expect the method to generate the value of 5

        :param graphql_response: the response to check
        :param path: path to check
        :param method_name: name of the instance method of the value geneated by the json path to consider
        :param args: args of the methd to invoke
        :param kwargs: kwargs of the method to invoke
        :param expected_result: the result we hope to have
        :param comparison_function: a function that is used to compare the result of the method name (first argument) with the expected result (second argument). If left missing, it is the "operator.eq" between the actual and the expected
        """

        def criterion(aresponse: GraphQLResponseInfo) -> Tuple[bool, str]:
            # actual may be a list, str, int
            actual = jmespath.search(path, aresponse.content)
            if actual is None:
                return False, f"in path {path}: expected object {expected_result}, but the path pointed to a None value"
            if not hasattr(actual, method_name):
                return False, f"in path {path}: The object pointed by the path is of type {type(actual)}, which does not have a method called {method_name}"
            actual_method = getattr(actual, method_name)
            actual_result = actual_method(*args, **kwargs)
            args_str = ', '.join(args)
            kwargs_str = ', '.join(map(lambda i: f"{i[0]}={i[1]}", kwargs.items()))

            nonlocal comparison_function
            if comparison_function is None:
                comparison_function = operator.eq
            return comparison_function(actual_result,
                                       expected_result), f"in path {path}: the <{type(actual)}>.{method_name}({args_str}, {kwargs_str}) yielded {actual_result}; however, we expected to be {expected_result}"

        self.assert_json_path_satisfies(graphql_response, criterion)

    def assert_json_path_to_be_of_length(self, graphql_response: GraphQLResponseInfo, path: str, expected_result: int):
        """
        Assert an array ot be of a determinated length length

        :param graphql_response: response top analyze
        :param path: path to consider
        :param expected_result: result of the length comparison
        """
        self.assert_json_path_obj_dynamic_method(
            graphql_response=graphql_response,
            path=path,
            method_name="__len__",
            args=[],
            kwargs={},
            expected_result=expected_result,
        )

    def assert_json_path_to_be_gt_length(self, graphql_response: GraphQLResponseInfo, path: str, expected_result: int):
        """
        Assert an array ot be of at least a (non included) determinated length length

        :param graphql_response: response top analyze
        :param path: path to consider
        :param expected_result: result of the length comparison
        """
        self.assert_json_path_obj_dynamic_method(
            graphql_response=graphql_response,
            path=path,
            method_name="__len__",
            args=[],
            kwargs={},
            expected_result=expected_result,
            comparison_function=operator.gt
        )

    def assert_json_path_to_be_geq_length(self, graphql_response: GraphQLResponseInfo, path: str, expected_result: int):
        """
        Assert an array of the actual result to be of at least an included determinated length length

        :param graphql_response: response top analyze
        :param path: path to consider
        :param expected_result: result of the length comparison
        """
        self.assert_json_path_obj_dynamic_method(
            graphql_response=graphql_response,
            path=path,
            method_name="__len__",
            args=[],
            kwargs={},
            expected_result=expected_result,
            comparison_function=operator.ge
        )

    def assert_json_path_to_be_lt_length(self, graphql_response: GraphQLResponseInfo, path: str, expected_result: int):
        """
        Assert an array ot be of at most a (non included) determinated length length

        :param graphql_response: response top analyze
        :param path: path to consider
        :param expected_result: result of the length comparison
        """
        self.assert_json_path_obj_dynamic_method(
            graphql_response=graphql_response,
            path=path,
            method_name="__len__",
            args=[],
            kwargs={},
            expected_result=expected_result,
            comparison_function=operator.lt
        )

    def assert_json_path_to_be_leq_length(self, graphql_response: GraphQLResponseInfo, path: str, expected_result: int):
        """
        Assert an array of the actual result to be of at most an included determinated length length

        :param graphql_response: response top analyze
        :param path: path to consider
        :param expected_result: result of the length comparison
        """
        self.assert_json_path_obj_dynamic_method(
            graphql_response=graphql_response,
            path=path,
            method_name="__len__",
            args=[],
            kwargs={},
            expected_result=expected_result,
            comparison_function=operator.le
        )

    def assert_json_path_to_be_ne_length(self, graphql_response: GraphQLResponseInfo, path: str, expected_result: int):
        """
        Assert an array of the actual result not to be of a determinated length length

        :param graphql_response: response top analyze
        :param path: path to consider
        :param expected_result: result of the length comparison
        """
        self.assert_json_path_obj_dynamic_method(
            graphql_response=graphql_response,
            path=path,
            method_name="__len__",
            args=[],
            kwargs={},
            expected_result=expected_result,
            comparison_function=operator.ne
        )

    def assert_json_path_to_be_nonzero_length(self, graphql_response: GraphQLResponseInfo, path: str):
        """
        Assert an array to have at least one element

        :param graphql_response: response top analyze
        :param path: path to consider
        """
        self.assert_json_path_obj_dynamic_method(
            graphql_response=graphql_response,
            path=path,
            method_name="__len__",
            args=[],
            kwargs={},
            expected_result=0,
            comparison_function=operator.gt
        )

    def assert_json_path_to_be_zero_length(self, graphql_response: GraphQLResponseInfo, path: str):
        """
        Assert an array to be empty

        :param graphql_response: response top analyze
        :param path: path to consider
        """
        self.assert_json_path_obj_dynamic_method(
            graphql_response=graphql_response,
            path=path,
            method_name="__len__",
            args=[],
            kwargs={},
            expected_result=0,
            comparison_function=operator.eq
        )

    def assert_json_path_to_be_in_range(self, graphql_response: GraphQLResponseInfo, path: str, lb, ub,
                                        lb_included: bool = True, ub_included: bool = False):
        """
        Assert an array of the actual result to be ioncluded in one of a range of type [a,b], [a,b[, ]a,b] or ]a,b[
        If we consider floats, we consider the number plus/minus the epsilon

        :param graphql_response: response top analyze
        :param path: path to consider
        :param lb: lowerbound fo the range
        :param ub: upperbound of the range
        :param lb_included: if true, the "lb" is included in the range (i.e., "[" bracket)
        :param ub_included: if true, the "ub" is included in the range (i.e., "]" bracket)
        """

        def compare_range(x, tpl) -> bool:
            (alb, aub, alb_included, aub_included) = tpl
            if isinstance(alb, float):
                y = sys.float_info.epsilon
            else:
                y = 1

            if not alb_included:
                alb = alb + y
            if not aub_included:
                aub = aub - y
            return alb <= x <= aub

        self.assert_json_path_obj_dynamic_method(
            graphql_response=graphql_response,
            path=path,
            method_name="__len__",
            args=[],
            kwargs={},
            expected_result=(lb, ub, lb_included, ub_included),
            comparison_function=compare_range
        )

    def assert_file_exists(self, f: str):
        """
        Assert the fact that some file exists
        :param f: file to check. Relative to MEDIA_ROOT
        :return:
        """
        p = os.path.abspath(os.path.relpath(f, start=os.path.abspath(settings.MEDIA_ROOT)))
        if not os.path.exists(p):
            raise AssertionError(f"file at path {p} does not exist!")

    def assert_file_with_search_regex_exists(self, regex: str, cwd: str = None):
        """
        List the files in the cwd directory consider.  if we are able to find a file whose basename
        follows the given regex, the assertion succeeds
        :param regex: regex we **search**
        :param cwd: directory where we need to look file
        :return:
        """
        if cwd is None:
            os.getcwd()
        cwd = os.path.abspath(cwd)
        for path in os.listdir(cwd):
            if os.path.isfile(os.path.join(cwd, path)):
                if re.search(regex, path) is not None:
                    return True
        else:
            raise AssertionError(f"no file under {cwd} has the search regex {regex}!")

    def assert_file_with_match_regex_exists(self, regex: str, cwd: str = None):
        """
        List the files in the cwd directory consider.  if we are able to find a file whose basename
        follows the given regex, the assertion succeeds
        :param regex: regex we **match**
        :param cwd: directory where we need to look file
        :return:
        """
        if cwd is None:
            os.getcwd()
        cwd = os.path.abspath(cwd)
        for path in os.listdir(cwd):
            if os.path.isfile(os.path.join(cwd, path)):
                if re.match(regex, path) is not None:
                    return True
        else:
            raise AssertionError(f"no file under {cwd} has the match regex {regex}!")

    def assert_file_with_search_regex_absent(self, regex: str, cwd: str = None):
        """
        List the files in the cwd directory consider.  if we are **not** able to find a file whose basename
        follows the given regex, the assertion succeeds
        :param regex: regex we **search**
        :param cwd: directory where we need to look file
        :return:
        """
        if cwd is None:
            os.getcwd()
        cwd = os.path.abspath(cwd)
        for path in os.listdir(cwd):
            if os.path.isfile(os.path.join(cwd, path)):
                if re.search(regex, path) is not None:
                    raise AssertionError(f"the file {path} under {cwd} has the search regex {regex}!")

    def assert_file_with_match_regex_absent(self, regex: str, cwd: str = None):
        """
        List the files in the cwd directory consider.  if we are able **not** to find a file whose basename
        follows the given regex, the assertion succeeds
        :param regex: regex we **match**
        :param cwd: directory where we need to look file
        :return:
        """
        if cwd is None:
            os.getcwd()
        cwd = os.path.abspath(cwd)
        for path in os.listdir(cwd):
            if os.path.isfile(os.path.join(cwd, path)):
                if re.match(regex, path) is not None:
                    raise AssertionError(f"the file {path} under {cwd} has the search regex {regex}!")

    def assert_string_contains(self, substring: str, actual: str, message: str = None):
        """
        Ensure that a string contains a substring
        :param substring: substring to check
        :param actual: string got
        :param message: emssage to show if the assertion fails
        """
        if substring not in actual:
            raise AssertionError(f"""'{substring}' is not in '{actual}': {message or ''}""")

    def assert_string_not_contains(self, substring: str, actual: str, message: str = None):
        """
        Ensure that a string does not contain a specified substring
        :param substring: substring to check
        :param actual: string got
        :param message: message to show if the assertion fails
        """
        if substring in actual:
            raise AssertionError(f"""'{substring}' is in '{actual}': {message or ''}""")


class GrapheneClientTestMixIn:
    """
    A mixin that support AbstractGraphQLTestMixin allowing you to u8se the standard graphene-django Client graphql test
    client
    """

    def _setup_graphql_client(self, graphql_url: str) -> any:
        from django.test.client import Client
        return Client()

    def _prepare_url(self, query: str, graphql_url: str) -> str:
        if not graphql_url.startswith("/"):
            graphql_url = "/" + graphql_url
        if not graphql_url.endswith("/"):
            graphql_url = graphql_url + "/"
        return graphql_url

    def _graphql_query(self,
                       query: str,
                       graphql_url: str,
                       client: any,
                       files: List[FileToUpload],
                       operation_name: str = None,
                       input_data: Dict[str, any] = None,
                       variables: Dict[str, any] = None,
                       headers: Dict[str, any] = None,
                       ):

        from django.core.files.uploadedfile import SimpleUploadedFile

        if len(files) > 0:
            files_dicts = []
            for file_to_upload in files:
                with open(os.path.abspath(file_to_upload.filepath), mode="rb") as f:
                    content = f.read()
                simple_uploaded_file = SimpleUploadedFile(name=file_to_upload.name, content=content,
                                                          content_type=file_to_upload.content_type)
                files_dicts.append(dict(file_to_upload=file_to_upload, simple_uploaded_file=simple_uploaded_file))

            response = file_graphql_query(
                query=query,
                op_name=operation_name,
                input_data=input_data,
                variables=variables,
                headers=headers,
                files={d["file_to_upload"].file_variable_name: d["simple_uploaded_file"] for d in files_dicts},
                graphql_url=graphql_url,
                client=client
            )
        else:
            response = graphql_query(
                query=query,
                operation_name=operation_name,
                input_data=input_data,
                variables=variables,
                headers=headers,
                client=client,
                graphql_url=graphql_url
            )

        return response

    def _load_json_body_from_response(self, response: any) -> Dict[str, any]:
        return json.loads(response.content)

    def _fetch_response_status_code_from_response(self, response: any) -> int:
        return response.status_code


class AsyncClientEnhancedSession(AsyncClientSession):

    async def execute(self, document: DocumentNode, *args, **kwargs) -> Dict:
        """
        Copied from AsyncClientSession class. We do not only return result.data, but the whole result paylaod
        """

        # Validate and execute on the transport
        result = await self._execute(document, *args, **kwargs)

        # Raise an error if an error is returned in the ExecutionResult object
        if result.errors:
            raise TransportQueryError(
                str(result.errors[0]), errors=result.errors, data=result.data
            )

        assert (
            result.data is not None
        ), "Transport returned an ExecutionResult without data or errors"

        return result


class GQLEnhancedClient(GQLClient):

    async def __aenter__(self):
        # code pasted from Client
        assert isinstance(
            self.transport, AsyncTransport
        ), "Only a transport of type AsyncTransport can be used asynchronously"

        await self.transport.connect()

        if not hasattr(self, "session"):
            self.session = AsyncClientEnhancedSession(client=self)

        # Get schema from transport if needed
        if self.fetch_schema_from_transport and not self.schema:
            await self.session.fetch_schema()

        return self.session


class RealGraphQLClientMixIn:
    """
    A mixin to support AbstractGraphQLTestMixIn that provides a real graphql client implementation (thus you will make
    actual http calls).

    If you are using this mixin, GRAPHQL_URl needs to be setup as the whole url to contact (with port and hostname)

    :see: https://docs.djangoproject.com/en/3.2/topics/testing/tools/#overview-and-a-quick-example
    """

    def _setup_graphql_client(self, graphql_url: str) -> any:
        return None

    def _prepare_url(self, query: str, graphql_url: str) -> str:
        if not graphql_url.endswith("/"):
            graphql_url = graphql_url + "/"
        return graphql_url

    def _graphql_query(self,
                       query: str,
                       graphql_url: str,
                       client: any,
                       operation_name: str = None,
                       input_data: Dict[str, any] = None,
                       variables: Dict[str, any] = None,
                       headers: Dict[str, any] = None,
                       files: List[FileToUpload] = None
                       ):
        from gql import gql
        from gql import Client as GQLClient
        from gql.transport.aiohttp import AIOHTTPTransport

        transport = AIOHTTPTransport(url=graphql_url, headers=headers)
        client = GQLEnhancedClient(
            transport=transport,
            fetch_schema_from_transport=True,
        )
        client.execute_timeout = self.graphql_client_timeout()

        files_opened = []
        try:
            upload_files = len(files) > 0
            if upload_files:
                # we need to add to the variable_values the files pointers as well
                for file_to_upload in files:
                    if file_to_upload.file_variable_name in variables:
                        raise ValueError(
                            f"variable name and file name are the same. Name involved: {file_to_upload.file_variable_name}")
                    fp = open(os.path.abspath(file_to_upload.filepath), mode="rb")
                    file_to_upload.append(fp)
                    variables[file_to_upload.file_variable_name] = fp

            gql_query = gql(query)
            LOG.info(f"Sending graphQL request...")
            LOG.info(f"url: {graphql_url}")
            LOG.info(f"data: {query}")
            result = client.execute(gql_query, variable_values=variables, upload_files=upload_files)
        finally:
            # close the files
            for fp in files_opened:
                fp.close()

        # format error
        result = result.formatted
        LOG.info(f"Response is {result}")
        return result

    def _load_json_body_from_response(self, response: any) -> Dict[str, any]:
        return response

    def _fetch_response_status_code_from_response(self, response: any) -> int:
        # TODO assume 200, since we have no way to fetch the correct http status code
        return 200


