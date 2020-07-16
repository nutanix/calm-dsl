import os
import sys
import inspect
from ruamel import yaml
from calm.dsl.providers import get_provider
from calm.dsl.builtins import file_exists

from .entity import EntityType
from .validator import PropertyValidator
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


class ProviderSpecType(EntityType):
    __schema_name__ = "ProviderSpec"
    __openapi_type__ = "app_provider_spec"


class _ProviderSpec(metaclass=ProviderSpecType):
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
    __kind__ = ProviderSpecType


def provider_spec(spec):
    return _ProviderSpec(spec)


def read_spec(filename, depth=1):
    file_path = os.path.join(
        os.path.dirname(inspect.getfile(sys._getframe(depth))), filename
    )

    if not file_exists(file_path):
        LOG.debug("file {} not found at location {}".format(filename, file_path))
        raise ValueError("file {} not found".format(filename))

    with open(file_path, "r") as f:
        spec = yaml.safe_load(f.read())

    return spec


def read_provider_spec(filename):
    spec = read_spec(filename, depth=2)
    return provider_spec(spec)


def read_ahv_spec(filename, disk_packages={}):
    spec = read_spec(filename, depth=2)
    if disk_packages:
        Provider = get_provider("AHV_VM")
        Provider.update_vm_image_config(spec, disk_packages)

    return provider_spec(spec)


def read_vmw_spec(filename, vm_template=None):
    spec = read_spec(filename, depth=2)
    if vm_template:
        Provider = get_provider("VMWARE_VM")
        Provider.update_vm_image_config(spec, vm_template)

    return provider_spec(spec)
