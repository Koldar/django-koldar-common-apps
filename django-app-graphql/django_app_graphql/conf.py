import inspect
import os

from django.conf import settings
from appconf import AppConf
from django_koldar_utils.django_toolbox.conf.DictSettingMergerAppConf import DictSettingMergerAppConf


class DjangoAppGraphQLAppConf(DictSettingMergerAppConf):
    class Meta:
        prefix = "DJANGO_APP_GRAPHQL"

    def configure(self):
        return self.merge_configurations()

    BACKEND_TYPE: str = "graphene"
    """
    Type of the backend. May either be "graphene" or "ariadne". 
    """
    ADD_DUMMY_QUERIES_IF_ABSENT = False
    """
    If no queries have been added by the user, forcibly add some of them ourselves.
    Might clashes with federation, hence the default is false.
    """
    ADD_DUMMY_MUTATIONS_IF_ABSENT = False
    """
    If no mutations have been added by the user, forcibly add some of them ourselves.
    Might clashes with federation, hence the default is false.
    """
    EXPOSE_GRAPHIQL = True
    """
    If set, we will expose the graphiql UI
    """
    GRAPHQL_SERVER_URL = ""
    """
    the endpoint where the graphql server is located
    """
    ENABLE_GRAPHQL_FEDERATION = True
    """
    If True, we will build the grpahql schema using graphql federation.
    False to disable.
    """
    SAVE_GRAPHQL_SCHEMA = os.path.join("output", "graphql", "schema.graphql")
    """
    If not None, represents the file where we will dump the generated grpahql schema.
    """

    INCLUDE_UPLOAD_MUTATION = False
    """
    If set, we will include graphene_file_upload and expose a a mutation you can use to upload your files
    """

