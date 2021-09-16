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
)

s.perform_setup()
