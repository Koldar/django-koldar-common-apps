from datetime import timedelta
from typing import Union

import aniso8601

from graphene import Scalar
from graphql.language import ast


class ArrowDurationScalar(Scalar):
    """
    Duration using arrow instead of Date.
    We serialize and deserialize using ISO8601
    """

    @classmethod
    def timedelta_to_iso8601(cls, delta: timedelta) -> str:
        hours, remainder = divmod(delta.seconds, 60*60)
        minutes, remainder = divmod(remainder, 60)
        seconds = remainder
        return f"P0Y0M{delta.days}T{hours}H{minutes}M{seconds}S"

    @staticmethod
    def serialize(dt: Union[timedelta, int, str]) -> str:
        if isinstance(dt, timedelta):
            return ArrowDurationScalar.timedelta_to_iso8601(dt)
        elif isinstance(dt, int):
            return ArrowDurationScalar.timedelta_to_iso8601(timedelta(seconds=dt))
        elif isinstance(dt, str):
            # Assumes ISO8601 string
            return dt
        else:
            raise TypeError(f"Cannot serialize {type(dt)} into a date time graphene scalar!")

    @staticmethod
    def parse_literal(node) -> timedelta:
        if isinstance(node, ast.StringValueNode):
            return aniso8601.parse_duration(node.value)
        else:
            raise TypeError(f"cannot parse literal {type(node.value)}!")

    @staticmethod
    def parse_value(value) -> timedelta:
        if isinstance(value, str):
            return aniso8601.parse_duration(value)
        else:
            raise TypeError(f"cannot parse literal {type(value)}!")