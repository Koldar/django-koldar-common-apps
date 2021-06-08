import abc
import inspect
import logging
import os
import trace
import traceback
from pathlib import Path
from typing import Dict, Any, Optional, Union, Callable, List, Tuple, Iterable

import graphene
import inflect as inflect
import stringcase
from django.db import models
import django_filters
from django_koldar_utils.django import django_helpers, filters_helpers, permissions_helpers
from django_koldar_utils.functions.stacktrace import filter_django_stack
from graphene.types import mutation
from graphene_django import DjangoObjectType
from graphene_django_extras import DjangoListObjectField
from graphql import GraphQLError
from graphql_jwt.decorators import login_required, permission_required

from django_koldar_utils.graphql.graphql_decorators import graphql_submutation, graphql_subquery

LOG = logging.getLogger(__name__)














class AbstractMutation:
    """
    Base class for deriving a graphql mutation section. A generic mutation needs to derive from it.
    To work with the setup, the subclass needs to contain the word "Mutation".

    .. code-block:: python

        class QuestionMutation(graphene.Mutation):
            class Arguments:
                # The input arguments for this mutation
                text = graphene.String(required=True)
                id = graphene.ID()

            # The class attributes define the response of the mutation
            question = graphene.Field(QuestionType)

            @classmethod
            def mutate(cls, root, info, text, id):
                question = Question.objects.get(pk=id)
                question.text = text
                question.save()
                # Notice we return an instance of this mutation
                return QuestionMutation(question=question)
    """
    pass
    #errors = graphene.Field(GraphQLAppError, description="If present, an errors occured")

    # @abc.abstractmethod
    # def perform_mutation(self, root, info, *args, **kwargs):
    #     pass
    #
    # @staticmethod
    # def mutate(root, info, *args, **kwargs):
    #     try:
    #         LOG.error(f"Trying to execute mutation!")
    #         return AbstractMutation().perform_mutation(root, info, *args, **kwargs)
    #     except Exception as e:
    #         raise e


class AbstractQuery(graphene.ObjectType, Helper):
    """
    Base class for deriving a graphql query section. A generic query needs to derive from it.
    To work with the setup, the subclass needs to contain the word "Query"
    """
    pass
