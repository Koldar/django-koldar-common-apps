import abc
import os
import sys
from pathlib import Path
from typing import List, Iterable, Dict, Optional

import pkg_resources
import stringcase
from semantic_version import Version
from setuptools import Command, find_packages, setup


# class NoopDistribution(Distribution):
#     pass




class PushTagCommand(Command):

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        from git import Repo
        p = os.path.abspath(".")
        print(f"Considering git repo {p}")
        repo = Repo(p, search_parent_directories=True)

        version_file = AbstractHandleVersion.get_file_version()
        version = AbstractHandleVersion.read_version(version_file)

        git = repo.git
        # push the version update
        git.add(os.path.abspath(version_file))
        git.commit(m=f"Automatic commit required to go to version {version}")
        git.push()

        # check if the repo is clean
        if repo.is_dirty(untracked_files=True):
            raise ValueError(f"""repository {repo} has some files to commit. 
            Please commit them first or reset them. We are going to make a new remote tag, 
            hence we need to be sure that the repo is clean! Files to commit are:
            {repo.index}
        """)

        # create and push the tag
        git.tag(f"v{version}", annotate=True, m=f"New release of the software to version {version}")
        git.push(tags=True)


class AbstractHandleVersion(Command, abc.ABC):

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        # do nothing. The command action is invoked at the beginning of the setup script
        pass

    @classmethod
    def get_file_version(cls, root_dir: str = None, print_result: bool = False) -> str:
        if root_dir is None:
            root_dir = "./"
        root_dir_length = len(Path(root_dir).parts)
        for dirpath, dnames, fnames in os.walk(root_dir):
            # print(f"considering dirpath {dirpath}")
            if len(Path(dirpath).parts) == root_dir_length:
                # Skip CWD
                continue
            main_directory = str(Path(dirpath).parts[root_dir_length])
            # print(f"main directory is {main_directory}")
            if main_directory.startswith("."):
                # ignore directories which starts with "."
                continue
            if any(map(lambda x: main_directory == x, ["venv", "dist", "build", "egg-info"])):
                # ignore big known folders
                continue
            for f in fnames:
                if f.endswith("version.py"):
                    result = os.path.join(dirpath, f)
                    if print_result:
                        print(f"found version file in {result}")
                    return result
        else:
            raise ValueError(f"Cannot detect version file!")

    @classmethod
    def read_version(cls, filename: str) -> Version:
        with open(filename, mode="r", encoding="utf8") as f:
            v = f.read()
        v = v.split("=")[1].strip("\"\' \t\n")
        return Version(v)

    @classmethod
    def _write_version(cls, filename: str, version: Version):
        with open(filename, mode="w", encoding="utf8") as f:
            f.write(f"VERSION = \"{version}\"")

    @abc.abstractmethod
    def update_version(self) -> str:
        pass


def update_version(next_type: str) -> str:
    version_file = AbstractHandleVersion.get_file_version()
    current_version = AbstractHandleVersion.read_version(version_file)
    if next_type == "patch":
        next_version = current_version.next_patch()
    elif next_type == "minor":
        next_version = current_version.next_minor()
    elif next_type == "major":
        next_version = current_version.next_major()
    else:
        raise ValueError(f"cannot increase version!")
    print(f"version file={version_file} current={current_version} next={next_version}")
    AbstractHandleVersion._write_version(version_file, next_version)
    print(f"done updating version file {version_file}")
    return next_version


class IncreasePatchVersion(AbstractHandleVersion):
    """
    Allows you to automatically increase version patch number.

    :see https://dankeder.com/posts/adding-custom-commands-to-setup-py/:
    """
    user_options = []

    def update_version(self) -> str:
        next_version = update_version("patch")
        return str(next_version)


class IncreaseMinorVersion(AbstractHandleVersion):
    """
    Allows you to automatically increase version minor number.

    :see https://dankeder.com/posts/adding-custom-commands-to-setup-py/:
    """
    user_options = []

    def update_version(self) -> str:
        next_version = update_version("minor")
        return str(next_version)


