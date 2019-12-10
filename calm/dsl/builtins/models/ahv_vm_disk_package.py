from .package import package
from .provider_spec import read_spec


# Downloadable package

# Constants
ImageType = "DISK_IMAGE"
ImageArchitecture = "X86_64"
ProductVersion = "1.0"
ConfigSections = ["image", "product", "checksum"]


def ahv_vm_disk_package(name="", description="", config_file=None, config_data={}):

    if not (config_file or config_data):
        raise ValueError("downloadable image configuration not found !!!")

    if not config_data:
        config = read_spec(filename=config_file, depth=2)

    else:
        config = config_data

    # Check for given sections, if not present add an empty one
    for section in ConfigSections:
        if section not in config:
            config[section] = {}

    kwargs = {
        "type": "SUBSTRATE_IMAGE",
        "options": {
            "name": config["image"].get("name", name),
            "description": "",
            "resources": {
                "image_type": config["image"].get("type", ImageType),
                "source_uri": config["image"].get("source_uri", ""),
                "version": {
                    "product_version": str(config["product"].get("version", ProductVersion)),
                    "product_name": config["product"].get("name", name),
                },
                "architecture": config["image"].get("architecture", ImageArchitecture),
            },
        },
    }

    # If image is ISO type, search for checksum data
    if kwargs["options"]["resources"]["image_type"] == "ISO_IMAGE":
        kwargs["options"]["resources"]["checksum"] = {
            "checksum_algorithm": config["checksum"].get("algorithm", ""),
            "checksum_value": str(config["checksum"].get("value", "")),
        }

    return package(name=name, description=description, **kwargs)
