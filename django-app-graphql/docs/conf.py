# # Configuration file for the Sphinx documentation builder.
# #
# # This file only contains a selection of the most common options. For a full
# # list see the documentation:
# # https://www.sphinx-doc.org/en/master/usage/configuration.html
#
# # -- Path setup --------------------------------------------------------------
#
# # If extensions (or modules to document with autodoc) are in another directory,
# # add these directories to sys.path here. If the directory is relative to the
# # documentation root, use os.path.abspath to make it absolute, like shown here.
# #
#

import os
import sys

sys.path.insert(0, os.path.abspath(os.pardir))

from django_koldar_utils.sphinx_toolbox.sphinx_helper import DjangoLibrarySphinxConfigurator

sphinx_configurator = DjangoLibrarySphinxConfigurator()
d = sphinx_configurator.configure(__name__)

locals_vars = locals()
for k, v in d.items():
    locals_vars[k] = v
