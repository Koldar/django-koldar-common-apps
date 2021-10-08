from datetime import datetime
from typing import Union

import arrow
from arrow import Arrow
from graphene import Scalar
from graphql.language import ast


class ArrowDateScalar(Scalar):
    """
    Date time using arrow instead of Date.
    We serialize and deserialize in UTC date
    """

    @staticmethod
    def serialize(dt: Union[Arrow, datetime, str]) -> str:
        if isinstance(dt, Arrow):
            return dt.to("utc").format("yyyy-MM-dd")
        elif isinstance(dt, datetime):
            return arrow.get(dt).to("utc").format("yyyy-MM-dd")
        elif isinstance(dt, str):
            return arrow.get(dt).to("utc").format("yyyy-MM-dd")
        else:
            raise TypeError(f"Cannot serialize {type(dt)} into a date time graphene scalar!")

    @staticmethod
    def parse_literal(node) -> Arrow:
        if isinstance(node, ast.StringValueNode):
            return arrow.get(arrow.get(node.value).utcnow().date())
        # return datetime.datetime.strptime(node.value, "%Y-%m-%dT%H:%M:%S.%f")
        else:
            raise TypeError(f"cannot parse literal {type(node.value)}!")

    @staticmethod
    def parse_value(value) -> Arrow:
        if isinstance(value, str):
            return arrow.get(arrow.get(value).utcnow().date())
        else:
            raise TypeError(f"cannot parse literal {type(value)}!")