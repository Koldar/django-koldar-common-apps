from typing import List


class ErrorCode(object):

    used_codes = set()

    """
    An object representing an error
    """
    def __init__(self, code: int, developer_string: str, required_keys: List[str]):
        if code in ErrorCode.used_codes:
            raise ValueError(f"Error code {code} already used. Try somethign that is not {ErrorCode.used_codes}!")
        ErrorCode.used_codes.add(code)

        self.code = code
        """
        Error code
        """
        self.developer_string = developer_string
        """
        String used by the developer. It should not be the string sent to the front end user, since this string is not i18n
        convertible
        """
        self.required_keys = required_keys
        """
        List of keys that are necessary to be sent to the network
        """