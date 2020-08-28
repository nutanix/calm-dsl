import sys

from .entity import EntityType
from .validator import PropertyValidator
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


# Project


class EnvironmentType(EntityType):
    __schema_name__ = "Environment"
    __openapi_type__ = "environment"  # TODO use mentioned in calm api schemas


class EnvironmentValidator(PropertyValidator, openapi_type="app_service"):
    __default__ = None
    __kind__ = EnvironmentType


def environment(**kwargs):
    name = kwargs.get("name", None)
    bases = ()
    return EnvironmentType(name, bases, kwargs)


Environment = environment()
