from appconf import AppConf


class DictSettingMergerAppConf(AppConf):
    """
    A derived class of AppConf that automatically merge the configurations from settings.py and the default ones.

    In the settings you should have:

    .. ::code-block:: python
        APPCONF_PREFIX = {
            "SETTINGS_1": 3
        }

    In the conf.py of the django_toolbox app, you need to code:

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
        # we have imported settings here in order to allow sphinx to buidl the documentation (otherwise it needs settings.py)
        from django.conf import settings

        prefix = getattr(self, "Meta").prefix
        if not hasattr(settings, prefix):
            return self.configured_data

        # the data the user has written in the settings.py
        data_in_settings = getattr(settings, prefix)
        # the data in the AppConf instance specyfing default values
        default_data = dict(self.configured_data)
        result = dict()

        # specify settings which do not have default values in the conf.py
        # (thus are requried) with the values specified in the settings.py
        for class_attribute_name, class_attribute_value in data_in_settings.items():
            result[class_attribute_name] = data_in_settings[class_attribute_name]

        # overwrite settings which have default values
        # with the values specified in the settings.py
        for class_attribute_name, class_attribute_value in default_data.items():
            if class_attribute_name not in result:
                result[class_attribute_name] = default_data[class_attribute_name]
        return result
