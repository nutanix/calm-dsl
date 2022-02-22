import sys

from calm.dsl.log import get_logging_handle

from .config_spec import patch_config_create

LOG = get_logging_handle(__name__)


class AppEdit:
    def __new__(cls, *args, **kwargs):
        raise TypeError("'{}' is not callable".format(cls.__name__))

    class UpdateConfig:
        def __new__(
            cls,
            name,
            target,
            patch_attrs,
        ):
            if target.__self__.substrate.__self__.provider_type != "AHV_VM":
                LOG.error(
                    "Config is not supported for {} provider. Please try again after changing the provider".format(
                        target.__self__.substrate.__self__.provider_type
                    )
                )
            return patch_config_create(
                name,
                target=target,
                patch_attrs=patch_attrs,
            )
