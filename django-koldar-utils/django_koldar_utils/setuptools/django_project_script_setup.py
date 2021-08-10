from typing import List, Dict


from django_koldar_utils.setuptools.commons import  AbstractScriptSetup


class DjangoProjectScriptSetup(AbstractScriptSetup):
    """
    A package that provides an ENTIRE django project.

    When installing, you can just call "console_script_name" program you have chosen
    """

    def __init__(self, author: str, author_mail: str, description: str, keywords: List[str], home_page: str,
                 python_minimum_version: str, license_name: str, main_package: str, classifiers: List[str] = None,
                 package_data: str = "package_data", required_dependencies: List[str] = None, scripts: List[str] = None):
        super().__init__(author, author_mail, description, keywords, home_page, python_minimum_version, license_name,
                         main_package, classifiers, package_data, required_dependencies, scripts)

    def get_scripts(self) -> List[str]:
        result = list(self.scripts) or []
        result.append('manage.py')
        return result