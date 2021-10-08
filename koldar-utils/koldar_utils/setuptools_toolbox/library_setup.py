from typing import List

from koldar_utils.setuptools_toolbox.commons import AbstractScriptSetup


class LibraryScriptSetup(AbstractScriptSetup):
    """
    A package that is simply a library tha tcan be used in another projects
    """

    def __init__(self, author: str, author_mail: str, description: str, keywords: List[str], home_page: str,
                 python_minimum_version: str, license_name: str, main_package: str, classifiers: List[str] = None,
                 package_data: str = "package_data", required_dependencies: List[str] = None, scripts: List[str] = None,
                 test_dependencies: List[str] = None, doc_dependencies: List[str] = None):
        super().__init__(
            author=author,
            author_mail=author_mail,
            description=description,
            keywords=keywords,
            home_page=home_page,
            python_minimum_version=python_minimum_version,
            license_name=license_name,
            main_package=main_package,
            classifiers=classifiers,
            package_data=package_data,
            required_dependencies=required_dependencies,
            scripts=scripts,
            test_dependencies=test_dependencies,
            doc_dependencies=doc_dependencies,
        )

