from .package import package
from .provider_spec import read_spec
from .package import PackageType
from .validator import PropertyValidator
from .entity import Entity
from calm.dsl.log import get_logging_handle


# Downloadable Image

# Constants
ImageType = "DISK_IMAGE"
ImageArchitecture = "X86_64"
ProductVersion = "1.0"
ConfigSections = ["image", "product", "checksum"]
LOG = get_logging_handle(__name__)


class VmDiskPackageType(PackageType):
    __schema_name__ = "VmDiskPackage"
    __openapi_type__ = "app_vm_disk_package"

    def get_ref(cls, kind=None):
        """Note: app_package kind to be used for downloadable image"""
        return super().get_ref(kind=PackageType.__openapi_type__)

    def get_dict(cls):

        attrs = cls.get_all_attrs()
        # convert keys to api schema
        cdict = {}
        display_map = getattr(type(cls), "__display_map__")
        for k, v in attrs.items():
            if getattr(v, "__is_object__", False):
                cdict.setdefault(display_map[k], v.get_dict())
            cdict.setdefault(display_map[k], v)

        # Add name & description if present
        if "name" in cdict and cdict["name"] == "":
            cdict["name"] = cls.__name__

        if "description" in cdict and cdict["description"] == "":
            cdict["description"] = cls.__doc__ if cls.__doc__ else ""

        return cdict

    def compile(cls):
        config = super().compile()

        pkg_name = config["name"]
        pkg_doc = config["description"]

        kwargs = {
            "type": "SUBSTRATE_IMAGE",
            "options": {
                "name": config["image"].get("name") or pkg_name,
                "description": "",
                "resources": {
                    "image_type": config["image"].get("type") or ImageType,
                    "source_uri": config["image"].get("source_uri") or "",
                    "version": {
                        "product_version": config["product"].get("version")
                        or ""
                        or ProductVersion,
                        "product_name": config["product"].get("name") or pkg_name,
                    },
                    "architecture": config["image"].get(
                        "architecture", ImageArchitecture
                    ),
                },
            },
        }

        # If image is ISO type, search for checksum data
        if kwargs["options"]["resources"]["image_type"] == "ISO_IMAGE":
            kwargs["options"]["resources"]["checksum"] = {
                "checksum_algorithm": config["checksum"].get("algorithm", ""),
                "checksum_value": config["checksum"].get("value", ""),
            }

        pkg = package(name=pkg_name, description=pkg_doc, **kwargs)
        # return the compile version of package
        return pkg.compile()

    @classmethod
    def decompile(mcls, cdict, context=[]):
        """decompile method for downloadble images"""

        name = cdict.get("name") or ""
        description = cdict.get("description") or ""

        options = cdict["options"]
        resources = options.get("resources", {})

        img_type = resources["image_type"]
        config = {
            "image": {
                "name": options["name"],
                "type": resources["image_type"],
                "source": resources["source_uri"],
                "architecture": resources["architecture"],
            }
        }

        if resources.get("version", None):
            config["product"] = {
                "name": resources["version"].get("product_name") or "",
                "version": resources["version"].get("product_version") or "",
            }

        if img_type == "ISO_IMAGE" and resources.get("checksum", None):
            config["checksum"] = {
                "algorithm": resources["checksum"].get("checksum_algorithm") or "",
                "value": resources["checksum"].get("checksum_value") or "",
            }

        config["description"] = description
        config["name"] = name

        cls = mcls(name, (Entity,), config)
        cls.__doc__ = description

        return cls


class VmDiskPackageValidator(PropertyValidator, openapi_type="app_vm_disk_package"):
    __default__ = None
    __kind__ = VmDiskPackageType


def vm_disk_package(name="", description="", config_file=None, config={}):

    if not (config_file or config):
        raise ValueError("Downloadable image configuration not found !!!")

    if not config:
        config = read_spec(filename=config_file, depth=2)

    if not isinstance(config, dict):
        LOG.debug("Downloadable Image Config: {}".format(config))
        raise TypeError("Downloadable image configuration is not of type dict")

    config["description"] = description or config.get("description", "")
    name = name or config.get("name") or getattr(VmDiskPackageType, "__schema_name__")
    bases = (Entity,)

    # Check for given sections, if not present add an empty one
    for section in ConfigSections:
        if section not in config:
            config[section] = {}

    # Convert product version and checksum value to string
    config["product"]["version"] = str(config["product"].get("version", ""))
    config["checksum"]["value"] = str(config["checksum"].get("value", ""))

    return VmDiskPackageType(name, bases, config)


def ahv_vm_disk_package(name="", description="", config_file=None, config_data={}):

    if not (config_file or config_data):
        raise ValueError("Downloadable image configuration not found !!!")

    if not config_data:
        config_data = read_spec(filename=config_file, depth=2)

    if not isinstance(config_data, dict):
        LOG.debug("Downloadable Image Config: {}".format(config_data))
        raise TypeError("Downloadable image configuration is not of type dict")

    return vm_disk_package(name=name, description=description, config=config_data)
