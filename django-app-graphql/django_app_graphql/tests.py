# TODO remove
# import json
# from typing import Any, Dict, Union, Tuple, Optional, Set, Callable, List
#
#
# from jsonpath_ng.ext import parse as parse_ext
# # os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings.SETTING_DIR)
# # import django
# # django.setup()
#
#
# from graphene_django.utils.testing import GraphQLTestCase
# from requests import Response
#
#
# class AbstractGraphQLTest(GraphQLTestCase):
#     """
#     An abstract class that can be used to perform tests on a graphql server.
#     To perform tests, just do the following:
#
#     .. code-block:: python
#
#         from django_app_graphql import tests
#         class MyGraphQLTests(tests.AbstractGraphQLTest):
#
#             def test_foobar_query():
#                 # your test
#
#     Generally speaking there are 3 ways of performing query: linear, chaining or standard
#
#     Linear testing is when you in one command perform a grpahql query and then check the satisfaction of an assertion:
#
#     .. code-block :: python
#
#         self.assert_query_data_equal("foobar(5) { id }") # perform a grpahql query and check the result
#
#     Chaining testing is when you first perform the query and then check the satisfaction of an assertion:
#
#     .. code-block :: python
#
#         result, response = self.do_query("foobar(5) { id }") # perform query
#         self.assert_query_data_equal(result) # check the result
#
#     Linear is quick, but chaining tsting allows you to check multiple assertions in one batch.
#
#     Finally, you can also use the stnadard function provided by the GraphQLTestCase itself, namely:
#
#     .. code-block :: python
#
#         body, response = self.do_query("foobar(5) { id }")
#         self.assertResdponseNoErrors(response)
#
#     """
#
#     @classmethod
#     def setUpClass(cls) -> None:
#         super(AbstractGraphQLTest, cls).setUpClass()
#
#     @classmethod
#     def tearDownClass(cls) -> None:
#         super(AbstractGraphQLTest, cls).tearDownClass()
#
#     def setUp(self) -> None:
#         pass
#
#     def ask_to_graphql(self, query: Union[str, Dict[str, any]], arguments: Dict[str, any] = None) -> Tuple[
#         Dict[str, any], Optional[Response]]:
#         if isinstance(query, Dict):
#             return query, None
#         elif isinstance(query, str):
#             pass
#         else:
#             raise TypeError(f"query should either be a dictionary or a string!")
#
#         if arguments is None:
#             arguments = {}
#         http_response = self.query(query, input_data=arguments)
#         if http_response.status_code != 200:
#             raise ValueError(
#                 f"graphQL response was encapsulated in a http response whose status code is {http_response.status_code}")
#         body = bytes.decode(http_response.content, http_response.charset)
#         body = json.loads(body)
#         assert 'data' in body, "GraphQL output should return 'data', but this call did not."
#         assert 'errors' not in body, f"Got graphQL errors: {body}"
#         assert body['data'] is not None, f"data payload is None. Output={body}"
#         return body['data'], http_response
#
#     def assert_data_equal(self, query: Union[str, Dict[str, any]], expected, context=None):
#         """
#         Check if the whole returned value of a graphql query/mutation is exactly as the one provided by the user
#
#         :param query: either a strijng, repersenting the query that we need to perform or a a dictionary,
#             representing the (assumed) output of do_query/do_mutation.
#         :param expected: expected data value
#         :param context: variables
#         :return:
#         """
#         output, response = self.ask_to_graphql(query, context)
#         assert output == expected, f"expected={expected} actual={output}"
#
#     def assert_data_contains_key(self, query: Union[str, Dict[str, any]], key: str, arguments: Dict[str, any] = None):
#         output, response = self.ask_to_graphql(query, arguments)
#         assert key in output, f"key {key} is not present in the graphql output (keys are {list(output.keys())})"
#
#     def assert_data_key_value(self, query: Union[str, Dict[str, any]], key: str, value: Any,
#                               arguments: Dict[str, any] = None):
#         output, response = self.ask_to_graphql(query, arguments)
#         assert key in output, f"""key "{key}" is not present in output (keys are {list(output.keys())})"""
#         assert output[key] is not None, f"value associated to {key} is None"
#         assert output[key] == value, f"value associated to {key}: expected={value} actual={output[key]}"
#
#     def assert_jsonpath_satisfy_condition(self, query: Union[str, Dict[str, any]], json_path: str,
#                                           constraint: Callable[[List[any]], Tuple[bool, str]],
#                                           arguments: Dict[str, any] = None):
#         """
#         Check if the json object returned by the query (the one stored "data") satisfies a condition
#
#         :param query: output of the grapql query/mutation OR query/mutation that needs to be performed
#         :param json_path: json path involved
#         :param constraint: a callable representing the condition. As input it has the match found in the actual response
#             while in output has a pair where the first argument is the condition satisfaction. The second return value
#             is an human readable error description describing why the constraint has failed
#         :param arguments: if query is the query/mutation that needs to be performed, the variables of such a query
#         :return:
#         :see: https://pypi.org/project/jsonpath-ng/
#         """
#         output, response = self.ask_to_graphql(query, arguments)
#         jsonpath_expr = parse_ext(json_path, debug=False)
#         matches = [m.value for m in jsonpath_expr.find(output)]
#         ok, error = constraint(matches)
#         assert ok, f"json path {jsonpath_expr} failed the constraint {constraint.__name__}\nerror: {error}\nmatches: {matches}\njson: {output}"
#
#     def assert_jsonpath_contains(self, query: Union[str, Dict[str, any]], json_path: str,
#                                  arguments: Dict[str, any] = None):
#         """
#         Check if a json path exists in the output (the one stored in "data")
#
#         :param query: output of the grapql query/mutation OR query/mutation that needs to be performed
#         :param json_path: json path involved
#         :param arguments: if query is the query/mutation that needs to be performed, the variables of such a query
#         :return:
#         :see: https://pypi.org/project/jsonpath-ng/
#         """
#
#         def constraint(matches: List[any]) -> Tuple[bool, str]:
#             return len(matches) > 0, f"no matches found"
#
#         return self.assert_jsonpath_satisfy_condition(query, json_path, constraint, arguments)
#
#     def assert_jsonpath_count_is(self, query: Union[str, Dict[str, any]], json_path: str, expected: int,
#                                  arguments: Dict[str, any] = None):
#         """
#         Check if a json path occurs n times in the output (the one stored in "data")
#
#         :param query: output of the grapql query/mutation OR query/mutation that needs to be performed
#         :param json_path: json path involved
#         :param expected: expecte dnumber of matches in the json output
#         :param arguments: if query is the query/mutation that needs to be performed, the variables of such a query
#         :return:
#         :see: https://pypi.org/project/jsonpath-ng/
#         """
#
#         def constraint(matches: List[any]) -> Tuple[bool, str]:
#             return len(matches) == expected, f"expected {expected} occurrences, but found {len(matches)}!"
#
#         return self.assert_jsonpath_satisfy_condition(query, json_path, constraint, arguments)
#
#     def assert_jsonpath_equal_to(self, query: Union[str, Dict[str, any]], json_path: str, expected_matches: Set[any],
#                                  arguments: Dict[str, any] = None):
#         """
#         Check if the values pointed by a json path has exact mathces
#
#         :param query: output of the grapql query/mutation OR query/mutation that needs to be performed
#         :param json_path: json path involved
#         :param expected_matches: expected matches in the json output
#         :param arguments: if query is the query/mutation that needs to be performed, the variables of such a query
#         :return:
#         :see: https://pypi.org/project/jsonpath-ng/
#         """
#         def constraint(matches: List[any]) -> Tuple[bool, str]:
#             actual_matches = set(matches)
#             if len(actual_matches) != len(expected_matches):
#                 return False, f"number of expcted matches {expected_matches} != actual matches {actual_matches}"
#             for exp in expected_matches:
#                 if exp not in actual_matches:
#                     return False, f"expected match {exp} not present in actual match"
#             return True, ""
#
#         return self.assert_jsonpath_satisfy_condition(query, json_path, constraint, arguments)
#
#     def assert_jsonpath_has_field_value_st(self, query: Union[str, Dict[str, any]], json_path: str,
#                                            constraint: Callable[[any], Tuple[bool, str]],
#                                            arguments: Dict[str, any] = None):
#         """
#         Check if the graphql response has exactly one field whose value matches the specified condition
#
#         :param query: graphql json output OR a query to perform
#         :param json_path: json path to consider
#         :param constraint: a callable representing the condition. As input it has the match found in the actual response
#             while in output has a pair where the first argument is the condition satisfaction. The second return value
#             is an human readable error description describing why the constraint has failed
#         ::param arguments: if a graphql query/mutation needs to be performed, the query/mutation argument
#         :see: https://pypi.org/project/jsonpath-ng/
#         """
#         output, response = self.ask_to_graphql(query, arguments)
#         jsonpath_expr = parse_ext(json_path, debug=False)
#         actual_matches = list(map(lambda x: x.value, jsonpath_expr.find(output)))
#         assert len(actual_matches) > 0, f"{json_path} has no matches in json {output}"
#         assert len(actual_matches) < 2, f"{json_path} has muyltiple matches in {output}, specifically {actual_matches}"
#         m = actual_matches[0]
#         result, error = constraint(m)
#         assert result, f"Value {m} does not satisfy the constraint {error}"
#
#     def assert_jsonpath_has_field_value_equal_to(self, query: Union[str, Dict[str, any]], json_path: str,
#                                                  expected: any, arguments: Dict[str, any] = None):
#         """
#         Check if the graphql response has exactly one field whose value has a particular value.
#         Checking is performed by "==" operator
#
#         :param query: graphql json output OR a query to perform
#         :param json_path: json path to consider
#         :param expected: value the field needs to have
#         ::param arguments: if a graphql query/mutation needs to be performed, the query/mutation argument
#         :see: https://pypi.org/project/jsonpath-ng/
#         """
#
#         def constraint(actual: any) -> Tuple[bool, str]:
#             return actual == expected, f"expected == actual: {expected} == {actual}"
#
#         self.assert_jsonpath_has_field_value_st(query, json_path, constraint, arguments)
#
#     def assert_jsonpath_has_field_value_of_type(self, query: Union[str, Dict[str, any]], json_path: str,
#                                                 expected_types: Union[type, List[type]],
#                                                 arguments: Dict[str, any] = None):
#         """
#         Check if the graphql response has exactly one field whose value has a particular type
#
#         :param query: graphql json output OR a query to perform
#         :param json_path: json path to consider
#         :param expected_types: type we expect the vlaue associated to the json path match has.
#             You can input multiple values, in this case
#             the assertion is correct if the value type is among the one specified in the list
#         ::param arguments: if a graphql query/mutation needs to be performed, the query/mutation argument
#         :see: https://pypi.org/project/jsonpath-ng/
#         """
#         if isinstance(expected_types, type):
#             expected_types = [expected_types]
#
#         def constraint(actual: any) -> Tuple[bool, str]:
#             return type(
#                 actual) in expected_types, f"expected type of {actual} (type {type(actual)}) would be one of: {expected_types}"
#
#         self.assert_jsonpath_has_field_value_st(query, json_path, constraint, arguments)
#
# # Create your tests here.
