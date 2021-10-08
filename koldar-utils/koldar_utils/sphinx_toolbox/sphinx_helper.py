import abc
from typing import Dict, Iterable, Optional, Union, Tuple

import arrow
import inspect
import os
import sys
import logging

from koldar_utils.functions import modules
from koldar_utils.models.AttrDict import AttrDict

LOG = logging.getLogger(__name__)


class AbstractSphinxConfigurator(abc.ABC):
    """
    Configure sphinx automatically. The configure method has been heavily inspired by a base start
    up project. We assume that the CWD is the docs directory, which a sibling of the directory containing the
    python package you have just developed. Another sibling of the "docs" directory is "setup.py", setuptools
    installer.
    """

    def __init__(self):
        self.project: str
        self.author: str
        self.version: str
        self.project_package_name: str
        self.copyright: str
        self.project_data: Dict[str, any] = dict()
        self.sphinx_script: AttrDict = AttrDict()

    @abc.abstractmethod
    def _pre_configure(self):
        """
        Steps to perform before starting configuring sphinx
        """
        pass

    def should_add_source_directory(self) -> bool:
        return False

    def should_add_source_parent_directory(self) -> bool:
        return False

    @abc.abstractmethod
    def fetch_project_information(self) -> Dict[str, any]:
        """
        fetch all project important information. You can put as many information as you want here,
        but the following are required:
         - author: name of the author
         - project: name of the project
         - version: version of the project
         - project_package_name: name of the package in the parent directory of "docs" specifying the python
            pacakge project
         :return: dictioanry of values. They will be available as self.project_data after this method
        """
        pass

    @abc.abstractmethod
    def do_after_reading_project_data(self):
        """
        Set of steps to perform after we heav the project information.
        Useful if you want to alter them in any way. The configurations are vavailable as "self.project_data"
        """
        pass

    def get_sphinx_extensions(self) -> Iterable[str]:
        """
        By default we yield nothing
        :return: An iterable specifying all the sphinx extensions that you want to use when building your documentation
        """
        yield from []

    @abc.abstractmethod
    def configure_sphinx_extension(self, extension_name: str) -> bool:
        """
        Configure a particular extension inside the output of get_sphinx_extensions.
        This operator has side effects! If you cannot configure a given extension, return false

        :param extension_name: name of the extension to configure
        :return: true if we could configure the extension, false otherwise
        """
        pass

    def configure_html_output(self):
        """
        Configure the HTML output of sphinx. By default we will use the read the docs theme
        """
        # The theme to use for HTML and HTML Help pages.  See the documentation for
        # a list of builtin themes.
        #
        self.sphinx_script.html_theme = 'sphinx_rtd_theme'

        # Add any paths that contain custom static files (such as style sheets) here,
        # relative to this directory. They are copied after the builtin static files,
        # so a file named "default.css" will overwrite the builtin "default.css".
        self.sphinx_script.html_static_path = ['_static']

    def configure_pdf_output(self):
        """
        Configure the HTML output of sphinx. By default we will use the read the docs theme
        """
        pass

    @abc.abstractmethod
    def configure_deploy(self):
        """
        Set of configuration in sphinx that can be used to deploy to a 3rd party documentation hosting
        (e.g., readthedocs)
        """
        pass

    def get_variables_to_export_to_sphinx_rst(self) -> Iterable[Union[str, Tuple[str, any]]]:
        """
        Set of variables you want to expose to RSt sphinx system. Then, in your system, you will be able to
        write "|VARIABLE_NAME| to use said variable. By default we will return all the variables in self.project_data
        """

    def get_variables_to_export(self) -> Dict[str, any]:
        """
        Set a dictionary of variables that you want to export to the RST system.
        Then, in your system, you will be able to
        write "|VARIABLE_NAME| to use said variable. By default we will return all the variables in self.project_data

        :return: dictionary of variables to set. By default, it is project_data
        """
        return self.project_data

    def configure_others(self):
        """
        Override thsi function to add any other information it would not fit inside the other overrideable methods
        """
        pass

    def configure(self, module_name: str) -> Dict[str, any]:
        """
        Copied from a standard sphinx configuration options.

        :param module_name: needs to be used in the conf.py of sphinx. It should be "__name__"
        """
        # Configuration file for the Sphinx documentation builder.
        #
        # This file only contains a selection of the most common options. For a full
        # list see the documentation:
        # https://www.sphinx-doc.org/en/master/usage/configuration.html

        # -- Path setup --------------------------------------------------------------

        # If extensions (or modules to document with autodoc) are in another directory,
        # add these directories to sys.path here. If the directory is relative to the
        # documentation root, use os.path.abspath to make it absolute, like shown here.
        #

        # the script is executed in the "docs" directory of sphinx.

        # create the variable repersenting the variables to set in the sphinx script
        self.sphinx_script: AttrDict = AttrDict()

        if self.should_add_source_directory():
            # docs directory
            sys.path.insert(0, os.path.abspath('.'))

        if self.should_add_source_parent_directory():
            # root dir dirctory (useful for finding setup.py)
            sys.path.insert(0, os.path.abspath(os.path.join('.', os.pardir)))

        # -- Project information -----------------------------------------------------

        self.project_data = self.fetch_project_information()

        if "project" in self.project_data:
            self.sphinx_script.project = str(self.project_data["project"])
        else:
            raise ValueError(f"We need fetch_project_information to yield project!")

        if "author" in self.project_data:
            self.sphinx_script.author = str(self.project_data["author"])
        else:
            raise ValueError(f"We need fetch_project_information to yield author!")

        if "version" in self.project_data:
            self.sphinx_script.version = str(self.project_data["version"])
        else:
            raise ValueError(f"We need fetch_project_information to yield version!")

        if "copyright" in self.project_data:
            self.sphinx_script.copyright = str(self.project_data["copyright"])
        else:
            self.sphinx_script.copyright = f"{arrow.utcnow().year}, {self.sphinx_script.author}"

        if "project_package_name" in self.project_data:
            self.sphinx_script.project_package_name = str(self.project_data["project_package_name"])
        else:
            raise ValueError(f"We need fetch_project_information to yield project_package_name")

        self.do_after_reading_project_data()

        # -- General configuration ---------------------------------------------------

        # Add any Sphinx extension module names here, as strings. They can be
        # extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
        # ones.
        self.sphinx_script.extensions = list(self.get_sphinx_extensions())

        # Add any paths that contain templates here, relative to this directory.
        self.sphinx_script.templates_path = ['_templates']

        # List of patterns, relative to docs directory, that match files and
        # directories to ignore when looking for docs files.
        # This pattern also affects html_static_path and html_extra_path.
        self.sphinx_script.exclude_patterns = []

        for _, extension_name in enumerate(self.sphinx_script.extensions):
            ok = self.configure_sphinx_extension(extension_name)
            if not ok:
                raise ValueError(f"Could not configure correctly {extension_name}!")

        # -- Options for HTML output -------------------------------------------------

        self.configure_html_output()

        # -- Options for PDF output -------------------------------------------------

        self.configure_pdf_output()

        # -- READ THE DOCS ----------------------------------------------------------

        self.configure_deploy()

        # -- LIST OF VARIABLES THAT WILL BE AVAILABLE IN THE DOCUMENTATION -------------------------------------------------

        tmp = self.get_variables_to_export()
        self.sphinx_script.rst_epilog = '\n'.join(map(lambda x: f".. |{x}| replace:: {tmp[x]}", tmp))

        # -- OTHER

        self.configure_others()

        return dict(self.sphinx_script)

        # print(f"module name is {module_name}")
        #
        # # ok, now copy all the things in self.sphinx_script in the conf.py module
        # print(f"Adding variables to conf.py...")
        # for k, v in self.sphinx_script.items():
        #     print(f"Adding to conf.py {k} = {v}")
        #     modules.add_variable_in_module(module_name, k, v)
        #
        # print(f"DONE!")


