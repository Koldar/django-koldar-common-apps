import os
from typing import Iterable

import setuptools
from django_koldar_utils import version
from django_koldar_utils.setuptools import library_setup


s = library_setup.LibraryScriptSetup(
    author="Massimo Bono",
    author_mail="massimobono1@gmail.com",
    description="Some stuff that i used when developing with django",
    keywords=["utils"],
    home_page="https://github.com/Koldar/django-koldar-common-apps",
    python_minimum_version="3.6",
    license_name="MIT",
    main_package="django_koldar_utils",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    required_dependencies=[
        "arrow>=1.1.0",
        "Django>=3.2.3",
        "django-currentuser>=0.5.3",
        "django-filter>=2.4.0",
        "django-graphql-jwt>=0.3.2",
        "django-polymorphic>=3.0.0",
        "graphene>=3.0b7",
        "graphene-django>=3.0.0b7",
        "graphene-django-extras>=0.5.1",
        "graphql-core>=3.1.5",
        "networkx>=2.5.1",
        "pydot>=1.4.2",
        "PyJWT>=2.1.0",
        "requests>=2.25.1",
        "stringcase>=1.2.0",
        "urllib3>=1.26.5",
        "jmespath>=0.10.0",
    ]
)

s.perform_setup()


#
# PACKAGE_NAME = "django-koldar-utils"
# PACKAGE_VERSION = version.VERSION
# PACKAGE_DESCRIPTION = "Some stuff that i used when developing with django"
# PACKAGE_URL = "https://github.com/Koldar/django-koldar-common-apps"
# PACKAGE_PYTHON_COMPLIANCE = ">=3.6"
# #PACKAGE_EXE = "pmakeup"
# #PACKAGE_MAIN_MODULE = "pmakeup.main"
# PACKAGE_CLASSIFIERS = [
#     "Programming Language :: Python :: 3",
#     "License :: OSI Approved :: MIT License",
#     "Operating System :: OS Independent",
# ]
# AUTHOR_NAME = "Massimo Bono"
# AUTHOR_EMAIL = "massimobono1@gmail.com"
#
# #########################################################
# # INTERNALS
# #########################################################
#
# with open("README.md", "r", encoding="utf-8") as fh:
#     long_description = fh.read()
#
#
# def get_dependencies(domain: str = None) -> Iterable[str]:
#     if domain is None:
#         filename = "requirements.txt"
#     else:
#         filename = f"requirements-{domain}.txt"
#     if os.path.exists(filename):
#         with open(filename, "r", encoding="utf-8") as fh:
#             for dep in fh.readlines():
#                 dep_name = dep.split("==")[0]
#                 dep_version = dep.split("==")[1].strip()
#                 yield dep_name + ">=" + dep_version
#
#
# setuptools.setup(
#     name=PACKAGE_NAME,  # Replace with your own username
#     version=PACKAGE_VERSION,
#     author=AUTHOR_NAME,
#     author_email=AUTHOR_EMAIL,
#     description=PACKAGE_DESCRIPTION,
#     long_description=long_description,
#     long_description_content_type="text/markdown",
#     license_files="LICEN[SC]E*",
#     url=PACKAGE_URL,
#     packages=setuptools.find_packages(),
#     classifiers=PACKAGE_CLASSIFIERS,
#     requires=[
#         "setuptools",
#         "wheel"
#     ],
#     install_requires=list(get_dependencies()),
#     extras_require={
#         "test": list(get_dependencies("test")),
#         "doc": list(get_dependencies("doc")),
#     },
#     include_package_data=True,
#     package_data={
#         "": ["package_data/*.*"],
#     },
#     python_requires=PACKAGE_PYTHON_COMPLIANCE,
#     # entry_points={"console_scripts": [f"{PACKAGE_EXE}={PACKAGE_MAIN_MODULE}:main"]},
# )