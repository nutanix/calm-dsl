from .entity import Entity, EntityType
from .validator import PropertyValidator
from .package import PackageType, package

# Package


class DownloadablePackageType(PackageType):
    __schema_name__ = "DownloadablePackage"
    __openapi_type__ = "app_downloadable_package"

    def get_ref(cls, kind=None):
        """Note app_package kind to be used for downloadable package"""
        return super().get_ref(kind=PackageType.__openapi_type__)

    def compile(cls):

        cdict = super().compile()

        kwargs = {
            "type": "SUBSTRATE_IMAGE",
            "options": {
                "name": cdict.get("image_name") or cls.__name__,
                "description": cdict["description"],
                "resources": {
                    "image_type": cdict["image_type"],
                    "source_uri": cdict["source_uri"],
                    "version": {
                        "product_version": cdict["product_version"],
                        "product_name": cdict.get("product_name") or cls.__name__
                    },
                    "architecture": cdict["architecture"]
                }
            }
        }

        pkg = package(name=cls.__name__, **kwargs)
        return pkg.compile()


class DownloadablePackageValidator(PropertyValidator, openapi_type="app_downloadable_package"):
    __default__ = None
    __kind__ = DownloadablePackageType


def downloadable_package(**kwargs):
    name = kwargs.get("name") or getattr(DownloadablePackageType, "__schema_name__")
    bases = (Entity,)
    return DownloadablePackageType(name, bases, kwargs)


DownloadablePackage = downloadable_package()
