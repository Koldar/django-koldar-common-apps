from typing import List

from django_koldar_utils.setuptools.commons import AbstractScriptSetup


class LibraryScriptSetup(AbstractScriptSetup):
    """
    A package that is simply a library tha tcan be used in another projects
    """

    def __init__(self, author: str, author_mail: str, description: str, keywords: List[str], home_page: str,
                 python_minimum_version: str, license_name: str, main_package: str, classifiers: List[str] = None,
                 package_data: str = "package_data", required_dependencies: List[str] = None):
        super().__init__(author, author_mail, description, keywords, home_page, python_minimum_version, license_name,
                         main_package, classifiers, package_data, required_dependencies)

