# import abc
# from typing import Iterable, Any, Dict, List
#
# from django_koldar_utils.django_toolbox.ApplicationProperty import ApplicationProperty
#
#
# class AbstractDjangoSection(abc.ABC):
#     """
#     An alternative way used to configure settings.py django_toolbox.
#     Use to sovle dependencies of INSTALLED_APPS, automatically add piece of
#     configurations in settings.py and configure authentication backends.
#     """
#
#     def __get_fullname(self):
#         klass = self.__class__
#         module = klass.__module__
#         if module == 'builtins':
#             return klass.__qualname__  # avoid outputs like 'builtins.str'
#         return module + '.' + klass.__qualname__
#
#     def get_app_name(self):
#         """
#
#         :return: app name
#         """
#         return self.__get_fullname().split('.')[-3]
#
#     @abc.abstractmethod
#     def depends_on_app(self) -> Iterable[str]:
#         """
#         list of all which this app depends on
#         :return:
#         """
#         pass
#
#     @abc.abstractmethod
#     def get_section_setup_dependencies(self) -> Iterable[str]:
#         """
#         Get a list of patterns representing the dependencies this section depends upon.
#         Each pattern represents a regex that is matched against the section get_app_name output.
#         The dependencies are used in the setup phase
#         """
#         pass
#
#     @abc.abstractmethod
#     def setup(self):
#         """
#         Application specific code invoked after the section dependency graph has been built.
#         Usually this code is the very first thing we execute
#         """
#
#         pass
#
#     @abc.abstractmethod
#     def is_exposing_http_endpoint(self) -> bool:
#         """
#         If true, we will configure urlpatterns. Otherwise we will implicitly set it as empty
#         """
#         pass
#
#     def get_route_options(self) -> Dict[str, Any]:
#         """
#         options to pass to the "path" method that register the routes in urls.py
#         :return:
#         """
#         return {}
#
#     @abc.abstractmethod
#     def update_middlewares(self, middlewares: List[str]) -> List[str]:
#         """
#         Alter the middlewares handled by the application. If you don't need to alter the middlewares,
#         you can safely just return the "middleware" in input
#         :param middlewares: list of middlesware to use
#         :return: list of middlewares that the django_toolbox project will use
#         """
#         pass
#
#     def _append_to_middlewares(self, name: str, middlewares: List[str]):
#         """
#         Append a new string at the end of the array middleswares. Used in :see: update_middlewares
#         :param name: string to add
#         :param middlewares:  array to alter
#         """
#         if name not in middlewares:
#             middlewares.append(name)
#
#     def _prepend_to_middlewares(self, name: str, middlewares: List[str]):
#         """
#         Append a new string at the beginning of the array middleswares. Used in :see: update_middlewares
#         :param name: string to add
#         :param middlewares:  array to alter
#         """
#         if name not in middlewares:
#             middlewares.insert(0, name)
#
#     @abc.abstractmethod
#     def get_route_prefix(self) -> str:
#         """
#         string that identfioies this section. All the routes of this section will be rpefixed with this string
#         :return:
#         """
#         pass
#
#     @abc.abstractmethod
#     def get_variables_to_add_in_project_settings(self, base_dir: str) -> Dict[str, Any]:
#         """
#         list of variables to add in the settings.py of django_toolbox project. The dictionary generated
#         will be put in place of settings.
#
#         :param base_dir: BASE_DIR
#         """
#         pass
#
#     @abc.abstractmethod
#     def get_authentication_backends(self) -> Iterable[str]:
#         """
#         string to add in the AUTHENTICATION_BACKENDS variable in settings.py
#         :return:
#         """
#         pass
#
#     @abc.abstractmethod
#     def get_configuration_dictionary_name(self) -> str:
#         """
#         The name fo the configuratrion dict that you can specify in settings for correctly configuring this application
#         :return:
#         """
#         pass
#
#     @abc.abstractmethod
#     def get_properties_declaration(self) -> Dict[str, ApplicationProperty]:
#         """
#         Generate all the properties that this application uses
#         :return:
#         """
#         pass
#
#     def _add_configuration_property(self, d: Dict[str, ApplicationProperty], name: str, property_type: type, help_text: str, has_default: bool, default_value: Any = None):
#         if name in d:
#             raise KeyError(f"Key {name} is already present in the dictionary")
#         d[name] = ApplicationProperty(
#             required=not has_default,
#             help_text=help_text,
#             name=name,
#             property_type=property_type,
#             default_value=default_value
#         )
#         return d
#
#     def _add_required_string(self, d: Dict[str, ApplicationProperty], name: str, help_text: str):
#         """
#         Add a configutation property that is required
#         :param d:
#         :param name:
#         :param help_text:
#         :return:
#         """
#         self._add_configuration_property(
#             d=d,
#             name=name,
#             property_type=str,
#             help_text=help_text,
#             has_default=False,
#             default_value=None
#         )
#
#     def _add_required_int(self, d: Dict[str, ApplicationProperty], name: str, help_text: str):
#         """
#         Add a configutation property that is required
#         :param d:
#         :param name:
#         :param help_text:
#         :return:
#         """
#         self._add_configuration_property(
#             d=d,
#             name=name,
#             property_type=int,
#             help_text=help_text,
#             has_default=False,
#             default_value=None
#         )
#
#
