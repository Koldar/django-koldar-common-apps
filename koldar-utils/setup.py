import os
from typing import Iterable

import setuptools
from koldar_utils import version
from koldar_utils.setuptools_toolbox import library_setup


s = library_setup.LibraryScriptSetup(
    author="Massimo Bono",
    author_mail="massimobono1@gmail.com",
    description="Some stuff that i used when developing with python. You can use this library pretty much anywhere",
    keywords=["utils"],
    home_page="https://github.com/Koldar/django-koldar-common-apps",
    python_minimum_version="3.6",
    license_name="MIT",
    main_package="koldar_utils",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)

if __name__ == "__main__":
    # introducted to handle the scenario: if we import thsi script only in order to fetch installation fields but not
    # for running the scripts (e.g., sphinx)
    s.perform_setup()
