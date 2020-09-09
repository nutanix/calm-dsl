import sys

from .entity import EntityType
from .validator import PropertyValidator
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


# Project


class EnvironmentType(EntityType):
    __schema_name__ = "Environment"
    __openapi_type__ = "environment"  # TODO use mentioned in calm api schemas

    def compile(cls):
        cdict = super().compile()

        substrates = cdict.get("substrate_definition_list", [])

        # NOTE Only one substrate per (provider_type, os_type) tuple can exist
        sub_set = set()
        for sub in substrates:
            _sub_tuple = (sub.provider_type, sub.os_type)
            if _sub_tuple in sub_set:
                LOG.error(
                    "Multiple substrates of provider_type '{}' for os type '{}' in an environment are not allowed.".format(
                        sub.provider_type, sub.os_type
                    )
                )
                sys.exit(-1)

            else:
                sub_set.add(_sub_tuple)

        return cdict


class EnvironmentValidator(PropertyValidator, openapi_type="environment"):
    __default__ = None
    __kind__ = EnvironmentType


def environment(**kwargs):
    name = kwargs.get("name", None)
    bases = ()
    return EnvironmentType(name, bases, kwargs)


Environment = environment()
