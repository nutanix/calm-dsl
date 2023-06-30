import sys
import uuid
from copy import deepcopy
from .entity import EntityType, Entity

from calm.dsl.log import get_logging_handle
from .validator import PropertyValidator
from calm.dsl.constants import ENTITY

LOG = get_logging_handle(__name__)

# CustomProvider


class CustomProviderType(EntityType):
    __schema_name__ = "CustomProviderAccountResources"
    __openapi_type__ = ENTITY.OPENAPI_TYPE.CUSTOM_PROVIDER

    def compile(cls):
        cdict = super().compile()

        parent_reference = cdict.pop("parent_reference", {})
        if parent_reference:
            cdict["parent_reference"] = parent_reference

        return cdict


class CustomProviderAccountResourcesTypeValidator(
    PropertyValidator, openapi_type=ENTITY.OPENAPI_TYPE.CUSTOM_PROVIDER
):
    __default__ = None
    __kind__ = CustomProviderType


def custom_provider_account(**kwargs):
    name = kwargs.pop("name", None)
    bases = (Entity,)
    return CustomProviderType(name, bases, kwargs)


CustomProviderAccountResources = custom_provider_account()
