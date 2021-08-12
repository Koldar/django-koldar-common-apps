import abc
from typing import List, Tuple, Dict

from django_koldar_utils.graphql.GraphQLHelper import GraphQLHelper
from django_koldar_utils.graphql.graphql_decorators import graphql_submutation
from graphene_file_upload.django.testing import GraphQLFileUploadTestCase
from graphene_file_upload.scalars import Upload

from django_app_graphql.conf import DjangoAppGraphQLAppConf
from django.core.files.uploadedfile import InMemoryUploadedFile

import graphene

settings = DjangoAppGraphQLAppConf()


class AbstractUploadMutationCreator(abc.ABC):
    """
    An object that generates a single mutation that accept
    """

    def _get_upload_mutation_name(self) -> str:
        """
        Name of the class representing the mutation
        :return:
        """
        return "UploadMutation"

    def _get_upload_mutation_description(self) -> str:
        """
        Description of the upload mutation. default to class __doc__ string
        :return:
        """
        doc = type(self).__doc__
        if doc is not None:
            return doc
        else:
            return ""

    def _upload_tag_name(self) -> str:
        """
        name fo the string controlling the logic of the mutation to create
        :return:
        """
        return "tag"

    def _upload_name_name(self) -> str:
        """
        name of the string controlling the name of the upload file
        :return:
        """
        return "name"

    def _upload_description_name(self) -> str:
        return "description"

    def _upload_file_name(self) -> str:
        return "file"

    def _ok_flag_name(self) -> str:
        return "ok"

    @abc.abstractmethod
    def _tag_check(self, info, file: InMemoryUploadedFile, name: str, description: str, tag: str, **kwargs) -> Tuple[bool, any]:
        """
        Check if the file the user has uploaded and the tags she has passed are compliant with server specification.
        E.g., here is the place where you should test that in the tag "photos" are uploaded only photos.

        :param info: graphql info structure
        :param file: file the user has uploaded
        :param name: name of the file. Orthogonal w.r.t its filename
        :param description: description of the file. May be None
        :param tag: tag the user has injected to the upload mutation
        :param kwargs: other arguments of the graphql
        :return: True if the upload is compliant, false otherwise. If False,
            you can add an arbitrary object that will be passed to do_if_tags_check_fails to raise a meaningful exception
        """
        pass

    def _do_if_tags_check_fails(self, info, file: InMemoryUploadedFile, name: str, description: str, tag: str, tag_check_output, **kwargs):
        """
        What should we do if a tag check fails?
        :param info: graphql info structure
        :param file: file the user has uploaded
        :param name: name of the file. Orthogonal w.r.t its filename
        :param description: description of the file. May be None
        :param tag: tag the user has injected to the upload mutation
        :param tag_check_output: an arbitrary object generated by the failed tag check that can help you in generating a meaningful exceptiom
        :param kwargs: other arguments of the graphql
        :return:
        """
        raise ValueError(f"Tag Check on file named \"{name}\" has failed: {tag_check_output}")

    def _generate_additional_mutation_arguments(self) -> Dict[str, any]:
        """
        geneate a dictionary of additional mutations arguments
        :return:
        """
        return dict()

    def _generate_additional_mutation_return_valies(self) -> Dict[str, any]:
        """
        Generate a dictionary of additionla mutation return values
        :return:
        """
        return dict()

    @abc.abstractmethod
    def _perform_action_with_file(self, info, file: InMemoryUploadedFile, name: str, description: str, tag: str, **kwargs):
        """
        Do something with the file that we have just received
        :param info:
        :param file:
        :param name:
        :param description:
        :param tags:
        :param kwargs:
        :return:
        """
        pass

    def _check_settings(self):
        if not settings.INCLUDE_UPLOAD_MUTATION:
            raise ValueError(f"INCLUDE_UPLOAD_MUTATION has been set to False. This mutation won't be work correctly! Please set INCLUDE_UPLOAD_MUTATION.")

    def _mutate(self, mutation_class, info, file: InMemoryUploadedFile, name: str, description: str, tag: str, **kwargs):
        satisfied, error_data = self._tag_check(info, file, name, description, tag, **kwargs)
        if not satisfied:
            self._do_if_tags_check_fails(info, file, name, description, tag, error_data, **kwargs)

        # do something with your file
        self._perform_action_with_file(info, file, name, description, tag, **kwargs)

        return mutation_class(**{self._ok_flag_name(): True})

    def generate_upload_mutation(self):


        self._check_settings()
        result = GraphQLHelper.create_mutation(
            mutation_class_name=self._get_upload_mutation_name(),
            description=self._get_upload_mutation_description(),
            arguments={
                self._upload_tag_name(): GraphQLHelper.argument_required_string(description="""tag associated to the upload. 
                        Usually you can use the tag to determine what to do with the upload 
                        (e.g., store the file in different static folders). We assume that it is the client 
                        that tells you the tags she wants. It is server responsibility to determine 
                        the correctness of these tags. Tags, by themselves, are just string with no further meaning."""),
                self._upload_name_name(): GraphQLHelper.argument_required_string(description="name of the file to upload. Orthogonal w.r.t the filename"),
                self._upload_description_name(): GraphQLHelper.argument_nullable_string(description="Description of the file. May be left missing"),
                self._upload_file_name(): Upload(required=True, description="The file to upload to the server via graphql"),
                **self._generate_additional_mutation_arguments(),
            },
            return_type={
                self._ok_flag_name(): GraphQLHelper.return_ok(),
                **self._generate_additional_mutation_return_valies(),
            },
            body=self._mutate
        )
        return result
