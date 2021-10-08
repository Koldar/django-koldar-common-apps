"""
Specifies some convenience function to interact to HTTP and HTTPS in a more general way.
It specifies convenience functions that solve commons problem, like sending and receiving jsons
"""

import json
from typing import Dict, Union, Tuple
import requests


import logging

LOG = logging.getLogger(__name__)

def send_json_and_return_json(url: str, http_method: str, json_body: Union[str, Dict[str, any]] = None, headers: Dict[str, str] = None, url_params: Dict[str, str] = None) -> Tuple[int, object]:
    """
    Create an HTTP request of type application/json and send the specified json to the url.
    Then, waits until we reach the corresponding response.

    This method is just a convenience method hiding requests package under the hood. Send and retrieving jsons is
    so common that I have decided to add such a function.

    :param http_method: http method to use. case insensitive. Either one of get, post, put, patch, delete, options, head
    :param json_body: data to send to the request. Can be a dictionary or a string. if it is a string, it is first
        converted into a dictionary via json.loads. If missing, we will send a request with no body content
    :param url_params: set of query parameters in the url. For example:

        .. code-block:: python

            payload = {'key1': 'value1', 'key2': 'value2'}
            r = requests.get('https://httpbin.org/get', params=payload)
            # yields https://httpbin.org/get?key2=value2&key1=value1
    :param headers: custom header to add in the HTTP request
    :return: a pair where the first element is the http response status code while the second is the generated json
    """

    if http_method.lower() not in ["get", "post", "put", "delete", "patch", "options", "head"]:
        raise ValueError(f"invalid HTTP method {http_method}!")
    if json_body is not None:
        if isinstance(json_body, str):
            json_body = json.loads(json_body)

    content = json.dumps(json_body)
    if headers is None:
        headers = {}

    headers["Content-Type"] = "application/json;charset=utf-8"
    headers["Content-Length"] = str(len(content))
    headers["User-Agent"] = "requests"

    LOG.info(f"Sending {http_method} {url} params={url_params} BODY={content}")
    response = requests.request(
        url=url,
        method=http_method,
        data=content,
        params=url_params,
        headers=headers
    )
    LOG.info(f"the endpoint {url} repied with {response.status_code}")
    return response.status_code, response.json()


