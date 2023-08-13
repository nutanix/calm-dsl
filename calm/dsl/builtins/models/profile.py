import re
import sys

from .entity import EntityType, Entity
from .validator import PropertyValidator
from .task import CalmTask, create_call_config, dag
from .ref import ref
from .action import action, _action_create
from .runbook import runbook_create
from .config_spec import SnapshotConfigSpecType, RestoreConfigSpecType
from calm.dsl.log import get_logging_handle
from .config_spec import PatchConfigSpecType


LOG = get_logging_handle(__name__)

# Profile


class ProfileType(EntityType):
    __schema_name__ = "Profile"
    __openapi_type__ = "app_profile"

    def get_task_target(cls):
        return

    @classmethod
    def pre_decompile(mcls, cdict, context, prefix=""):
        cdict = super().pre_decompile(cdict, context, prefix=prefix)

        if "__name__" in cdict:
            cdict["__name__"] = "{}{}".format(prefix, cdict["__name__"])

        # TODO add support for decompilation of profile environment
        env_uuids = cdict.pop("environment_reference_list", None)
        if env_uuids:
            cdict["environment_reference_list"] = [
                {"kind": "environment", "uuid": _eid} for _eid in env_uuids
            ]

        return cdict

    def compile(cls):
        cdict = super().compile()
        # description attribute in profile gives bp launch error: https://jira.nutanix.com/browse/CALM-19380
        cdict.pop("description", None)

        config_type_map = {
            "restore": "AHV_RESTORE",
            "snapshot": "AHV_SNAPSHOT",
            "patch": "PATCH",
        }
        config_action_prefix_map = {"restore": "Restore_", "snapshot": "Snapshot_"}
        action_names = list(map(lambda x: x.name, cdict["action_list"]))

        def make_runbook(config, target, action_name):
            call_config_task = create_call_config(
                target, config, "Call_Config_Task_{}".format(action_name)
            )
            dag_task = dag(
                "DAG_Task_{}".format(action_name), child_tasks=[call_config_task]
            )
            return runbook_create(
                name=action_name + "_runbook",
                main_task_local_reference=dag_task.get_ref(),
                tasks=[dag_task, call_config_task],
            )

        def set_config_type_based_on_target(config, config_type):
            # Set the target to first deployment incase target for the config is not specified

            # deployment = config.attrs_list[0].target_any_local_reference.__self__
            # if deployment.substrate.__self__.provider_type == "AHV_VM":
            #    config.type = config_type_map[config_type]
            # else:
            #    raise Exception(
            if config.attrs_list[0]["target_any_local_reference"] is None:
                config.attrs_list[0]["target_any_local_reference"] = ref(
                    cdict["deployment_create_list"][0]
                )
            deployment = config.attrs_list[0]["target_any_local_reference"].__self__
            if deployment.substrate.__self__.provider_type == "AHV_VM":
                config.type = config_type_map[config_type]
            else:
                LOG.error(
                    "Config is not supported for {} provider. Please try again after changing the provider".format(
                        deployment.substrate.__self__.provider_type
                    )
                )
                sys.exit(
                    "{} doesn't support {} config".format(
                        deployment.substrate.__self__.provider_type, config_type
                    )
                )
            return config

        def create_config_action_if_not_present(action_name, config):
            if action_name not in action_names:
                return _action_create(
                    **{
                        "name": action_name,
                        "description": "",
                        "critical": True,
                        "type": "user",
                        "runbook": make_runbook(
                            ref(config),
                            config.attrs_list[0]["target_any_local_reference"],
                            action_name,
                        ),
                    }
                )

        def get_config_action_name(config, config_type):
            suffix = config.name
            if suffix.startswith(config_type.title() + "_Config"):
                suffix = config.name.split(config_type.title() + "_Config")[1]
            return config_action_prefix_map[config_type] + re.sub(
                r"[^A-Za-z0-9-_]+", "_", suffix
            )

        if cdict.get("restore_config_list") and not cdict.get("snapshot_config_list"):
            LOG.error(
                "No RestoreConfig found. Please add/associate a RestoreConfig with the SnapshotConfig(s)."
            )
            sys.exit("Missing snapshot configs")

        if cdict.get("snapshot_config_list") and not cdict.get("restore_config_list"):
            LOG.error(
                "No snapshot config found. Cannot use RestoreConfig without a SnapshotConfig."
            )
            sys.exit("Missing restore configs")
        for config in cdict.get("patch_list", []):
            if not isinstance(config, PatchConfigSpecType):
                LOG.error(
                    "{} is not an object of PatchConfig. patch_config is an array of PatchConfig objects".format(
                        config
                    )
                )
                sys.exit("{} is not an instance of PatchConfig".format(config))
            config = set_config_type_based_on_target(config, "patch")

        for config in cdict.get("restore_config_list", []):
            if not isinstance(config, RestoreConfigSpecType):
                LOG.error(
                    "{} is not an object of RestoreConfig. restore_configs is an array of AppProtection.RestoreConfig objects".format(
                        config
                    )
                )
                sys.exit("{} is not an instance of RestoreConfig".format(config))
            config = set_config_type_based_on_target(config, "restore")
            a_name = get_config_action_name(config, "restore")
            config_action = create_config_action_if_not_present(a_name, config)
            if config_action:
                cdict["action_list"].append(config_action)

        for config in cdict.get("snapshot_config_list", []):
            if not isinstance(config, SnapshotConfigSpecType):
                LOG.error(
                    "{} is not an object of SnapshotConfig. snapshot_configs is an array of AppProtection.SnapshotConfig objects".format(
                        config
                    )
                )
                sys.exit("{} is not an instance of SnapshotConfig".format(config))
            config = set_config_type_based_on_target(config, "snapshot")
            if not config.config_references:
                config.config_references = [ref(cdict["restore_config_list"][0])]
            a_name = get_config_action_name(config, "snapshot")
            config_action = create_config_action_if_not_present(a_name, config)
            if config_action:
                cdict["action_list"].append(config_action)

            # Set app_protection_policy, app_protection_rule references in corresponding restore config's attrs_list[0]
            app_protection_policy_ref = config.attrs_list[0].get(
                "app_protection_policy_reference", None
            )
            app_protection_rule_ref = config.attrs_list[0].get(
                "app_protection_rule_reference", None
            )
            if app_protection_policy_ref and app_protection_rule_ref:
                for restore_config_ref in config.config_references:
                    restore_config = restore_config_ref.__self__
                    restore_config.attrs_list[0][
                        "app_protection_policy_reference"
                    ] = app_protection_policy_ref
                    restore_config.attrs_list[0][
                        "app_protection_rule_reference"
                    ] = app_protection_rule_ref

        environments = cdict.pop("environment_reference_list", [])
        if len(environments) > 1:
            LOG.error("Multiple environments are not allowed in a profile.")
            sys.exit(-1)

        # Compile env first
        environments = [_e.get_dict() for _e in environments]
        environments = [_e["uuid"] for _e in environments]

        if environments:
            cdict["environment_reference_list"] = environments

        return cdict


class ProfileValidator(PropertyValidator, openapi_type="app_profile"):
    __default__ = None
    __kind__ = ProfileType


def profile(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return ProfileType(name, bases, kwargs)


Profile = profile()
