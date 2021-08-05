import abc
import os
import sys
from pathlib import Path
from typing import List, Iterable, Dict

import stringcase
from semantic_version import Version
from setuptools import Distribution, Command, find_packages, setup


class NoopDistribution(Distribution):
    pass


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

        # check if the repo is clean
        if repo.is_dirty(untracked_files=True):
            raise ValueError(
                f"repository {repo} has some files to commit. Please commit them first or reset them. We are going to make a new remote tag, hence we need to be sure that the repo is clean!")

        version_file = AbstractHandleVersion.get_file_version()
        version = AbstractHandleVersion.read_version(version_file)

        git = repo.git
        # push the version update
        git.add(os.path.abspath(version_file))
        git.commit(m=f"Automatic commit required to go to version {version}")
        git.push()
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
    def get_file_version(cls) -> str:
        for dirpath, dnames, fnames in os.walk("./"):
            if len(Path(dirpath).parts) == 0:
                # Skip CWD
                continue
            main_directory = str(Path(dirpath).parts[0])
            if main_directory.startswith("."):
                continue
            if any(map(lambda x: main_directory == x, ["venv", "dist", "build", "egg-info"])):
                # ignore big folders
                continue
            for f in fnames:
                if f.endswith("version.py"):
                    return os.path.join(dirpath, f)
        else:
            raise ValueError(f"Cannot detect version file!")

    @classmethod
    def read_version(cls, filename: str) -> Version:
        with open(filename, mode="r", encoding="utf8") as f:
            v = f.read()
        v = v.split("=")[1].strip("\"\' \t\n")
        return Version(v)

    def _write_version(self, filename: str, version: Version):
        with open(filename, mode="w", encoding="utf8") as f:
            f.write(f"VERSION = \"{version}\"")

    @abc.abstractmethod
    def update_version(self) -> str:
        pass


class IncreasePatchVersion(AbstractHandleVersion):
    """
    Allows you to automatically increase version patch number.

    :see https://dankeder.com/posts/adding-custom-commands-to-setup-py/:
    """
    user_options = []

    def update_version(self) -> str:
        version_file = self.get_file_version()
        current_version = self.read_version(version_file)
        next_version = current_version.next_patch()
        print(f"version file={version_file} current={current_version} next={next_version}")
        self._write_version(version_file, next_version)
        print(f"done updating version file {version_file}")
        return str(next_version)


class IncreaseMinorVersion(AbstractHandleVersion):
    """
    Allows you to automatically increase version minor number.

    :see https://dankeder.com/posts/adding-custom-commands-to-setup-py/:
    """
    user_options = []

    def update_version(self) -> str:
        version_file = self.get_file_version()
        current_version = self.read_version(version_file)
        next_version = current_version.next_minor()
        print(f"version file={version_file} current={current_version} next={next_version}")
        self._write_version(version_file, next_version)
        print(f"done updating version file {version_file}")
        return str(next_version)


class IncreaseMajorVersion(AbstractHandleVersion):
    """
    Allows you to automatically increase version major number.

    :see https://dankeder.com/posts/adding-custom-commands-to-setup-py/:
    """
    user_options = []

    def update_version(self) -> str:
        version_file = self.get_file_version()
        current_version = self.read_version(version_file)
        next_version = current_version.next_major()
        print(f"version file={version_file} current={current_version} next={next_version}")
        self._write_version(version_file, next_version)
        print(f"done updating version file {version_file}")
        return str(next_version)


class AbstractScriptSetup(abc.ABC):

    def __init__(self, author: str, author_mail: str, description: str, keywords: List[str], home_page: str,
                      python_minimum_version: str, license_name: str, main_package: str, classifiers: List[str] = None,
                      package_data: str = "package_data", required_dependencies: List[str] = None):
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

    def get_name(self) -> str:
        return stringcase.spinalcase(self.main_package)

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
        if self.license_name == "MIT":
            return f"License :: OSI Approved :: MIT License"
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

    def handle_version(self) -> str:
        if "update_version_patch" in sys.argv:
            return IncreasePatchVersion(dist=NoopDistribution()).update_version()
        elif "update_version_minor" in sys.argv:
            return IncreaseMinorVersion(dist=NoopDistribution()).update_version()
        elif "update_version_major" in sys.argv:
            return IncreaseMajorVersion(dist=NoopDistribution()).update_version()
        else:

            version_file = AbstractHandleVersion.get_file_version()
            return str(AbstractHandleVersion.read_version(version_file))

    def get_dependencies(self, domain: str = None) -> Iterable[str]:
        if domain is None:
            filename = "requirements.txt"
        else:
            filename = f"requirements-{domain}.txt"
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as fh:
                for dep in fh.readlines():
                    dep_name = dep.split("==")[0]
                    dep_version = dep.split("==")[1].strip()
                    yield dep_name + ">=" + dep_version

    def perform_setup(self, **kwargs):
        cmdclass = {
            'update_version_patch': IncreasePatchVersion,
            'update_version_minor': IncreaseMinorVersion,
            'update_version_major': IncreaseMajorVersion,
            'push_tag': PushTagCommand,
        }

        if "cmdclass" in kwargs:
            cmdclass = {**cmdclass, **kwargs["cmdclass"]}
            del kwargs["cmdclass"]


        setup(
            name=self.get_name(),
            version=self.handle_version(),
            author=self.author,
            author_email=self.author_mail,
            description=self.description,
            license=self.license_name,
            keywords=self.keywords,
            url=self.home_page,
            packages=find_packages(),
            long_description=self.read_file_content('README.md'),
            long_description_content_type="text/markdown",
            classifiers=self.classifiers,
            license_files="LICEN[SC]E*.md",
            # REQUIREMENTS
            python_requires=self.get_python_requires(),
            install_requires=self.get_install_requires(),
            # NON PYTHON DATA
            include_package_data=True,
            package_data=self.get_package_data(),
            # CONSOLE SCRIPT
            #entry_points={"console_scripts": [f"{console_script_name}={main_package}.main:main"]},
            # TEST
            test_suite=self.get_test_suite(),
            # CUSTOM COMMANDS
            cmdclass=cmdclass,
            # OTHER ARGUMENTS
            **kwargs
        )