class DjangoLibrarySphinxConfigurator(AbstractSphinxConfigurator):
    """
    A configurator that allows you to build the documentation of a django project
    """

    def configure_deploy(self):
        # Configure to be able to deploy to readthedocs

        # Readthedocs theme
        # on_rtd is whether on readthedocs.org, this line of code grabbed from docs.readthedocs.org...
        on_rtd = os.environ.get("READTHEDOCS", None) == "True"
        if not on_rtd:  # only import and set the theme if we're building docs locally
            import sphinx_rtd_theme
            self.sphinx_script.html_theme = "sphinx_rtd_theme"
            self.sphinx_script.html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]
        self.sphinx_script.html_css_files = ["readthedocs-custom.css"]  # Override some CSS settings

        # Pydata theme
        # html_theme = "pydata_sphinx_theme"
        # html_logo = "_static/logo-company.png"
        # html_theme_options = { "show_prev_next": False}
        # html_css_files = ['pydata-custom.css']

        # Add any paths that contain custom static files (such as style sheets) here,
        # relative to this directory. They are copied after the builtin static files,
        # so a file named "default.css" will overwrite the builtin "default.css".
        self.sphinx_script.html_static_path = ['_static']

    def get_sphinx_extensions(self) -> Iterable[str]:
        yield from super().get_sphinx_extensions()
        yield from [
            'sphinx.ext.autodoc',  # Core library for html generation from docstrings
            'sphinx.ext.autosummary',  # Create neat summary tables
            'sphinx.ext.intersphinx',  # Link to other project's documentation (see mapping below
            'sphinx.ext.viewcode',  # Add a link to the Python docs code for classes, functions etc.
            'sphinx_autodoc_typehints',  # Automatically document param types (less noise in class signature)
        ]

    def configure_sphinx_extension(self, extension_name: str):
        LOG.info(f"Trying to configure {extension_name}...")
        if extension_name == 'sphinx.ext.viewcode':
            self.sphinx_script.html_show_sourcelink = False  # Remove 'view docs code' from top of page (for html, not python)
        elif extension_name == 'sphinx_autodoc_typehints':
            self.sphinx_script.set_type_checking_flag = True  # Enable 'expensive' imports for sphinx_autodoc_typehints
        elif extension_name == "sphinx.ext.autodoc":
            self.sphinx_script.autodoc_inherit_docstrings = True  # If no docstring, inherit from base class
            self.sphinx_script.add_module_names = False  # Remove namespaces from class/method signatures
        elif extension_name == "sphinx.ext.autosummary":
            self.sphinx_script.autosummary_generate = True  # Turn on sphinx.ext.autosummary
            self.sphinx_script.autoclass_content = "both"  # Add __init__ doc (ie. params) to class summaries
        elif extension_name == "sphinx.ext.intersphinx":
            # Mappings for sphinx.ext.intersphinx. Projects have to have Sphinx-generated doc! (.inv file)
            self.sphinx_script.intersphinx_mapping = {
                "python": ("https://docs.python.org/3/", None),
                'django': ('http://docs.djangoproject.com/en/3.2.7/', 'http://docs.djangoproject.com/en/3.2.7/_objects/'),
            }
        else:
            return False
        return True

    def do_after_reading_project_data(self):
        # sys.path.insert(0, os.path.abspath(os.path.join('.', os.pardir, os.pardir)))
        sys.path.insert(0, os.path.abspath(os.path.join('.', os.pardir, self.sphinx_script.project_package_name)))
        LOG.info(f"PATH[{len(sys.path)}] {sys.path}")
        LOG.info(f"CWD = {os.path.abspath('.')}")

        # #################################################
        # INTEGRATE DJANGO
        # #################################################
        # it is a project using djang, which likely requires to use some apps (e.g., auth). So add them:
        # see also https://stackoverflow.com/a/49677052/1887602

        import django
        from django.conf import settings

        # pass settings into configure
        settings.configure(
            SECRET_KEY="dummysecret",
            INSTALLED_APPS=[
                'django.contrib.admin',
                'django.contrib.auth',
                'django.contrib.contenttypes',
                'django.contrib.sessions',
                'django.contrib.messages',
                'django.contrib.staticfiles',
            ]
        )

        # call django.setup to load installed apps and other stuff
        django.setup()

    def fetch_project_information(self) -> Dict[str, any]:
        from setup import s

        project = s.get_name()
        copyright = f'2021, {s.get_author()}'
        author = s.get_author()
        version = s.get_version(root_dir=os.path.join(os.pardir), print_result=True)
        package_name = s.get_main_package()

        return dict(
            project=project,
            copyright=copyright,
            author=author,
            version=version,
            project_package_name=package_name,
        )

    def _pre_configure(self):
        pass