import os
import sys
import inspect
from ruamel import yaml
from calm.dsl.providers import get_provider

from .entity import EntityType
from .validator import PropertyValidator
from .ref import ref


class ProviderSpecType(EntityType):
    __schema_name__ = "ProviderSpec"
    __openapi_type__ = "app_provider_spec"


class ProviderSpec(metaclass=ProviderSpecType):
    def __init__(self, spec, disk_packages={}, vm_template=None):

        self.spec = spec
        self.ahv_disk_packages = disk_packages
        self.vm_template = vm_template

    def __validate__(self, provider_type):

        Provider = get_provider(provider_type)
        Provider.validate_spec(self.spec)

        return self.spec

    def __get__(self, instance, cls):

        provider_type = cls.provider_type

        # If there are disk_packages, unrool them here for AHV provider
        if provider_type == "AHV_VM":
            disk_list = self.spec["resources"].get("disk_list", [])

            for disk_address, img_address in self.ahv_disk_packages.items():
                if disk_address > len(disk_list):
                    raise ValueError("invalid disk address ({})". format(disk_address))

                disk = disk_list[disk_address - 1]

                if "data_source_reference" not in disk:
                    raise ValueError("unable to set downloadable image in disk {}". format(disk_address))

                pkg = img_address.compile()
                image_type = pkg["options"]["resources"]["image_type"]

                IMAGE_DISK_TYPE_MAP = {"DISK_IMAGE": "DISK", "ISO_IMAGE": "CDROM"}

                if IMAGE_DISK_TYPE_MAP[image_type] != disk["device_properties"]["device_type"]:
                    raise ValueError("image type mismatch in disk {}". format(disk_address))

                # Set the reference of this disk
                disk["data_source_reference"] = ref(img_address).compile()

        # If downloadable temnplate is given for VMW provider
        elif provider_type == "VMW_VM":
            self.spec["template"] = self.vm_template.__name__

        return self.__validate__(cls.provider_type)


class ProviderSpecValidator(PropertyValidator, openapi_type="app_provider_spec"):
    __default__ = None
    __kind__ = ProviderSpec


def provider_spec(spec, disk_packages={}, vm_template=""):
    return ProviderSpec(spec, disk_packages=disk_packages, vm_template=vm_template)


def read_spec(filename, depth=1):
    file_path = os.path.join(
        os.path.dirname(inspect.getfile(sys._getframe(depth))), filename
    )

    with open(file_path, "r") as f:
        spec = yaml.safe_load(f.read())

    return spec


def read_provider_spec(filename, disk_packages={}, vm_template=""):
    spec = read_spec(filename, depth=2)
    return provider_spec(spec, disk_packages=disk_packages, vm_template=vm_template)
