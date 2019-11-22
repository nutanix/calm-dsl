from .package import package
import os
import inspect
import sys
import configparser


# Downloadable package

# Constants
ImageType = "DISK_IMAGE"
ImageArchitecture = "X86_64"
ProductVersion = "1.0"
ConfigSections = ["IMAGE", "PRODUCT", "CHECKSUM"]


def ahv_vm_disk_package(name="", description="", config_file=None):
    if not config_file:
        raise ValueError("file not valid !!!")

    config = configparser.ConfigParser()
    config.optionxform = str

    config_file = os.path.join(os.path.dirname(inspect.getfile(sys._getframe(1))), config_file)
    if os.path.isfile(config_file):
        config.read(config_file)

    # Check for given sections, if not present add an empty one
    for section in ConfigSections:
        if section not in config:
            config.add_section(section)

    kwargs = {
        "type": "SUBSTRATE_IMAGE",
        "options": {
            "name": config["IMAGE"].get("name", name),
            "description": "",
            "resources": {
                "image_type": config["IMAGE"].get("type", ImageType),
                "source_uri": config["IMAGE"].get("source_uri", ""),
                "version": {
                    "product_version": config["PRODUCT"].get("version", ProductVersion),
                    "product_name": config["PRODUCT"].get("name", name)
                },
                "architecture": config["IMAGE"].get("architecture", ImageArchitecture)
            }
        }
    }

    # If image is ISO type, search for checksum data
    if kwargs["options"]["resources"]["image_type"] == "ISO_IMAGE":
        kwargs["options"]["resources"]["checksum"] = {
            "checksum_algorithm": config["CHECKSUM"].get("algorithm", ""),
            "checksum_value": config["CHECKSUM"].get("value", ""),
        }

    return package(name=name, description=description, **kwargs)
