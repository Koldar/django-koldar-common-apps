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
        "django-appconf>=1.0.4",
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
        "pillow>=8.3.1",
        "hurry.filesize>=0.9",
        "datasize>=1.0.0",
    ]
)

s.perform_setup()