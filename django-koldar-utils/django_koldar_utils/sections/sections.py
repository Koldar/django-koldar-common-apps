import re
from collections import OrderedDict
from typing import Iterable, Any, List

import networkx as nx
from django.core.exceptions import ImproperlyConfigured
from django.urls import path, include

from django_koldar_utils.functions import modules
from django_koldar_utils.sections.AbstractDjangoSection import AbstractDjangoSection

import logging

LOG = logging.getLogger(__name__)
SECTION_DEPENDENCY_GRAPH: nx.DiGraph = nx.DiGraph(name="section dependency graph")


def setup_dependency_graph(sections: List[AbstractDjangoSection], filename: str = None) -> nx.DiGraph:
    """
    Setup the section dependency graph SECTION_DEPENDENCY_GRAPH
    """

    # add nodes
    for s in sections:
        LOG.info(f"Added section {s.get_app_name()}")
        SECTION_DEPENDENCY_GRAPH.add_node(s.get_app_name(), section=s)
    # add dependencies
    for source_section in sections:
        for dependency_pattern in source_section.get_section_setup_dependencies():
            for sink_section in sections:
                if sink_section == source_section:
                    continue
                m = re.search(dependency_pattern, sink_section.get_app_name())
                if m is not None:
                    LOG.info(f"{source_section.get_app_name()} depends on section {sink_section.get_app_name()}")
                    SECTION_DEPENDENCY_GRAPH.add_edge(source_section.get_app_name(), sink_section.get_app_name(), label="setup")

    if filename is not None:
        g = nx.drawing.nx_pydot.to_pydot(SECTION_DEPENDENCY_GRAPH)
        g.write_svg(filename + ".svg")

    setup()

    return SECTION_DEPENDENCY_GRAPH


def setup():
    for s in get_ordered_sections():
        s.setup()


def get_ordered_sections() -> Iterable["AbstractDjangoSection"]:
    """
    Generates a list of sections, where the one with no setup dependency are outputted first
    """
    for section_name in reversed(list(nx.topological_sort(SECTION_DEPENDENCY_GRAPH))):
        yield SECTION_DEPENDENCY_GRAPH.nodes[section_name]["section"]


def patch_middlewares(middleswares: List[str]) -> List[str]:
    result = list(middleswares)
    for s in get_ordered_sections():
        result = s.update_middlewares(result)
        # remove duplicates from list. see https://stackoverflow.com/a/7961390/1887602
        result = list(OrderedDict.fromkeys(result))
    return result


def patch_installed_apps(installed_apps):
    """
    Update the Django INSTALLED_APPS

    :param installed_apps: django INSTALLED_APPS
    :return: the updated value
    """

    result = set()
    for s in get_ordered_sections():
        for dep in s.depends_on_app():
            result.add(dep)
        result.add(s.get_app_name())

    # remove duplicate entries
    for r in installed_apps:
        if r in result:
            result.remove(r)

    for r in result:
        LOG.info(f"INSTALLED_APPS is extended with {r}")
    installed_apps.extend(result)
    return installed_apps


def generate_properties(section: "AbstractDjangoSection", settings, destination_settings: str):
    namespace = section.get_configuration_dictionary_name()
    properties = section.get_properties_declaration()
    required_keys = list(filter(lambda x: x.required, properties.values()))
    namespace_in_settings = getattr(settings, namespace, None)
    if namespace_in_settings is None and len(required_keys) > 0:
        raise ImproperlyConfigured(f"application {section.get_app_name()} requires to have set {', '.join(*required_keys)}, but you have not set event the app configuraton dictionary {namespace}!")
    for key, prop in section.get_properties_declaration().items():
        if prop.required and not hasattr(namespace_in_settings, key):
            raise ImproperlyConfigured(f"application {section.get_app_name()} requires to have set {key}, but you did not have set it in {namespace}!")
        property_in_settings = getattr(namespace_in_settings, key)
        if prop.property_type != type(property_in_settings):
            raise ImproperlyConfigured(
                f"application {section.get_app_name()} requires to have ther variable {key} set to type {prop.property_type}, but you not have set as a {type(property_in_settings)}!")
        # ok, set it in the settings
        modules.add_variable_in_module(destination_settings, key, property_in_settings)


def patch_urlpatterns(urlpatterns) -> Iterable[Any]:
    result = []

    for s in get_ordered_sections():
        if not s.is_exposing_http_endpoint():
            continue
        prefix = s.get_route_prefix()
        if prefix[-1] != "/":
            prefix = prefix + "/"
        p = path(prefix, include(f"{s.get_app_name()}.urls", s.get_route_options()))
        LOG.info(f"Extending urlpattern with {p}")
        result.append(p)

    urlpatterns.extend(result)
    return urlpatterns


def patch_authentication_backends(authentication_backends) -> Iterable[str]:
    result = set()
    for s in get_ordered_sections():
        for d in s.get_authentication_backends():
            result.add(d)
    authentication_backends.extend(result)
    return authentication_backends


def add_new_configurations(settings: str):
    """
    Update the setting file with the expected properties required by the sections

    :param settings: name of the settings for configuring your django project. Ususally it is the value of __name__
        variable
    """
    for s in get_ordered_sections():
        d = s.get_variables_to_add_in_project_settings()
        for var_name, var_value in d.items():
            modules.add_variable_in_module(settings, var_name, var_value)
