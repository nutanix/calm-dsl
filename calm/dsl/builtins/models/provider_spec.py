import os
import sys
import inspect
from ruamel import yaml
from calm.dsl.providers import get_validator

from .entity import EntityType
from .validator import PropertyValidator


class ProviderSpecType(EntityType):
    __schema_name__ = "ProviderSpec"
    __openapi_type__ = "app_provider_spec"


class ProviderSpec(metaclass=ProviderSpecType):
    def __init__(self, create_spec):

        self.create_spec = create_spec

    def __validate__(self, provider_type):

        ValidatorClass = get_validator(provider_type)
        validator = ValidatorClass()
        validator.validate(self.create_spec)

        return self.create_spec

    def __get__(self, instance, cls):

        return self.__validate__(cls.type)


class ProviderSpecValidator(PropertyValidator, openapi_type="app_provider_spec"):
    __default__ = None
    __kind__ = ProviderSpec


def provider_spec(create_spec):
    return ProviderSpec(create_spec)


def read_provider_spec(filename):

    file_path = os.path.join(
        os.path.dirname(inspect.getfile(sys._getframe(1))), filename
    )

    with open(file_path, "r") as f:
        create_spec = yaml.safe_load(f.read())

    return provider_spec(create_spec)
