import abc
from typing import Dict

from django_koldar_utils.graphql.GraphQLHelper import GraphQLHelper

from django_app_graphql.graphene.AbstractUploadMutationCreator import AbstractUploadMutationCreator


class AbstractUploadMutationTokenCreation(AbstractUploadMutationCreator, abc.ABC):
    """
    An upload mutation that needs a token in the arguments in order to work. The token is optional
    """

    def get_token_name(self) -> str:
        """
        Name of the additional token
        """
        return "token"

    def _generate_additional_mutation_arguments(self) -> Dict[str, any]:
        return {
            self.get_token_name(): GraphQLHelper.argument_jwt_token()
        }