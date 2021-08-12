from appconf import AppConf
from django.conf import settings


class DictSettingMergerAppConf(AppConf):
    """
    A derived class of AppConf that automatically merge the configurations from settings.py and the default ones.

    In the settings you should have:

    .. ::code-block:: python
        APPCONF_PREFIX = {
            "SETTINGS_1": 3
        }

    In the conf.py of the django app, you need to code:

    .. ::code-block:: python
        class DjangoAppGraphQLAppConf(DictSettingMergerAppConfMixIn):
            class Meta:
                prefix = "APPCONF_PREFIX"

            def configure(self):
                return self.merge_configurations()

            SETTINGS_1: int = 0

    After that settings will be set to 3, rather than 0.

    Note that this class merges only if in the settings.py there is a dictionary with the same name of the prefix!
    """

    def merge_configurations(self):
        prefix = getattr(self, "Meta").prefix
        if not hasattr(settings, prefix):
            return self.configured_data
        data_in_settings = getattr(settings, prefix)
        for class_attribute_name, class_attribute_value in self.configured_data.items():
            if class_attribute_name in data_in_settings:
                self.configured_data[class_attribute_name] = data_in_settings[class_attribute_name]
        return self.configured_data
