For details on Simple Blueprint Models refer [here](../../../release-notes/3.2.0/README.md#simpleblueprint-model)

Allows you to add `packages` attribute which specifies downloadable images to be used in blueprint. See following example to use downloadable images in simple blueprint model:

```
DISK_IMAGE_SOURCE = "<url_of_image_source>"
DownloadableDiskPackage = vm_disk_package(
    name="<name_of_disk>",
    config={"image": {"source": DISK_IMAGE_SOURCE}},
)

class SampleSimpleBlueprint(SimpleBlueprint):
    """SimpleBlueprint configuration"""

    deployments = [MySqlDeployment]
    environments = [Ref.Environment(name=ENV_NAME)]
    packages = [DownloadableDiskPackage]  # add downloadable image packages here

```