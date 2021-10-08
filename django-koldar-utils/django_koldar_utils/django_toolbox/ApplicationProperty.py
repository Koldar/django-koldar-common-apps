from typing import Any


class ApplicationProperty(object):
    """
    A property in a django_toolbox application
    """

    def __init__(self, required: bool, help_text: str, name: str, property_type: type, default_value: Any):
        self.required = required
        self.help_text = help_text
        self.property_type = property_type
        self.name = name
        self.default_value = default_value

    def __str__(self):
        return self.name
