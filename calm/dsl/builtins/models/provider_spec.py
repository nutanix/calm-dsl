import os
import sys
import inspect
from ruamel import yaml
from calm.dsl.providers import get_provider

from .entity import EntityType
from .validator import PropertyValidator


class ProviderSpecType(EntityType):
    __schema_name__ = "ProviderSpec"
    __openapi_type__ = "app_provider_spec"


class ProviderSpec(metaclass=ProviderSpecType):
    def __init__(self, spec):

        self.spec = spec

    def __validate__(self, provider_type):

        Provider = get_provider(provider_type)
        Provider.validate_spec(self.spec)

        return self.spec

    def __get__(self, instance, cls):

        return self.__validate__(cls.provider_type)


class ProviderSpecValidator(PropertyValidator, openapi_type="app_provider_spec"):
    __default__ = None
    __kind__ = ProviderSpec


def provider_spec(spec):
    return ProviderSpec(spec)


def read_provider_spec(filename):

    file_path = os.path.join(
        os.path.dirname(inspect.getfile(sys._getframe(1))), filename
    )

    with open(file_path, "r") as f:
        spec = yaml.safe_load(f.read())

    return provider_spec(spec)