class IncreaseMajorVersion(AbstractHandleVersion):
    """
    Allows you to automatically increase version major number.

    :see https://dankeder.com/posts/adding-custom-commands-to-setup-py/:
    """
    user_options = []

    def update_version(self) -> str:
        next_version = update_version("major")
        return str(next_version)


class AbstractScriptSetup(abc.ABC):
    """
    Allows you to manage your package. setuptools commands built in are:

    - patch_version: increase the version file patchwise
    - patch_minor: increase the version file patchwise
    - patch_major: increase the version file patchwise
    - bdist_wheel: build a wheel pacakge
    - upload: upload to pypi (use -r to pass a private pypi repository)
    - push_tags:
    """

    def __init__(self, author: str, author_mail: str, description: str, keywords: List[str], home_page: str,
                      python_minimum_version: str, license_name: str, main_package: str, classifiers: List[str] = None,
                      package_data: str = "package_data", required_dependencies: List[str] = None, scripts: List[str] = None, test_dependencies: List[str] = None, doc_dependencies: List[str] = None):
        self.version: Optional[str] = None
        self.author = author
        self.author_mail = author_mail
        self.description = description
        self.keywords = keywords
        self.home_page = home_page
        self.classifiers = classifiers
        self.python_minimum_version = python_minimum_version
        self.license_name = license_name
        self.required_dependencies = required_dependencies
        self.main_package = main_package
        self.package_data = package_data
        self.scripts = scripts
        self.test_dependencies = test_dependencies or []
        self.doc_dependencies = doc_dependencies or []

    def get_author(self) -> str:
        """
        :return: Author name
        """
        return self.author

    def get_name(self) -> str:
        """
        :return: project name. Normally it is the main package in spinal case
        """
        return stringcase.spinalcase(self.main_package)

    def get_main_package(self) -> str:
        """
        :return: main pacakge of the project
        """
        return self.main_package

    def get_python_requires(self) -> str:
        return f">={self.python_minimum_version}"

    def get_install_requires(self) -> List[str]:
        if self.required_dependencies is None:
            return list(self.get_dependencies())
        else:
            return self.required_dependencies

    def get_classifiers(self) -> List[str]:
        if self.classifiers is None:
            return [
                "Programming Language :: Python :: 3",
                self.get_license_classifier_name(),
                "Operating System :: OS Independent",
            ]
        else:
            return self.classifiers

    def get_license_classifier_name(self) -> str:
        if self.license_name.lower() == "mit":
            return f"License :: OSI Approved :: MIT License"
        elif self.license_name.lower() in ["proprietary", "commercial", "close"]:
            return f"Other/Proprietary License"
        else:
            raise ValueError(f"Cannot determine license classifiier name of license {self.license_name}")

    def get_package_data(self) -> Dict[str, any]:
        return {
            "": [f"{self.package_data}/*.*"],
        }

    def get_test_suite(self) -> str:
        return f'{self.main_package}.tests'

    def read_file_content(self, name: str) -> str:
        return open(name).read()

    def get_version(self, root_dir: str = None, print_result: bool = False) -> str:
        if self.version is None:
            # before reading the version we need to check if the user wants to also updates it.
            # if this is the case, we first ned to update the version and then retrieve the increased version
            if "update_version_patch" in sys.argv:
                self.version = update_version("patch")
            elif "update_version_minor" in sys.argv:
                self.version = update_version("minor")
            elif "update_version_major" in sys.argv:
                self.version = update_version("major")
            if "patch_version" in sys.argv:
                self.version = update_version("patch")
            elif "minor_version" in sys.argv:
                self.version = update_version("minor")
            elif "major_version" in sys.argv:
                self.version = update_version("major")
            else:
                version_file = AbstractHandleVersion.get_file_version(root_dir, print_result=print_result)
                self.version = str(AbstractHandleVersion.read_version(version_file))
        return self.version

    def get_dependencies(self, domain: str = None) -> Iterable[str]:
        if domain is None:
            filename = "requirements.txt"
        else:
            filename = f"requirements-{domain}.txt"

        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as fh:
                for dep in pkg_resources.parse_requirements(fh):
                    # we need to replace a==3 with a>=3. Other requirements are skipped
                    if len(dep.specs) == 1 and dep.specs[0][0] == "==":
                        yield dep.unsafe_name + ">=" + dep.specs[0][1]
                    else:
                        yield str(dep)
                # for dep in fh.readlines():
                #     # a requirement may not be simply a==0.0.1
                #     dep_name = dep.split("==")[0]
                #     dep_version = dep.split("==")[1].strip()
                #     yield dep_name + ">=" + dep_version

    def get_scripts(self) -> List[str]:
        return self.scripts or []

    def get_long_description(self) -> str:
        readme_name = 'README.md'
        if os.path.exists(readme_name):
            # developer has a readme file encoded in markdown. We need to convert it first into rst
            from m2r import convert
            text = self.read_file_content('README.md')
            rst_string = convert(text)
            return rst_string
        else:
            return "<no readme found>"

    def get_long_description_content_type(self) -> str:
        readme_name = 'README.md'
        if os.path.exists(readme_name):
            return "text/markdown"
        else:
            return "text/plain"

    def get_command_options(self) -> Dict[str, any]:
        """
        Configure the commands
        """
        return {
            'build_sphinx': {
                # 'project': ('setup.py', name),
                # 'version': ('setup.py', version),
                # 'release': ('setup.py', release),
                'source_dir': ('setup.py', 'docs')
            }
        }

    def get_license_name(self) -> str:
        return "LICEN[SC]E*.md"

    def get_packages_of_application(self, root_dir: str = None) -> List[str]:
        """
        fetch all the packages of the module.
        By default we call "find_packages".

        :param root_dir: directory where you should be able t find all the packages. If left unspecified, it is "."
        :return: list of python packages discovered (e.g., "foo", "foo.bar", "foo.bar.baz1").
        """
        if root_dir is None:
            root_dir = os.curdir
        return find_packages(where=root_dir)

    def get_docs_requirements(self, section_name: str) -> List[str]:
        result = [
            "sphinx",
            "sphinx-rtd-theme",
        ]
        result.extend(self.doc_dependencies)
        return result

    def get_test_requirements(self, section_name: str) -> List[str]:
        result = [
            "pytest",
            "mock",
        ]
        result.extend(self.test_dependencies)
        return result

    def get_other_extra_requirements(self) -> Dict[str, List[str]]:
        return {}

    def perform_setup(self, **kwargs):
        cmdclass = {
            'update_version_patch': IncreasePatchVersion,
            'update_version_minor': IncreaseMinorVersion,
            'update_version_major': IncreaseMajorVersion,
            'patch_version': IncreasePatchVersion,
            'minor_version': IncreaseMinorVersion,
            'major_version': IncreaseMajorVersion,
            'push_tag': PushTagCommand,
        }

        if "cmdclass" in kwargs:
            cmdclass = {**cmdclass, **kwargs["cmdclass"]}
            del kwargs["cmdclass"]


        setup(
            name=self.get_name(),
            version=self.get_version(),
            author=self.author,
            author_email=self.author_mail,
            description=self.description,
            license=self.license_name,
            keywords=self.keywords,
            url=self.home_page,
            packages=self.get_packages_of_application(),
            long_description=self.get_long_description(),
            long_description_content_type=self.get_long_description_content_type(),
            classifiers=self.get_classifiers(),
            license_files=self.get_license_name(),
            # REQUIREMENTS
            python_requires=self.get_python_requires(),
            install_requires=self.get_install_requires(),
            extras_require={
                "docs": self.get_docs_requirements("docs"),
                "test": self.get_test_requirements("test"),
                **self.get_other_extra_requirements(),
            },
            # NON PYTHON DATA
            include_package_data=True,
            package_data=self.get_package_data(),
            # SCRIPTS TO INSTALL IN PYTHON "Script" folder
            scripts=self.get_scripts(),
            # CONSOLE SCRIPT
            #entry_points={"console_scripts": [f"{console_script_name}={main_package}.main:main"]},
            # TEST
            test_suite=self.get_test_suite(),
            # CUSTOM COMMANDS
            cmdclass=cmdclass,
            command_options=self.get_command_options(),
            # OTHER ARGUMENTS
            **kwargs
        )
