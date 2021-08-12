import abc
from typing import List, Tuple

from django_koldar_utils.graphql.GraphQLHelper import GraphQLHelper
from django_koldar_utils.graphql.graphql_decorators import graphql_submutation
from graphene_file_upload.django.testing import GraphQLFileUploadTestCase
from graphene_file_upload.scalars import Upload

from django_app_graphql.conf import DjangoAppGraphQLAppConf

import graphene


class AbstractUploadMutationCreator(abc.ABC):
    """
    An object that generates a single mutation that accept
    """

    def get_upload_mutation_name(self) -> str:
        """
        Name of the class representing the mutation
        :return:
        """
        return "UploadMutation"

    def get_upload_mutation_description(self) -> str:
        """
        Description of the upload mutation. default to class __doc__ string
        :return:
        """
        doc = type(self).__doc__
        if doc is not None:
            return doc
        else:
            return ""

    def upload_tag_name(self) -> str:
        """
        name fo the string controlling the logic of the mutation to create
        :return:
        """
        return "tag"

    def upload_name_name(self) -> str:
        """
        name of the string controlling the name of the upload file
        :return:
        """
        return "name"

    def upload_description_name(self) -> str:
        return "description"

    def upload_file_name(self) -> str:
        return "file"

    def ok_flag_name(self) -> str:
        return "ok"

    @abc.abstractmethod
    def tag_check(self, info, file, name: str, description: str, tag: str, **kwargs) -> Tuple[bool, any]:
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

    def do_if_tags_check_fails(self, info, file, name: str, description: str, tag: str, tag_check_output, **kwargs):
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

    @abc.abstractmethod
    def perform_action_with_file(self, info, file, name: str, description: str, tags: List[str], **kwargs):
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

    def mutate(self, cls, info, file, name: str, description: str, tag: str, **kwargs):
        satisfied, error_data = self.tag_check(info, file, name, description, tag, **kwargs)
        if not satisfied:
            self.do_if_tags_check_fails(info, file, name, description, tag, error_data, **kwargs)

        # do something with your file


        return cls(success=True)

    def check_settings(self):
        pass
        # if not settings.INCLUDE_UPLOAD_MUTATION:
        #     raise ValueError(f"INCLUDE_UPLOAD_MUTATION has been set to False. This mutation won't be work correctly! Please set INCLUDE_UPLOAD_MUTATION.")

    def generate_upload_mutation(self):
        self.check_settings()
        result = GraphQLHelper.create_mutation(
            mutation_class_name=self.get_upload_mutation_name(),
            description=self.get_upload_mutation_description(),
            arguments={
                self.upload_tag_name(): GraphQLHelper.argument_required_string(description="""tag associated to the upload. 
                        Usually you can use the tag to determine what to do with the upload 
                        (e.g., store the file in different static folders). We assume that it is the client 
                        that tells you the tags she wants. It is server responsibility to determine 
                        the correctness of these tags. Tags, by themselves, are just string with no further meaning."""),
                self.upload_name_name(): GraphQLHelper.argument_required_string(description="name of the file to upload. Orthogonal w.r.t the filename"),
                self.upload_description_name(): GraphQLHelper.argument_nullable_string(description="Description of the file. May be left missing"),
                self.upload_file_name(): Upload(required=True, help_text="The file to upload to the server via graphql"),
            },
            return_type={
                self.ok_flag_name(): GraphQLHelper.return_ok()
            },
            body=self.mutate
        )
        return result