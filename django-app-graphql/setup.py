from django_app_graphql import version
from django_koldar_utils.setuptools import library_setup


s = library_setup.LibraryScriptSetup(
    author="Massimo Bono",
    author_mail="massimobono1@gmail.com",
    description="Some stuff that i used when developing with django",
    keywords=["utils"],
    home_page="https://github.com/Koldar/django-koldar-common-apps",
    python_minimum_version="3.6",
    license_name="MIT",
    main_package="django_app_graphql",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    required_dependencies=[
        "aniso8601>=8.1.1",
        "arrow>=1.1.0",
        "Django>=3.2.4",
        "django-appconf>=1.0.4",
        "django-currentuser>=0.5.3",
        "django-koldar-utils>=2.8.1",
        "django-polymorphic>=3.0.0",
        "graphene>=3.0b7",
        "graphene-django>=3.0.0b7",
        "graphene-django-extras>=0.5.1",
        "graphql-core>=3.1.5",
        "jsonpath-ng>=1.5.2",
        "pydot>=1.4.2",
        "stringcase>=1.2.0",
        "graphene_file_upload>=1.3.0",
        "semantic-version>=2.8.5",
        "gql>=3.0.0a6",
    ],
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

# import os
# from typing import Iterable
#
# import setuptools
# from django_app_graphql import version
#
# PACKAGE_NAME = "django_app_graphql"
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
#         PACKAGE_NAME: [f"data/graphql/ariadne/*.graphql"],
#     },
#     python_requires=PACKAGE_PYTHON_COMPLIANCE,
#     # entry_points={"console_scripts": [f"{PACKAGE_EXE}={PACKAGE_MAIN_MODULE}:main"]},
# )