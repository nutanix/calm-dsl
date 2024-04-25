import sys

from calm.dsl.log import get_logging_handle
from calm.dsl.store import Cache

from .config_spec import snapshot_config_create, restore_config_create
from .helper import common as common_helper
from .metadata_payload import get_metadata_obj
from calm.dsl.constants import PROVIDER
from calm.dsl.builtins import Ref

LOG = get_logging_handle(__name__)


class AppProtection:
    def __new__(cls, *args, **kwargs):
        raise TypeError("'{}' is not callable".format(cls.__name__))

    class ProtectionPolicy:
        def __new__(cls, name, **kwargs):

            # Capturing metadata object to read project name supplied in blueprint
            # Use config project if no project supplied in metadata
            metadata = get_metadata_obj()
            if metadata.get("project_reference", {}):
                project_name = metadata.get("project_reference", {}).get("name")
            else:
                project_cache_data = common_helper.get_cur_context_project()
                project_name = project_cache_data.get("name")
            kwargs["project_name"] = project_name

            return Ref.ProtectionPolicy(name, **kwargs)

    class SnapshotConfig:
        class Ahv:
            def __new__(
                cls,
                name,
                target=None,
                num_of_replicas="ONE",
                restore_config=None,
                policy=None,
                description="",
                snapshot_location_type="LOCAL",
            ):
                if not restore_config:
                    LOG.error("Restore Config reference not supplied.")
                    sys.exit(-1)

                return snapshot_config_create(
                    name=name,
                    provider=PROVIDER.TYPE.AHV,
                    target=target,
                    num_of_replicas=num_of_replicas,
                    config_references=[restore_config],
                    policy=policy,
                    description=description,
                    snapshot_location_type=snapshot_location_type,
                )

        class Vmware:
            def __new__(
                cls,
                name,
                target=None,
                num_of_replicas="ONE",
                restore_config=None,
                policy=None,
                description="",
            ):
                if not restore_config:
                    LOG.error("Restore Config reference not supplied.")
                    sys.exit(-1)

                return snapshot_config_create(
                    name=name,
                    provider=PROVIDER.TYPE.VMWARE,
                    target=target,
                    num_of_replicas=num_of_replicas,
                    config_references=[restore_config],
                    policy=policy,
                    description=description,
                )

        # AHV snapshot object will be created by default for backward compatibility
        def __new__(
            cls,
            name,
            target=None,
            num_of_replicas="ONE",
            restore_config=None,
            policy=None,
            description="",
            snapshot_location_type="LOCAL",
        ):
            return cls.Ahv.__new__(
                cls,
                name=name,
                target=target,
                num_of_replicas=num_of_replicas,
                restore_config=restore_config,
                policy=policy,
                description=description,
                snapshot_location_type=snapshot_location_type,
            )

    class RestoreConfig:
        class Ahv:
            def __new__(
                cls,
                name,
                target=None,
                delete_vm_post_restore=False,
                description="",
            ):
                return restore_config_create(
                    name=name,
                    provider=PROVIDER.TYPE.AHV,
                    target=target,
                    delete_vm_post_restore=delete_vm_post_restore,
                    description=description,
                )

        class Vmware:
            def __new__(
                cls,
                name,
                target=None,
                description="",
            ):
                return restore_config_create(
                    name=name,
                    provider=PROVIDER.TYPE.VMWARE,
                    target=target,
                    description=description,
                )

        # AHV restore object will be created by default for backward compatibility
        def __new__(
            cls,
            name,
            target=None,
            delete_vm_post_restore=False,
            description="",
        ):
            return cls.Ahv.__new__(
                cls,
                name=name,
                target=target,
                delete_vm_post_restore=delete_vm_post_restore,
                description=description,
            )
