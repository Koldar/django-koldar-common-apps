import os
from pathlib import Path
from typing import Tuple, List

import environ
import logging

from urllib import parse


def allows_deploy_to_aws(url: str, allowed_hosts: List[str]) -> List[str]:
    """
    Patch settings file of a django_toolbox in order to be deployed to AWS with zappa

    :param url: URL shown by zappa at the end of "zappa deploy"
    :param allowed_hosts: the list in settings.py representing the ALLOWED_HOSTS
    :return: allowed_hosts udpated with zappa information
    """

    try:
        import pymysql
    except ImportError:
        raise ValueError(f"In order to deploy to AWS using Zappa you need to do 'pip install pymysql'")
    # we have imported settings here in order to allow sphinx to buidl the documentation (otherwise it needs settings.py)
    from django.conf import settings
    pymysql.install_as_MySQLdb()

    result = parse.urlsplit(url)
    url = result.netloc

    # in order to deploy to AWS lambda.
    # See https://auth0.com/blog/deploying-django-restful-apis-as-serverless-applications-with-zappa/
    allowed_hosts.append(url)
    return allowed_hosts


def get_paths(file: str) -> Tuple[str, str, str, str]:
    """
    get the interesting paths w.r.t a django_toolbox project

    :return: tuple.
        - first is SETTING_DIR (absolute path of the settings.py of the project)
        - second is BASE_DIR: directory where the django_toolbox PROJECT_DIR is located (both in apps and in project directory)
        - third PROJECT_DIR: directory where settings.py is located
        - fourth PROJECT_DIRNAME: directory name of PROJECT_DIR
    """
    settings_dir = Path(file).resolve()
    # Build paths inside the project like this: BASE_DIR / 'subdir'.
    base_dir = Path(file).resolve().parent.parent
    project_dir = Path(file).resolve().parent
    project_dirname = os.path.basename(project_dir)
    return settings_dir, base_dir, project_dir, project_dirname


def read_env_file(env_file_environment_variable: str = None, default_env_file: str = None, env_file_cwd: str = None, **env_file_default_values) -> environ.Env:
    """
    Read the .env file configuration. You should use it in the settings.py of django_toolbox.
    We fetch the .env file to load by looking at the environment variabole "env_file_environment_variable". If such an
    environment variable is not found, we will load the file "default_env_file" in the CWD.

    :param env_file_environment_variable: the environment variable to consider
    :param default_env_file: the .env file to load from the CWD to load if no variable named "env_file_environment_variable"
        can be found
    :param env_file_cwd: if the env file is a relative path, this is the directory where the relative computation is based on.
        If missing, it is the CWD of the spawned process
    :param env_file_default_values: parameters that are passed as-is in the env file.
    :return: environ.Env
    """
    # ###################################################################################
    # django_toolbox-environ setup
    # ###################################################################################
    # see https://django-environ.readthedocs.io/en/latest/#settings-py

    env = environ.Env(**env_file_default_values)
    if env_file_environment_variable is None:
        env_file_environment_variable = "ENV_FILE"
    if default_env_file is None:
        default_env_file = "production.env"
    if env_file_cwd is None:
        env_file_cwd = os.path.abspath(os.curdir)

    if env_file_environment_variable in os.environ.keys():
        env_file = os.environ.get(env_file_environment_variable)
    else:
        logging.info(f"\"{env_file_environment_variable}\" environment variable not detected. Using the env file \"{default_env_file}\" in the CWD...")
        env_file = default_env_file

    if not os.path.isabs(env_file):
        env_file = os.path.join(env_file_cwd, env_file)
    env_file = os.path.abspath(os.path.normcase(env_file))

    logging.info(f"Reading the content of the env file \"{env_file}\"")
    environ.Env.read_env(env_file=env_file)
    return env
