from ariadne import ScalarType
from arrow import Arrow
import arrow
from dateutil.tz import tz

from django_app_graphql.ariadne.AbstractScalarType import AbstractScalarType, T


class ZonedDateTimeScalar(AbstractScalarType):
    """
    Serialize time zone sensitive date time
    """

    @property
    def _name(self):
        return "ZonedDateTime"

    def _serialize(self, value: Arrow, *args, **kwargs) -> str:
        return value.isoformat()

    def _deserialize(self, value: str, *args, **kwargs) -> Arrow:
        return arrow.get(value)


class UTCDateTimeScalar(AbstractScalarType):
    """
    Serialize time zone sensitive date time using UTC
    """

    @property
    def _name(self):
        return "UTCDateTime"

    def _serialize(self, value: Arrow, *args, **kwargs) -> str:
        return value.to(tz.gettz("UTC")).isoformat()

    def _deserialize(self, value: str, *args, **kwargs) -> Arrow:
        return arrow.get(value).to(tz.gettz("UTC"))


class LocalDateScalar(AbstractScalarType):
    """
    Serialize time zone sensitive date time using UTC
    """

    @property
    def _name(self):
        return "LocalDate"

    def _serialize(self, value: Arrow, *args, **kwargs) -> str:
        return value.to(tz.gettz("UTC")).format("YYYY-MM-DD")

    def _deserialize(self, value: str, *args, **kwargs) -> Arrow:
        return arrow.get(value, 'YYYY-MM-DD')


class LocalTimeScalar(AbstractScalarType):
    """
    Serialize time zone sensitive date time using UTC
    """

    @property
    def _name(self):
        return "LocalDate"

    def _serialize(self, value: Arrow, *args, **kwargs) -> str:
        return value.to(tz.gettz("UTC")).format("HH:mm:ss")

    def _deserialize(self, value: str, *args, **kwargs) -> Arrow:
        return arrow.get(value, 'HH:mm:ss')


zonedatetime_scalar, zonedatetime_serializer, zonedatetime_deserializer = ZonedDateTimeScalar().generate_scalar()
utcdatetime_scalar, utcdatetime_serializer, utcdatetime_deserializer = UTCDateTimeScalar().generate_scalar()
localdae_scalar, localdate_serializer, localdate_deserializer = LocalDateScalar().generate_scalar()
localtime_scalar, localtime_serializer, localtime_deserializer = LocalTimeScalar().generate_scalar()