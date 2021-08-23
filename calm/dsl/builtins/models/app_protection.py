import sys

from calm.dsl.log import get_logging_handle
from calm.dsl.store import Cache

from .config_spec import snapshot_config_create, restore_config_create
from .helper import common as common_helper

LOG = get_logging_handle(__name__)


class AppProtection:
    def __new__(cls, *args, **kwargs):
        raise TypeError("'{}' is not callable".format(cls.__name__))

    class ProtectionPolicy:
        def __new__(cls, name, **kwargs):
            rule_name = kwargs.get("rule_name", None)
            rule_uuid = kwargs.get("rule_uuid", None)
            project_cache_data = common_helper.get_cur_context_project()
            project_name = project_cache_data.get("name")
            protection_policy_cache_data = Cache.get_entity_data(
                entity_type="app_protection_policy",
                name=name,
                rule_name=rule_name,
                rule_uuid=rule_uuid,
                project_name=project_name,
            )

            if not protection_policy_cache_data:
                LOG.error(
                    "Protection Policy {} not found. Please run: calm update cache".format(
                        name
                    )
                )
                sys.exit("Protection policy {} does not exist".format(name))
            return {
                "kind": "app_protection_policy",
                "name": protection_policy_cache_data["name"],
                "uuid": protection_policy_cache_data["uuid"],
                "rule_uuid": protection_policy_cache_data["rule_uuid"],
            }

    class SnapshotConfig:
        def __new__(
            cls,
            name,
            target=None,
            num_of_replicas="ONE",
            restore_config=None,
            policy=None,
            description="",
        ):
            if restore_config:
                return snapshot_config_create(
                    name,
                    target=target,
                    num_of_replicas=num_of_replicas,
                    config_references=[restore_config],
                    policy=policy,
                    description=description,
                )
            return snapshot_config_create(
                name,
                target=target,
                num_of_replicas=num_of_replicas,
                policy=policy,
                description=description,
            )

        class CrashConsistent:
            def __new__(
                cls,
                name,
                target=None,
                num_of_replicas="ONE",
                restore_config=None,
                policy=None,
                description="",
            ):
                if restore_config:
                    return snapshot_config_create(
                        name,
                        target=target,
                        num_of_replicas=num_of_replicas,
                        config_references=[restore_config],
                        policy=policy,
                        description=description,
                    )
                return snapshot_config_create(
                    name,
                    target=target,
                    num_of_replicas=num_of_replicas,
                    policy=policy,
                    description=description,
                )

    class RestoreConfig:
        def __new__(
            cls,
            name,
            target=None,
            delete_vm_post_restore=False,
            description="",
        ):
            return restore_config_create(
                name,
                target=target,
                delete_vm_post_restore=delete_vm_post_restore,
                description=description,
            )
